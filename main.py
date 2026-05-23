import time
import threading
def clean_payload(data: dict) -> dict:
    """Recursively convert bools to int for JSON"""
    return {k: int(v) if isinstance(v, bool) else v for k, v in data.items()}
from simulation.stm32_simulator import STM32Simulator
from simulation.esp32_simulator import ESP32Simulator
from navigation.kalman_ins      import KalmanINS
from navigation.gps_fusion      import GPSFusion
from ai.lstm_model              import LSTMAnomalyDetector
from mqtt.broker_client         import MQTTClient
from thingsboard.tb_client      import ThingsBoardClient
from config import DEVICE_TOKENS, UPDATE_INTERVAL, NUM_VEHICLES

# ================================================
print("=" * 55)
print("🚀  AI-Augmented Autonomous Fleet & Navigation System")
print("=" * 55)

# ── Init MQTT ────────────────────────────────────
mqtt = MQTTClient()

# ── Init vehicles ────────────────────────────────
vehicles = []
for i in range(1, NUM_VEHICLES + 1):
    vehicles.append({
        "id":       i,
        "stm32":    STM32Simulator(i),
        "esp32":    ESP32Simulator(i),
        "kalman":   KalmanINS(i),
        "gps":      GPSFusion(i),
        "ai":       LSTMAnomalyDetector(),
        "tb_stm32": ThingsBoardClient(
                        f"STM32_Unit_{i}",
                        DEVICE_TOKENS[f"stm32_unit_{i}"]
                    ),
        "tb_esp32": ThingsBoardClient(
                        f"ESP32_Unit_{i}",
                        DEVICE_TOKENS[f"esp32_unit_{i}"]
                    ),
    })

print(f"✅ {NUM_VEHICLES} vehicles initialized\n" + "-" * 55)

# ── Vehicle loop ─────────────────────────────────
def run_vehicle(v: dict):
    """Main loop for one vehicle"""
    vid = v["id"]

    # Register RPC handlers
    def handle_rpc(cmd):
        method = cmd.get("method", "")
        if method == "reset_kalman":
            v["kalman"].reset()
            v["gps"].reset()
            return {"status": "Kalman reset OK"}
        elif method == "reset_ai":
            v["ai"].reset()
            return {"status": "AI detector reset OK"}
        elif method == "get_status":
            return {"vehicle": vid, "status": "RUNNING"}
        return {"status": "unknown command"}

    v["tb_stm32"].listen_rpc(handle_rpc)

    while True:
        # ── STM32 data ───────────────────────────
        stm_data = v["stm32"].get_all()

        # ── Kalman INS ───────────────────────────
        accel = [stm_data["accel_x"],
                 stm_data["accel_y"],
                 stm_data["accel_z"]]
        kalman_pos = v["kalman"].predict(accel)

        gps_pos = [stm_data["latitude"] * 111000,
                   stm_data["longitude"] * 111000,
                   stm_data["altitude"]]
        kalman_pos = v["kalman"].update(gps_pos)
        kalman_metrics = v["kalman"].get_metrics()

        # ── GPS Fusion ───────────────────────────
        gps_data = v["gps"].fuse(
            {
                "latitude":  stm_data["latitude"],
                "longitude": stm_data["longitude"],
                "altitude":  stm_data["altitude"],
            },
            kalman_pos
        )

        # ── AI Anomaly Detection ─────────────────
        ai_features = {
            **{k: stm_data.get(k, 0) for k in
               ["accel_x","accel_y","accel_z",
                "gyro_x","gyro_y","gyro_z"]},
            "drift_error":     kalman_metrics["drift_error"],
            "innovation_avg":  kalman_metrics["innovation_avg"],
            "position_error":  gps_data["position_error"],
        }
        ai_result = v["ai"].add_sample(ai_features)

        # ── ESP32 data ───────────────────────────
        esp_data = v["esp32"].get_all()

        # ── Build ThingsBoard payload ─────────────
        tb_payload = {
            **stm_data,
            **kalman_metrics,
            **gps_data,
            **ai_result,
        }

        # ── Send to ThingsBoard ──────────────────
        ok = v["tb_stm32"].send_telemetry(clean_payload(tb_payload))
        v["tb_esp32"].send_telemetry(clean_payload(esp_data))

        # ── Publish to MQTT ──────────────────────
        mqtt.publish(f"fleet/vehicle_{vid}/telemetry", tb_payload)

        # ── Console log ──────────────────────────
        anomaly = "🔴 ANOMALY!" if ai_result["is_anomaly"] else "🟢 OK"
        print(
            f"🚗 V{vid} | "
            f"GPS({stm_data['latitude']:.4f},{stm_data['longitude']:.4f}) | "
            f"drift={kalman_metrics['drift_error']:.3f}m | "
            f"AI={ai_result['anomaly_score']:.2f} {anomaly}"
        )

        time.sleep(UPDATE_INTERVAL)

# ── Start all vehicles ────────────────────────────
threads = []
for v in vehicles:
    t = threading.Thread(target=run_vehicle, args=(v,))
    t.daemon = True
    threads.append(t)
    t.start()

print(f"🏁 All {NUM_VEHICLES} vehicles running!\n" + "=" * 55)

try:
    while True:
        time.sleep(60)
except KeyboardInterrupt:
    mqtt.stop()
    print("\n🛑 System shutdown.")