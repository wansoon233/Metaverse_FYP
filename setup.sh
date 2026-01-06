#!/bin/bash

# ==========================================
# METAVERSE SMART HOME - ENVIRONMENT SETUP
# ==========================================

echo "🚀 Starting Project Setup..."

# 1. Check for Python 3
if ! command -v python3 &> /dev/null
then
    echo "❌ Python 3 could not be found. Please install it."
    exit 1
fi

# 2. Create Virtual Environment (if it doesn't exist)
if [ ! -d "venv" ]; then
    echo "🔹 Creating Virtual Environment (venv)..."
    python3 -m venv venv
else
    echo "🔹 Virtual Environment already exists."
fi

# 3. Activate Environment
echo "🔹 Activating venv..."
source venv/bin/activate

# 4. Upgrade pip
echo "🔹 Upgrading pip..."
pip install --upgrade pip

# 5. Install Dependencies
if [ -f "requirements.txt" ]; then
    echo "🔹 Installing Dependencies from requirements.txt..."
    pip install -r requirements.txt
else
    echo "⚠️  requirements.txt not found! Skipping library installation."
fi

# 6. Sinergym Setup Reminder
echo ""
echo "=========================================="
echo "✅ SETUP COMPLETE!"
echo "=========================================="
echo "To start working, run:"
echo "   source venv/bin/activate"
echo ""
echo "⚠️  IMPORTANT: Sinergym requires EnergyPlus."
echo "   Make sure you have installed EnergyPlus (e.g., v23.1.0)"
echo "   and set the path: export EPLUS_PATH=/usr/local/EnergyPlus-23-1-0"
echo "=========================================="
