import requests
import threading
from config import TB_BASE_URL, RPC_TIMEOUT


class ThingsBoardClient:

    def __init__(self, device_id: str, token: str):
        self.device_id = device_id
        self.token = token
        self.base_url = f"{TB_BASE_URL}/{token}"
        self.rpc_callbacks = {}

    def send_telemetry(self, data: dict) -> bool:
        try:
            clean = {k: int(v) if isinstance(v, bool) else v for k, v in data.items()}
            r = requests.post(f"{self.base_url}/telemetry", json=clean, timeout=5)
            return r.status_code == 200
        except Exception as e:
            print(f"❌ [{self.device_id}] Telemetry error: {e}")
            return False

    def send_attributes(self, data: dict) -> bool:
        try:
            r = requests.post(f"{self.base_url}/attributes", json=data, timeout=5)
            return r.status_code == 200
        except:
            return False

    def listen_rpc(self, callback):
        def _listen():
            print(f"👂 [{self.device_id}] Listening for RPC...")
            while True:
                try:
                    r = requests.get(f"{self.base_url}/rpc", timeout=RPC_TIMEOUT)
                    if r.status_code == 200:
                        cmd = r.json()
                        print(f"📨 [{self.device_id}] RPC: {cmd.get('method')}")
                        result = callback(cmd)
                        requests.post(
                            f"{self.base_url}/rpc/{cmd['id']}",
                            json=result or {"status": "ok"},
                            timeout=5
                        )
                except:
                    pass
        t = threading.Thread(target=_listen)
        t.daemon = True
        t.start()
        return t