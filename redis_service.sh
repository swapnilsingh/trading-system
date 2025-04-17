#!/bin/bash

RELEASE_NAME="redis"
NAMESPACE="trading"
CHART_PATH="./helm/redis"  # ✅ Updated path

ACTION=$1

if [[ -z "$ACTION" ]]; then
  echo "❌ Usage: $0 start|stop"
  exit 1
fi

case "$ACTION" in
  start)
    echo "🚀 Starting Redis Helm release..."
    helm upgrade --install $RELEASE_NAME $CHART_PATH -n $NAMESPACE
    ;;
  stop)
    echo "🛑 Stopping Redis Helm release..."
    helm uninstall $RELEASE_NAME -n $NAMESPACE
    ;;
  *)
    echo "❌ Invalid action: $ACTION"
    echo "Usage: $0 start|stop"
    exit 1
    ;;
esac
