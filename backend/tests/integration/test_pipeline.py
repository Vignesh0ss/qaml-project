import uuid
from app.services.pipeline import run_pipeline


class MockMongoCollection:
    def __init__(self):
        self.data = []

    def insert_one(self, doc):
        self.data.append(doc)

    def update_one(self, filt, update):
        pass

    def find_one(self, filter=None, *args, **kwargs):
        return self.data[-1] if self.data else None


class MockDB:
    def __init__(self):
        self.collections = {"results": MockMongoCollection(), "queries": MockMongoCollection(),
                            "audit_log": MockMongoCollection()}

    def __getitem__(self, name):
        return self.collections[name]


def test_pipeline_end_to_end():
    # Setup mock db
    mock_db = MockDB()
    task_id = str(uuid.uuid4())
    query = {"disease_name": "Progeria", "top_k": 3, "user_id": "test_user"}

    # Run pipeline sync
    results = run_pipeline(task_id, query, db=mock_db)

    assert results["task_id"] == task_id
    assert results["disease_name"] == "Progeria"
    assert results["top_k"] == 3
    assert len(results["ranked_drugs"]) <= 3
    assert "qubo_energy" in results

    # Check that results were inserted
    assert len(mock_db.collections["results"].data) == 1
    # Check that audit log was generated (pipeline can emit multiple stage events)
    assert len(mock_db.collections["audit_log"].data) >= 1
    audit_entry = mock_db.collections["audit_log"].data[-1]
    assert audit_entry["event_type"] == "PIPELINE_COMPLETE"
    assert "entry_hash" in audit_entry
