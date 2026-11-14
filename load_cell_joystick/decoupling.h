// decoupling.h - geometry-driven reconstruction matrix and per-axis shaping (§4.2, §4.3).
#ifndef DECOUPLING_H
#define DECOUPLING_H

#include <Arduino.h>
#include <math.h>
#include "config.h"

struct DecoupleMatrix {
  float row[3][CELL_COUNT];   // rows: Pitch, Roll, Z
};

// Pitch_theta = sum r_i sin(phi_i - theta) N_i
// Roll_theta  = sum r_i cos(phi_i - theta) N_i
// Z           = sum N_i
// r_i is radiusMm / RADIUS_REF_MM (so 1.0 for the equal-radius triad).
// Invert flags are folded into the rows, so a flipped axis is flipped everywhere
// (deadzone, auto re-zero, calibration peaks) consistently.
inline void buildMatrix(DecoupleMatrix &m) {
  const float d2r = 0.017453292519943295f;
  for (uint8_t i = 0; i < CELL_COUNT; i++) {
    float r = CELLS[i].radiusMm / RADIUS_REF_MM;
    float a = (CELLS[i].angleDeg - AXIS_FORWARD_DEG) * d2r;
    m.row[AX_PITCH][i] = (INVERT_PITCH ? -1.0f : 1.0f) * r * sinf(a);
    m.row[AX_ROLL][i]  = (INVERT_ROLL  ? -1.0f : 1.0f) * r * cosf(a);
    m.row[AX_Z][i]     = (INVERT_Z     ? -1.0f : 1.0f);
  }
}

// N[] = tare-corrected, span-normalised cell counts. v[] = Pitch, Roll, Z in
// matrix-output units (the units the deadzones and axis_scale are expressed in).
inline void decouple(const DecoupleMatrix &m, const float *N, float *v) {
  for (uint8_t a = 0; a < 3; a++) {
    float s = 0.0f;
    for (uint8_t i = 0; i < CELL_COUNT; i++) s += m.row[a][i] * N[i];
    v[a] = s;
  }
}

// Deadband with rescale: edge of band -> 0, fullScale -> +/-32767, no jump (§4.3).
inline int16_t shapeAxis(float v, float deadzone, float fullScale) {
  float a = fabsf(v);
  if (a <= deadzone) return 0;
  float span = fullScale - deadzone;
  if (span < 1.0f) span = 1.0f;
  float o = (a - deadzone) / span;
  if (o > 1.0f) o = 1.0f;
  int16_t out = (int16_t)(o * (float)HID_AXIS_MAX + 0.5f);
  return v < 0.0f ? (int16_t)-out : out;
}

#endif  // DECOUPLING_H
