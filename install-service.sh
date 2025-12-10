#!/bin/bash

# Install systemd service for yt-mcp-server

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SERVICE_NAME="yt-mcp-server"
SERVICE_FILE="/etc/systemd/system/${SERVICE_NAME}.service"
TEMPLATE_FILE="${SCRIPT_DIR}/yt-mcp-server.service.template"

echo "📦 Installing systemd service for ${SERVICE_NAME}..."

# Check if running as root
if [ "$EUID" -ne 0 ]; then 
    echo "⚠️  This script needs sudo privileges to install systemd service."
    echo "   Re-running with sudo..."
    sudo "$0" "$@"
    exit $?
fi

# Replace placeholders in template
sed -e "s|%USER%|${SUDO_USER}|g" \
    -e "s|%WORKDIR%|${SCRIPT_DIR}|g" \
    -e "s|%HOME%|/home/${SUDO_USER}|g" \
    "${TEMPLATE_FILE}" > "${SERVICE_FILE}"

echo "✅ Service file created at: ${SERVICE_FILE}"

# Reload systemd
systemctl daemon-reload

echo "✅ Systemd daemon reloaded"
echo ""
echo "📝 Service installed successfully!"
echo ""
echo "To start the service:"
echo "   sudo systemctl start ${SERVICE_NAME}"
echo ""
echo "To enable auto-start on boot:"
echo "   sudo systemctl enable ${SERVICE_NAME}"
echo ""
echo "To check status:"
echo "   sudo systemctl status ${SERVICE_NAME}"
echo ""
echo "To view logs:"
echo "   sudo journalctl -u ${SERVICE_NAME} -f"
