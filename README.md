# 🔐 ASCON Encryption for IoT: Secure MQTT Communication with ESP32 & HC-SR04

[![ESP32](https://img.shields.io/badge/Platform-ESP32-blue)](https://www.espressif.com/en/products/socs/esp32)
[![ASCON](https://img.shields.io/badge/Encryption-ASCON--128-green)](https://ascon.iaik.tugraz.at/)
[![MQTT](https://img.shields.io/badge/Protocol-MQTT-orange)](https://mqtt.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-yellow)](https://www.python.org/)
[![License](https://img.shields.io/badge/License-MIT-red)](LICENSE)

> A comprehensive implementation of lightweight ASCON-128 AEAD encryption for securing IoT sensor data transmission over MQTT protocol.

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [System Architecture](#-system-architecture)
- [Hardware Requirements](#-hardware-requirements)
- [Software Requirements](#-software-requirements)
- [Installation](#-installation)
- [Usage](#-usage)
- [Performance Metrics](#-performance-metrics)
- [Security Testing](#-security-testing)
- [Project Structure](#-project-structure)
- [Contributors](#-contributors)
- [References](#-references)

---

## 🌟 Overview

This project implements **ASCON-128**, a lightweight Authenticated Encryption with Associated Data (AEAD) algorithm, to secure data transmission from IoT sensors. The system uses an ESP32 microcontroller with an HC-SR04 ultrasonic sensor to measure distance, encrypt the data using ASCON, and transmit it securely via MQTT protocol.

### Why ASCON?

- ✅ **Lightweight**: Optimized for resource-constrained IoT devices
- ✅ **NIST Standard**: Winner of NIST Lightweight Cryptography competition
- ✅ **Authenticated Encryption**: Combines confidentiality, integrity, and authenticity
- ✅ **Fast**: Encryption time ~1-2ms, suitable for real-time applications
- ✅ **Secure**: Protects against eavesdropping, tampering, and replay attacks

---

## ✨ Features

### Core Functionality
- 🔒 **End-to-End Encryption**: Data encrypted before transmission and decrypted at receiver
- 📡 **MQTT Communication**: Reliable publish-subscribe messaging protocol
- 📊 **Real-Time Monitoring**: Live distance measurements from HC-SR04 sensor
- ⚡ **Low Latency**: Sub-millisecond encryption/decryption performance
- 🔋 **Energy Efficient**: Optimized power consumption (~195mJ per cycle)

### Security Features
- 🛡️ **Integrity Protection**: Authentication tag verification
- 🚫 **Tamper Detection**: Automatic rejection of modified ciphertext
- 👁️ **Attack Monitoring**: Real-time detection of suspicious activities
- 🔐 **Confidentiality**: Encrypted data unreadable without proper keys

### Testing & Analysis
- 📈 **Performance Metrics**: Encryption/decryption time measurement
- 🔌 **Energy Analysis**: Power consumption tracking per cycle
- 🎯 **Attack Simulation**: Passive (eavesdropping) and active (modification, DoS) attacks
- 📉 **ThingSpeak Integration**: Cloud-based data visualization

---

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                         IoT Security System                      │
└─────────────────────────────────────────────────────────────────┘

┌──────────────┐     Raw Data      ┌─────────────────┐
│   ESP32 +    │ ───────────────►  │  MQTT Broker    │
│   HC-SR04    │  (Unencrypted)    │  (HiveMQ)       │
└──────────────┘                   └─────────────────┘
                                           │
                                           ▼
                    ┌──────────────────────────────────────┐
                    │      Python MQTT Publisher           │
                    │  ┌────────────────────────────────┐  │
                    │  │  ASCON-128 Encryption Engine   │  │
                    │  │  • Key Management              │  │
                    │  │  • Nonce Generation            │  │
                    │  │  • Tag Authentication          │  │
                    │  └────────────────────────────────┘  │
                    └──────────────────────────────────────┘
                                           │
                                  Encrypted Data
                                           │
                                           ▼
                    ┌─────────────────────────────────────┐
                    │      MQTT Broker (Encrypted)        │
                    └─────────────────────────────────────┘
                                           │
                    ┌──────────────────────┼──────────────────────┐
                    ▼                      ▼                      ▼
          ┌─────────────────┐  ┌─────────────────┐  ┌──────────────────┐
          │    Subscriber   │  │ Attack Monitor  │  │ Energy Analyzer  │
          │   (Decryption)  │  │  (Security)     │  │  (Performance)   │
          └─────────────────┘  └─────────────────┘  └──────────────────┘
```

### Data Flow

1. **Sensor Reading**: ESP32 reads distance from HC-SR04 sensor
2. **Raw Transmission**: Data sent to MQTT broker in JSON format
3. **Encryption**: Python publisher encrypts data using ASCON-128
4. **Secure Transmission**: Encrypted data published to secure topic
5. **Decryption**: Subscriber decrypts and validates data integrity
6. **Monitoring**: Parallel analysis of security and energy metrics

---

## 🛠️ Hardware Requirements

| Component | Specification | Purpose |
|-----------|---------------|---------|
| **ESP32 DevKit** | ESP32-WROOM-32 | Main microcontroller |
| **HC-SR04** | Ultrasonic Sensor | Distance measurement (2-400cm) |
| **Jumper Wires** | Male-Female | Connections |
| **USB Cable** | Micro-USB/USB-C | Programming & Power |
| **Breadboard** | Optional | Prototyping |

### Wiring Diagram

```
HC-SR04          ESP32
────────         ─────────
VCC     ──────►  5V
TRIG    ──────►  GPIO 5
ECHO    ──────►  GPIO 18
GND     ──────►  GND
```

---

## 💻 Software Requirements

### Arduino IDE Setup
- **Arduino IDE**: Version 1.8.x or 2.x
- **ESP32 Board Support**: 
  ```
  https://dl.espressif.com/dl/package_esp32_index.json
  ```
- **Library**: PubSubClient (MQTT client)

### Python Environment
- **Python**: 3.8 or higher
- **Required Libraries**:
  ```bash
  pip install paho-mqtt requests cryptography numpy
  ```

### External Services
- **MQTT Broker**: HiveMQ Public Broker (`broker.hivemq.com:1883`)
- **Visualization** (Optional): ThingSpeak account for data plotting

---

## 📥 Installation

### 1. Clone Repository

```bash
git clone https://github.com/mutiarardsl/Project-Akhir-Kriptografi.git
cd Project-Akhir-Kriptografi
```

### 2. Arduino Setup

1. Open Arduino IDE
2. Install ESP32 board support via Board Manager
3. Install **PubSubClient** library via Library Manager
4. Open `arduino/mqtt_hcsr04_Ascon.ino`
5. Configure WiFi credentials:
   ```cpp
   const char* ssid = "YOUR_WIFI_SSID";
   const char* password = "YOUR_WIFI_PASSWORD";
   ```
6. Select **ESP32 Dev Module** as board
7. Upload sketch to ESP32

### 3. Python Setup

```bash
cd python
pip install -r requirements.txt  # If available, or install manually
```

Create `requirements.txt`:
```txt
paho-mqtt>=1.6.1
requests>=2.28.0
cryptography>=3.4.8
numpy>=1.21.0
```

### 4. Configuration

Ensure all Python scripts use the same:
- **MQTT Broker**: `broker.hivemq.com`
- **Encryption Key**: Matching 16-byte key in publisher & subscriber
- **Nonce**: Matching 16-byte nonce
- **Topics**: 
  - Raw data: `iot/sensor/distance/raw`
  - Encrypted: `iot/sensor/distance/enc`
  - Energy: `iot/sensor/energy`

---

## 🚀 Usage

### Running the Complete System

Open **4 separate terminal windows** and run:

#### Terminal 1: MQTT Publisher (Encryption)
```bash
python python/mqtt_publisher.py
```
*Listens to raw data and encrypts using ASCON*

#### Terminal 2: MQTT Subscriber (Decryption)
```bash
python python/mqtt_subscriber.py
```
*Receives encrypted data and decrypts it*

#### Terminal 3: Energy Analyzer
```bash
python python/energy_analyzer.py
```
*Monitors power consumption and performance*

#### Terminal 4: Attack Monitor
```bash
python python/attack_monitor.py
```
*Detects security anomalies and attacks*

### Optional: Attack Simulation

```bash
python python/attack_simulator.py
```

Available attacks:
- **Eavesdropping**: Passive data interception
- **Plaintext Modification**: Injecting fake raw data
- **Ciphertext Tampering**: Modifying encrypted data
- **DoS (Flooding)**: Message spam attack

---

## 📊 Performance Metrics

### Encryption/Decryption Speed

| Metric | Average | Range |
|--------|---------|-------|
| **Encryption Time** | ~1.5 ms | 1.0 - 4.0 ms |
| **Decryption Time** | ~1.7 ms | 1.6 - 1.8 ms |
| **Round-Trip Latency** | <10 ms | Network dependent |

### Energy Consumption

| Component | Time (μs) | Energy (mJ) |
|-----------|-----------|-------------|
| Sensor Reading | 2,500 - 7,200 | ~50 - 150 |
| JSON Encoding | ~500 | ~10 |
| MQTT Publish | 900 - 1,100 | ~20 - 30 |
| **Total per Cycle** | ~10,000 | **~195** |

**Cumulative Energy** (280 cycles): 54,753 mJ (≈15.21 Wh)  
**Average Power**: 19.56 W

### Data Overhead

- **Plaintext Size**: ~80 bytes (JSON)
- **Ciphertext Size**: ~96 bytes (with tag)
- **Overhead**: ~20% (acceptable for security gain)

---

## 🛡️ Security Testing

### Test Results Summary

| Attack Type | Detection | Result |
|-------------|-----------|--------|
| **Eavesdropping** (Passive) | N/A | ✅ Data encrypted, unreadable |
| **Plaintext Modification** | ⚠️ Limited | ⚠️ System processes fake data |
| **Ciphertext Modification** | ✅ Detected | ✅ ASCON rejects invalid tag |
| **DoS (Flooding)** | ✅ Detected | ✅ Anomaly flagged by monitor |

### Key Findings

1. **Confidentiality**: Encrypted data remains secure against eavesdropping
2. **Integrity**: ASCON successfully detects and rejects tampered ciphertext
3. **Authenticity**: Authentication tag prevents data forgery
4. **Vulnerability**: Raw data topic (`/raw`) exposed; recommend encrypting at ESP32 level

---

## 📁 Project Structure

```
project-akhir-kriptografi/
│
├── arduino/
│   └── mqtt_hcsr04_Ascon.ino      # ESP32 firmware (sensor + MQTT)
│
├── python/
│   ├── ascon.py                    # ASCON-128 encryption implementation
│   ├── mqtt_publisher.py           # Encrypts raw data from ESP32
│   ├── mqtt_subscriber.py          # Decrypts and displays data
│   ├── attack_simulator.py         # Security testing tool
│   ├── attack_monitor.py           # Real-time threat detection
│   └── energy_analyzer.py          # Power consumption tracker
│
├── docs/
│   └── Laporan_Kelompok_5.pdf     # Full technical report (Bahasa)
│
└── README.md                       # This file
```

---

## 👥 Contributors

This project was developed as a final assignment for **Cryptography Course (Class A)** at **Universitas Brawijaya**.

| Name | Student ID | Role |
|------|------------|------|
| **Cindy Zakya Andini** | 
| **Afifah Chairunnisa Hariyawan** | 
| **Antike Rahma Safira** | 

**Supervisor**: Ir. Ari Kusyanti, S.T., M.Sc  
**Institution**: Faculty of Computer Science, Universitas Brawijaya  
**Year**: 2025

---

## 🎓 Academic Context

**Course**: Cryptography  
**Department**: Information Systems  
**Faculty**: Computer Science  
**University**: Universitas Brawijaya

This implementation demonstrates the practical application of lightweight cryptography in IoT environments, addressing real-world security challenges in resource-constrained devices.

---

## 📚 References

1. **ASCON**: [Official ASCON Website](https://ascon.iaik.tugraz.at/)
2. **NIST Lightweight Cryptography**: [NIST LWC Project](https://csrc.nist.gov/projects/lightweight-cryptography)
3. **ESP32 Documentation**: [Espressif Systems](https://docs.espressif.com/projects/esp-idf/en/latest/esp32/)
4. **MQTT Protocol**: [MQTT.org](https://mqtt.org/)
5. **HC-SR04 Datasheet**: [Ultrasonic Sensor Specs](https://cdn.sparkfun.com/datasheets/Sensors/Proximity/HCSR04.pdf)

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🤝 Acknowledgments

- **ASCON Team** for the excellent lightweight cryptography algorithm
- **HiveMQ** for free MQTT broker service

---

## 📞 Contact
- 📧 Email: [mutiararosidas07@gmail.com]
- 🔗 GitHub: [@mutiarardsl](https://github.com/mutiarardsl)
- 💼 LinkedIn: [www.linkedin.com/in/mutiararosidasholihat]

---
