import os
from dotenv import load_dotenv

# Load environment variables from a .env file
load_dotenv()

# --- OpenRouter Configuration ---
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# --- Chatbot Configuration ---
MESSAGE_COLLECTION_SECONDS = int(os.getenv("MESSAGE_COLLECTION_SECONDS", 30))
LIVE_CHECK_INTERVAL_SECONDS = int(os.getenv("LIVE_CHECK_INTERVAL_SECONDS", 30))

# --- WebSocket Configuration ---
KICK_WEBSOCKET_URL = "wss://ws-us2.pusher.com/app/32cbd69e4b950bf97679?protocol=7&client=js&version=8.4.0&flash=false"

def load_accounts():
    """Loads accounts from accs.txt."""
    accounts = []
    try:
        with open("accs.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if not line or '|' not in line:
                    continue
                parts = line.split('|')
                if len(parts) >= 2:
                    auth_token = f"{parts[0]}|{parts[1]}"
                    # The rest of the line might contain user:pass info
                    rest = parts[2] if len(parts) > 2 else ""
                    username = rest.split(':')[0].strip() if ':' in rest else None
                    accounts.append({"auth_token": auth_token, "username": username})
    except FileNotFoundError:
        print("Warning: accs.txt not found. The bot will not be able to send messages.")
    return accounts

def load_proxies():
    """Loads proxies from proxies.txt."""
    proxies = []
    try:
        with open("proxies.txt", "r", encoding="utf-8") as f:
            for line in f:
                line = line.strip()
                if line:
                    proxies.append(f"http://{line}")
    except FileNotFoundError:
        print("Warning: proxies.txt not found. Messages will be sent without proxies.")
    return proxies

# --- Load Accounts and Proxies ---
ACCOUNTS = load_accounts()
PROXIES = load_proxies()
BOT_USERNAMES = {acc["username"] for acc in ACCOUNTS if acc["username"]}


# --- Validation ---
if not OPENROUTER_API_KEY:
    raise ValueError("OPENROUTER_API_KEY environment variable not set. Please provide your OpenRouter API key.") 