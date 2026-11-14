// ads122c04.h - thin in-repo ADS122C04 driver (§4.4, §4.6).
// All register values/commands are from DS Table 16-23; nothing is read from the
// datasheets/ folder at build time.
#ifndef ADS122C04_H
#define ADS122C04_H

#include <Arduino.h>
#include <Wire.h>
#include "config.h"

class Ads122c04 {
 public:
  enum : uint8_t {
    CMD_RESET     = 0x06,
    CMD_START     = 0x08,
    CMD_POWERDOWN = 0x02,
    CMD_RDATA     = 0x10,
    CMD_RREG      = 0x20,   // | (reg << 2)
    CMD_WREG      = 0x40    // | (reg << 2)
  };

  void begin(uint8_t addr) {
    _addr = addr;
    _muxValid = false;
    _lastErr = 0;
  }

  bool probe() {
    Wire.beginTransmission(_addr);
    return Wire.endTransmission() == 0;
  }

  bool reset()     { _muxValid = false; return command(CMD_RESET); }
  bool startSync() { return command(CMD_START); }
  bool powerDown() { return command(CMD_POWERDOWN); }

  bool writeReg(uint8_t reg, uint8_t value) {
    uint8_t tx[2] = {(uint8_t)(CMD_WREG | (reg << 2)), value};
    return xfer(tx, 2, nullptr, 0);
  }

  bool readReg(uint8_t reg, uint8_t &value) {
    uint8_t tx[1] = {(uint8_t)(CMD_RREG | (reg << 2))};
    return xfer(tx, 1, &value, 1);
  }

  // RDATA: 3 bytes, MSB first, two's complement. CRC/inverted-data modes are off.
  bool readData(int32_t &out) {
    uint8_t tx[1] = {CMD_RDATA};
    uint8_t rx[3];
    if (!xfer(tx, 1, rx, 3)) return false;
    uint32_t u = ((uint32_t)rx[0] << 16) | ((uint32_t)rx[1] << 8) | rx[2];
    if (u & 0x800000UL) u |= 0xFF000000UL;   // sign-extend 24 -> 32 bit
    out = (int32_t)u;
    return true;
  }

  // DRDY bit (config reg 2, bit 7). Used only when USE_DRDY_PINS is false.
  bool drdyBit(bool &ready) {
    uint8_t v;
    if (!readReg(2, v)) return false;
    ready = (v & 0x80) != 0;
    return true;
  }

  // Select the input pair. Skipped when unchanged: a WREG also restarts the
  // digital filter, so redundant writes just cost bus time.
  bool setMux(uint8_t mux) {
    if (_muxValid && mux == _mux) return true;
    if (!writeReg(0, reg0(mux))) return false;
    _mux = mux;
    _muxValid = true;
    return true;
  }

  bool configure(uint8_t mux) {
    if (!writeReg(0, reg0(mux))) return false;
    if (!writeReg(1, reg1())) return false;
    if (!writeReg(2, 0x00)) return false;   // no DCNT, no CRC, no burn-out, IDACs off
    if (!writeReg(3, 0x00)) return false;   // IDAC routing off
    _mux = mux;
    _muxValid = true;
    return true;
  }

  // Read registers back and compare (bit 7 of reg 2 is the read-only DRDY flag).
  bool verify(uint8_t mux) {
    uint8_t v;
    if (!readReg(0, v) || v != reg0(mux)) return false;
    if (!readReg(1, v) || v != reg1()) return false;
    if (!readReg(2, v) || (v & 0x7F) != 0x00) return false;
    if (!readReg(3, v) || v != 0x00) return false;
    return true;
  }

  uint8_t lastError() const { return _lastErr; }

 private:
  static uint8_t reg0(uint8_t mux) { return (uint8_t)((mux << 4) | (ADS_GAIN << 1)); }  // PGA enabled
  static uint8_t reg1() {
    return (uint8_t)((ADS_DR << 5) | (ADS_MODE << 4) | (ADS_CM << 3) | (ADS_VREF << 1));
  }

  bool command(uint8_t c) { return xfer(&c, 1, nullptr, 0); }

  // Write tx[], optionally followed by a repeated-start read of rxLen bytes.
  // NACKs and short reads are retried with a doubling back-off (only the error
  // path ever waits).
  bool xfer(const uint8_t *tx, uint8_t txLen, uint8_t *rx, uint8_t rxLen) {
    for (uint8_t attempt = 0; attempt <= I2C_RETRIES; attempt++) {
      Wire.beginTransmission(_addr);
      for (uint8_t i = 0; i < txLen; i++) Wire.write(tx[i]);
      uint8_t err = Wire.endTransmission(rxLen == 0 ? 1 : 0);  // 0 => repeated start
      if (err == 0) {
        if (rxLen == 0) return true;
        uint8_t got = Wire.requestFrom(_addr, rxLen);
        if (got == rxLen) {
          for (uint8_t i = 0; i < rxLen; i++) rx[i] = Wire.read();
          return true;
        }
        while (Wire.available()) Wire.read();
        err = 0xFE;   // short read
      }
      _lastErr = err;
      if (attempt < I2C_RETRIES) delayMicroseconds((uint16_t)(I2C_BACKOFF_US << attempt));
    }
    return false;
  }

  uint8_t _addr = 0x40;
  uint8_t _mux = 0;
  bool _muxValid = false;
  uint8_t _lastErr = 0;
};

#endif  // ADS122C04_H
