#!/bin/bash

set -e

RELEASE_NAME="trading-engine"
NAMESPACE="trading"
HELM_PATH="helm/trading-engine"
GLOBAL_CONFIG="values.global.yaml"

usage() {
  echo "Usage:"
  echo "  $0 start <node-name>    # Deploy all containers to the given node"
  echo "  $0 stop                 # Delete the Helm release"
  exit 1
}

start() {
  NODE=$1

  if [[ -z "$NODE" ]]; then
    echo "❌ Error: Node name not provided."
    usage
  fi

  echo "🚀 Updating nodeSelector in $GLOBAL_CONFIG to $NODE..."
  yq eval ".global.nodeSelector.\"kubernetes.io/hostname\" = \"$NODE\"" -i "$GLOBAL_CONFIG"

  echo "✅ Deploying trading engine to node [$NODE]..."
  helm upgrade --install "$RELEASE_NAME" "$HELM_PATH" -n "$NAMESPACE" -f "$GLOBAL_CONFIG"
}

stop() {
  echo "🛑 Stopping all containers in [$RELEASE_NAME]..."
  helm uninstall "$RELEASE_NAME" -n "$NAMESPACE" || echo "Release not found."
}

# --- Main Execution ---
case "$1" in
  start)
    start "$2"
    ;;
  stop)
    stop
    ;;
  *)
    usage
    ;;
esac
