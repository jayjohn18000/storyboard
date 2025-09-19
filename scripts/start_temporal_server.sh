#!/bin/bash
"""Startup script for Temporal Server.

This script starts the Temporal server with the legal-sim namespace
and development configuration.
"""

set -e

# Configuration
TEMPORAL_HOST=${TEMPORAL_HOST:-"localhost:7233"}
TEMPORAL_NAMESPACE=${TEMPORAL_NAMESPACE:-"legal-sim"}
TEMPORAL_CONFIG=${TEMPORAL_CONFIG:-"./temporal/config/dynamicconfig/development.yaml"}

echo "Starting Temporal Server..."
echo "Host: $TEMPORAL_HOST"
echo "Namespace: $TEMPORAL_NAMESPACE"
echo "Config: $TEMPORAL_CONFIG"

# Check if temporal CLI is installed
if ! command -v temporal &> /dev/null; then
    echo "Temporal CLI not found. Installing..."
    
    # Install Temporal CLI
    case "$(uname -s)" in
        Darwin*)
            # macOS
            curl -sSf https://temporal.download/cli.sh | sh
            ;;
        Linux*)
            # Linux
            curl -sSf https://temporal.download/cli.sh | sh
            ;;
        *)
            echo "Unsupported OS. Please install Temporal CLI manually."
            exit 1
            ;;
    esac
fi

# Start Temporal server
echo "Starting Temporal server with development configuration..."

# Create namespace if it doesn't exist
temporal operator namespace create $TEMPORAL_NAMESPACE --retention 7d || true

# Start server (this would typically be done with docker-compose or systemd)
echo "Temporal server configuration complete."
echo "To start the server, run:"
echo "  docker-compose up temporal"
echo "Or install Temporal server locally and run:"
echo "  temporal server start-dev --dynamic-config-value-file $TEMPORAL_CONFIG"
