import random
import math
from config import IMU_NOISE, UPDATE_INTERVAL

class ESP32Simulator:
    """
    Simulates ESP32 microcontroller with:
    - WiFi connectivity
    - MQTT publisher
    - Sensor fusion (temperature, humidity, battery)
    - Communication with STM32
    """

    def __init__(self, unit_id: int):
        self.unit_id     = unit_id
        self.time        = 0.0
        self.dt          = UPDATE_INTERVAL
        self.wifi_rssi   = -65       # dBm
        self.battery     = 100.0     # %
        self.temperature = 25.0      # °C (MCU temp)
        self.connected   = True

    def get_wifi_status(self) -> dict:
        """Simulate WiFi signal variation"""
        self.wifi_rssi += random.gauss(0, 2)
        self.wifi_rssi  = max(-90, min(-40, self.wifi_rssi))
        return {
            "wifi_rssi":   round(self.wifi_rssi, 1),
            "wifi_quality": self._rssi_to_quality(self.wifi_rssi),
            "connected":   1,
        }

    def _rssi_to_quality(self, rssi: float) -> int:
        """Convert RSSI to quality percentage"""
        if rssi >= -50:  return 100
        if rssi <= -100: return 0
        return int(2 * (rssi + 100))

    def get_system_status(self) -> dict:
        """Get ESP32 system health"""
        self.time        += self.dt
        self.battery     -= random.uniform(0, 0.01)
        self.battery      = max(0, self.battery)
        self.temperature += random.gauss(0, 0.3)
        self.temperature  = max(20, min(85, self.temperature))

        # Occasional packet loss simulation
        packet_loss = random.random() < 0.02

        return {
            "battery_pct":   round(self.battery, 2),
            "mcu_temp_c":    round(self.temperature, 2),
            "heap_free_kb":  round(random.uniform(100, 250), 1),
            "uptime_s":      round(self.time, 1),
            "packet_loss":   int(packet_loss),
            "mqtt_connected": int(not packet_loss),
        }

    def get_all(self) -> dict:
        """Get complete ESP32 reading"""
        data = {
            "unit_id": f"ESP32_{self.unit_id}",
        }
        data.update(self.get_wifi_status())
        data.update(self.get_system_status())
        return data

    def reset(self):
        self.__init__(self.unit_id)