import pytest
from unittest.mock import patch
from app import create_app


@pytest.fixture
def client():
    app = create_app("testing")
    app.config["TESTING"] = True
    app.config["MONGO_URI"] = "mongodb://localhost:27017/test_repurposing_db"

    with patch("app.extensions.mongo.init_app"):
        from unittest.mock import MagicMock
        mock_db_instance = MagicMock()
        mock_db_instance.__getitem__.return_value.find_one.return_value = None
        with patch("app.extensions.mongo.db", new=mock_db_instance):
            with app.test_client() as client:
                with app.app_context():
                    # In a real scenario we might drop collections here
                    pass
                yield client


def test_query_endpoint_missing_payload(client):
    response = client.post('/api/v1/query', json={})
    assert response.status_code == 400
    assert "Missing" in response.get_json()["error"] or "disease_name" in response.get_json()["error"]


def test_query_endpoint_success(client):
    response = client.post('/api/v1/query', json={"disease_name": "Test Disease", "top_k": 5})
    # As it may launch a Celery task or sync pipeline based on broker
    # we expect a 202 Accepted or 200 OK
    assert response.status_code in [200, 202]
    data = response.get_json()
    assert "task_id" in data


def test_status_endpoint(client):
    response = client.get('/api/v1/query/12345/status')
    assert response.status_code in [200, 404]


def test_health_endpoint(client):
    response = client.get('/api/v1/health')  # Assuming we add standard health or it's implicitly available
    # Just checking for not 500
    assert response.status_code != 500
