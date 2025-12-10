#!/bin/bash

# Docker deployment script for yt-mcp-server

set -e

CONTAINER_NAME="yt-mcp-server"
IMAGE_NAME="yt-mcp-server:latest"
PORT=8000

echo "🐳 Starting Docker deployment for yt-mcp-server..."

# Check if container is already running
if docker ps -a --format '{{.Names}}' | grep -q "^${CONTAINER_NAME}$"; then
    echo "⚠️  Container ${CONTAINER_NAME} already exists. Stopping and removing..."
    docker stop ${CONTAINER_NAME} 2>/dev/null || true
    docker rm ${CONTAINER_NAME} 2>/dev/null || true
fi

# Build the Docker image
echo "🔨 Building Docker image..."
docker build -t ${IMAGE_NAME} .

# Check if .env file exists
if [ ! -f .env ]; then
    echo "⚠️  Warning: .env file not found. Please create one based on .env.example"
    echo "   The container will start but may not function properly without API keys."
fi

# Check if GPU is available
if command -v nvidia-smi &> /dev/null; then
    echo "✅ NVIDIA GPU detected. Starting container with GPU support..."
    docker run -d \
        --name ${CONTAINER_NAME} \
        --gpus all \
        -p ${PORT}:8000 \
        -v "$(pwd)/.cache:/app/.cache" \
        -v "$(pwd)/.env:/app/.env" \
        --restart unless-stopped \
        ${IMAGE_NAME}
else
    echo "⚠️  No GPU detected. Starting container in CPU mode..."
    echo "   Note: The application is configured for GPU-only mode and may fail to start."
    docker run -d \
        --name ${CONTAINER_NAME} \
        -p ${PORT}:8000 \
        -v "$(pwd)/.cache:/app/.cache" \
        -v "$(pwd)/.env:/app/.env" \
        --restart unless-stopped \
        ${IMAGE_NAME}
fi

echo ""
echo "✅ Container started successfully!"
echo ""
echo "📊 Container status:"
docker ps --filter "name=${CONTAINER_NAME}"
echo ""
echo "📝 To view logs, run:"
echo "   docker logs -f ${CONTAINER_NAME}"
echo ""
echo "🌐 API should be available at:"
echo "   http://localhost:${PORT}"
echo ""
echo "🛑 To stop the container, run:"
echo "   ./docker-stop.sh"
