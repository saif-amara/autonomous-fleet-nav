# ================================================
# AI-Augmented Autonomous Fleet & Navigation System
# Configuration
# ================================================

# ── ThingsBoard ──────────────────────────────────
TB_HOST     = "localhost"
TB_PORT     = 9090
TB_BASE_URL = f"http://{TB_HOST}:{TB_PORT}/api/v1"

# Device tokens — أنشئهم في ThingsBoard لاحقاً
DEVICE_TOKENS = {
    "stm32_unit_1": "it2UBdev77gU4NXW4zpt",
    "stm32_unit_2": "IvovEq8IOXpxhKizNEuT",
    "esp32_unit_1": "QsQ6KX3LJF8xCLMdPocj",
    "esp32_unit_2": "TWLuwr8uyhvdOKIbnsy4",
}

# ── MQTT ─────────────────────────────────────────
MQTT_BROKER   = "localhost"
MQTT_PORT     = 1883
MQTT_TOPICS   = {
    "telemetry": "fleet/+/telemetry",
    "gps":       "fleet/+/gps",
    "imu":       "fleet/+/imu",
    "alarm":     "fleet/+/alarm",
}

# ── Simulation ───────────────────────────────────
UPDATE_INTERVAL = 0.5      # seconds
NUM_VEHICLES    = 2        # number of simulated vehicles

# ── Navigation ───────────────────────────────────
GPS_NOISE       = 0.0001   # degrees
IMU_NOISE       = 0.05     # m/s²
BARO_NOISE      = 0.5      # meters
DRIFT_RATE      = 0.001    # m/step

# ── AI / LSTM ────────────────────────────────────
SEQUENCE_LEN    = 50       # timesteps for LSTM input
ANOMALY_THRESH  = 0.85     # detection threshold
MODEL_PATH      = "ai/lstm_model.h5"

# ── Alarm Thresholds ─────────────────────────────
THRESHOLDS = {
    "max_drift":       5.0,    # meters
    "max_accel":       20.0,   # m/s²
    "max_gyro":        5.0,    # rad/s
    "min_altitude":   -10.0,   # meters
    "max_altitude":   500.0,   # meters
    "anomaly_score":   0.85,   # LSTM threshold
}
RPC_TIMEOUT = 30