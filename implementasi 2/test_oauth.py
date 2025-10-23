import requests

# Ganti dengan credentials Anda
CLIENT_ID = 'http://1070506598093-fh66ogvcqvsiv2tfct7a8cs98jm6ahhv.apps.googleusercontent.com'
CLIENT_SECRET = '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'
REDIRECT_URI = 'http://localhost:5000/google-callback'

def test_oauth_config():
    print("=== Testing OAuth Configuration ===")
    print(f"Client ID: {CLIENT_ID}")
    print(f"Redirect URI: {REDIRECT_URI}")
    
    # Test jika Client ID valid
    auth_url = f"https://accounts.google.com/.well-known/openid-configuration"
    try:
        response = requests.get(auth_url)
        if response.status_code == 200:
            print("✅ OpenID configuration accessible")
        else:
            print("❌ OpenID configuration not accessible")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_oauth_config()