import asyncio
import random
import time
from collections import deque
from typing import Optional

from . import config
from . import kick_api
from . import websocket_client
from . import llm_generator
from . import message_sender

class MessagePool:
    """A thread-safe pool of messages that can be completely replaced."""
    def __init__(self):
        self.messages = []
        self._lock = asyncio.Lock()
        self._has_messages = asyncio.Event()

    async def replace(self, new_messages: list[str]):
        """Replaces the entire pool with a new list of messages."""
        async with self._lock:
            self.messages = new_messages
            if self.messages:
                self._has_messages.set()
            else:
                self._has_messages.clear()
        print(f"Message pool refreshed with {len(new_messages)} new messages.")

    async def get_message(self) -> str | None:
        """Gets a random message from the pool, removing it."""
        await self._has_messages.wait()  # Wait here if the pool is empty
        async with self._lock:
            if not self.messages:
                return None
            
            message = random.choice(self.messages)
            self.messages.remove(message)

            if not self.messages:
                self._has_messages.clear()
            
            return message

async def generation_loop(ws_client: websocket_client.WebSocketClient, message_pool: MessagePool):
    """
    Periodically fetches messages from the websocket client, generates new ones,
    and refreshes the message pool.
    """
    while True:
        await asyncio.sleep(config.MESSAGE_COLLECTION_SECONDS)
        
        chat_history, ignored_count = await ws_client.get_and_clear_messages()

        if not chat_history:
            continue
            
        try:
            if ignored_count > 0:
                print(f"({ignored_count} messages from own bots were ignored before sending to LLM)")

            # Run the synchronous LLM call in a separate thread to avoid blocking the event loop
            generated_messages = await asyncio.to_thread(
                llm_generator.generate_messages,
                chat_history
            )
            await message_pool.replace(generated_messages)

        except llm_generator.LlmApiError as e:
            print(f"--- Error generating messages: {e} ---")

async def sender_loop(chatroom_id: int, message_pool: MessagePool, messages_per_minute: int, sender_count: int, message_log: Optional[deque] = None):
    """
    Takes messages from the pool and sends them to the chatroom, respecting the rate limit.
    """
    if not config.ACCOUNTS:
        print("No accounts loaded. The sender loop will not run.")
        return

    # Calculate the AVERAGE delay required to meet the target rate across all senders.
    average_delay = sender_count * (60.0 / messages_per_minute)
    
    while True:
        try:
            message_to_send = await message_pool.get_message()
            if message_to_send is None:
                continue
            
            account = random.choice(config.ACCOUNTS)
            proxy = random.choice(config.PROXIES) if config.PROXIES else None
            
            sender = message_sender.MessageSender(
                auth_token=account["auth_token"],
                chatroom_id=chatroom_id,
                proxy=proxy,
                username=account.get("username")
            )
            
            await asyncio.to_thread(
                sender.send_message,
                message_to_send
            )
            
            if message_log is not None:
                username = account.get("username", "Unknown")
                message_log.append(f"[{username}]: {message_to_send}")

            # Sleep for a RANDOMIZED duration around the average delay to prevent bursting.
            # This creates a more natural, continuous flow of messages.
            jitter = average_delay * 0.5  # e.g., +/- 50% of the average delay
            randomized_delay = random.uniform(average_delay - jitter, average_delay + jitter)
            await asyncio.sleep(randomized_delay)
            
        except Exception as e:
            print(f"An error occurred in the sender loop: {e}")

async def run_bot(channel_name: str, messages_per_minute: int, sender_count: int, message_log: Optional[deque] = None):
    """
    Connects to the chatbot, starts all loops, and runs until cancellation.
    """
    try:
        chatroom_id = kick_api.get_chatroom_id(channel_name)
        
        ws_client = websocket_client.WebSocketClient(chatroom_id, config.BOT_USERNAMES)
        await ws_client.connect()
        
        message_pool = MessagePool()
        
        # --- Create and run tasks ---
        listener_task = asyncio.create_task(ws_client.listen())
        generator_task = asyncio.create_task(generation_loop(ws_client, message_pool))
        
        sender_tasks = [
            asyncio.create_task(sender_loop(chatroom_id, message_pool, messages_per_minute, sender_count, message_log))
            for _ in range(sender_count)
        ]
        
        all_tasks = [listener_task, generator_task] + sender_tasks
        print(f"Bot started for channel: {channel_name}")
        await asyncio.gather(*all_tasks)

    except kick_api.KickApiError as e:
        print(f"Failed to start chatbot due to a Kick API error: {e}")
    except asyncio.CancelledError:
        print(f"Bot for channel {channel_name} is stopping as the stream is offline.")
    except Exception as e:
        print(f"An unexpected error occurred in the bot runner: {e}")
    finally:
        # This block will execute upon cancellation
        print(f"Bot for {channel_name} has been shut down.") 