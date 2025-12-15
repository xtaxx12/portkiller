#!/bin/bash
echo "========================================"
echo "   PortKiller - Port Management Tool"
echo "========================================"
echo ""

# Check if Python is installed
if ! command -v python3 &> /dev/null; then
    echo "[ERROR] Python 3 is not installed"
    echo "Please install Python 3.8+ using your package manager"
    exit 1
fi

# Check if venv exists, if not create it
if [ ! -d "venv" ]; then
    echo "[INFO] Creating virtual environment..."
    python3 -m venv venv
fi

# Activate virtual environment
echo "[INFO] Activating virtual environment..."
source venv/bin/activate

# Install/update dependencies
echo "[INFO] Installing dependencies..."
pip install -r requirements.txt --quiet

# Run the application
echo ""
echo "[INFO] Starting PortKiller..."
echo ""
python main.py
