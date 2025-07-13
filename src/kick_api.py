import primp
import json
from . import config

class KickApiError(Exception):
    """Custom exception for Kick API errors."""
    pass

def get_chatroom_id(channel_name: str) -> int:
    """
    Fetches the chatroom ID for a given Kick channel name.

    Args:
        channel_name: The name of the Kick channel.

    Returns:
        The integer ID of the chatroom.

    Raises:
        KickApiError: If the API request fails or the response is invalid.
    """
    api_url = f"https://kick.com/api/v2/channels/{channel_name}/chatroom"
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.5",
        "referer": f"https://kick.com/{channel_name}",
    }

    try:
        client = primp.Client(
            impersonate="chrome_124", 
            impersonate_os="windows",
            headers=headers,
            timeout=30
        )
        
        print(f"Fetching chatroom ID for channel: {channel_name}")
        resp = client.get(api_url)

        if resp.status_code >= 400:
            raise KickApiError(f"HTTP Error: {resp.status_code}. Response: {resp.text}")

        data = resp.json()
        
        chatroom_id = data.get("id")
        if not chatroom_id or not isinstance(chatroom_id, int):
            raise KickApiError(f"Could not find 'id' in response from {api_url}. Response: {data}")
            
        print(f"Successfully found chatroom ID: {chatroom_id}")
        return chatroom_id

    except Exception as e:
        print(f"An unexpected error occurred while fetching chatroom ID: {e}")
        raise KickApiError(f"Failed to get chatroom ID for {channel_name}.") from e

def is_channel_live(channel_name: str) -> bool:
    """
    Checks if a Kick channel is currently live.

    Args:
        channel_name: The name of the Kick channel.

    Returns:
        True if the channel is live, False otherwise.

    Raises:
        KickApiError: If the API request fails or the response is invalid.
    """
    api_url = f"https://kick.com/api/v2/channels/{channel_name}"
    
    headers = {
        "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.5",
        "referer": f"https://kick.com/{channel_name}",
    }

    try:
        client = primp.Client(
            impersonate="chrome_124", 
            impersonate_os="windows",
            headers=headers,
            timeout=30
        )
        
        print(f"Checking live status for channel: {channel_name}")
        resp = client.get(api_url)

        if resp.status_code >= 400:
            raise KickApiError(f"HTTP Error: {resp.status_code}. Response: {resp.text}")

        data = resp.json()
        
        livestream = data.get("livestream")
        return livestream is not None

    except Exception as e:
        print(f"An unexpected error occurred while checking live status: {e}")
        raise KickApiError(f"Failed to check live status for {channel_name}.") from e 