#!/bin/bash
set -e

echo "🚀 Starting URL Shortener DevOps Environment..."

# 1. Start minikube if not running
if ! minikube status &>/dev/null; then
    echo "▶️  Starting Minikube..."
    minikube start
else
    echo "✅ Minikube is already running."
fi

# 2. Apply manifests
echo "📦 Applying core application manifests..."
kubectl apply -k k8s/

echo "📊 Applying monitoring stack manifests..."
kubectl apply -f k8s/monitoring/

# 3. Wait for all pods to be Running
echo "⏳ Waiting for all deployments in url-shortener namespace to be Ready..."
kubectl wait --for=condition=available deployment --all -n url-shortener --timeout=120s

echo "⏳ Waiting for all pods to be fully initialized..."
kubectl wait --for=condition=Ready pod --all -n url-shortener --timeout=120s

# 4. Print all service URLs
echo ""
echo "🔗 Service URLs:"
echo "----------------------------------------"
echo "⚠️  Mac/Docker users: You must run these commands in separate terminal tabs"
echo "to open the tunnels and keep them running!"
echo ""
echo "🌐 App         : minikube service url-shortener -n url-shortener --url"
echo "📈 Prometheus  : minikube service prometheus -n url-shortener --url"
echo "📊 Grafana     : minikube service grafana -n url-shortener --url"
echo "🚨 AlertManager: minikube service alertmanager -n url-shortener --url"
echo "----------------------------------------"
echo ""

# 5. Print completion message
echo "✅ All systems go!"
echo "Once you open your App tunnel, you can visit the UI in your browser or test the API:"
echo ""
echo "curl -X POST \"http://127.0.0.1:<YOUR_APP_PORT>/shorten\" \\"
echo "     -H \"Content-Type: application/json\" \\"
echo "     -d '{\"url\": \"https://www.github.com\"}'"
echo ""
