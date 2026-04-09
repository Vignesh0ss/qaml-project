"""
Run Flask app. From repo root: PYTHONPATH=backend python backend/run.py
Or from backend: python run.py (if PYTHONPATH includes .)
"""
import os
import sys

# Add backend to path so "app" and "quantum" resolve
BACKEND = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)

from app import create_app

app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 5000)), debug=app.config.get("DEBUG", True))
