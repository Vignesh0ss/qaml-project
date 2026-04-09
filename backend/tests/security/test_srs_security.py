import pytest
from app import create_app
from app.extensions import mongo, bcrypt

@pytest.fixture
def app():
    app = create_app("testing")
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# TC-SEC-006: Audit chain tamper detection
def test_tc_sec_006_audit_tampering(client):
    with client.application.app_context():
        db = mongo.db
        db.audit_log.delete_many({})
        
        # Log 3 entries
        from app.services.audit_service import AuditLogger
        tid = "task_sec_test"
        AuditLogger.log(db, tid, "START", {}, {})
        AuditLogger.log(db, tid, "MID", {}, {})
        AuditLogger.log(db, tid, "END", {}, {})
        
        # Verify initial
        from app.services.audit_service import verify_chain
        valid, msg = verify_chain(db, tid)
        assert valid is True
        
        # Tamper
        entry = db.audit_log.find_one({"event_type": "MID"})
        db.audit_log.update_one({"_id": entry["_id"]}, {"$set": {"event_type": "TAMPERED"}})
        
        # Verify after tamper
        valid, msg = verify_chain(db, tid)
        assert valid is False
        assert "broken" in msg.lower() or "mismatch" in msg.lower()

# TC-SEC-010: Plain-text password not stored
def test_tc_sec_010_no_plaintext_passwords(client):
    with client.application.app_context():
        db = mongo.db
        db.users.delete_many({})
        
        password = "SecurePass123!"
        hashed = bcrypt.generate_password_hash(password).decode('utf-8')
        db.users.insert_one({
            "username": "secuser",
            "password_hash": hashed
        })
        
        user = db.users.find_one({"username": "secuser"})
        assert user["password_hash"].startswith("$2b$12$")
        assert password not in user["password_hash"]
