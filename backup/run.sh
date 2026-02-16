
#!/bin/bash
echo "Starting AI Mouse (Video Mode)..."
source venv/bin/activate
echo "---------------------------------------------------------"
echo "GESTURES:"
echo "1. OPEN HAND: Move Mouse."
echo "2. CLOSED FIST: Scroll Mode (Hold & Move Up/Down)."
echo "3. CLICK: Close Fist -> Open Hand (Quickly)."
echo "4. DOUBLE CLICK: Plays/Stops the VIDEO."
echo "---------------------------------------------------------"
echo "INSTRUCTIONS:"
echo "1. MANUALLY DRAG 'Projector' window to wall."
echo "2. MAXIMIZE 'Projector' window."
echo "3. CALIBRATE by clicking Red Targets on Laptop."
echo "---------------------------------------------------------"

python ai_mouse.py
