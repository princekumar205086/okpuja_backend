#!/usr/bin/env python
"""
Simple HTTP Server for Email Preview
Serves the email preview file locally
"""

import http.server
import socketserver
import webbrowser
import os
import threading
import time

def serve_preview():
    """Start a simple HTTP server to serve the preview"""
    PORT = 8001
    
    # Change to the directory containing the preview file
    os.chdir(r'C:\Users\Prince Raj\Desktop\comestro\okpuja_backend')
    
    Handler = http.server.SimpleHTTPRequestHandler
    
    try:
        with socketserver.TCPServer(("", PORT), Handler) as httpd:
            print(f"📧 EMAIL PREVIEW SERVER")
            print(f"=" * 50)
            print(f"Server running at: http://localhost:{PORT}")
            print(f"Email preview: http://localhost:{PORT}/email_preview_professional.html")
            print(f"=" * 50)
            print("Press Ctrl+C to stop the server")
            
            # Start the server in a separate thread
            server_thread = threading.Thread(target=httpd.serve_forever)
            server_thread.daemon = True
            server_thread.start()
            
            # Wait a moment for server to start
            time.sleep(1)
            
            # Keep the server running
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nShutting down server...")
                httpd.shutdown()
                
    except Exception as e:
        print(f"Error starting server: {str(e)}")

if __name__ == "__main__":
    serve_preview()