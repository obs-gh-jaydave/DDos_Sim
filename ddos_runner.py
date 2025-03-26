# # ddos_runner.py
# import logging
# import random
# import time
# import json
# import requests
# from datetime import datetime

# ip_pool = ["203.0.113.1", "203.0.113.2", "203.0.113.3"]
# TARGET_URL = "http://astronomy-app.checkout.svc.cluster.local/checkout"
# ATTACK_DURATION = 60  # seconds
# REQ_PER_SECOND = 10

# logging.basicConfig(level=logging.INFO)

# def emit_log(ip, status_code):
#     log_entry = {
#         "event": "ddos_simulated_request",
#         "timestamp": datetime.utcnow().isoformat() + "Z",
#         "source_ip": ip,
#         "target": "/checkout",
#         "status_code": status_code,
#         "suspicious": True,
#         "attack_type": "ddos"
#     }
#     print(json.dumps(log_entry))

# def run_attack():
#     end_time = time.time() + ATTACK_DURATION
#     while time.time() < end_time:
#         for _ in range(REQ_PER_SECOND):
#             ip = random.choice(ip_pool)
#             headers = {"X-Forwarded-For": ip}
#             try:
#                 r = requests.get(TARGET_URL, headers=headers, timeout=1)
#                 emit_log(ip, r.status_code)
#             except Exception:
#                 emit_log(ip, "timeout")
#         time.sleep(1)

# if __name__ == "__main__":
#     run_attack()

import logging
import random
import time
import json
import requests
import sys
from datetime import datetime

# IP pools with geographic data from the document
china_ips = [
    {"ip": "203.0.113.10", "lat": 39.9042, "lon": 116.4074},  # Beijing
    {"ip": "203.0.113.11", "lat": 31.2304, "lon": 121.4737},  # Shanghai
    {"ip": "203.0.113.12", "lat": 23.1291, "lon": 113.2644}   # Guangzhou
]

russia_ips = [
    {"ip": "203.0.113.20", "lat": 55.7558, "lon": 37.6173},   # Moscow
    {"ip": "203.0.113.21", "lat": 59.9343, "lon": 30.3351},   # St. Petersburg
    {"ip": "203.0.113.22", "lat": 54.9833, "lon": 73.3667}    # Omsk
]

# Attack vector configurations with weighted distribution
ATTACK_VECTORS = {
    "http_flood": {
        "method": "GET",
        "path": "/checkout",
        "rate": 0.7
    },
    "slowloris": {
        "method": "POST",
        "path": "/api",
        "rate": 0.2
    },
    "udp_amplification": {
        "method": "UDP",
        "rate": 0.1
    }
}

TARGET_URL = "http://astronomy-app.checkout.svc.cluster.local"
ATTACK_DURATION = 60  # seconds
REQ_PER_SECOND = 10

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

# Safeguards configuration
SAFEGUARDS = {
    "dns_resolution": "astronomy-app.checkout.svc.cluster.local",
    "ip_whitelist": ["192.168.0.0/16", "10.0.0.0/8"],
    "rate_limit": "1000/5s"
}

class RateLimiter:
    def __init__(self, max_rps):
        self.interval = 1 / max_rps
        self.last_request = 0
    
    def acquire(self):
        elapsed = time.time() - self.last_request
        wait_time = max(0, self.interval - elapsed)
        time.sleep(wait_time)
        self.last_request = time.time()
        
    def __enter__(self):
        self.acquire()
        return self
        
    def __exit__(self, exc_type, exc_val, exc_tb):
        pass

def random_user_agent():
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/14.1.1 Safari/605.1.15",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/92.0.4515.107 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:90.0) Gecko/20100101 Firefox/90.0"
    ]
    return random.choice(user_agents)

def simulate_asn(ip):
    # Simulate autonomous system number based on IP address
    asn_map = {
        "203.0.113.10": "AS4808",  # China Unicom
        "203.0.113.11": "AS4812",  # China Telecom
        "203.0.113.12": "AS4134",  # China Telecom
        "203.0.113.20": "AS8997",  # MTS Russia
        "203.0.113.21": "AS31133", # MegaFon
        "203.0.113.22": "AS12389"  # Rostelecom
    }
    return asn_map.get(ip, "AS" + str(random.randint(1000, 60000)))

def generate_traceroute():
    # Generate a simplified traceroute path
    hops = random.randint(3, 8)
    return ["10.{}.{}.{}".format(random.randint(0, 255), random.randint(0, 255), random.randint(0, 255)) for _ in range(hops)]

def generate_vector():
    seed = random.random()
    for vector, config in ATTACK_VECTORS.items():
        if seed <= config["rate"]:
            return vector, config
        seed -= config["rate"]
    return "http_flood", ATTACK_VECTORS["http_flood"]

def build_request(target):
    vector_name, vector = generate_vector()
    origin = random.choice(china_ips + russia_ips)
    
    headers = {
        "X-Forwarded-For": origin["ip"],
        "User-Agent": random_user_agent(),
        "CF-Connecting-IP": origin["ip"]
    }
    
    url = f"{target}{vector['path']}"
    timeout = (3, 1) if vector["method"] == "POST" else 1
    
    return origin, vector_name, {
        "method": vector["method"],
        "url": url,
        "headers": headers,
        "timeout": timeout
    }

def emit_log(origin, vector_name, response):
    status_code = response.status_code if response else 599
    latency = response.elapsed.total_seconds() if response else None
    
    log_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "geo": {
            "lat": origin["lat"],
            "lon": origin["lon"],
            "country": "CN" if origin in china_ips else "RU"
        },
        "network": {
            "source_ip": origin["ip"],
            "asn": simulate_asn(origin["ip"]),
            "traceroute": generate_traceroute()
        },
        "http": {
            "method": response.request.method if response else "UNKNOWN",
            "status": status_code,
            "latency": latency
        },
        "attack_vector": vector_name,
        "suspicious": True,
        "attack_type": "ddos"
    }
    logging.info(json.dumps(log_entry))

def validate_environment():
    # Simplified validation - in a real implementation, would perform DNS resolution
    if not TARGET_URL.endswith(SAFEGUARDS["dns_resolution"]):
        logging.critical("Environment validation failed: Invalid target URL")
        sys.exit(1)
    logging.info("Environment validation passed")

def send_request(session, request_config):
    try:
        return session.request(**request_config)
    except requests.RequestException:
        return None

def run_attack():
    validate_environment()
    
    session = requests.Session()
    limiter = RateLimiter(REQ_PER_SECOND)
    
    end_time = time.time() + ATTACK_DURATION
    logging.info(f"Starting DDoS simulation for {ATTACK_DURATION} seconds")
    
    while time.time() < end_time:
        with limiter:
            origin, vector_name, request_config = build_request(TARGET_URL)
            response = send_request(session, request_config)
            emit_log(origin, vector_name, response)
    
    logging.info("DDoS simulation completed")

if __name__ == "__main__":
    run_attack()