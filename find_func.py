with open('backend/app/services/pipeline.py', 'r', encoding='utf-8') as f:
    for i, line in enumerate(f):
        if 'def load_candidates' in line:
            print(f"FOUND AT LINE {i+1}: {line.strip()}")
            break
