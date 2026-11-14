// calibration.h - calibration record, defaults and validity-checked EEPROM storage (§4.8, §4.11).
#ifndef CALIBRATION_H
#define CALIBRATION_H

#include <Arduino.h>
#include <EEPROM.h>
#include <math.h>
#include "config.h"

static const uint16_t CAL_MAGIC = 0x4C43;   // "LC"
static const uint8_t  CAL_VERSION = 1;
static const int      CAL_EEPROM_ADDR = 0;

struct __attribute__((packed)) CalData {
  uint16_t magic;
  uint8_t  version;
  uint8_t  cellCount;
  float    geomAngle[CELL_COUNT];
  float    geomRadius[CELL_COUNT];
  float    axisForwardDeg;
  uint8_t  invertPitch, invertRoll, invertZ, invertYHid;
  float    tare[CELL_COUNT];
  float    span[CELL_COUNT];        // dimensionless per-cell gain, default 1.0
  float    axisScale[3];            // Pitch, Roll, Z full-scale in matrix units
  float    deadzone[3];             // Pitch, Roll, Z in matrix units
  uint16_t rezeroIdleMs;
  float    rezeroSlewCps;
  float    rezeroIdleFrac;
  uint16_t crc;                     // must stay last
};

enum LoadResult : uint8_t {
  LOAD_OK = 0,
  LOAD_INVALID,        // blank EEPROM, bad magic/version, or CRC failure
  LOAD_GEOMETRY        // valid record but for a different cell count / geometry
};

inline uint16_t calCrc16(const uint8_t *d, size_t n) {   // CRC-16/CCITT-FALSE
  uint16_t c = 0xFFFF;
  while (n--) {
    c ^= (uint16_t)(*d++) << 8;
    for (uint8_t b = 0; b < 8; b++) c = (c & 0x8000) ? (uint16_t)((c << 1) ^ 0x1021) : (uint16_t)(c << 1);
  }
  return c;
}

inline void calDefaults(CalData &c) {
  memset(&c, 0, sizeof(c));
  c.magic = CAL_MAGIC;
  c.version = CAL_VERSION;
  c.cellCount = CELL_COUNT;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    c.geomAngle[i] = CELLS[i].angleDeg;
    c.geomRadius[i] = CELLS[i].radiusMm;
    c.tare[i] = 0.0f;
    c.span[i] = 1.0f;
  }
  c.axisForwardDeg = AXIS_FORWARD_DEG;
  c.invertPitch = INVERT_PITCH;
  c.invertRoll = INVERT_ROLL;
  c.invertZ = INVERT_Z;
  c.invertYHid = INVERT_Y_HID;
  for (uint8_t a = 0; a < 3; a++) {
    c.axisScale[a] = DEFAULT_AXIS_SCALE[a];
    c.deadzone[a] = DEFAULT_DEADZONE[a];
  }
  c.rezeroIdleMs = REZERO_IDLE_MS;
  c.rezeroSlewCps = REZERO_SLEW_CPS;
  c.rezeroIdleFrac = REZERO_IDLE_FRAC;
}

inline bool calGeometryMatches(const CalData &c) {
  if (c.cellCount != CELL_COUNT) return false;
  if (fabsf(c.axisForwardDeg - AXIS_FORWARD_DEG) > 1e-3f) return false;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    if (fabsf(c.geomAngle[i] - CELLS[i].angleDeg) > 1e-3f) return false;
    if (fabsf(c.geomRadius[i] - CELLS[i].radiusMm) > 1e-3f) return false;
  }
  return true;
}

// On anything other than LOAD_OK the caller gets nominal defaults (never a fault, §4.11).
inline LoadResult calLoad(CalData &out) {
  CalData tmp;
  EEPROM.get(CAL_EEPROM_ADDR, tmp);
  bool ok = tmp.magic == CAL_MAGIC && tmp.version == CAL_VERSION &&
            tmp.crc == calCrc16((const uint8_t *)&tmp, sizeof(tmp) - sizeof(tmp.crc));
  if (!ok) {
    calDefaults(out);
    return LOAD_INVALID;
  }
  if (!calGeometryMatches(tmp)) {
    calDefaults(out);
    return LOAD_GEOMETRY;
  }
  out = tmp;
  return LOAD_OK;
}

// EEPROM.put() only rewrites bytes that changed.
inline void calSave(CalData &c) {
  c.magic = CAL_MAGIC;
  c.version = CAL_VERSION;
  c.crc = calCrc16((const uint8_t *)&c, sizeof(c) - sizeof(c.crc));
  EEPROM.put(CAL_EEPROM_ADDR, c);
}

#endif  // CALIBRATION_H
