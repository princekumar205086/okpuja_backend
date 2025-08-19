#!/usr/bin/env python
"""
Start Django development server
"""
import os
import sys
import subprocess

def start_server():
    """Start the Django development server"""
    try:
        # Change to the project directory
        os.chdir(r'c:\Users\Prince Raj\Desktop\comestro\okpuja_backend')
        
        print("Starting Django development server...")
        print("Server will be available at: http://localhost:8000")
        print("Press Ctrl+C to stop the server")
        
        # Start the server
        subprocess.run([sys.executable, 'manage.py', 'runserver'], check=True)
        
    except KeyboardInterrupt:
        print("\nServer stopped by user")
    except Exception as e:
        print(f"Error starting server: {str(e)}")

if __name__ == "__main__":
    start_server()