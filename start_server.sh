#!/bin/bash

# Get the directory where this script is located
SCRIPT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Set LD_LIBRARY_PATH to include cuDNN and cuBLAS libraries
export LD_LIBRARY_PATH="$SCRIPT_DIR/.venv/lib/python3.12/site-packages/nvidia/cudnn/lib:$SCRIPT_DIR/.venv/lib/python3.12/site-packages/nvidia/cublas/lib:$LD_LIBRARY_PATH"

echo "✅ Set LD_LIBRARY_PATH: $LD_LIBRARY_PATH"
echo "🚀 Starting ubuntu_backend.py..."

# Run the backend using uv
~/.local/bin/uv run python ubuntu_backend.py
