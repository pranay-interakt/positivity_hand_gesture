#!/bin/bash

# Quick Start Script for Gesture Recognition App
# This script starts the server and opens the app in your default browser

echo "🚀 Starting Gesture Recognition App..."
echo ""

# Check if Python 3 is installed
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed. Please install Python 3 first."
    exit 1
fi

# Navigate to the project directory
cd "$(dirname "$0")"

# Start the server in the background
echo "📡 Starting server on http://localhost:8000..."
python3 server.py &
SERVER_PID=$!

# Wait for server to start
sleep 2

# Open in default browser
echo "🌐 Opening in browser..."
if [[ "$OSTYPE" == "darwin"* ]]; then
    # macOS
    open http://localhost:8000
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    # Linux
    xdg-open http://localhost:8000
elif [[ "$OSTYPE" == "msys" || "$OSTYPE" == "cygwin" ]]; then
    # Windows
    start http://localhost:8000
fi

echo ""
echo "✅ App is running!"
echo "📍 URL: http://localhost:8000"
echo "⚠️  Press Ctrl+C to stop the server"
echo ""

# Wait for Ctrl+C
trap "echo ''; echo '👋 Stopping server...'; kill $SERVER_PID; exit 0" INT
wait $SERVER_PID
