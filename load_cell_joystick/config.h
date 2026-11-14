// config.h - pin map, ADC settings, cell geometry and all tunables.
// Section references (§) are to SPECIFICATION.md; "DS" is the ADS122C04
// datasheet (SBAS751B).
#ifndef CONFIG_H
#define CONFIG_H

#include <Arduino.h>

#define FW_VERSION "0.1.0"

// 0 = no serial code at all, 1 = status, 2 = verbose (1 Hz status line),
// 3 = raw sample stream for the serial plotter (§4.10).
#ifndef DEBUG_LEVEL
#define DEBUG_LEVEL 1
#endif

#if F_CPU != 8000000UL
#warning "Spec targets the Pro Micro 3.3V/8MHz; TWBR=10 only gives 222 kHz at 8 MHz."
#endif

// ---------------------------------------------------------------- Pins (§3.1)
static const uint8_t I2C_SDA_PIN = 2;
static const uint8_t I2C_SCL_PIN = 3;
static const uint8_t NUM_SWITCHES = 4;
static const uint8_t SWITCH_PINS[NUM_SWITCHES] = {4, 5, 6, 7};  // Button 1: Trigger (D4), Button 2: Left (D5), Button 3: Right (D6), Button 4: Stick Click (D7)
static const uint8_t ADC_COUNT = 2;
static const uint8_t ADC_ADDR[ADC_COUNT] = {0x40, 0x41};
static const uint8_t DRDY_PINS[ADC_COUNT] = {16, 10};  // active low, open drain

// ---------------------------------------------------- Mini-Joystick (hw-v1.1)
// Adafruit #512 analog 2-axis thumb joystick + select button.
// Physical mounting follows the orientation on the PCB silkscreen.
static const uint8_t MINIJOY_PIN_XOUT = A9;  // Pro Micro Pin 9 (SB300 Col 19 / Brown)
static const uint8_t MINIJOY_PIN_YOUT = A8;  // Pro Micro Pin 8 (SB300 Col 20 / White-Brown)

// Orientation mapping:
// Mounted following silkscreen orientation: Xout maps directly to physical X,
// and Yout maps directly to physical Y.
#define SWAP_MINIJOY_AXES   false
#define INVERT_MINIJOY_X    false
#define INVERT_MINIJOY_Y    false

static const int16_t MINIJOY_CENTER_RAW = 512;
static const int16_t MINIJOY_DEADZONE_RAW = 35; // ~3.5% deadzone around center rest

#define USE_DRDY_PINS true     // true: check physical DRDY GPIO pin; false: poll config reg 2
#define USE_HW_RESET  false   // optional shared !RST on Arduino pin 14
static const uint8_t ADC_RST_PIN = 14;

#define OVERLOAD_LED_PIN 17   // on-board RX LED, active low (§4.13)

// ------------------------------------------------------------- I2C (§4.5)
// ATmega32U4 needs TWBR >= 10 in master mode: 8 MHz / (16 + 2*10) = 222 kHz.
static const uint8_t I2C_TWBR = 10;
static const uint8_t I2C_RETRIES = 2;            // extra attempts after a NACK/short read
static const uint16_t I2C_BACKOFF_US = 200;      // doubles each retry
static const uint32_t I2C_WIRE_TIMEOUT_US = 5000;  // used only if the core has setWireTimeout()

// ------------------------------------------------- ADS122C04 settings (§4.1)
// Config0: MUX[7:4] GAIN[3:1] PGA_BYPASS[0]
// Config1: DR[7:5] MODE[4] CM[3] VREF[2:1] TS[0]
static const uint8_t ADS_GAIN = 0x07;   // 128x
static const uint8_t ADS_DR   = 0x05;   // 1000 SPS in Normal mode (2000 in Turbo)
static const uint8_t ADS_MODE = 1;      // 0 = Normal, 1 = Turbo
static const uint8_t ADS_CM   = 0;      // 0 = single-shot (required for mux round-robin)
static const uint8_t ADS_VREF = 0x01;   // external REFP/REFN (ratiometric)

// MUX[3:0] codes, DS Table 19. NOT a linear mapping of the AIN index.
static const uint8_t MUX_AIN0_AIN1 = 0x0;  // AINP = AIN0, AINN = AIN1
static const uint8_t MUX_AIN1_AIN0 = 0x3;  // AINP = AIN1, AINN = AIN0
static const uint8_t MUX_AIN2_AIN3 = 0x6;  // AINP = AIN2, AINN = AIN3
static const uint8_t MUX_AIN3_AIN2 = 0x7;  // AINP = AIN3, AINN = AIN2

// ------------------------------------------------------- Cell geometry (§4.2)
// Each ADC has one converter behind a 4-input mux, so a frame is two phases.
// Rule: at most ONE cell per ADC per phase.
//   Phase 0: cell 0 (chip 0x40, Pair 1 MUX_AIN3_AIN2) and cell 2 (chip 0x41, Pair 1 MUX_AIN3_AIN2) convert in parallel.
//   Phase 1: cell 1 (chip 0x40, Pair 0 MUX_AIN1_AIN0); chip 0x41 is idle.
// Zero-crossover routing: inverted MUX codes (0x7 and 0x3) allow parallel PCB jumpering with 0 wire crossings.
#define CELL_COUNT 3
#define ACQ_PHASES 2

struct CellDef {
  uint8_t adc;      // index into ADC_ADDR
  uint8_t mux;      // MUX[3:0] code selecting this cell's S+/S- pair
  uint8_t phase;    // acquisition phase 0..ACQ_PHASES-1
  float angleDeg;   // mount angle phi, CCW from +X viewed from above
  float radiusMm;   // effective moment-arm radius (starts ~27 mm, §4.2)
};

static const CellDef CELLS[CELL_COUNT] = {
  {0, MUX_AIN3_AIN2, 0,   0.0f, 27.0f},   // Cell 0 @   0 deg (ADC1 Pair 1, cols 2-3)
  {0, MUX_AIN1_AIN0, 1, 120.0f, 27.0f},   // Cell 1 @ 120 deg (ADC1 Pair 0, cols 4-5)
  {1, MUX_AIN3_AIN2, 0, 240.0f, 27.0f},   // Cell 2 @ 240 deg (ADC2 Pair 1, cols 12-13)
};

// Reconstruction matrix uses the dimensionless r_bar_i = r_i / RADIUS_REF_MM (§4.2, §4.12),
// so equal radii give r_bar = 1.0 and all three matrix rows come out in ADC counts.
// This is what makes the default axis_scale / deadzone values (144000 / 54000 / 1200 / 2100) valid.
// Physical radii stay in mm in CELLS[] and in the EEPROM record.
static const float RADIUS_REF_MM = 27.0f;

#define AXIS_FORWARD_DEG 0.0f
#define INVERT_PITCH     true
#define INVERT_ROLL      false
#define INVERT_Z         false
#define INVERT_Y_HID     false   // forward stick = positive Y (crosshair moves away/up)

// ------------------------------------------------------ Scaling / defaults
static const float COUNTS_PER_KG_NOMINAL = 107374.0f;  // 2^23 * 3.3mV / (25.78mV) per 10 kg
static const float DEFAULT_AXIS_SCALE[3] = {144000.0f, 144000.0f, 54000.0f};  // Pitch, Roll, Z
static const float DEFAULT_DEADZONE[3]   = {1200.0f, 1200.0f, 2100.0f};
static const int16_t HID_AXIS_MAX = 32767;

enum { AX_PITCH = 0, AX_ROLL = 1, AX_Z = 2 };

// Idle auto re-zero (§4.3)
#define REZERO_ENABLED 1
static const uint16_t REZERO_IDLE_MS = 2000;
static const float REZERO_SLEW_CPS = 1.0f;     // counts per second per cell
static const float REZERO_IDLE_FRAC = 0.25f;   // "idle" = all axes inside this fraction of their deadzone

// Overload (§4.13)
static const float OVERLOAD_WARN_KG  = 8.0f;
static const float OVERLOAD_HYST_KG  = 0.5f;
static const float OVERLOAD_EVENT_KG = 12.0f;
static const uint16_t LED_OVERLOAD_HALF_PERIOD_MS = 125;  // 4 Hz flash
static const uint16_t LED_FAULT_HALF_PERIOD_MS = 500;     // 1 Hz blink (not in spec - my choice)

// ---------------------------------------------------------------- Timing
static const uint16_t TARE_SAMPLES = 64;
static const uint8_t  TARE_SKIP_FRAMES = 2;
static const uint8_t  BUTTON_SCAN_MS = 5;
static const uint8_t  DEBOUNCE_COUNT = 3;
static const uint32_t ADC_PHASE_TIMEOUT_US = 20000UL;     // nominal phase is ~3.5 ms
static const uint8_t  MAX_CONSECUTIVE_FRAME_FAILS = 3;
static const uint16_t STUCK_FRAMES = 150;                 // identical consecutive results => stuck
static const uint16_t FAULT_RETRY_MIN_MS = 500;
static const uint16_t FAULT_RETRY_MAX_MS = 4000;
#define RETARE_AFTER_FAULT true    // spec flow FAULT -> BUS_SCAN -> TARE; set false to keep the RAM tare

// Re-tare gesture: hold Left Flank + Right Flank (bits 1 and 2, mask 0x06) with the stick untouched.
static const uint8_t  GESTURE_MASK = 0x06;
static const uint16_t GESTURE_HOLD_MS = 2000;

// Bench cell test (§4.8)
static const uint16_t BENCH_TEST_WEIGHT_G = 200;
static const float BENCH_TOLERANCE = 0.10f;
static const uint8_t BENCH_SETTLE_FRAMES = 15;

// Debug output
static const uint8_t  DEBUG_STREAM_DECIMATION = 2;   // level 3: print every Nth frame
static const uint16_t DEBUG_STATUS_MS = 1000;        // level 2 status period

// ---------------------------------------------------------------- Logging
// Avoid `if (Serial)` on ATmega32U4: the Arduino AVR core's Serial_::operator bool()
// has a hardcoded delay(10) (10 ms) inside it (CDC.cpp:263)!
// Use Serial.dtr() or direct checks instead to keep the loop non-blocking.
static inline bool serialConnected() {
#if defined(USBCON)
  return Serial.dtr();
#else
  return (bool)Serial;
#endif
}

#if DEBUG_LEVEL > 0
  #define LOGP(...)   do { if (serialConnected()) Serial.print(__VA_ARGS__); } while (0)
  #define LOGLN(...)  do { if (serialConnected()) Serial.println(__VA_ARGS__); } while (0)
#else
  #define LOGP(...)   do { } while (0)
  #define LOGLN(...)  do { } while (0)
#endif

#endif  // CONFIG_H
