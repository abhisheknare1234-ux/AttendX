import os
import sys

# Ensure project root is on sys.path for module resolution
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from apps.api.src.main import app

# Vercel Serverless Function entrypoint
# The ASGI application 'app' is automatically detected and served by @vercel/python
