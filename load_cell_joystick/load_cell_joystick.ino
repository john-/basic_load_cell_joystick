// load_cell_joystick.ino - 3-DOF load-cell flight stick (Phase 1), per SPECIFICATION.md.
//
// Board: SparkFun Pro Micro 3.3V/8MHz (ATmega32U4).
// Libraries: Wire, EEPROM, Joystick v2.1.1 (Matthew Heironimus).
//
// Cooperative superloop: no delay() in the control path, DRDY is polled each
// pass, button scan runs on its own 5 ms tick.
//
// States (§4.7): BOOT -> BUS_SCAN -> TARE -> RUN, FAULT reachable from anywhere.

#include <Wire.h>
#include <EEPROM.h>
#include <Joystick.h>

#include "config.h"
#include "ads122c04.h"
#include "calibration.h"
#include "decoupling.h"
#include "switches.h"

// ============================================================ Types / globals

enum State : uint8_t { ST_BOOT, ST_BUS_SCAN, ST_TARE, ST_RUN, ST_FAULT };
enum UiMode : uint8_t { UI_NONE, UI_CAL, UI_BENCH };
enum CalStep : uint8_t { CS_TARE_WAIT, CS_TARE_AVG, CS_PITCH, CS_ROLL, CS_Z };
enum BenchStep : uint8_t { BS_BASE_WAIT, BS_BASE_AVG, BS_CELL_WAIT, BS_CELL_AVG, BS_CONFIRM };
enum AcqResult : uint8_t { ACQ_BUSY, ACQ_FRAME, ACQ_FAIL };

Joystick_ Joystick(JOYSTICK_DEFAULT_REPORT_ID, JOYSTICK_TYPE_JOYSTICK,
                   NUM_SWITCHES, 0,        // buttons, hat switches
                   true, true, true,       // X (Roll), Y (Pitch), Z
                   true, true, false,      // Rx (MiniJoy X), Ry (MiniJoy Y), Rz
                   false, false, false, false, false);  // rudder, throttle, accel, brake, steering

static Ads122c04 g_adc[ADC_COUNT];
static Switches g_sw;
static CalData g_cal;
static DecoupleMatrix g_mat;
static LoadResult g_loadResult = LOAD_OK;
static bool g_calLoaded = false;

static State g_state = ST_BOOT;
static bool g_fromFault = false;       // BUS_SCAN entered from FAULT
static bool g_wasFaulted = false;
static bool g_hasTare = false;
static const __FlashStringHelper *g_faultReason = nullptr;
static uint32_t g_faultAt = 0;
static uint16_t g_retryMs = FAULT_RETRY_MIN_MS;
static uint32_t g_lastNeutralMs = 0;

// Cell data
static int32_t g_raw[CELL_COUNT];
static float g_tare[CELL_COUNT];       // working tare (RAM); EEPROM only via explicit save
static float g_cellKg[CELL_COUNT];
static bool g_warn[CELL_COUNT];
static bool g_nearLimit = false;
static bool g_overloadLatched = false; // RAM only, clears on power cycle (§4.13)
static float g_v[3];                   // decoupled Pitch, Roll, Z (pre-deadzone)
static int16_t g_axes[3];              // shaped output Pitch, Roll, Z
static bool g_stuckCheck = true;

// Acquisition
static struct {
  bool running;
  uint8_t phase;
  uint8_t pending;
  uint32_t phaseStartUs;
  uint8_t fails;
  uint32_t errors;
  uint32_t frames;
  int32_t last[CELL_COUNT];
  uint16_t same[CELL_COUNT];
} g_acq;

// Frame-rate stats
static uint32_t g_fpsWindowStart = 0;
static uint16_t g_fpsCount = 0;
static uint16_t g_fps = 0;

// Averager (tare, calibration, bench)
static struct {
  bool active;
  uint8_t skip;
  uint16_t target;
  uint16_t count;
  int32_t sum[CELL_COUNT];
} g_avg;

// Tare / gesture / auto re-zero
static bool g_tareSave = false;
static bool g_gestureActive = false;
static bool g_gestureFired = false;
static uint32_t g_gestureStart = 0;
static uint32_t g_idleSince = 0;
static uint32_t g_lastSlewMs = 0;

// Serial UI
static UiMode g_ui = UI_NONE;
#if DEBUG_LEVEL > 0
static CalStep g_calStep = CS_TARE_WAIT;
static BenchStep g_benchStep = BS_BASE_WAIT;
static uint8_t g_benchCell = 0;
static float g_filt = 0.0f;
static float g_peak[3];                // signed value at peak magnitude per axis
static float g_benchBase[CELL_COUNT];
static float g_benchDelta[CELL_COUNT];
static bool g_serialWasUp = false;
static char g_prevKey = 0;
#endif
#if DEBUG_LEVEL == 2
static uint32_t g_lastStatusMs = 0;
#endif
#if DEBUG_LEVEL >= 3
static uint8_t g_streamCount = 0;
#endif

// Prototypes (kept explicit so the sketch also builds outside the Arduino IDE)
static void enterFault(uint32_t now, const __FlashStringHelper *why);
static void sendHid();
static void requestTare(bool save);
static void uiAbort();
static void handleSerial();

// ================================================================ Helpers

static inline void ledWrite(bool on) { digitalWrite(OVERLOAD_LED_PIN, on ? LOW : HIGH); }  // active low

static void setupI2c() {
  Wire.begin();
  TWBR = I2C_TWBR;   // 222 kHz at 8 MHz, prescaler 1 (Wire.begin() leaves it at 100 kHz)
#if defined(WIRE_HAS_TIMEOUT)
  Wire.setWireTimeout(I2C_WIRE_TIMEOUT_US, true);
#endif
}

// Clock SCL 9 times to free any slave stuck holding SDA low before re-initializing Wire.
static void recoverI2cBus() {
  pinMode(I2C_SDA_PIN, INPUT_PULLUP);
  pinMode(I2C_SCL_PIN, OUTPUT);
  for (uint8_t i = 0; i < 9; i++) {
    digitalWrite(I2C_SCL_PIN, HIGH);
    delayMicroseconds(5);
    digitalWrite(I2C_SCL_PIN, LOW);
    delayMicroseconds(5);
  }
  // Generate a STOP condition: SCL high while SDA transitions LOW to HIGH
  pinMode(I2C_SDA_PIN, OUTPUT);
  digitalWrite(I2C_SDA_PIN, LOW);
  delayMicroseconds(5);
  digitalWrite(I2C_SCL_PIN, HIGH);
  delayMicroseconds(5);
  digitalWrite(I2C_SDA_PIN, HIGH);
  delayMicroseconds(5);
  pinMode(I2C_SDA_PIN, INPUT_PULLUP);
  pinMode(I2C_SCL_PIN, INPUT_PULLUP);
}

static void hwReset() {
#if USE_HW_RESET
  digitalWrite(ADC_RST_PIN, LOW);
  delayMicroseconds(100);                 // datasheet minimum is 250 ns
  digitalWrite(ADC_RST_PIN, HIGH);
  delayMicroseconds(100);
#endif
}

static uint8_t initialMux(uint8_t adc) {
  for (uint8_t c = 0; c < CELL_COUNT; c++)
    if (CELLS[c].adc == adc && CELLS[c].phase == 0) return CELLS[c].mux;
  return MUX_AIN0_AIN1;
}

static bool adcInit(uint8_t a) {
  uint8_t mux = initialMux(a);
  return g_adc[a].reset() && g_adc[a].configure(mux) && g_adc[a].verify(mux);
}

static bool adcReady(uint8_t a) {
#if USE_DRDY_PINS
  return digitalRead(DRDY_PINS[a]) == LOW;
#else
  bool r = false;
  return g_adc[a].drdyBit(r) && r;
#endif
}

// ============================================================== Averaging

static void avgStart(uint16_t n, uint8_t skip) {
  g_avg.active = true;
  g_avg.skip = skip;
  g_avg.target = n;
  g_avg.count = 0;
  for (uint8_t i = 0; i < CELL_COUNT; i++) g_avg.sum[i] = 0;
}

// Feed one frame. Returns true when the requested number of frames is in.
static bool avgAddFrame() {
  if (!g_avg.active) return false;
  if (g_avg.skip) { g_avg.skip--; return false; }
  for (uint8_t i = 0; i < CELL_COUNT; i++) g_avg.sum[i] += g_raw[i];   // 64 * 2^23 fits int32
  if (++g_avg.count >= g_avg.target) { g_avg.active = false; return true; }
  return false;
}

static float avgMean(uint8_t i) { return (float)g_avg.sum[i] / (float)g_avg.count; }

static void avgToTare() {
  for (uint8_t i = 0; i < CELL_COUNT; i++) g_tare[i] = avgMean(i);
  g_idleSince = g_lastSlewMs = millis();
}

// ============================================================ Acquisition
// Two phases per frame (§4.2/§4.5). Per phase: WREG MUX (if changed) -> START/SYNC ->
// wait for DRDY -> RDATA. Fully non-blocking: each loop() pass just checks DRDY.

static void acqReset() {
  g_acq.running = false;
  g_acq.phase = 0;
  g_acq.pending = 0;
  g_acq.fails = 0;
  g_faultReason = nullptr;
  for (uint8_t i = 0; i < CELL_COUNT; i++) { g_acq.same[i] = 0; g_acq.last[i] = 0x7FFFFFFF; }
}

static AcqResult acqFail() {
  g_acq.errors++;
  g_acq.running = false;
  g_acq.pending = 0;
  if (!g_faultReason) g_faultReason = F("I2C communication failure");
  if (++g_acq.fails >= MAX_CONSECUTIVE_FRAME_FAILS) return ACQ_FAIL;
  return ACQ_BUSY;     // try the frame again
}

static bool acqBeginPhase() {
  g_acq.pending = 0;
  // Select all muxes first, then start the chips back to back so they convert in parallel.
  for (uint8_t c = 0; c < CELL_COUNT; c++) {
    if (CELLS[c].phase != g_acq.phase) continue;
    uint8_t a = CELLS[c].adc;
    if (adcReady(a)) { int32_t dummy; g_adc[a].readData(dummy); }   // flush any stale result
    if (!g_adc[a].setMux(CELLS[c].mux)) return false;
  }
  for (uint8_t c = 0; c < CELL_COUNT; c++) {
    if (CELLS[c].phase != g_acq.phase) continue;
    if (!g_adc[CELLS[c].adc].startSync()) return false;
    g_acq.pending |= (uint8_t)(1 << c);
  }
  g_acq.phaseStartUs = micros();
  return true;
}

static AcqResult acqService() {
  if (!g_acq.running) {
    g_acq.phase = 0;
    if (!acqBeginPhase()) return acqFail();
    g_acq.running = true;
    return ACQ_BUSY;
  }

  for (uint8_t c = 0; c < CELL_COUNT; c++) {
    if (!(g_acq.pending & (1 << c))) continue;
    if (!adcReady(CELLS[c].adc)) continue;
    int32_t v;
    if (!g_adc[CELLS[c].adc].readData(v)) return acqFail();
    g_raw[c] = v;
    g_acq.pending &= (uint8_t)~(1 << c);
    if (v == g_acq.last[c]) { if (g_acq.same[c] < 0xFFFF) g_acq.same[c]++; }
    else g_acq.same[c] = 0;
    g_acq.last[c] = v;
  }

  if (g_acq.pending == 0) {
    if (++g_acq.phase < ACQ_PHASES) {
      if (!acqBeginPhase()) return acqFail();
      return ACQ_BUSY;
    }
    g_acq.running = false;
    g_acq.fails = 0;
    g_acq.frames++;
    if (g_stuckCheck) {
      for (uint8_t c = 0; c < CELL_COUNT; c++) {
        if (g_acq.same[c] >= STUCK_FRAMES) {
          g_acq.same[c] = 0;
          g_faultReason = F("ADC result stuck");
          return ACQ_FAIL;
        }
      }
    }
    return ACQ_FRAME;
  }

  if ((uint32_t)(micros() - g_acq.phaseStartUs) > ADC_PHASE_TIMEOUT_US) {
    g_faultReason = F("DRDY timeout");
    return acqFail();
  }
  return ACQ_BUSY;
}

// Evaluates per-cell |raw - working_tare| in kg for overload BEFORE auto re-zero
// slew, and projects decoupled Pitch, Roll, Z in one pass (§4.2, §4.3, §4.13).
static void checkOverloadAndDecouple() {
  float N[CELL_COUNT];
  bool near = false;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    float n = ((float)g_raw[i] - g_tare[i]) * g_cal.span[i];
    N[i] = n;
    float kg = fabsf(n) / COUNTS_PER_KG_NOMINAL;
    g_cellKg[i] = kg;
    if (kg >= OVERLOAD_EVENT_KG) g_overloadLatched = true;
    if (kg >= OVERLOAD_WARN_KG) g_warn[i] = true;
    else if (kg < OVERLOAD_WARN_KG - OVERLOAD_HYST_KG) g_warn[i] = false;
    if (g_warn[i]) near = true;
  }
  g_nearLimit = near;
  decouple(g_mat, N, g_v);
}

static void updateAutoRezero(uint32_t now) {
#if REZERO_ENABLED
  bool idle = true;
  for (uint8_t a = 0; a < 3; a++)
    if (fabsf(g_v[a]) > g_cal.rezeroIdleFrac * g_cal.deadzone[a]) idle = false;
  if (!idle || (uint32_t)(now - g_idleSince) < g_cal.rezeroIdleMs) {
    if (!idle) g_idleSince = now;
    g_lastSlewMs = now;
    return;
  }
  float step = g_cal.rezeroSlewCps * (float)(now - g_lastSlewMs) * 0.001f;
  g_lastSlewMs = now;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    float d = (float)g_raw[i] - g_tare[i];
    if (d > step) d = step;
    else if (d < -step) d = -step;
    g_tare[i] += d;     // RAM only - never written to EEPROM
  }
#else
  (void)now;
#endif
}

// ===================================================================== HID

// Mini-joystick conditioned axes (Rx, Ry)
static int16_t g_minijoy[2] = {0, 0};

static void readMiniJoy() {
  int16_t rawA = analogRead(MINIJOY_PIN_XOUT);
  int16_t rawB = analogRead(MINIJOY_PIN_YOUT);

  int16_t physX = SWAP_MINIJOY_AXES ? rawB : rawA;
  int16_t physY = SWAP_MINIJOY_AXES ? rawA : rawB;

  int16_t devX = physX - MINIJOY_CENTER_RAW;
  if (abs(devX) <= MINIJOY_DEADZONE_RAW) devX = 0;
  else devX = (devX > 0) ? (devX - MINIJOY_DEADZONE_RAW) : (devX + MINIJOY_DEADZONE_RAW);

  int16_t devY = physY - MINIJOY_CENTER_RAW;
  if (abs(devY) <= MINIJOY_DEADZONE_RAW) devY = 0;
  else devY = (devY > 0) ? (devY - MINIJOY_DEADZONE_RAW) : (devY + MINIJOY_DEADZONE_RAW);

  int32_t span = 512 - MINIJOY_DEADZONE_RAW;
  int32_t sX = ((int32_t)devX * HID_AXIS_MAX) / span;
  int32_t sY = ((int32_t)devY * HID_AXIS_MAX) / span;

  int16_t outX = (int16_t)constrain(sX, -HID_AXIS_MAX, HID_AXIS_MAX);
  int16_t outY = (int16_t)constrain(sY, -HID_AXIS_MAX, HID_AXIS_MAX);

  g_minijoy[0] = INVERT_MINIJOY_X ? (int16_t)-outX : outX;
  g_minijoy[1] = INVERT_MINIJOY_Y ? (int16_t)-outY : outY;
}

static uint8_t hidButtons() {
  if (g_state == ST_FAULT) return 0;
  uint8_t b = g_sw.state();
  if (g_gestureActive) b &= (uint8_t)~GESTURE_MASK;   // masked while the re-tare gesture is held
  return b;
}

static void sendHid() {
  readMiniJoy();
  int16_t pitch = g_axes[AX_PITCH];
  Joystick.setXAxis(g_axes[AX_ROLL]);
  Joystick.setYAxis(INVERT_Y_HID ? (int16_t)-pitch : pitch);   // forward = negative Y
  Joystick.setZAxis(g_axes[AX_Z]);
  Joystick.setRxAxis(g_minijoy[0]);
  Joystick.setRyAxis(g_minijoy[1]);
  uint8_t b = hidButtons();
  for (uint8_t i = 0; i < NUM_SWITCHES; i++) Joystick.setButton(i, (b >> i) & 1);
  Joystick.sendState();
}

static void sendNeutral() {
  g_axes[AX_PITCH] = g_axes[AX_ROLL] = g_axes[AX_Z] = 0;
  g_minijoy[0] = g_minijoy[1] = 0;
  sendHid();
}

// =================================================================== Fault

static void enterFault(uint32_t now, const __FlashStringHelper *why) {
  if (why) g_faultReason = why;
  if (g_wasFaulted) {
    g_retryMs = (g_retryMs >= FAULT_RETRY_MAX_MS / 2) ? FAULT_RETRY_MAX_MS : (uint16_t)(g_retryMs * 2);
  } else {
    g_retryMs = FAULT_RETRY_MIN_MS;
  }
  g_wasFaulted = true;
  g_state = ST_FAULT;
  g_faultAt = now;
  uiAbort();
  g_avg.active = false;
  g_stuckCheck = true;
  sendNeutral();     // centre axes, release buttons
  g_lastNeutralMs = now;
  LOGP(F("[FAULT] "));
  LOGP(g_faultReason ? g_faultReason : F("unknown"));
  LOGP(F("; retry in "));
  LOGP(g_retryMs);
  LOGLN(F(" ms"));
}

static void stateFault(uint32_t now) {
  if ((uint32_t)(now - g_lastNeutralMs) >= 100) { sendNeutral(); g_lastNeutralMs = now; }
  if ((uint32_t)(now - g_faultAt) >= g_retryMs) {
    g_fromFault = true;
    g_state = ST_BUS_SCAN;
  }
}

// ================================================================ BUS_SCAN

static void stateBusScan(uint32_t now) {
  if (g_fromFault) {
    Wire.end();
    recoverI2cBus();
    setupI2c();
    hwReset();
  }

  bool ok = true;
  for (uint8_t a = 0; a < ADC_COUNT; a++) {
    if (!g_adc[a].probe()) {
      LOGP(F("[SCAN] no ACK from 0x"));
      LOGLN(ADC_ADDR[a], HEX);
      ok = false;
    }
  }
  for (uint8_t a = 0; ok && a < ADC_COUNT; a++) {
    if (!adcInit(a)) {
      LOGP(F("[SCAN] init/verify failed on 0x"));
      LOGLN(ADC_ADDR[a], HEX);
      ok = false;
    }
  }
  if (!ok) { enterFault(now, F("ADC missing or unresponsive")); return; }

  if (!g_calLoaded) {
    g_loadResult = calLoad(g_cal);
    g_calLoaded = true;
    for (uint8_t i = 0; i < CELL_COUNT; i++) g_tare[i] = g_cal.tare[i];
    buildMatrix(g_mat);
    if (g_loadResult == LOAD_INVALID)
      LOGLN(F("[WARN] EEPROM invalid - running with defaults, calibration needed"));
    else if (g_loadResult == LOAD_GEOMETRY)
      LOGLN(F("[WARN] EEPROM geometry differs from config.h - running with defaults, calibration needed"));
  }

  acqReset();
  g_wasFaulted = false;
  g_retryMs = FAULT_RETRY_MIN_MS;
  LOGLN(F("[SCAN] both ADCs OK"));

  if (g_fromFault && g_hasTare && !RETARE_AFTER_FAULT) {
    g_fromFault = false;
    g_state = ST_RUN;
    return;
  }
  g_fromFault = false;
  g_tareSave = false;
  avgStart(TARE_SAMPLES, TARE_SKIP_FRAMES);
  g_state = ST_TARE;
  LOGLN(F("[TARE] keep the stick untouched..."));
}

static void requestTare(bool save) {
  g_tareSave = save;
  acqReset();
  avgStart(TARE_SAMPLES, TARE_SKIP_FRAMES);
  g_state = ST_TARE;
  LOGLN(F("[TARE] keep the stick untouched..."));
}

// ================================================================== Frames

static void finishTare() {
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    if (fabsf(avgMean(i)) >= 8388000.0f) {
      LOGP(F("[TARE] cell ")); LOGP(i); LOGLN(F(" pegged at rail limit!"));
      enterFault(millis(), F("ADC channel railed at boot"));
      return;
    }
  }
  avgToTare();
  g_overloadLatched = false;
  g_nearLimit = false;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    g_cellKg[i] = 0.0f;
    g_warn[i] = false;
  }
  g_hasTare = true;
  if (g_tareSave) {
    for (uint8_t i = 0; i < CELL_COUNT; i++) g_cal.tare[i] = g_tare[i];
    calSave(g_cal);
    g_loadResult = LOAD_OK;
    LOGLN(F("[TARE] done, saved to EEPROM"));
  } else {
    LOGLN(F("[TARE] done"));
  }
  g_tareSave = false;
  g_state = ST_RUN;
}

#if DEBUG_LEVEL > 0
static void uiFrame(uint32_t now);
#endif

static void debugFrame(uint32_t now) {
#if DEBUG_LEVEL >= 3
  if (++g_streamCount >= DEBUG_STREAM_DECIMATION) {
    g_streamCount = 0;
    if (serialConnected()) {
      for (uint8_t i = 0; i < CELL_COUNT; i++) {
        Serial.print('N'); Serial.print(i); Serial.print(':');
        Serial.print((long)((float)g_raw[i] - g_tare[i])); Serial.print(',');
      }
      Serial.print(F("Pitch:")); Serial.print((long)g_v[AX_PITCH]);
      Serial.print(F(",Roll:")); Serial.print((long)g_v[AX_ROLL]);
      Serial.print(F(",Z:")); Serial.println((long)g_v[AX_Z]);
    }
  }
#elif DEBUG_LEVEL >= 2
  if ((uint32_t)(now - g_lastStatusMs) >= DEBUG_STATUS_MS) {
    g_lastStatusMs = now;
    if (serialConnected()) {
      Serial.print(F("[STAT] fps=")); Serial.print(g_fps);
      Serial.print(F(" P=")); Serial.print((long)g_v[AX_PITCH]);
      Serial.print(F(" R=")); Serial.print((long)g_v[AX_ROLL]);
      Serial.print(F(" Z=")); Serial.print((long)g_v[AX_Z]);
      Serial.print(F(" kg="));
      for (uint8_t i = 0; i < CELL_COUNT; i++) { Serial.print(g_cellKg[i], 2); Serial.print(' '); }
      Serial.print(F(" warn=")); Serial.print(g_nearLimit);
      Serial.print(F(" ovl=")); Serial.println(g_overloadLatched);
    }
  }
#else
  (void)now;
#endif
}

static void onRunFrame(uint32_t now) {
  checkOverloadAndDecouple();  // 1. overload check & 2. decouple in one pass

#if DEBUG_LEVEL > 0
  if (g_ui != UI_NONE) {    // guided calibration / bench test: axes held neutral
    uiFrame(now);
    sendNeutral();
    debugFrame(now);
    return;
  }
#endif

  updateAutoRezero(now);    // 3. only after the overload check
  for (uint8_t a = 0; a < 3; a++)
    g_axes[a] = shapeAxis(g_v[a], g_cal.deadzone[a], g_cal.axisScale[a]);
  sendHid();
  debugFrame(now);
}

static void onFrame(uint32_t now) {
  if (now - g_fpsWindowStart >= 1000) { g_fps = g_fpsCount; g_fpsCount = 0; g_fpsWindowStart = now; }
  g_fpsCount++;

  if (g_state == ST_TARE) {
    if (avgAddFrame()) finishTare();
    sendNeutral();
  } else if (g_state == ST_RUN) {
    onRunFrame(now);
  }
}

static void serviceAcquisition(uint32_t now) {
  AcqResult r = acqService();
  if (r == ACQ_FAIL) {
    enterFault(now, g_faultReason ? g_faultReason : F("ADC acquisition failed"));
    return;
  }
  if (r == ACQ_FRAME) onFrame(now);
}

// ========================================================= Gesture / LED

static void updateGesture(uint32_t now) {
  bool combo = (g_sw.state() & GESTURE_MASK) == GESTURE_MASK;
  if (!combo) { g_gestureActive = false; g_gestureFired = false; return; }
  if (g_state != ST_RUN || g_ui != UI_NONE) return;

  if (!g_gestureActive) {
    g_gestureActive = true;
    g_gestureStart = now;
  }

  // Stick must be centered to advance the re-tare hold timer (§4.8)
  bool centered = true;
  for (uint8_t a = 0; a < 3; a++) {
    if (fabsf(g_v[a]) > 2.0f * g_cal.deadzone[a]) centered = false;
  }
  if (!centered) {
    g_gestureStart = now;   // reset hold timer if deflected under load
    return;
  }

  if (!g_gestureFired && (uint32_t)(now - g_gestureStart) >= GESTURE_HOLD_MS) {
    g_gestureFired = true;
    requestTare(true);      // same as serial 't': RAM + EEPROM
  }
}

static void updateLed(uint32_t now) {
  bool on;
  if (g_state == ST_FAULT) on = ((now / LED_FAULT_HALF_PERIOD_MS) & 1) == 0;
  else if (g_overloadLatched) on = ((now / LED_OVERLOAD_HALF_PERIOD_MS) & 1) == 0;   // 4 Hz flash
  else on = g_nearLimit;                                                              // solid
  ledWrite(on);
}

// ============================================================== Serial UI
#if DEBUG_LEVEL > 0

static void printF(float v, uint8_t d) { LOGP(v, d); }

static void printBanner() {
  LOGP(F("\nload_cell_joystick v")); LOGLN(F(FW_VERSION));
  LOGLN(F("Release the stick at power-up (boot tare). Commands: t=tare c=calibrate b=bench d=dump"));
  if (g_loadResult == LOAD_INVALID)
    LOGLN(F("[WARN] EEPROM invalid - running with defaults, calibration needed"));
  else if (g_loadResult == LOAD_GEOMETRY)
    LOGLN(F("[WARN] EEPROM geometry differs from config.h - running with defaults"));
}

static void printDump() {
  static const char *const names[] = {"INIT", "SCAN", "TARE", "RUN", "FAULT"};
  LOGP(F("state=")); LOGP(names[g_state]);
  LOGP(F(" fps=")); LOGP(g_fps);
  LOGP(F(" errors=")); LOGP((unsigned long)g_acq.errors);
  LOGP(F(" eeprom=")); LOGLN(g_loadResult == LOAD_OK ? F("ok") : F("defaults"));
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    LOGP(F(" cell")); LOGP(i);
    LOGP(F(" raw=")); LOGP((long)g_raw[i]);
    LOGP(F(" tare=")); printF(g_tare[i], 1);
    LOGP(F(" span=")); printF(g_cal.span[i], 4);
    LOGP(F(" kg=")); printF(g_cellKg[i], 3);
    LOGP(F(" warn=")); LOGLN(g_warn[i]);
  }
  LOGP(F(" Pitch=")); printF(g_v[AX_PITCH], 0);
  LOGP(F(" Roll=")); printF(g_v[AX_ROLL], 0);
  LOGP(F(" Z=")); printF(g_v[AX_Z], 0); LOGLN();
  LOGP(F(" deadzone P/R/Z=")); printF(g_cal.deadzone[0], 0); LOGP('/');
  printF(g_cal.deadzone[1], 0); LOGP('/'); printF(g_cal.deadzone[2], 0);
  LOGP(F("  axis_scale P/R/Z=")); printF(g_cal.axisScale[0], 0); LOGP('/');
  printF(g_cal.axisScale[1], 0); LOGP('/'); printF(g_cal.axisScale[2], 0); LOGLN();
  LOGP(F(" near_limit=")); LOGP(g_nearLimit);
  LOGP(F(" overload_latched=")); LOGLN(g_overloadLatched);
}

static void calPrompt() {
  switch (g_calStep) {
    case CS_TARE_WAIT: LOGLN(F("[CAL] Step 0: ensure stick is untouched at rest. Press Enter.")); break;
    case CS_PITCH: LOGLN(F("[CAL] Step 1: push stick FORWARD with the max force you want for full Pitch, hold 1 s, release. Press Enter when done.")); break;
    case CS_ROLL:  LOGLN(F("[CAL] Step 2: push stick RIGHT with the max force you want for full Roll, hold 1 s, release. Press Enter when done.")); break;
    case CS_Z:     LOGLN(F("[CAL] Step 3: pull UP (or push down) with the max force you want for full Z, hold 1 s, release. Press Enter when done.")); break;
    default: break;
  }
}

static void benchPrompt() {
  if (g_benchStep == BS_BASE_WAIT) {
    LOGLN(F("[BENCH] Step 1: top plate OFF, no load on any cell. Press Enter for unloaded baseline."));
  } else if (g_benchStep == BS_CELL_WAIT) {
    if (g_benchCell > 0) LOGLN(F("[BENCH] (Remove previous test weight first)"));
    LOGP(F("[BENCH] Place ")); LOGP(BENCH_TEST_WEIGHT_G);
    LOGP(F(" g on the free M4 tip of Cell ")); LOGP(g_benchCell);
    LOGLN(F(". Press Enter."));
  }
}

static void uiAbort() {
  if (g_ui != UI_NONE) LOGLN(F("[UI] aborted, nothing saved"));
  g_ui = UI_NONE;
  g_avg.active = false;
  g_stuckCheck = true;
}

static void startCal() {
  if (g_state != ST_RUN || g_ui != UI_NONE) { LOGLN(F("[CAL] busy")); return; }
  g_ui = UI_CAL;
  g_calStep = CS_TARE_WAIT;
  LOGLN(F("[CAL] (q aborts)"));
  calPrompt();
}

static void startBench() {
  if (g_state != ST_RUN || g_ui != UI_NONE) { LOGLN(F("[BENCH] busy")); return; }
  g_ui = UI_BENCH;
  g_benchStep = BS_BASE_WAIT;
  g_benchCell = 0;
  g_stuckCheck = false;      // a pegged/constant channel is a finding here, not a fault
  LOGLN(F("[BENCH] (q aborts)"));
  benchPrompt();
}

static void calFinish() {
  static const char *const nm[3] = {"Pitch", "Roll", "Z"};
  bool ok = true;
  for (uint8_t a = 0; a < 3; a++) {
    if (fabsf(g_peak[a]) <= g_cal.deadzone[a]) {
      LOGP(F("[CAL] ")); LOGP(nm[a]); LOGLN(F(" peak is inside its deadzone - rejected"));
      ok = false;
    }
  }
  if (!ok) { LOGLN(F("[CAL] nothing saved")); g_ui = UI_NONE; return; }
  for (uint8_t a = 0; a < 3; a++) g_cal.axisScale[a] = fabsf(g_peak[a]);
  for (uint8_t i = 0; i < CELL_COUNT; i++) g_cal.tare[i] = g_tare[i];
  calSave(g_cal);
  g_loadResult = LOAD_OK;
  LOGP(F("[CAL] saved. axis_scale P/R/Z="));
  printF(g_cal.axisScale[0], 0); LOGP('/'); printF(g_cal.axisScale[1], 0); LOGP('/');
  printF(g_cal.axisScale[2], 0); LOGLN();
  g_ui = UI_NONE;
}

static void calKey(bool enter) {
  if (!enter) return;
  switch (g_calStep) {
    case CS_TARE_WAIT:
      avgStart(TARE_SAMPLES, TARE_SKIP_FRAMES);
      g_calStep = CS_TARE_AVG;
      break;
    case CS_PITCH:
    case CS_ROLL: {
      uint8_t a = (g_calStep == CS_PITCH) ? AX_PITCH : AX_ROLL;
      LOGP(F("[CAL] peak = ")); printF(g_peak[a], 0); LOGLN();
      if (a == AX_PITCH && g_peak[a] < 0.0f)
        LOGLN(F("[WARN] forward push read NEGATIVE Pitch - check cell sign / INVERT_PITCH (§4.2)"));
      if (a == AX_ROLL && g_peak[a] < 0.0f)
        LOGLN(F("[WARN] right push read NEGATIVE Roll - check cell sign / INVERT_ROLL (§4.2)"));
      g_calStep = (g_calStep == CS_PITCH) ? CS_ROLL : CS_Z;
      g_filt = 0.0f; g_peak[g_calStep == CS_ROLL ? AX_ROLL : AX_Z] = 0.0f;
      calPrompt();
      break;
    }
    case CS_Z:
      LOGP(F("[CAL] peak = ")); printF(g_peak[AX_Z], 0); LOGLN();
      calFinish();
      break;
    default: break;
  }
}

static void benchFinish(bool store) {
  g_ui = UI_NONE;
  g_stuckCheck = true;
  if (!store) { LOGLN(F("[BENCH] discarded, nothing saved")); return; }
  const float expected = COUNTS_PER_KG_NOMINAL * (float)BENCH_TEST_WEIGHT_G / 1000.0f;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    float ratio = g_benchDelta[i] / expected;
    if (g_benchDelta[i] > 0.0f && ratio > 0.5f && ratio < 2.0f) g_cal.span[i] = expected / g_benchDelta[i];
    else { g_cal.span[i] = 1.0f; LOGP(F("[BENCH] cell ")); LOGP(i); LOGLN(F(" implausible, Span left at 1.0")); }
  }
  calSave(g_cal);
  g_loadResult = LOAD_OK;
  LOGLN(F("[BENCH] Span_i saved to EEPROM"));
}

static void benchKey(char ch, bool enter) {
  if (g_benchStep == BS_BASE_WAIT && enter) {
    avgStart(TARE_SAMPLES, BENCH_SETTLE_FRAMES);
    g_benchStep = BS_BASE_AVG;
  } else if (g_benchStep == BS_CELL_WAIT && enter) {
    avgStart(TARE_SAMPLES, BENCH_SETTLE_FRAMES);
    g_benchStep = BS_CELL_AVG;
  } else if (g_benchStep == BS_CONFIRM) {
    if (ch == 'y' || ch == 'Y') benchFinish(true);
    else if (ch == 'n' || ch == 'N') benchFinish(false);
  }
}

// Called once per frame while a guided session is active.
static void uiFrame(uint32_t now) {
  (void)now;
  if (g_ui == UI_CAL) {
    if (g_calStep == CS_TARE_AVG) {
      if (avgAddFrame()) {
        avgToTare();
        g_calStep = CS_PITCH;
        g_filt = 0.0f; g_peak[AX_PITCH] = 0.0f;
        calPrompt();
      }
    } else if (g_calStep >= CS_PITCH) {
      uint8_t a = (uint8_t)(g_calStep - CS_PITCH);   // CS_PITCH/ROLL/Z map to axes 0/1/2
      g_filt += 0.25f * (g_v[a] - g_filt);            // light smoothing so noise spikes don't set the peak
      if (fabsf(g_filt) > fabsf(g_peak[a])) g_peak[a] = g_filt;
    }
  } else if (g_ui == UI_BENCH) {
    if (g_benchStep == BS_BASE_AVG) {
      if (avgAddFrame()) {
        LOGLN(F("[BENCH] unloaded baseline (raw counts):"));
        for (uint8_t i = 0; i < CELL_COUNT; i++) {
          g_benchBase[i] = avgMean(i);
          LOGP(F("  cell ")); LOGP(i); LOGP(F(": ")); printF(g_benchBase[i], 0);
          if (fabsf(g_benchBase[i]) > 8388000.0f) LOGP(F("  PEGGED at rail!"));
          LOGLN();
        }
        g_benchCell = 0;
        g_benchStep = BS_CELL_WAIT;
        benchPrompt();
      }
    } else if (g_benchStep == BS_CELL_AVG) {
      if (avgAddFrame()) {
        const float expected = COUNTS_PER_KG_NOMINAL * (float)BENCH_TEST_WEIGHT_G / 1000.0f;
        float delta = avgMean(g_benchCell) - g_benchBase[g_benchCell];
        g_benchDelta[g_benchCell] = delta;
        float ratio = delta / expected;
        LOGP(F("[BENCH] cell ")); LOGP(g_benchCell);
        LOGP(F(": delta=")); printF(delta, 0);
        LOGP(F(" expected=")); printF(expected, 0);
        LOGP(F(" ratio=")); printF(ratio, 3);
        if (delta <= 0.0f) LOGLN(F("  POLARITY WRONG (bending down should increase count)"));
        else if (fabsf(ratio - 1.0f) <= BENCH_TOLERANCE) LOGLN(F("  OK"));
        else LOGLN(F("  outside tolerance"));
        if (++g_benchCell >= CELL_COUNT) {
          g_benchStep = BS_CONFIRM;
          LOGLN(F("[BENCH] Remove test weight."));
          LOGLN(F("[BENCH] Store Span_i = expected/observed to EEPROM? (y/n)"));
        } else {
          g_benchStep = BS_CELL_WAIT;
          benchPrompt();
        }
      }
    }
  }
}

static void uiKey(char ch) {
  bool enter = (ch == '\n' || ch == '\r');
  if (ch == '\n' && g_prevKey == '\r') { g_prevKey = ch; return; }   // swallow LF of a CRLF pair
  g_prevKey = ch;

  if (g_ui == UI_NONE) {
    switch (ch) {
      case 't': if (g_state == ST_RUN) requestTare(true); else LOGLN(F("busy")); break;
      case 'c': startCal(); break;
      case 'b': startBench(); break;
      case 'd': printDump(); break;
      default:  if (!enter) LOGLN(F("commands: t=tare c=calibrate b=bench d=dump")); break;
    }
    return;
  }
  if (ch == 'q' || ch == 'Q') { uiAbort(); return; }
  if (g_ui == UI_CAL) calKey(enter);
  else benchKey(ch, enter);
}

static void handleSerial() {
  bool up = serialConnected();
  if (up && !g_serialWasUp) printBanner();   // boot banner is usually lost; re-send on connect
  g_serialWasUp = up;
  if (!up) return;
  while (Serial.available()) uiKey((char)Serial.read());
}

#else   // DEBUG_LEVEL 0: all serial code compiled out

static void uiAbort() { g_ui = UI_NONE; g_avg.active = false; g_stuckCheck = true; }
static void handleSerial() {}

#endif

// ================================================================ Arduino

void setup() {
  pinMode(OVERLOAD_LED_PIN, OUTPUT);
  ledWrite(false);
  for (uint8_t a = 0; a < ADC_COUNT; a++) pinMode(DRDY_PINS[a], INPUT_PULLUP);   // DRDY is open-drain
#if USE_HW_RESET
  pinMode(ADC_RST_PIN, OUTPUT);
  digitalWrite(ADC_RST_PIN, HIGH);
#endif
  g_sw.begin();
  setupI2c();
  for (uint8_t a = 0; a < ADC_COUNT; a++) g_adc[a].begin(ADC_ADDR[a]);

  Joystick.setXAxisRange(-HID_AXIS_MAX, HID_AXIS_MAX);
  Joystick.setYAxisRange(-HID_AXIS_MAX, HID_AXIS_MAX);
  Joystick.setZAxisRange(-HID_AXIS_MAX, HID_AXIS_MAX);
  Joystick.setRxAxisRange(-HID_AXIS_MAX, HID_AXIS_MAX);
  Joystick.setRyAxisRange(-HID_AXIS_MAX, HID_AXIS_MAX);
  Joystick.begin(false);     // we call sendState() ourselves, once per frame

#if DEBUG_LEVEL > 0
  Serial.begin(115200);      // never wait for the host (§4.10)
#endif
  acqReset();
  g_state = ST_BUS_SCAN;
}

void loop() {
  uint32_t now = millis();

  bool swChanged = g_sw.update(now);
  updateGesture(now);
  if (swChanged && (g_state == ST_RUN || g_state == ST_TARE)) sendHid();   // button edge
  handleSerial();

  switch (g_state) {
    case ST_BUS_SCAN: stateBusScan(now); break;
    case ST_TARE:
    case ST_RUN:      serviceAcquisition(now); break;
    case ST_FAULT:    stateFault(now); break;
    default: break;
  }
  updateLed(now);
}
