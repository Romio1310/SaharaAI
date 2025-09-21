from flask import Flask
import sys
import os

# Add the parent directory to Python path so we can import from the main app
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the main Flask app
from app import app

# Vercel serverless function handler
def handler(request):
    return app(request.environ, lambda status, headers: None)

# For compatibility with Vercel's Python runtime
if __name__ == "__main__":
    app.run()