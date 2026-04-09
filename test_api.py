import requests, time

start = time.time()
print('Testing API for ALS...')
resp = requests.post('http://localhost:5000/api/v1/query', json={'disease_name': 'ALS', 'top_k': 5}).json()
task_id = resp.get('task_id')

while True:
    status = requests.get(f'http://localhost:5000/api/v1/query/{task_id}/status').json()
    if status.get('status') == 'done':
        break
    if time.time() - start > 30:
        print('Timeout')
        break
    time.sleep(1)

res = requests.get(f'http://localhost:5000/api/v1/results/{task_id}').json()
print('Successful Ranked Drugs:', len(res.get('ranked_drugs', [])))
print('Rejected Drugs:', len(res.get('rejected_drugs', [])))
for r in res.get('rejected_drugs', [])[:5]:
    print('Rejected:', r.get('name'), 'Reason:', r.get('reason'))
if res.get('message'):
    print('Message:', res['message'])
