"""
Root conftest.py - adds the backend directory to sys.path so that
`from app.xxx import ...` and `from quantum.xxx import ...` both resolve
when pytest is run from the project root or from backend/.
"""
import os
import sys

# Insert backend/ directory so `app`, `quantum`, `optimizer` etc. are importable
_BACKEND = os.path.dirname(os.path.abspath(__file__))
if _BACKEND not in sys.path:
    sys.path.insert(0, _BACKEND)

collect_ignore = ["test_output.txt"]
