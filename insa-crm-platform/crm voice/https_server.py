#!/usr/bin/env python3
"""
HTTPS Server for INSA Command Center
Enables microphone access over Tailscale network
"""
import http.server
import ssl
import socketserver
import os

# Configuration
PORT = 8007
CERTFILE = 'ssl/cert.pem'
KEYFILE = 'ssl/key.pem'

class MyHTTPRequestHandler(http.server.SimpleHTTPRequestHandler):
    def end_headers(self):
        # Add CORS headers for API access
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type, Authorization')
        super().end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.end_headers()

if __name__ == '__main__':
    # Change to script directory
    os.chdir(os.path.dirname(os.path.abspath(__file__)))

    # Create HTTPS server
    with socketserver.TCPServer(("0.0.0.0", PORT), MyHTTPRequestHandler) as httpd:
        # Wrap socket with SSL
        context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
        context.load_cert_chain(certfile=CERTFILE, keyfile=KEYFILE)
        httpd.socket = context.wrap_socket(httpd.socket, server_side=True)

        print(f"🔒 HTTPS Server running on https://100.100.101.1:{PORT}")
        print(f"📱 Access UI: https://100.100.101.1:{PORT}/insa-command-center-v3.html")
        print(f"🎤 Microphone access enabled!")
        print(f"⚠️  Accept the self-signed certificate in your browser")
        print(f"🛑 Press Ctrl+C to stop")

        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")
