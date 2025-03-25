# ddos_runner.py
import logging
import random
import time
import json
import requests
from datetime import datetime

ip_pool = ["203.0.113.1", "203.0.113.2", "203.0.113.3"]
TARGET_URL = "http://astronomy-app.checkout.svc.cluster.local/checkout"
ATTACK_DURATION = 60  # seconds
REQ_PER_SECOND = 10

logging.basicConfig(level=logging.INFO)

def emit_log(ip, status_code):
    log_entry = {
        "event": "ddos_simulated_request",
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "source_ip": ip,
        "target": "/checkout",
        "status_code": status_code,
        "suspicious": True,
        "attack_type": "ddos"
    }
    print(json.dumps(log_entry))

def run_attack():
    end_time = time.time() + ATTACK_DURATION
    while time.time() < end_time:
        for _ in range(REQ_PER_SECOND):
            ip = random.choice(ip_pool)
            headers = {"X-Forwarded-For": ip}
            try:
                r = requests.get(TARGET_URL, headers=headers, timeout=1)
                emit_log(ip, r.status_code)
            except Exception:
                emit_log(ip, "timeout")
        time.sleep(1)

if __name__ == "__main__":
    run_attack()