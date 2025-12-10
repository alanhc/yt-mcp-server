#!/bin/bash

# Simple deployment script using screen or tmux

set -e

SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
SESSION_NAME="yt-mcp-server"

echo "🚀 Starting yt-mcp-server in background..."

# Check if screen is available
if command -v screen &> /dev/null; then
    echo "📺 Using screen..."
    
    # Kill existing session if it exists
    screen -S ${SESSION_NAME} -X quit 2>/dev/null || true
    
    # Start new screen session
    screen -dmS ${SESSION_NAME} bash -c "cd ${SCRIPT_DIR} && ./start_server.sh"
    
    echo "✅ Server started in screen session: ${SESSION_NAME}"
    echo ""
    echo "To attach to the session:"
    echo "   screen -r ${SESSION_NAME}"
    echo ""
    echo "To detach from session: Ctrl+A, then D"
    echo ""
    echo "To stop the server:"
    echo "   ./simple-stop.sh"
    
elif command -v tmux &> /dev/null; then
    echo "📺 Using tmux..."
    
    # Kill existing session if it exists
    tmux kill-session -t ${SESSION_NAME} 2>/dev/null || true
    
    # Start new tmux session
    tmux new-session -d -s ${SESSION_NAME} "cd ${SCRIPT_DIR} && ./start_server.sh"
    
    echo "✅ Server started in tmux session: ${SESSION_NAME}"
    echo ""
    echo "To attach to the session:"
    echo "   tmux attach -t ${SESSION_NAME}"
    echo ""
    echo "To detach from session: Ctrl+B, then D"
    echo ""
    echo "To stop the server:"
    echo "   ./simple-stop.sh"
    
else
    echo "❌ Neither screen nor tmux is installed."
    echo "   Please install one of them:"
    echo "   sudo apt-get install screen"
    echo "   or"
    echo "   sudo apt-get install tmux"
    exit 1
fi
