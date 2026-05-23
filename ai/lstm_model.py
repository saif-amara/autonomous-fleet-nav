import numpy as np
import os
from config import SEQUENCE_LEN, ANOMALY_THRESH, MODEL_PATH

class LSTMAnomalyDetector:
    """
    LSTM-based anomaly detector for INS/GPS data
    Uses reconstruction error to detect anomalies
    """

    def __init__(self):
        self.sequence_len  = SEQUENCE_LEN
        self.threshold     = ANOMALY_THRESH
        self.model         = None
        self.buffer        = []
        self.trained       = False
        self.feature_names = [
            "accel_x", "accel_y", "accel_z",
            "gyro_x",  "gyro_y",  "gyro_z",
            "drift_error", "innovation_avg", "position_error"
        ]
        self.n_features = len(self.feature_names)

        # Running stats for normalization
        self.mean = np.zeros(self.n_features)
        self.std  = np.ones(self.n_features)
        self.n_samples = 0

    def _normalize(self, x: np.ndarray) -> np.ndarray:
        """Normalize input features"""
        return (x - self.mean) / (self.std + 1e-8)

    def _update_stats(self, x: np.ndarray):
        """Online mean/std update"""
        self.n_samples += 1
        delta      = x - self.mean
        self.mean += delta / self.n_samples
        delta2     = x - self.mean
        self.std   = np.sqrt(
            ((self.n_samples - 1) * self.std**2 + delta * delta2)
            / self.n_samples + 1e-8
        )

    def build_model(self):
        """Build LSTM autoencoder"""
        try:
            from tensorflow.keras.models import Sequential
            from tensorflow.keras.layers import LSTM, Dense, RepeatVector, TimeDistributed
            from tensorflow.keras.optimizers import Adam

            model = Sequential([
                LSTM(64, activation='relu',
                     input_shape=(self.sequence_len, self.n_features),
                     return_sequences=False),
                RepeatVector(self.sequence_len),
                LSTM(64, activation='relu', return_sequences=True),
                TimeDistributed(Dense(self.n_features))
            ])
            model.compile(optimizer=Adam(0.001), loss='mse')
            self.model = model
            print("✅ LSTM model built successfully")
            return True
        except ImportError:
            print("⚠️  TensorFlow not found — using statistical detector")
            return False

    def add_sample(self, features: dict) -> dict:
        """Add new sample and detect anomaly"""
        # Extract features
        x = np.array([features.get(f, 0.0) for f in self.feature_names])
        self._update_stats(x)
        x_norm = self._normalize(x)

        # Add to buffer
        self.buffer.append(x_norm)
        if len(self.buffer) > self.sequence_len:
            self.buffer.pop(0)

        # Detect anomaly
        if len(self.buffer) >= 10:
            score, is_anomaly = self._detect(x_norm)
        else:
            score, is_anomaly = 0.0, False

        return {
            "anomaly_score":   round(score, 4),
            "is_anomaly":      int(is_anomaly),
            "buffer_size":     len(self.buffer),
            "detector_ready":  int(len(self.buffer) >= 10),
        }

    def _detect(self, x_norm: np.ndarray) -> tuple:
        """Statistical anomaly detection (fallback when no TF)"""
        if self.model and self.trained:
            return self._lstm_detect()

        # Statistical: z-score based
        recent = np.array(self.buffer[-10:])
        mean_r = recent.mean(axis=0)
        std_r  = recent.std(axis=0) + 1e-8
        z_score = np.abs((x_norm - mean_r) / std_r).mean()
        score   = min(z_score / 5.0, 1.0)
        return score, score > self.threshold

    def _lstm_detect(self) -> tuple:
        """LSTM reconstruction error detection"""
        seq = np.array(self.buffer[-self.sequence_len:])
        seq = seq[np.newaxis, :, :]
        reconstruction = self.model.predict(seq, verbose=0)
        error = np.mean(np.abs(seq - reconstruction))
        score = min(error * 10, 1.0)
        return score, score > self.threshold

    def reset(self):
        self.buffer    = []
        self.n_samples = 0
        self.mean      = np.zeros(self.n_features)
        self.std       = np.ones(self.n_features)
        print("🔄 LSTM detector reset")