import primp
import time

class MessageSenderError(Exception):
    """Custom exception for the MessageSender."""
    pass

class MessageSender:
    """
    Handles the sending of a single message to a Kick chatroom using a specific account and proxy.
    """
    def __init__(self, auth_token: str, chatroom_id: int, proxy: str | None = None, username: str | None = None):
        if not auth_token:
            raise MessageSenderError("Authorization token cannot be empty.")
            
        self.auth_token = auth_token
        self.chatroom_id = chatroom_id
        self.proxy = proxy
        self.username = username
        self.api_url = f"https://kick.com/api/v2/messages/send/{self.chatroom_id}"

    def send_message(self, message_content: str) -> bool:
        """
        Sends a message to the chatroom.

        Args:
            message_content: The text of the message to send.

        Returns:
            True if the message was sent successfully, False otherwise.
        """
        headers = {
            "accept": "application/json",
            "accept-language": "en,tr;q=0.9",
            "authorization": f"Bearer {self.auth_token}",
            "content-type": "application/json",
            "sec-ch-ua": '"Not)A;Brand";v="8", "Chromium";v="138"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-origin",
        }
        
        message_ref = str(int(time.time() * 1000))
        
        body = {
            "content": message_content,
            "type": "message",
            "message_ref": message_ref
        }

        try:
            client = primp.Client(
                impersonate="chrome_124", 
                proxy=self.proxy,
                timeout=15
            )
            resp = client.post(
                url=self.api_url,
                headers=headers,
                json=body
            )

            if resp.status_code == 200:
                user_prefix = f"<{self.username}>" if self.username else ""
                print(f"-> {user_prefix} Sent: '{message_content}'")
                return True
            else:
                print(f"-> Failed to send message. Status: {resp.status_code}, Response: {resp.text}")
                return False
        except Exception as e:
            print(f"-> An error occurred while sending message: {e}")
            return False 