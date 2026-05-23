import json
import threading
import time
import requests
from config import MQTT_BROKER, MQTT_PORT, TB_BASE_URL

class MQTTClient:
    """
    MQTT client for fleet communication
    Uses paho-mqtt to publish/subscribe
    Falls back to HTTP if MQTT unavailable
    """

    def __init__(self):
        self.broker    = MQTT_BROKER
        self.port      = MQTT_PORT
        self.client    = None
        self.connected = False
        self.messages  = []
        self._init_mqtt()

    def _init_mqtt(self):
        """Initialize MQTT client"""
        try:
            import paho.mqtt.client as mqtt

            self.client = mqtt.Client()
            self.client.on_connect    = self._on_connect
            self.client.on_message    = self._on_message
            self.client.on_disconnect = self._on_disconnect

            self.client.connect(self.broker, self.port, keepalive=60)
            self.client.loop_start()
            print(f"✅ MQTT connected to {self.broker}:{self.port}")
        except Exception as e:
            print(f"⚠️  MQTT unavailable: {e} — using HTTP fallback")
            self.client = None

    def _on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.connected = True
            print("📡 MQTT broker connected")
            # Subscribe to all fleet topics
            client.subscribe("fleet/#")
        else:
            print(f"❌ MQTT connection failed: rc={rc}")

    def _on_message(self, client, userdata, msg):
        try:
            payload = json.loads(msg.payload.decode())
            self.messages.append({
                "topic":   msg.topic,
                "payload": payload
            })
            if len(self.messages) > 100:
                self.messages.pop(0)
        except:
            pass

    def _on_disconnect(self, client, userdata, rc):
        self.connected = False
        print("⚠️  MQTT disconnected")

    def publish(self, topic: str, payload: dict) -> bool:
        """Publish message to MQTT topic"""
        if self.client and self.connected:
            try:
                self.client.publish(topic, json.dumps(payload))
                return True
            except Exception as e:
                print(f"❌ MQTT publish error: {e}")
                return False
        return False

    def send_to_thingsboard(self, token: str, data: dict) -> bool:
        """HTTP fallback — send directly to ThingsBoard"""
        try:
            url = f"{TB_BASE_URL}/{token}/telemetry"
            r   = requests.post(url, json=data, timeout=5)
            return r.status_code == 200
        except Exception as e:
            print(f"❌ TB HTTP error: {e}")
            return False

    def stop(self):
        if self.client:
            self.client.loop_stop()
            self.client.disconnect()
            print("🛑 MQTT client stopped")