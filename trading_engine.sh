#!/bin/bash

set -e

RELEASE_NAME="trading-engine"
NAMESPACE="trading"
HELM_PATH="helm/trading-engine"
GLOBAL_CONFIG="values.global.yaml"

usage() {
  echo "Usage:"
  echo "  $0 start   # Deploy using configured nodeSelectors and registry"
  echo "  $0 stop    # Delete the Helm release"
  exit 1
}

start() {
  echo "🛠️  Updating image repositories to internal registry..."
  yq eval '.global.image.repository = "registry.devops.svc.cluster.local:30000"' -i "$GLOBAL_CONFIG"

  echo "🚀 Deploying trading engine using values from $GLOBAL_CONFIG..."
  helm upgrade --install "$RELEASE_NAME" "$HELM_PATH" -n "$NAMESPACE" --create-namespace -f "$GLOBAL_CONFIG"
}

stop() {
  echo "🛑 Stopping Helm release [$RELEASE_NAME]..."
  helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || echo "Release not found."
}

# --- Main Execution ---
case "$1" in
  start)
    start
    ;;
  stop)
    stop
    ;;
  *)
    usage
    ;;
esac
