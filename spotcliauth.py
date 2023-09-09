from flask import Flask, redirect, request, jsonify
import random
import string
import urllib.parse
import base64
import requests

client_id = 'your_client_id'
client_secret = 'your_client_secret'
redirect_uri = 'http://localhost:8888/callback'

app = Flask(__name__)

def generate_random_string(length):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

@app.route('/login')
def login():
    state = generate_random_string(16)
    scope = 'user-read-playback-state user-modify-playback-state user-read-currently-playing playlist-read-private playlist-modify-private playlist-modify-public user-follow-modify user-follow-read user-library-modify user-library-read user-read-private'  
    auth_url = 'https://accounts.spotify.com/authorize?' + urllib.parse.urlencode({
        'response_type': 'code',
        'client_id': client_id,
        'scope': scope,
        'redirect_uri': redirect_uri,
        'state': state
    })
    
    return redirect(auth_url)

@app.route('/callback')
def callback():
    auth_code = request.args.get('code')
    state = request.args.get('state')
    token_url = 'https://accounts.spotify.com/api/token'
    data = {
        'grant_type': 'authorization_code',
        'code': auth_code,
        'redirect_uri': redirect_uri,
    }
    headers = {
        'Authorization': f'Basic {base64.b64encode(f"{client_id}:{client_secret}".encode()).decode()}',
    }
    response = requests.post(token_url, data=data, headers=headers)
    
    if response.status_code == 200:
        token_data = response.json()

        return token_data

    else:
        error_data = response.json()
        error_description = error_data.get('error_description', 'Token exchange failed.')
        
        return f"Token exchange failed: {error_description}"

if __name__ == '__main__':
    app.run(port=8888)

