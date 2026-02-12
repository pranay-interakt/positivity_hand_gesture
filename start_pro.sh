#!/bin/bash

# Kill any existing python servers on port 8000
lsof -ti:8000 | xargs kill -9 2>/dev/null

echo "Starting Web Server..."
python3 -m http.server 8000 &
SERVER_PID=$!

echo "Opening Browser..."
open "http://localhost:8000/index.html"

echo "---------------------------------------------------"
echo "INSTRUCTIONS:"
echo "1. The browser will open. Click 'CLICK TO ENTER IMMERSIVE MODE'."
echo "2. Allow Fullscreen."
echo "3. The Python Vision Script will start."
echo "4. Follow the calibration steps in the 'Calibration' window."
echo "   (Click the 4 corners of the PROJECTED screen on the camera feed)"
echo "5. Once calibrated, use your OPEN HAND (5 fingers) to trigger the video."
echo "---------------------------------------------------"
echo "Starting Vision Pro Engine... (Press Ctrl+C to stop)"

python3 vision_pro.py

# Cleanup
kill $SERVER_PID
