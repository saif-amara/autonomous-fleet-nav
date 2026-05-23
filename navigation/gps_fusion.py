import math
import numpy as np
from config import GPS_NOISE

class GPSFusion:
    """
    Fuses GPS coordinates with INS position estimates
    Converts GPS (lat/lon/alt) to local frame (x/y/z meters)
    """

    def __init__(self, unit_id: int):
        self.unit_id    = unit_id
        self.origin_lat = None
        self.origin_lon = None
        self.origin_alt = None
        self.initialized = False

    def _gps_to_local(self, lat, lon, alt) -> list:
        """Convert GPS coordinates to local NED frame (meters)"""
        R = 6371000.0   # Earth radius in meters
        dlat = math.radians(lat - self.origin_lat)
        dlon = math.radians(lon - self.origin_lon)
        x = R * dlon * math.cos(math.radians(self.origin_lat))
        y = R * dlat
        z = alt - self.origin_alt
        return [x, y, z]

    def fuse(self, gps: dict, kalman_pos: list) -> dict:
        """Fuse GPS with Kalman position estimate"""
        lat = gps["latitude"]
        lon = gps["longitude"]
        alt = gps["altitude"]

        # Initialize origin on first reading
        if not self.initialized:
            self.origin_lat  = lat
            self.origin_lon  = lon
            self.origin_alt  = alt
            self.initialized = True

        # Convert GPS to local frame
        gps_local = self._gps_to_local(lat, lon, alt)

        # Fusion — weighted average
        w_gps    = 0.3
        w_kalman = 0.7
        fused = [
            w_gps * gps_local[i] + w_kalman * kalman_pos[i]
            for i in range(3)
        ]

        # Position error (GPS vs Kalman)
        error = math.sqrt(sum((gps_local[i] - kalman_pos[i])**2 for i in range(3)))

        return {
            "gps_local_x":  round(gps_local[0], 3),
            "gps_local_y":  round(gps_local[1], 3),
            "gps_local_z":  round(gps_local[2], 3),
            "fused_x":      round(fused[0], 3),
            "fused_y":      round(fused[1], 3),
            "fused_z":      round(fused[2], 3),
            "position_error": round(error, 4),
            "latitude":     round(lat, 6),
            "longitude":    round(lon, 6),
            "altitude":     round(alt, 2),
        }

    def reset(self):
        self.__init__(self.unit_id)