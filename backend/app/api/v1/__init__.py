"""
API v1 blueprints registration.
"""


def register_blueprints(app):
    from app.api.v1 import auth, query, results, audit, models, reports, stats, experimental
    for bp in [auth.bp, query.bp, results.bp, audit.bp, models.bp, reports.bp, stats.bp, experimental.bp]:
        app.register_blueprint(bp, url_prefix="/api/v1")


# Re-export for create_app
__all__ = ["register_blueprints"]
