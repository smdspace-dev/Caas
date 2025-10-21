#!/usr/bin/env python3
"""
Frontend Server for Phase 4 Advanced RAG System
Serves the HTML frontend on a separate port
"""

import http.server
import socketserver
import os
import webbrowser
from urllib.parse import urlparse
import threading
import time

class CORSHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    """HTTP Request Handler with CORS support"""
    
    def end_headers(self):
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        super().end_headers()
    
    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

def start_frontend_server(port=3000, directory=None):
    """Start the frontend server"""
    
    if directory:
        os.chdir(directory)
    
    handler = CORSHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", port), handler) as httpd:
            print(f"🌐 Frontend server starting on http://localhost:{port}")
            print(f"📁 Serving directory: {os.getcwd()}")
            print(f"🔗 Backend API: http://localhost:5000")
            print("=" * 50)
            print("📋 Frontend Features:")
            print("   • Modern responsive design with glass morphism")
            print("   • Real-time chat interface")
            print("   • Document upload with drag & drop")
            print("   • Advanced search with multiple types")
            print("   • API endpoint testing")
            print("   • System status monitoring")
            print("   • Performance metrics display")
            print("=" * 50)
            print(f"🚀 Open http://localhost:{port} in your browser")
            print("Press Ctrl+C to stop the server")
            print("=" * 50)
            
            # Auto-open browser after a short delay
            def open_browser():
                time.sleep(2)
                try:
                    webbrowser.open(f'http://localhost:{port}')
                except:
                    pass
            
            threading.Thread(target=open_browser, daemon=True).start()
            
            httpd.serve_forever()
            
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Port {port} is already in use. Trying port {port + 1}...")
            start_frontend_server(port + 1, directory)
        else:
            print(f"❌ Error starting server: {e}")
    except KeyboardInterrupt:
        print("\n👋 Frontend server stopped")

if __name__ == "__main__":
    # Change to frontend directory
    frontend_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'frontend')
    
    if not os.path.exists(frontend_dir):
        print(f"❌ Frontend directory not found: {frontend_dir}")
        exit(1)
    
    print("🎨 Phase 4 Advanced RAG System - Frontend Server")
    print("=" * 50)
    
    start_frontend_server(3000, frontend_dir)