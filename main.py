import requests
import re
import base64
import json
from bs4 import BeautifulSoup
import os


def xor_decrypt(data_base64, key):
    try:
        decoded_bytes = base64.b64decode(data_base64)
        output = []
        key_length = len(key)
        for i in range(len(decoded_bytes)):
            decoded_byte = decoded_bytes[i]
            key_char_code = ord(key[i % key_length])
            output.append(chr(decoded_byte ^ key_char_code))
        return "".join(output)
    except Exception as e:
        print(f"[ERROR] Decryption error: {e}")
        return None

def fetch_and_decrypt_stream_info(url, content_id):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Referer': url
    }
    
    print(f"\n-> Processing ID: {content_id}")
    try:
        response = requests.get(url, headers=headers, timeout=10)
        response.raise_for_status() 
        html_content = response.text
    except requests.exceptions.RequestException as e:
        print(f"[ERROR] Error fetching stream URL ({url}): {e}")
        return None

    key_match = re.search(r'const decryptionKey = "(.*?)";', html_content)
    encrypted_match = re.search(r'let encrypted = "(.*?)";', html_content)
    if not key_match or not encrypted_match:
        print("[WARNING] Could not find decryption key or encrypted data on the page.")
        return None

    decryption_key = key_match.group(1)
    encrypted_data = encrypted_match.group(1)
    decrypted_js = xor_decrypt(encrypted_data, decryption_key)
    if not decrypted_js:
        return None

    mpd_url_match = re.search(r"const mpdUrl = '(.*?)';", decrypted_js)
    kid_match = re.search(r"const kid = '(.*?)';", decrypted_js)
    key_value_match = re.search(r"const key = '(.*?)';", decrypted_js)

    if not mpd_url_match or not kid_match or not key_value_match:
        print("[WARNING] Could not find stream details in the decrypted JavaScript.")
        return None

    stream_info = {
        "mpdUrl": mpd_url_match.group(1),
        "kid": kid_match.group(1),
        "key": key_value_match.group(1)
    }

    print(f"[SUCCESS] Extracted data for {content_id}: mpdUrl (start)={stream_info['mpdUrl'][:25]}...")
    return stream_info

def save_to_json(data, filename="api_data.json"):
    try:
        with open(filename, 'w') as f:
            json.dump(data, f, indent=4)
        print(f"[INFO] Successfully saved all data to {filename}.")
    except Exception as e:
        print(f"[ERROR] Failed to save JSON file: {e}")

def get_channel_ids(base_listing_url):
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    print(f"[INFO] Fetching channel listing from: {base_listing_url}")
    try:
        response = requests.get(base_listing_url, headers=headers, timeout=15)
        response.raise_for_status()
    except requests.exceptions.RequestException as e:
        print(f"[FATAL] Error fetching listing URL: {e}")
        return []

    soup = BeautifulSoup(response.text, 'html.parser')
    ids = set()
    for link in soup.select('div.channel a[href*="play.php?id="]'):
        href = link.get('href')
        match = re.search(r'id=([a-fA-F0-9]+)', href)
        if match:
            ids.add(match.group(1))
    print(f"[INFO] Found {len(ids)} unique channel IDs.")
    return list(ids)

# --- MAIN EXECUTION ---

def main():
    BASE_LISTING_URL = os.getenv("BASE_LISTING_URL")
    BASE_STREAM_URL = os.getenv("BASE_STREAM_URL")
    
    if not BASE_LISTING_URL or not BASE_STREAM_URL:
        print("[FATAL] BASE_LISTING_URL or BASE_STREAM_URL not set in environment variables!")
        return

    channel_ids = get_channel_ids(BASE_LISTING_URL)
    if not channel_ids:
        print("No IDs found. Exiting.")
        return

    all_stream_data = {}
    try:
        with open("api_data.json", 'r') as f:
            all_stream_data = json.load(f)
        print("[INFO] Loaded existing data from api_data.json.")
    except (FileNotFoundError, json.JSONDecodeError):
        print("[INFO] Starting with an empty dataset.")

    for content_id in channel_ids:
        full_url = BASE_STREAM_URL + content_id
        stream_info = fetch_and_decrypt_stream_info(full_url, content_id)
        if stream_info:
            all_stream_data[content_id] = stream_info

    save_to_json(all_stream_data)

if __name__ == "__main__":
    main()
