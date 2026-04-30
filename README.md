# URL Shortener DevOps Project

## Project Overview
This project is a minimal URL shortener API built with FastAPI and Redis, designed specifically to demonstrate a complete DevOps workflow. It is fully containerized and orchestrated via Kubernetes, featuring a comprehensive monitoring stack with Prometheus, Grafana, and AlertManager for real-time observability and alerting.

## Architecture Diagram
```text
           +-----------------+
           |      User       |
           +--------+--------+
                    |
                    v (HTTP 8000)
           +--------+--------+      (Storage)     +-------+
           |  FastAPI App    | <----------------> | Redis |
           +--------+--------+                      +-------+
                    |
                    | (Scrapes /metrics)
                    v
           +--------+--------+
           |   Prometheus    |
           +--------+--------+
             |            |
  (Alerts)   |            | (Datasource)
             v            v
+------------+--+      +--+-------------+
| AlertManager  |      |    Grafana     |
+---------------+      +----------------+
```

## Prerequisites
- **Docker**: For building the container images.
- **Minikube**: To run the local Kubernetes cluster.
- **kubectl**: For interacting with the Kubernetes cluster.

## Quick Start
1. **Start Minikube**: Run `minikube start`.
2. **Build the Docker Image**: `docker build -t url-shortener:v1 ./app`
3. **Load Image into Minikube**: `minikube image load url-shortener:v1`
4. **Deploy Everything**: Run `./scripts/start.sh` (or apply manually: `kubectl apply -k k8s/` and `kubectl apply -f k8s/monitoring/`).

## Service URLs
Since this is deployed on Minikube using NodePort services, you can retrieve the URLs dynamically by running `minikube service <name> -n url-shortener --url`.

| Service | Component | Port | Minikube Command |
|---------|-----------|------|------------------|
| **url-shortener** | FastAPI App | 30080 | `minikube service url-shortener -n url-shortener --url` |
| **prometheus** | Prometheus UI | 30090 | `minikube service prometheus -n url-shortener --url` |
| **grafana** | Grafana UI | 30030 | `minikube service grafana -n url-shortener --url` |
| **alertmanager** | AlertManager UI | 30093 | `minikube service alertmanager -n url-shortener --url` |

*Note: Log into Grafana using `admin` / `admin123`.*

## How to Test
1. **Create a Short URL:**
   ```bash
   APP_URL=$(minikube service url-shortener -n url-shortener --url)
   curl -X POST "${APP_URL}/shorten" \
        -H "Content-Type: application/json" \
        -d '{"url": "https://www.google.com"}'
   ```
2. **Test the Redirect:**
   ```bash
   # Replace <SHORT_CODE> with the code returned above
   curl -i ${APP_URL}/<SHORT_CODE>
   ```

## How to Trigger Alerts
We have configured an alert (`HighRedirectRate`) that fires when the redirect rate exceeds 0.5 requests/sec over 1 minute.
To trigger this for a demo, run a loop to hit your short URL repeatedly:
```bash
for i in {1..200}; do 
  curl -s -o /dev/null ${APP_URL}/<SHORT_CODE>
done
```
Wait 15–30 seconds, and the alert will appear as **FIRING** in Prometheus and trigger a webhook via AlertManager!

## Folder Structure
```text
.
├── app/
│   ├── main.py            # FastAPI application
│   ├── config.py          # Environment configuration
│   ├── requirements.txt   # Python dependencies
│   └── Dockerfile         # Docker image definition
├── k8s/
│   ├── kustomization.yaml # Kustomize configuration
│   ├── namespace.yaml     # url-shortener namespace
│   ├── app-deployment.yaml# App Deployment & Service
│   ├── redis-deployment.yaml # Redis Deployment & Service
│   └── monitoring/
│       ├── prometheus-config.yaml
│       ├── prometheus-deployment.yaml
│       ├── prometheus-rules.yaml
│       ├── grafana-datasource.yaml
│       ├── grafana-dashboard-config.yaml
│       ├── grafana-deployment.yaml
│       ├── alertmanager-config.yaml
│       └── alertmanager-deployment.yaml
├── scripts/
│   └── start.sh           # One-click startup script
├── docker-compose.yml     # Local docker-compose alternative
└── README.md
```
