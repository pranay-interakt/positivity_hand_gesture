#!/usr/bin/env python3
"""
Simple HTTP Server for Gesture Recognition App
Serves the application with proper MIME types and CORS headers
"""

import http.server
import socketserver
import os
import sys
from pathlib import Path

# Configuration
PORT = 8000
DIRECTORY = Path(__file__).parent

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """Custom handler with proper MIME types and CORS headers"""
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(DIRECTORY), **kwargs)
    
    def end_headers(self):
        # Add CORS headers for cross-origin requests
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        # Cache control
        self.send_header('Cache-Control', 'no-store, no-cache, must-revalidate')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()
    
    def guess_type(self, path):
        """Override to ensure correct MIME types"""
        mimetype = super().guess_type(path)
        
        # Ensure JavaScript files have correct MIME type
        if path.endswith('.js'):
            return 'application/javascript'
        elif path.endswith('.mjs'):
            return 'application/javascript'
        
        return mimetype

def run_server():
    """Start the HTTP server"""
    try:
        with socketserver.TCPServer(("", PORT), CustomHTTPRequestHandler) as httpd:
            print("=" * 60)
            print("🚀 Gesture Recognition Server Started!")
            print("=" * 60)
            print(f"\n📍 Server running at: http://localhost:{PORT}")
            print(f"📁 Serving directory: {DIRECTORY}")
            print("\n🎥 Instructions:")
            print("  1. Open http://localhost:{} in your browser".format(PORT))
            print("  2. Allow camera access when prompted")
            print("  3. Show middle finger 🖕 to reveal the image")
            print("  4. Show prayer hands 🙏 to hide the image")
            print("\n⚠️  Press Ctrl+C to stop the server\n")
            print("=" * 60)
            
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n👋 Server stopped. Goodbye!")
        sys.exit(0)
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"\n❌ Error: Port {PORT} is already in use.")
            print(f"💡 Try stopping other servers or use a different port.")
        else:
            print(f"\n❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run_server()
