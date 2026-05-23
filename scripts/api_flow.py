#!/usr/bin/env python3
import json
import random
import time
import urllib.request
import urllib.error

BASE = 'http://127.0.0.1:8000'

def req(method, path, data=None, headers=None, timeout=10):
    url = BASE + path
    body = None
    if data is not None:
        body = json.dumps(data).encode('utf-8')
    req = urllib.request.Request(url, data=body, method=method)
    req.add_header('Content-Type', 'application/json')
    if headers:
        for k,v in headers.items():
            req.add_header(k, v)
    try:
        with urllib.request.urlopen(req, timeout=timeout) as r:
            return json.loads(r.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print('HTTP', e.code, e.read().decode('utf-8', errors='ignore'))
        raise
    except Exception as e:
        print('ERR', repr(e))
        raise

if __name__ == '__main__':
    username = 'copilot' + str(random.randint(1000,9999))
    password = 'TestPass123!'
    print('Registering', username)
    try:
        reg = req('POST', '/register', {'username': username, 'password': password})
    except Exception:
        print('Registration failed')
        raise
    print('Registered. Tokens keys:', list(reg.keys()))
    access = reg.get('access_token')
    refresh = reg.get('refresh_token')
    if not access:
        print('No access token returned')
        raise SystemExit(1)

    headers = {'Authorization': 'Bearer ' + access}
    print('Creating task')
    create = req('POST', '/tasks', {'data': 'hello from copilot'}, headers=headers)
    task_id = create.get('task_id')
    print('Task created:', task_id)

    print('Polling task...')
    for i in range(30):
        try:
            t = req('GET', f'/tasks/{task_id}', headers=headers)
        except Exception:
            print('Poll error, retrying')
            time.sleep(1)
            continue
        status = t.get('status')
        print(i, 'status=', status)
        if status in ('done', 'error'):
            print('Final task object:')
            print(json.dumps(t, indent=2, ensure_ascii=False))
            break
        time.sleep(1)
    else:
        print('Timed out waiting for task')

    print('Done')
