#!/bin/bash

set -e

RELEASE_NAME="trading-engine"
NAMESPACE="trading"
HELM_PATH="helm/trading-engine"
VALUES_FILE="helm/trading-engine/values.yaml"  # Path to the values.yaml for the Helm chart
NODE="rpslave1"  # Default node for indicator-api, can be updated

usage() {
  echo "Usage:"
  echo "  $0 start [node_name]  # Deploy using configured nodeSelectors for indicator-api (optionally specify node)"
  echo "  $0 stop               # Delete the Helm release"
  exit 1
}

start() {
  # Update the nodeSelector for indicator-api
  if [ -n "$1" ]; then
    NODE="$1"  # Override the default node if user provides one
  fi
  echo "🏷️  Setting nodeSelector for indicator-api to node: $NODE"
  
  # Update the nodeSelector in values.yaml
  yq eval ".indicator-api.nodeSelector.\"kubernetes.io/hostname\" = \"$NODE\"" -i "$VALUES_FILE"
  yq eval ".ohlcv-api.nodeSelector.\"kubernetes.io/hostname\" = \"$NODE\"" -i "$VALUES_FILE"
  yq eval ".websocket-api.nodeSelector.\"kubernetes.io/hostname\" = \"$NODE\"" -i "$VALUES_FILE"

  echo "🚀 Deploying trading engine using values from $VALUES_FILE..."
  helm upgrade --install "$RELEASE_NAME" "$HELM_PATH" -n "$NAMESPACE" --create-namespace -f "$VALUES_FILE"
}

stop() {
  echo "🛑 Stopping Helm release [$RELEASE_NAME]..."
  helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || echo "Release not found."
}

# --- Main Execution ---
case "$1" in
  start)
    start "$2"  # Pass the second argument (node name) to start function
    ;;
  stop)
    stop
    ;;
  *)
    usage
    ;;
esac
