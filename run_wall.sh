
#!/bin/bash
echo "Starting Wall Touch (Video Controller)..."
source venv/bin/activate
echo "---------------------------------------------------------"
echo "INSTRUCTIONS:"
echo "1. USE 1 FINGER (Point Index) to control cursor."
echo "2. HOLD CURSOR STILL to click."
echo "3. CLICK toggles between BLANK and VIDEO."
echo "---------------------------------------------------------"

python wall_touch.py
