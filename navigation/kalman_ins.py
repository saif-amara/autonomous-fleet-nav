import numpy as np
from config import THRESHOLDS

class KalmanINS:
    """
    Extended Kalman Filter for INS + GPS fusion
    State: [x, y, z, vx, vy, vz, ax, ay, az]
    """

    def __init__(self, unit_id: int):
        self.unit_id = unit_id
        self.dt      = 0.5
        n            = 9   # state dimension

        # State vector [x, y, z, vx, vy, vz, ax, ay, az]
        self.x = np.zeros((n, 1))

        # State covariance
        self.P = np.eye(n) * 0.1

        # State transition matrix
        dt = self.dt
        self.F = np.eye(n)
        self.F[0, 3] = dt;  self.F[1, 4] = dt;  self.F[2, 5] = dt
        self.F[3, 6] = dt;  self.F[4, 7] = dt;  self.F[5, 8] = dt
        self.F[0, 6] = 0.5*dt**2
        self.F[1, 7] = 0.5*dt**2
        self.F[2, 8] = 0.5*dt**2

        # Process noise
        self.Q = np.eye(n) * 0.01

        # Measurement matrix (GPS measures x, y, z)
        self.H = np.zeros((3, n))
        self.H[0, 0] = 1.0
        self.H[1, 1] = 1.0
        self.H[2, 2] = 1.0

        # Measurement noise
        self.R = np.eye(3) * 0.5

        # Metrics
        self.drift_error  = 0.0
        self.innovations  = []

    def predict(self, accel: list):
        """Predict step using IMU acceleration"""
        u = np.array([[accel[0]], [accel[1]], [accel[2]]])
        B = np.zeros((9, 3))
        B[6, 0] = 1.0; B[7, 1] = 1.0; B[8, 2] = 1.0

        self.x = self.F @ self.x + B @ u
        self.P = self.F @ self.P @ self.F.T + self.Q

        return self.x[:3, 0].tolist()

    def update(self, gps_pos: list):
        """Update step using GPS measurement"""
        z = np.array([[gps_pos[0]], [gps_pos[1]], [gps_pos[2]]])

        innovation = z - self.H @ self.x
        S = self.H @ self.P @ self.H.T + self.R
        K = self.P @ self.H.T @ np.linalg.inv(S)

        self.x = self.x + K @ innovation
        self.P = (np.eye(9) - K @ self.H) @ self.P

        # Track innovation for AI
        self.innovations.append(float(np.linalg.norm(innovation)))
        if len(self.innovations) > 100:
            self.innovations.pop(0)

        return self.x[:3, 0].tolist()

    def get_metrics(self) -> dict:
        pos = self.x[:3, 0]
        vel = self.x[3:6, 0]
        self.drift_error = float(np.linalg.norm(pos)) * 0.001

        return {
            "kalman_x":      round(float(pos[0]), 3),
            "kalman_y":      round(float(pos[1]), 3),
            "kalman_z":      round(float(pos[2]), 3),
            "kalman_vx":     round(float(vel[0]), 3),
            "kalman_vy":     round(float(vel[1]), 3),
            "kalman_vz":     round(float(vel[2]), 3),
            "drift_error":   round(self.drift_error, 4),
            "innovation_avg": round(np.mean(self.innovations) if self.innovations else 0, 4),
            "drift_alert": int(self.drift_error > THRESHOLDS["max_drift"]),
        }

    def reset(self):
        self.__init__(self.unit_id)