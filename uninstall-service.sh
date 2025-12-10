#!/bin/bash

# Uninstall systemd service for yt-mcp-server

set -e

SERVICE_NAME="yt-mcp-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"

echo "🗑️  Uninstalling systemd service for ${SERVICE_NAME}..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges to uninstall systemd service."
    echo "   Re-running with sudo..."
    sudo "$0" "$@"
    exit $?
fi

# Stop the service if running
if systemctl is-active --quiet ${SERVICE_NAME}; then
    echo "⏸️  Stopping service..."
    systemctl stop ${SERVICE_NAME}
fi

# Disable the service if enabled
if systemctl is-enabled --quiet ${SERVICE_NAME}; then
    echo "🔓 Disabling service..."
    systemctl disable ${SERVICE_NAME}
fi

# Remove service file
if [ -f "${SERVICE_FILE}" ]; then
    echo "🗑️  Removing service file..."
    rm "${SERVICE_FILE}"
fi

# Reload systemd
systemctl daemon-reload

echo "✅ Service uninstalled successfully!"
