#!/bin/bash

# Docker stop script for yt-mcp-server

CONTAINER_NAME="yt-mcp-server"

echo "🛑 Stopping yt-mcp-server Docker container..."

# Check if container exists
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    # Stop the container
    echo "⏸️  Stopping container..."
    docker stop ${CONTAINER_NAME}
    
    # Remove the container
    echo "🗑️  Removing container..."
    docker rm ${CONTAINER_NAME}
    
    echo "✅ Container stopped and removed successfully!"
else
    echo "⚠️  Container ${CONTAINER_NAME} not found."
    echo "   Nothing to stop."
fi

echo ""
echo "💡 To start the container again, run:"
echo "   ./docker-start.sh"
