import urllib.request
import json

url = "http://127.0.0.1:5000/api/chat"
data = json.dumps({
    "message": "How is my current health condition?",
    "user_id": 1
}).encode('utf-8')

req = urllib.request.Request(url, data=data, headers={'Content-Type': 'application/json'})

try:
    with urllib.request.urlopen(req) as response:
        result = response.read().decode('utf-8')
        print(json.dumps(json.loads(result), indent=4))
except Exception as e:
    print(f"Error: {e}")
