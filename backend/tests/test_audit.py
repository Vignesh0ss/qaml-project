import os
import sys
# Add backend to path so modules resolve automatically
WORKSPACE_DIR = os.path.dirname(os.path.abspath(__file__))
if 'backend/tests' in WORKSPACE_DIR.replace('\\', '/'):
    BACKEND_DIR = os.path.dirname(WORKSPACE_DIR)
else:
    BACKEND_DIR = os.path.join(WORKSPACE_DIR, 'backend')
if BACKEND_DIR not in sys.path:
    sys.path.insert(0, BACKEND_DIR)

"""Tests for audit service hash chain."""


def test_audit_sha256():
    from app.services.audit_service import _sha256
    h = _sha256({"a": 1, "b": 2})
    assert isinstance(h, str)
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_audit_verify_chain_empty_db():
    from app.services.audit_service import verify_chain
    valid, msg = verify_chain(None, "any")
    assert valid is False
    assert "database" in msg.lower() or "not available" in msg.lower()
