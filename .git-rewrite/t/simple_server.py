#!/usr/bin/env python3
"""
Simple HTTP server to serve STL files and HTML viewer
"""
import os
import http.server
import socketserver
from urllib.parse import urlparse

class STLHandler(http.server.SimpleHTTPRequestHandler):
    def guess_type(self, path):
        mimetype, encoding = super().guess_type(path)
        if path.endswith('.stl'):
            return 'application/octet-stream'
        return mimetype, encoding

    def end_headers(self):
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        super().end_headers()

if __name__ == "__main__":
    PORT = 8000
    
    print(f"🌐 Starting simple HTTP server on port {PORT}")
    print(f"📁 Serving files from: {os.getcwd()}")
    print(f"🔗 Open: http://localhost:{PORT}/working_model_viewer.html")
    print(f"🔗 STL files: http://localhost:{PORT}/generated_models/")
    print("")
    
    with socketserver.TCPServer(("", PORT), STLHandler) as httpd:
        httpd.serve_forever()
