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
sys.path.insert(0, './backend')
import os
os.environ['GEMINI_API_KEY'] = 'AIzaSyDdGVmZsT8_hJJVOXlo9MD5xqQvN6n8lPE'

print("=== Gemini Disease Recognition ===")
from app.services.gemini_service import recognize_disease
info = recognize_disease("progeria")
print(info)

print("\n=== Gemini Candidates for Unknown Disease ===")
from app.services.gemini_service import generate_gemini_candidates
cands = generate_gemini_candidates("Hutchinson-Gilford Progeria Syndrome", top_k=3)
for c in cands:
    print(f"  - {c['target_name']} | score={c.get('score')} | evidence={c.get('evidence_level')}")

print("\n=== Gemini Medical Summary ===")
from app.services.gemini_service import generate_medical_summary
summary = generate_medical_summary("Hutchinson-Gilford Progeria Syndrome", cands[:3])
print(summary[:500])
