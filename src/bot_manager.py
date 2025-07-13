import asyncio
from typing import Dict, Any, Optional
from collections import deque

from . import kick_api, config
from .main import run_bot # Re-use the run_bot logic

class BotManager:
    """Manages the lifecycle of multiple chatbot instances."""
    def __init__(self):
        self._bots: Dict[str, Dict[str, Any]] = {}
        self._lock = asyncio.Lock()

    async def start_bot(self, channel_name: str, messages_per_minute: int, sender_count: int) -> bool:
        """
        Starts a monitoring task for a given channel if it's not already running.
        """
        async with self._lock:
            if channel_name in self._bots:
                return False  # Bot is already running or being managed

            monitor_task = asyncio.create_task(
                self._monitor_channel(channel_name, messages_per_minute, sender_count)
            )
            self._bots[channel_name] = {
                "task": monitor_task,
                "status": "initializing",
                "recent_messages": deque(maxlen=20)
            }
            print(f"Bot manager started monitoring for channel: {channel_name}")
            return True

    async def stop_bot(self, channel_name: str) -> bool:
        """
        Stops the monitoring task for a given channel.
        """
        async with self._lock:
            bot_info = self._bots.get(channel_name)
            if not bot_info:
                return False # Bot not found

            bot_info["task"].cancel()
            await asyncio.wait([bot_info["task"]])
            # The task cleans itself up from the dict in its `finally` block.
            # No need to delete it here.
            print(f"Bot manager stopped monitoring for channel: {channel_name}")
            return True

    def get_bot_status(self, channel_name: str) -> Optional[Dict[str, Any]]:
        """
        Returns the status of a specific bot.
        """
        bot_info = self._bots.get(channel_name)
        if not bot_info:
            return None
        
        return {
            "status": bot_info.get("status"),
            "recent_messages": list(bot_info.get("recent_messages", []))
        }

    def list_bots(self) -> Dict[str, str]:
        """
        Returns a dictionary of all managed bots and their statuses.
        """
        return {name: info["status"] for name, info in self._bots.items()}

    async def _monitor_channel(self, channel_name: str, messages_per_minute: int, sender_count: int):
        """
        The core monitoring loop for a single channel.
        This is the task that runs in the background for each managed bot.
        """
        bot_task = None
        try:
            while True:
                try:
                    is_live = await asyncio.to_thread(kick_api.is_channel_live, channel_name)
                    
                    self._bots[channel_name]["status"] = "live" if is_live else "offline"

                    if is_live and (bot_task is None or bot_task.done()):
                        print(f"Channel {channel_name} is live. Starting bot...")
                        self._bots[channel_name]["status"] = "running"
                        message_log = self._bots[channel_name]["recent_messages"]
                        bot_task = asyncio.create_task(run_bot(
                            channel_name, 
                            messages_per_minute, 
                            sender_count,
                            message_log
                        ))
                    
                    elif not is_live and bot_task is not None and not bot_task.done():
                        print(f"Channel {channel_name} is offline. Stopping bot...")
                        bot_task.cancel()
                        await asyncio.wait([bot_task])
                        bot_task = None
                        self._bots[channel_name]["status"] = "offline"
                
                except kick_api.KickApiError as e:
                    print(f"API error for {channel_name}: {e}. Retrying...")
                    self._bots[channel_name]["status"] = f"api_error"
                except Exception as e:
                    print(f"Unexpected error for {channel_name}: {e}. Retrying...")
                    self._bots[channel_name]["status"] = "internal_error"
                
                await asyncio.sleep(config.LIVE_CHECK_INTERVAL_SECONDS)
        except asyncio.CancelledError:
            if bot_task and not bot_task.done():
                bot_task.cancel()
                await asyncio.wait([bot_task])
            print(f"Monitoring for {channel_name} was cancelled.")
        finally:
            self._bots.pop(channel_name, None)
            print(f"Stopped monitoring {channel_name}.") 