# DDoS Simulator for Astronomy App (EKS)

Simulates a DDoS-style attack on the `/checkout` route of the Astronomy Demo app.  
Generates high-volume requests with randomized attacker IPs and emits structured JSON logs. These logs can be shipped to Observe for demoing security signal ingestion and trace correlation.

---

## Usage

### 1. Set Your AWS ECR Details

In `Makefile`, update:
- `AWS_REGION` (e.g., `us-west-2`)
- `PROJECT_NAME` (default: `ddos-sim`)

These values are used to tag and push the Docker image.

---

### 2. Create ECR Repo (one-time setup)

```bash
aws ecr create-repository --repository-name ddos-sim
```

### 3. Build and Push the Image to ECR

```bash
make push
```

This will:
* Build the Docker image
* Tag it with your AWS account ID and region
* Authenticate with ECR
* Push the image to your private repo

### 4. Deploy CronJob to EKS

```bash
make deploy
```

This creates a Kubernetes CronJob in the astronomy namespace that runs every `10 minutes by default`.

You can modify the schedule or concurrency behavior in `k8s/ddos-cronjob.yaml`.

### 5. Confirm Logs Are Flowing

To view logs from the most recent run:
```bash
kubectl logs -n astronomy job/$(kubectl get jobs -n astronomy --sort-by=.metadata.creationTimestamp | tail -1 | awk '{print $1}')
```

You should see structured logs like: 

```bash
{
  "timestamp": "2025-03-26T00:39:34.592263Z",
  "geo": {
    "lat": 23.1291,
    "lon": 113.2644,
    "country": "CN"
  },
  "network": {
    "source_ip": "203.0.113.12",
    "asn": "AS4134",
    "traceroute": [
      "10.190.170.61",
      "10.46.63.159",
      "10.31.25.136",
      "10.225.17.17",
      "10.225.205.142",
      "10.76.217.97"
    ]
  },
  "http": {
    "method": "UNKNOWN",
    "status": 599,
    "latency": null
  },
  "attack_vector": "http_flood",
  "suspicious": true,
  "attack_type": "ddos"
}
```