#!/bin/bash

# Kill existing processes on specific ports
lsof -ti :8000,5001 | xargs kill -9 2>/dev/null || true
pkill -f vision_engine.py
pkill -f "python3 -m http.server"

# Start Vision Engine in background
echo "🚀 Starting Vision Engine..."
python3 vision_engine.py &

# Start Web Server for Frontend
echo "🌐 Starting Frontend Server..."
python3 -m http.server 8000 &

echo "✨ System ready!"
echo "1. Open http://localhost:8000 in your projector's browser (Chrome recommended)"
echo "2. Focus the Python window and press 'C' to calibrate"
echo "3. Follow the on-screen dots and press SPACE on each"
echo "4. Enjoy the vibe!"

# Keep script alive
wait
