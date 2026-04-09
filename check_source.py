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

import sys
from pathlib import Path
from app.services.pipeline import load_candidates, BINDING_CSV

print('CSV exists?', BINDING_CSV.is_file())
if BINDING_CSV.is_file():
    with open(BINDING_CSV, 'r', encoding='utf-8') as f:
        print('CSV lines:', sum(1 for _ in f))

try:
    drugs, scores, smiles = load_candidates("Hutchinson-Gilford Progeria Syndrome", max_drugs=300, allowed_targets=[])
    print(f"Loaded {len(drugs)} drugs with empty allowed_targets")
except Exception as e:
    print('Error loading:', e)
