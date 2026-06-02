import requests

payload = {
    'action': 'opened',
    # Here is your PR number!
    'pull_request': {'number': 1}, 
    # Here is your exact GitHub username and repo!
    'repository': {'full_name': 'Thanvitha-mitta/Python'} 
}

print("Sending simulated GitHub webhook to your local server...")

# Send the POST request to our FastAPI server
response = requests.post('http://127.0.0.1:8000/webhook', json=payload)

print('Server replied:', response.json())