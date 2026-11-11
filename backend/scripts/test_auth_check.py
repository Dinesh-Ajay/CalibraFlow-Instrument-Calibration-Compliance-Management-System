import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

import urllib.request
import json
from app.services.bootstrap_service import REQUIRED_USERS

for u in REQUIRED_USERS:
    req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/auth/login',
        data=json.dumps({'username': u['username'], 'password': u['password']}).encode(),
        headers={'Content-Type': 'application/json'}
    )
    res = urllib.request.urlopen(req)
    data = json.loads(res.read())
    username = u['username']
    roles = data['user']['roles']
    user_id = data['user']['id']
    token = data['access_token']
    
    # Test /auth/me with Bearer token
    me_req = urllib.request.Request(
        'http://127.0.0.1:8000/api/v1/auth/me',
        headers={'Authorization': f'Bearer {token}'}
    )
    me_res = urllib.request.urlopen(me_req)
    me_data = json.loads(me_res.read())
    print(f"PASS: {username} (ID {user_id}) -> /auth/me authenticated as {me_data['username']} with roles {me_data['roles']}")
