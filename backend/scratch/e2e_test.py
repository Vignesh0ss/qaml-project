import urllib.request, json, time

# Submit
req = urllib.request.Request(
    'http://localhost:5000/api/v1/query',
    data=json.dumps({'disease_name': 'Progeria', 'top_k': 5}).encode(),
    headers={'Content-Type': 'application/json'}, method='POST'
)
with urllib.request.urlopen(req, timeout=10) as r:
    resp = json.loads(r.read().decode())
task_id = resp['task_id']
print('Task:', task_id)

# Poll
for i in range(24):
    time.sleep(5)
    with urllib.request.urlopen(f'http://localhost:5000/api/v1/results/{task_id}', timeout=10) as r:
        d = json.loads(r.read().decode())
    status = d.get('status')
    print(f'  [{(i+1)*5}s] {status}')
    if status == 'done':
        drugs = d.get('ranked_drugs', [])
        print(f'CANDIDATES ({len(drugs)}):')
        for dr in drugs:
            print(f'  Rank {dr.get("rank","-")}: {dr.get("drug_name")} | score={dr.get("score")} | phase={dr.get("max_phase")}')
        summary = d.get('medical_summary') or d.get('ai_summary', '')
        print('\nAI SUMMARY (first 500 chars):')
        print(summary[:500])
        # Check audit
        with urllib.request.urlopen(f'http://localhost:5000/api/v1/audit/{task_id}', timeout=10) as r:
            audit = json.loads(r.read().decode())
        entries = audit.get('entries', [])
        print(f'\nAUDIT ENTRIES: {len(entries)}')
        for e in entries:
            print(f'  - {e.get("action") or e.get("event_type")}')
        with urllib.request.urlopen(f'http://localhost:5000/api/v1/audit/verify/{task_id}', timeout=10) as r:
            verify = json.loads(r.read().decode())
        print(f'\nAUDIT CHAIN VALID: {verify.get("valid")} | {verify.get("message")}')
        break
    if status == 'failed':
        print('FAILED:', d.get('message'))
        break
