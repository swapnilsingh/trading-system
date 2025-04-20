#!/bin/bash

set -e

echo "🚀 Building and pushing indicator-api..."
docker build -t 192.168.1.200:30000/indicator-api:latest -f services/indicator_api/Dockerfile .
docker push 192.168.1.200:30000/indicator-api:latest

echo "🚀 Building and pushing ohlcv-api..."
docker build -t 192.168.1.200:30000/ohlcv-api:latest -f services/ohlcv_api/Dockerfile .
docker push 192.168.1.200:30000/ohlcv-api:latest

echo "🚀 Building and pushing websocket-api..."
docker build -t 192.168.1.200:30000/websocket-api:latest -f services/websocket_api/Dockerfile .
docker push 192.168.1.200:30000/websocket-api:latest

echo "🐳 Tagging and pushing ARM-compatible Redis..."
docker tag redis:7 192.168.1.200:30000/redis:7
docker push 192.168.1.200:30000/redis:7

echo "✅ All services and Redis pushed successfully!"
