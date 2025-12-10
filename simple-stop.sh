#!/bin/bash

# Simple stop script for screen or tmux session

SESSION_NAME="yt-mcp-server"

echo "🛑 Stopping yt-mcp-server..."

# Try screen first
if screen -list | grep -q "${SESSION_NAME}"; then
    screen -S ${SESSION_NAME} -X quit
    echo "✅ Screen session stopped"
    exit 0
fi

# Try tmux
if tmux list-sessions 2>/dev/null | grep -q "${SESSION_NAME}"; then
    tmux kill-session -t ${SESSION_NAME}
    echo "✅ Tmux session stopped"
    exit 0
fi

echo "⚠️  No running session found with name: ${SESSION_NAME}"
