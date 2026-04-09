from app.extensions import mongo

_real_init_app = mongo.init_app


def _init_app_with_mock_fallback(app, *args, **kwargs):
    """Fallback to mongomock automatically when MongoDB is offline."""
    try:
        _real_init_app(app, *args, **kwargs)
        mongo.cx.admin.command("ping")
    except Exception:
        import mongomock

        mongo.cx = mongomock.MongoClient()
        db_name = app.config.get("MONGODB_DB", "quantum_drug_repurposing_test")
        mongo.db = mongo.cx[db_name]
        app.extensions["pymongo"] = mongo


mongo.init_app = _init_app_with_mock_fallback
