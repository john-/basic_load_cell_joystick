// switches.h - grip switch scan + debounce (§4.9). Active-low, INPUT_PULLUP.
#ifndef SWITCHES_H
#define SWITCHES_H

#include <Arduino.h>
#include "config.h"

class Switches {
 public:
  void begin() {
    for (uint8_t i = 0; i < NUM_SWITCHES; i++) {
      pinMode(SWITCH_PINS[i], INPUT_PULLUP);
      _cnt[i] = 0;
    }
    _state = 0;
    _last = millis();
  }

  // Call every loop. Returns true if the debounced state changed this call.
  bool update(uint32_t now) {
    if ((uint32_t)(now - _last) < BUTTON_SCAN_MS) return false;
    _last = ((uint32_t)(now - _last) >= 2UL * BUTTON_SCAN_MS) ? now : _last + BUTTON_SCAN_MS;

    bool changed = false;
    for (uint8_t i = 0; i < NUM_SWITCHES; i++) {
      bool pressed = digitalRead(SWITCH_PINS[i]) == LOW;
      bool cur = (_state >> i) & 1;
      if (pressed == cur) {
        _cnt[i] = 0;
      } else if (++_cnt[i] >= DEBOUNCE_COUNT) {   // N identical differing reads in a row
        _state ^= (uint8_t)(1 << i);
        _cnt[i] = 0;
        changed = true;
      }
    }
    return changed;
  }

  uint8_t state() const { return _state; }   // bit0 = button 1 ... bit5 = button 6

 private:
  uint8_t _state = 0;
  uint8_t _cnt[NUM_SWITCHES];
  uint32_t _last = 0;
};

#endif  // SWITCHES_H
