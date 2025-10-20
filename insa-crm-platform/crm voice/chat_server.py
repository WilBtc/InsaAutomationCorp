#!/usr/bin/env python3
"""
Simple HTTP server for INSA CRM Chat UI
Serves the chat interface on Tailscale network
"""
from http.server import HTTPServer, SimpleHTTPRequestHandler
import os
from pathlib import Path

class CRMChatHandler(SimpleHTTPRequestHandler):
    """Custom handler for CRM chat UI"""

    def do_GET(self):
        """Handle GET requests"""
        # Serve chat.html for / and /chat
        if self.path == '/' or self.path == '/chat':
            self.path = '/chat.html'

        return SimpleHTTPRequestHandler.do_GET(self)

    def end_headers(self):
        """Add CORS headers"""
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', '*')
        SimpleHTTPRequestHandler.end_headers(self)


def run_server(port=8003):
    """Run the chat server"""
    # Change to static directory
    static_dir = Path(__file__).parent.parent / 'core' / 'static'
    if static_dir.exists():
        os.chdir(static_dir)
        print(f"📁 Serving from: {static_dir}")
    else:
        print(f"❌ Static directory not found: {static_dir}")
        return

    server_address = ('0.0.0.0', port)
    httpd = HTTPServer(server_address, CRMChatHandler)

    print(f"")
    print(f"╔════════════════════════════════════════════════════════════╗")
    print(f"║                                                            ║")
    print(f"║   🤖 INSA CRM Chat Server                                  ║")
    print(f"║   Web-based Chat Interface with Voice Support             ║")
    print(f"║                                                            ║")
    print(f"╚════════════════════════════════════════════════════════════╝")
    print(f"")
    print(f"✅ Server running on: http://100.100.101.1:{port}/chat")
    print(f"🌐 Tailscale network: accessible to all devices")
    print(f"🎤 Voice backend: http://100.100.101.1:5000")
    print(f"")
    print(f"Press Ctrl+C to stop the server")
    print(f"")

    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print(f"\n\n👋 Server stopped")
        httpd.shutdown()


if __name__ == '__main__':
    import argparse

    parser = argparse.ArgumentParser(description='INSA CRM Chat Server')
    parser.add_argument('--port', type=int, default=8003, help='Port to run on (default: 8003)')

    args = parser.parse_args()
    run_server(args.port)
