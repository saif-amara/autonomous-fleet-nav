import numpy as np
import random
import math
from config import IMU_NOISE, GPS_NOISE, BARO_NOISE, DRIFT_RATE

class STM32Simulator:
    """
    Simulates STM32 microcontroller with:
    - 6-DOF IMU (accelerometer + gyroscope)
    - GPS (NMEA-like data)
    - Barometer (altitude)
    """

    def __init__(self, unit_id: int):
        self.unit_id  = unit_id
        self.time     = 0.0
        self.dt       = 0.5

        # True state
        self.true_lat  = 36.8000 + unit_id * 0.001   # Tunis coords
        self.true_lon  = 10.1800 + unit_id * 0.001
        self.true_alt  = 50.0
        self.true_vel  = np.array([0.0, 0.0, 0.0])   # vx, vy, vz
        self.true_pos  = np.array([0.0, 0.0, 0.0])   # x, y, z (meters)
        self.heading   = 0.0   # degrees

        # Drift accumulator
        self.drift     = 0.0

    def _update_true_state(self):
        """Simulate vehicle moving in a circle"""
        self.time    += self.dt
        self.heading  = (self.time * 10) % 360   # rotate 10°/s

        speed = 5.0   # m/s
        rad   = math.radians(self.heading)
        self.true_vel = np.array([
            speed * math.cos(rad),
            speed * math.sin(rad),
            0.1 * math.sin(self.time * 0.1)
        ])
        self.true_pos += self.true_vel * self.dt

        # Update GPS coords
        self.true_lat += self.true_vel[1] * 0.000009
        self.true_lon += self.true_vel[0] * 0.000009
        self.true_alt += self.true_vel[2]

        # Accumulate drift
        self.drift += DRIFT_RATE * self.time * 0.01

    def get_imu(self) -> dict:
        """Get noisy IMU readings"""
        # True acceleration (circular motion)
        rad = math.radians(self.heading)
        true_accel = np.array([
            -math.sin(rad) * 2.0,
             math.cos(rad) * 2.0,
             9.81
        ])

        accel = true_accel + np.random.normal(0, IMU_NOISE, 3)
        gyro  = np.array([
            0.1 * math.sin(self.time),
            0.1 * math.cos(self.time),
            math.radians(10)   # yaw rate
        ]) + np.random.normal(0, IMU_NOISE * 0.5, 3)

        return {
            "accel_x": round(float(accel[0]), 4),
            "accel_y": round(float(accel[1]), 4),
            "accel_z": round(float(accel[2]), 4),
            "gyro_x":  round(float(gyro[0]),  4),
            "gyro_y":  round(float(gyro[1]),  4),
            "gyro_z":  round(float(gyro[2]),  4),
        }

    def get_gps(self) -> dict:
        """Get noisy GPS readings"""
        return {
            "latitude":  round(self.true_lat + random.gauss(0, GPS_NOISE), 6),
            "longitude": round(self.true_lon + random.gauss(0, GPS_NOISE), 6),
            "altitude":  round(self.true_alt + random.gauss(0, BARO_NOISE), 2),
            "speed":     round(float(np.linalg.norm(self.true_vel)), 2),
            "heading":   round(self.heading, 1),
            "fix":       1,
        }

    def get_barometer(self) -> dict:
        """Get barometer reading"""
        return {
            "baro_altitude": round(self.true_alt + random.gauss(0, BARO_NOISE), 2),
            "pressure_hpa":  round(1013.25 * math.exp(-self.true_alt / 8500), 2),
        }

    def get_all(self) -> dict:
        """Get complete STM32 reading"""
        self._update_true_state()
        data = {
            "unit_id":       f"STM32_{self.unit_id}",
            "timestamp":     round(self.time, 1),
            "drift":         round(self.drift, 4),
            "true_x":        round(float(self.true_pos[0]), 2),
            "true_y":        round(float(self.true_pos[1]), 2),
        }
        data.update(self.get_imu())
        data.update(self.get_gps())
        data.update(self.get_barometer())
        return data

    def reset(self):
        self.__init__(self.unit_id)