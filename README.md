# 🚀 AI-Augmented Autonomous Fleet & Navigation System

Real-time autonomous vehicle fleet monitoring with INS, GPS fusion, Kalman filtering,
and LSTM-based AI anomaly detection — built on ThingsBoard IoT platform.

![Python](https://img.shields.io/badge/Python-3.8+-blue)
![ThingsBoard](https://img.shields.io/badge/ThingsBoard-4.x-green)
![Docker](https://img.shields.io/badge/Docker-ready-blue)
![AI](https://img.shields.io/badge/AI-LSTM_Anomaly_Detection-red)
![Vehicles](https://img.shields.io/badge/Vehicles-2-orange)
![License](https://img.shields.io/badge/License-MIT-yellow)

## 📋 Overview

This system simulates a fleet of autonomous vehicles, each equipped with:
- **STM32** microcontroller → IMU (6-DOF) + GPS + Barometer
- **ESP32** microcontroller → WiFi/MQTT connectivity + system health
- **Kalman Filter INS** → drift correction + GPS fusion
- **LSTM AI Detector** → real-time anomaly detection
- **ThingsBoard Dashboard** → live telemetry visualization

## 🏗️ System Architecture

```
┌─────────────────────────────────────────────────┐
│                SIMULATION LAYER                  │
│   STM32 Simulator        ESP32 Simulator         │
│   - 6-DOF IMU            - WiFi/MQTT client      │
│   - GPS (NMEA)           - System health         │
│   - Barometer            - Packet loss sim       │
└──────────────┬──────────────────┬───────────────┘
               │                  │
               └────────┬─────────┘
                        │ HTTP / MQTT
         ┌──────────────▼──────────────┐
         │       PROCESSING LAYER       │
         │  Kalman INS  │  GPS Fusion   │
         │  LSTM AI     │  Anomaly Det  │
         └──────────────┬──────────────┘
                        │
         ┌──────────────▼──────────────┐
         │      ThingsBoard IoT         │
         │  Dashboard │ Alarms │ RPC    │
         └─────────────────────────────┘
```

## 📁 Project Structure

```
autonomous-fleet-nav/
├── simulation/
│   ├── stm32_simulator.py    # STM32: IMU + GPS + Barometer
│   └── esp32_simulator.py    # ESP32: WiFi + MQTT + Health
├── navigation/
│   ├── kalman_ins.py         # 9-state Kalman Filter INS
│   └── gps_fusion.py         # GPS + INS weighted fusion
├── ai/
│   └── lstm_model.py         # LSTM autoencoder anomaly detector
├── mqtt/
│   └── broker_client.py      # MQTT publisher + HTTP fallback
├── thingsboard/
│   └── tb_client.py          # ThingsBoard HTTP API client
├── docker/
│   └── docker-compose.yml    # ThingsBoard + Mosquitto MQTT
├── assets/
│   └── dashboard.png         # Dashboard screenshot
├── config.py                 # Global configuration
├── main.py                   # Entry point
├── requirements.txt
└── README.md
```

## 🚀 Getting Started

### Prerequisites
- Python 3.8+
- Docker Desktop

### 1. Clone & Install

```bash
git clone https://github.com/saif-amara/autonomous-fleet-nav.git
cd autonomous-fleet-nav
pip install -r requirements.txt
```

### 2. Start Infrastructure

```bash
cd docker
docker-compose up -d
```

### 3. Configure ThingsBoard

- Open `http://localhost:9090`
- Login: `tenant@thingsboard.org` / `tenant`
- Create 4 devices: `STM32_Unit_1`, `STM32_Unit_2`, `ESP32_Unit_1`, `ESP32_Unit_2`
- Copy tokens to `config.py`

### 4. Run the System

```bash
python main.py
```

## 📊 Telemetry Data (39 keys per vehicle)

| Category | Keys |
|----------|------|
| IMU | `accel_x/y/z`, `gyro_x/y/z` |
| GPS | `latitude`, `longitude`, `altitude`, `speed`, `heading` |
| Barometer | `baro_altitude`, `pressure_hpa` |
| Kalman INS | `kalman_x/y/z`, `kalman_vx/vy/vz`, `drift_error` |
| GPS Fusion | `fused_x/y/z`, `gps_local_x/y/z`, `position_error` |
| AI | `anomaly_score`, `is_anomaly`, `detector_ready` |
| ESP32 | `wifi_rssi`, `battery_pct`, `mcu_temp_c`, `uptime_s` |

## 🤖 AI Anomaly Detection

The LSTM autoencoder analyzes 9 features in real-time:

```python
features = [
    "accel_x", "accel_y", "accel_z",
    "gyro_x",  "gyro_y",  "gyro_z",
    "drift_error", "innovation_avg", "position_error"
]
```

- **Normal behavior** → anomaly_score < 0.85
- **Anomaly detected** → anomaly_score ≥ 0.85 → ThingsBoard alarm

## 🔧 RPC Commands

| Command | Description |
|---------|-------------|
| `reset_kalman` | Reset Kalman filter + GPS fusion |
| `reset_ai` | Reset LSTM anomaly detector |
| `get_status` | Get vehicle status |

## 🐳 Docker Services

| Service | Port | Description |
|---------|------|-------------|
| ThingsBoard | 9090 | IoT dashboard |
| MQTT (TB) | 1883 | ThingsBoard broker |
| Mosquitto | 1884 | External MQTT broker |
| WebSocket | 7070 | Real-time updates |

## 🎯 Applications

- Autonomous vehicle fleet monitoring
- UAV/Drone navigation systems
- Aerospace avionics prototyping
- Embedded systems research

## 👤 Author

**Saif Eddine Amara**
Teaching Assistant — Robotics Lab, ISSAT Sousse
Embedded Systems & Avionics Engineer
