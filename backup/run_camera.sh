#!/bin/bash

# Positivity Boost App Launcher
# Quick and easy way to start the app

echo "🚀 Starting Positivity Boost App..."
echo ""

# Navigate to script directory
cd "$(dirname "$0")"

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 not found!"
    echo "💡 Install Python 3 first"
    exit 1
fi

# Check if dependencies are installed
echo "📦 Checking dependencies..."
python3 -c "import cv2, mediapipe, numpy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "⚠️  Missing dependencies!"
    echo "💡 Installing required packages..."
    pip3 install opencv-python mediapipe numpy
fi

echo "✅ All dependencies ready!"
echo ""
echo "🎥 Launching app..."
echo ""
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo "  CONTROLS:"
echo "  👍 Thumbs up  - Show surprise"
echo "  ESC          - Hide image"
echo "  Q            - Quit app"
echo "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"
echo ""

# Run the app
python3 camera.py

echo ""
echo "👋 App closed. Have a great day!"
