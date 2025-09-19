import requests
import os

def test_elevenlabs_api():
    """Test ElevenLabs API connection"""
    
    # Get API key from user
    api_key = input("Enter your ElevenLabs API key: ").strip()
    
    if not api_key:
        print("No API key provided")
        return
    
    # Test API connection by getting voices
    url = "https://api.elevenlabs.io/v1/voices"
    headers = {
        "Accept": "application/json",
        "xi-api-key": api_key
    }
    
    try:
        print("Testing ElevenLabs API connection...")
        response = requests.get(url, headers=headers)
        
        print(f"Status Code: {response.status_code}")
        print(f"Response: {response.text}")
        
        if response.status_code == 200:
            voices = response.json()
            print(f"Success! Found {len(voices.get('voices', []))} voices")
        else:
            print(f"Error: {response.status_code} - {response.text}")
            
    except Exception as e:
        print(f"Exception occurred: {e}")

if __name__ == "__main__":
    test_elevenlabs_api()
