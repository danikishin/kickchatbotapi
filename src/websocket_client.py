import asyncio
import json
import time
import websockets
from websockets.client import WebSocketClientProtocol
from websockets.typing import Data
from . import config

class WebSocketClient:
    """
    Manages the WebSocket connection to Kick's chat servers to receive live messages.
    """
    def __init__(self, chatroom_id: int, bot_usernames: set[str]):
        self.chatroom_id = chatroom_id
        self.ws_url = config.KICK_WEBSOCKET_URL
        self.websocket: WebSocketClientProtocol | None = None
        self.messages = []
        self._last_ping_time = time.time()
        self.bot_usernames = bot_usernames
        self.ignored_message_count = 0
        self._lock = asyncio.Lock()

    async def connect(self):
        """
        Connects to the WebSocket server and subscribes to the chatroom channels.
        """
        print(f"Connecting to WebSocket server for chatroom {self.chatroom_id}...")
        try:
            self.websocket = await websockets.connect(self.ws_url)
            print("WebSocket connection established.")
            await self._subscribe()
        except Exception as e:
            print(f"Failed to connect to WebSocket: {e}")
            raise

    async def _subscribe(self):
        """
        Sends subscription messages to the chatroom channels.
        """
        assert self.websocket is not None
        subscriptions = [
            {"event": "pusher:subscribe", "data": {"auth": "", "channel": f"chatrooms.{self.chatroom_id}.v2"}},
            {"event": "pusher:subscribe", "data": {"auth": "", "channel": f"chatrooms.{self.chatroom_id}"}},
        ]
        for sub in subscriptions:
            await self.websocket.send(json.dumps(sub))
            print(f"Subscribed to channel: {sub['data']['channel']}")

    async def _handle_message(self, raw_message: Data):
        """
        Parses and handles incoming WebSocket messages.
        """
        assert self.websocket is not None
        
        message_text: str
        if isinstance(raw_message, bytes):
            message_text = raw_message.decode('utf-8')
        else:
            message_text = raw_message
            
        message = json.loads(message_text)
        event = message.get("event")
        data_str = message.get("data", "{}")
        data = json.loads(data_str)

        if event == "pusher:connection_established":
            print("Pusher connection confirmed.")
        elif event == "App\\Events\\ChatMessageEvent":
            async with self._lock:
                sender_username = data.get("sender", {}).get("username")
                if sender_username in self.bot_usernames:
                    self.ignored_message_count += 1
                    return  # Ignore messages from our own bots

                message_content = {
                    "id": data.get("id"),
                    "content": data.get("content"),
                    "sender": sender_username,
                    "created_at": data.get("created_at"),
                }
                self.messages.append(message_content)
        elif event == "pusher:ping":
            await self.websocket.send(json.dumps({"event": "pusher:pong"}))
            self._last_ping_time = time.time()
            
    async def _keep_alive(self):
        """
        Sends a ping to the server every 50 seconds to keep the connection alive.
        Pusher servers disconnect after 60 seconds of inactivity.
        """
        while True:
            await asyncio.sleep(50)
            if self.websocket and self.websocket.open:
                await self.websocket.send(json.dumps({"event": "pusher:ping"}))

    async def listen(self):
        """
        Listens for incoming messages and handles them.
        """
        if not self.websocket:
            await self.connect()

        assert self.websocket is not None
        # Start the keep-alive task
        asyncio.create_task(self._keep_alive())

        print("Listening for chat messages...")
        async for message in self.websocket:
            await self._handle_message(message)

    async def get_and_clear_messages(self) -> tuple[list, int]:
        """
        Safely returns the list of collected messages and the ignored count,
        then clears the internal data.
        """
        async with self._lock:
            current_messages = self.messages.copy()
            ignored_count = self.ignored_message_count
            
            self.messages.clear()
            self.ignored_message_count = 0
            
            return current_messages, ignored_count 