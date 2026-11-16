"""
Vercel Serverless Entrypoint for CloudPulse Backend API
"""

import sys
from pathlib import Path

# Add project root to sys.path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from backend.app.main import app

# Export WSGI application
application = app
