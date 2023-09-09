import argparse
import configparser
from cryptography.fernet import Fernet
import os
import requests

def get_spotify_country(bearer_token):
    # Define the Spotify API endpoint URL
    api_url = "https://api.spotify.com/v1/me"

    # Set up the headers with the bearer token
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    try:
        # Make the GET request to the Spotify API
        response = requests.get(api_url, headers=headers)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Retrieve the "country" attribute from the JSON
            country = data.get("country")

            if country:
                return country
            else:
                return "Country not found in response."

        else:
            return f"Request failed with status code {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

def get_decrypted_token():
    # Define the path to the user's home directory
    home_dir = os.path.expanduser("~")
    config_file_path = os.path.join(home_dir, 'config.ini')
    key_file = os.path.join(home_dir, 'encryption_key.key')

    # Check if config.ini and the encryption key exist
    if not (os.path.exists(config_file_path) and os.path.exists(key_file)):
        return None  # Return None if either the config or key files are missing

    # Read the encryption key
    with open(key_file, 'rb') as key_file:
        key = key_file.read()

    # Read the encrypted token from config.ini
    config = configparser.ConfigParser()
    config.read(config_file_path)
    if 'Credentials' in config and 'token' in config['Credentials']:
        encrypted_token = config['Credentials']['token']
    else:
        return None  # Return None if the token is not found in the config

    # Decrypt the token and return it
    try:
        f = Fernet(key)
        decrypted_token = f.decrypt(encrypted_token.encode()).decode()
        return decrypted_token
    except Exception as e:
        print(f"Error decrypting token: {e}")
        return None

def get_current_track_id(bearer_token, market):
    # Define the Spotify API endpoint URL
    api_url = "https://api.spotify.com/v1/me/player"

    # Set up the headers with the bearer token
    headers = {
        "Authorization": f"Bearer {bearer_token}"
    }

    # Set up the query parameters
    params = {
        "market": market
    }

    try:
        # Make the GET request to the Spotify API
        response = requests.get(api_url, headers=headers, params=params)

        # Check if the request was successful (HTTP status code 200)
        if response.status_code == 200:
            # Parse the JSON response
            data = response.json()

            # Check if the "item" attribute exists in the JSON
            if "item" in data:
                # Retrieve the "id" attribute from the "item" dictionary
                track_id = data["item"].get("id")

                if track_id:
                    return track_id
                else:
                    return "Track ID not found in response."

            else:
                return "No track currently playing."

        else:
            return f"Request failed with status code {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

def add_tracks_to_liked(bearer_token, track_ids):
    # Define the Spotify API endpoint URL
    api_url = "https://api.spotify.com/v1/me/tracks"

    # Set up the headers with the bearer token
    headers = {
        "Authorization": f"Bearer {bearer_token}",
        "Content-Type": "application/json"
    }

    # Create a dictionary with the track IDs
    data = {
        "ids": track_ids
    }

    try:
        # Make the PUT request to the Spotify API
        response = requests.put(api_url, headers=headers, json=data)

        # Check if the request was successful (HTTP status code 200 or 201)
        if response.status_code in [200, 201]:
            return "Tracks added to library successfully."

        else:
            return f"Request failed with status code {response.status_code}"

    except requests.exceptions.RequestException as e:
        return f"Request error: {e}"

def handle_config(args):    
    # Generate a secret key for encryption
    def generate_key():
        return Fernet.generate_key()

    # Encrypt sensitive data
    def encrypt_data(key, data):
        f = Fernet(key)
        return f.encrypt(data.encode()).decode()

    # Define the path to the user's home directory
    home_dir = os.path.expanduser("~")
    config_file_path = os.path.join(home_dir, 'config.ini')

    # Create or load the encryption key
    key_file = os.path.join(home_dir, 'encryption_key.key')
    try:
        with open(key_file, 'rb') as key_file:
            key = key_file.read()
    except FileNotFoundError:
        key = generate_key()
        with open(key_file, 'wb') as key_file:
            key_file.write(key)

    # Encrypt sensitive data
    encrypted_token = encrypt_data(key, args.token)

    # Store encrypted data in config.ini
    config = configparser.ConfigParser()
    config['Credentials'] = {
        'token': encrypted_token
    }

    with open(config_file_path, 'w') as config_file:
        config.write(config_file)

def handle_help(args):
    print(f"help text here")

def handle_current(args):
    if args.add and args.album:
        print("Like current album")
    elif args.add and args.artist:
        print("Follow current artist")
    elif args.add and args.playlist:
        print("Add current song from playlists")
    elif args.add:
        token = get_decrypted_token()
        country = get_spotify_country(token)
        track_id = get_current_track_id(token, country)
        if track_id:
          add_tracks_to_liked(get_decrypted_token(), [track_id])
          print("Added track to liked tracks.")
        else:
          print("Unable to get the current track ID.")
    elif args.remove and args.album:
        print("Remove liked album")
    elif args.remove and args.artist:
        print("Unfollow artist")
    elif args.remove and args.playlist:
        print("Remove current song from playlists")
    elif args.remove:
        print("Remove current song from liked")
    else:
        print("Invalid operation")

def main():
    parser = argparse.ArgumentParser(description='Desc')

    subparsers = parser.add_subparsers(title='Commands', dest='command', required=True)

    # Subparser for the 'help' command
    help_parser = subparsers.add_parser('help', help='Display commands')
    help_parser.set_defaults(func=handle_help)

    # Subparser for the 'config' command
    name_parser = subparsers.add_parser('config', help='Set token')
    name_parser.add_argument('--token', required=True, help='Set token for requests')
    name_parser.set_defaults(func=handle_config)

    # Subparser for the 'current' command
    current_parser = subparsers.add_parser('current', help='Actions for current playing track.')
    current_parser.add_argument('--remove', action='store_true', required=False, help='Remove from Playlists/Liked')
    current_parser.add_argument('--add', action='store_true', required=False, help='Like/Add current track')
    current_parser.add_argument('--playlist', action='store_true', required=False, help='Select which playlists to add into')
    current_parser.add_argument('--album', action='store_true', required=False, help='Like current album')
    current_parser.add_argument('--artist', action='store_true', required=False, help='Follow current artist')
    current_parser.set_defaults(func=handle_current)

    args = parser.parse_args()

    # Call the appropriate function based on the selected command
    args.func(args)

if __name__ == '__main__':
    main()
    
    
