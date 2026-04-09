import pytest
import json
from app import create_app
from app.extensions import mongo, bcrypt
from flask_jwt_extended import create_access_token

@pytest.fixture
def app():
    app = create_app("testing")
    with app.app_context():
        # Setup test data
        db = mongo.db
        db.users.delete_many({})
        hashed = bcrypt.generate_password_hash("TestPass123!").decode('utf-8')
        db.users.insert_one({
            "username": "testuser",
            "email": "test@example.com",
            "password_hash": hashed,
            "role": "researcher"
        })
    return app

@pytest.fixture
def client(app):
    return app.test_client()

# TC-I-001: Valid login returns JWT pair
def test_tc_i_001_valid_login(client):
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestPass123!"
    })
    assert resp.status_code == 200
    data = resp.get_json()
    assert "access_token" in data
    assert "refresh_token" in data

# TC-I-007: Valid query enqueued (Async 202)
def test_tc_i_007_query_async(client):
    # Get token
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestPass123!"
    })
    token = resp.get_json()["access_token"]
    
    resp = client.post("/api/v1/query", json={
        "disease_name": "Progeria",
        "top_k": 5
    }, headers={"Authorization": f"Bearer {token}"})
    
    assert resp.status_code == 202
    data = resp.get_json()
    assert "task_id" in data
    assert data["status"] == "queued"

# TC-I-008: Schema validation
def test_tc_i_008_schema_validation(client):
    resp = client.post("/api/v1/auth/login", json={
        "username": "testuser",
        "password": "TestPass123!"
    })
    token = resp.get_json()["access_token"]
    
    # Missing disease_name
    resp = client.post("/api/v1/query", json={
        "top_k": 5
    }, headers={"Authorization": f"Bearer {token}"})
    assert resp.status_code == 422
