"""
Global ML Engine Registry.
Decoupled from app.extensions to prevent circular imports.
"""
import os
from .services.ml_service import MLService

# Instantiate as a global singleton at module level
# This is loaded once when the module is first imported.
ml_service = MLService(model_path=os.environ.get("ML_MODEL_PATH"))
