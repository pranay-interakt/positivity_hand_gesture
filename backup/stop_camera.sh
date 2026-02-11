#!/bin/bash

# Stop Positivity Boost App
# Kills all running instances

echo "🛑 Stopping Positivity Boost App..."
echo ""

# Find and kill the process
if pgrep -f "camera.py" > /dev/null; then
    pkill -f "camera.py"
    echo "✅ App stopped successfully!"
else
    echo "ℹ️  App is not running"
fi

echo ""
