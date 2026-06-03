"""
Run Flask app. From repo root: PYTHONPATH=backend python backend/run.py
Or from backend: python run.py (if PYTHONPATH includes .)

Production (e.g. Render): set FLASK_ENV=production, PORT (provided by host),
MONGO_URI, SECRET_KEY, JWT_SECRET_KEY, CORS_ORIGINS in the environment — do not commit secrets.

Render free tier: the service sleeps; first HTTP request can be slow. Socket.IO/WebSocket
clients may see reconnect failures after idle — prefer polling or tolerate retries for demos.
"""
from app import create_app
import os
import sys

# Add backend to path so "app" and "quantum" resolve
BACKEND = os.path.dirname(os.path.abspath(__file__))
if BACKEND not in sys.path:
    sys.path.insert(0, BACKEND)


from app.extensions import socketio
app = create_app()

if __name__ == "__main__":
    socketio.run(
        app,
        host="0.0.0.0",
        port=int(os.environ.get("PORT", 5000)),
        debug=app.config.get("DEBUG", True),
        use_reloader=False,  # Essential for stability on Windows with SocketIO
        allow_unsafe_werkzeug=True
    )
