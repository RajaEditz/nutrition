import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"
messages = [
    "Log my weight as 95kg",
    "How is my health status now?"
]

for msg in messages:
    print(f"User: {msg}")
    data = json.dumps({
        "message": msg,
        "user_id": 1
    }).encode('utf-8')
    req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print(f"AI: {json.loads(result)['response']}\n")
