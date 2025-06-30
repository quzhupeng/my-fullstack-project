#!/usr/bin/env python3
"""
Simple HTTP server to serve the integrated frontend locally.
This avoids CORS issues that can occur when opening HTML files directly in the browser.
"""

import http.server
import socketserver
import webbrowser
import os
import sys
from pathlib import Path

# Configuration
PORT = 3000
HOST = 'localhost'

class CustomHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers to allow requests to localhost:8787
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        # Handle preflight requests
        self.send_response(200)
        self.end_headers()

def main():
    # Change to the directory containing this script
    script_dir = Path(__file__).parent
    os.chdir(script_dir)
    
    # Check if the integrated frontend file exists
    frontend_file = "原先的前端页面.html"
    if not os.path.exists(frontend_file):
        print(f"❌ Error: {frontend_file} not found in current directory")
        print(f"Current directory: {os.getcwd()}")
        sys.exit(1)
    
    print("🚀 Starting local web server for integrated frontend testing...")
    print(f"📁 Serving files from: {os.getcwd()}")
    print(f"🌐 Server URL: http://{HOST}:{PORT}")
    print(f"📄 Frontend URL: http://{HOST}:{PORT}/{frontend_file}")
    print("\n📋 Testing Instructions:")
    print("1. Make sure the backend is running on http://localhost:8787")
    print("2. Use the following test credentials:")
    print("   - Invite Code: SPRING2024")
    print("   - Test Users:")
    print("     * Username: admin, Password: admin123")
    print("     * Username: test, Password: test123") 
    print("     * Username: demo, Password: demo123")
    print("3. Or register a new user with the invite code")
    print("\n🛑 Press Ctrl+C to stop the server")
    print("-" * 60)
    
    try:
        with socketserver.TCPServer((HOST, PORT), CustomHTTPRequestHandler) as httpd:
            print(f"✅ Server started successfully on http://{HOST}:{PORT}")
            
            # Open browser automatically
            frontend_url = f"http://{HOST}:{PORT}/{frontend_file}"
            print(f"🌐 Opening browser to: {frontend_url}")
            webbrowser.open(frontend_url)
            
            # Start serving
            httpd.serve_forever()
            
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except OSError as e:
        if e.errno == 48:  # Address already in use
            print(f"❌ Error: Port {PORT} is already in use")
            print("Try using a different port or stop the process using that port")
        else:
            print(f"❌ Error starting server: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
