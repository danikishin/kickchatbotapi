from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

from .bot_manager import BotManager
from . import config

app = FastAPI(
    title="Kick Chatbot API",
    description="An API to manage chatbot instances for Kick.com channels.",
    version="1.0.0"
)

# --- State ---
bot_manager = BotManager()

# --- Models ---
class BotStartRequest(BaseModel):
    messages_per_minute: int = Field(20, gt=0, description="Messages the bot should send per minute.")
    sender_count: int = Field(10, gt=0, description="Number of concurrent senders.")

class BotStatusResponse(BaseModel):
    status: str
    recent_messages: list[str] = []

class BotListResponse(BaseModel):
    bots: dict[str, str]

# --- Endpoints ---
@app.on_event("startup")
async def startup_event():
    if not config.ACCOUNTS:
        print("Warning: accs.txt is empty or not found. The bot will not be able to send messages.")

@app.post("/bots/{channel_name}/start", status_code=202)
async def start_bot_endpoint(channel_name: str, request: BotStartRequest):
    """
    Start a new chatbot for a given Kick channel.
    This will begin monitoring the channel and will run the bot whenever the channel is live.
    """
    success = await bot_manager.start_bot(
        channel_name,
        request.messages_per_minute,
        request.sender_count
    )
    if not success:
        raise HTTPException(status_code=409, detail="A bot for this channel is already being managed.")
    return {"message": f"Bot monitoring has been initiated for channel '{channel_name}'."}

@app.post("/bots/{channel_name}/stop", status_code=200)
async def stop_bot_endpoint(channel_name: str):
    """
    Stop the chatbot for a given Kick channel.
    This will cancel the monitoring task and shut down the bot if it's running.
    """
    success = await bot_manager.stop_bot(channel_name)
    if not success:
        raise HTTPException(status_code=404, detail="No bot found for the specified channel.")
    return {"message": f"Bot for channel '{channel_name}' has been stopped."}

@app.get("/bots/{channel_name}", response_model=BotStatusResponse)
async def get_bot_status_endpoint(channel_name: str):
    """
    Get the current status of a specific chatbot, including recent messages.
    """
    bot_info = bot_manager.get_bot_status(channel_name)
    if bot_info is None:
        raise HTTPException(status_code=404, detail="No bot found for the specified channel.")
    return bot_info

@app.get("/bots", response_model=BotListResponse)
async def list_bots_endpoint():
    """
    List all currently managed bots and their statuses.
    """
    bots = bot_manager.list_bots()
    return {"bots": bots} 