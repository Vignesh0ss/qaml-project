"""
Run Flask app. From repo root: PYTHONPATH=backend python backend/run.py
Or from backend: python run.py (if PYTHONPATH includes .)
"""
from app import create_app
import os
import sys

# Add backend to path so "app" and "quantum" resolve
BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


from app.extensions import socketio
app = create_app(os.environ.get("FLASK_ENV", "development"))

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", True),
        use_reloader=False,  # Essential for stability on Windows with SocketIO
        allow_unsafe_werkzeug=True
    )
