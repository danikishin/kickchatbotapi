# Kick Realistic Chatbot API

This project provides an API to run and manage multiple Python-based chatbots for Kick.com live streams. It reads chat messages in real-time, understands the context of the conversation, and uses a Large Language Model (LLM) via OpenRouter to generate and send new, realistic messages that mimic the style of the chat.

## Features

- **API-Driven**: Manage multiple bots across different channels programmatically.
- **Automatic Live/Offline Handling**: Bots automatically start when a channel goes live and stop when it goes offline.
- **Live Chat Monitoring**: Connects to any public Kick.com chatroom via WebSockets.
- **Context-Aware Message Generation**: Gathers recent chat messages to understand the live conversation's context, tone, and style.
- **Realistic AI Chatting**: Uses a sophisticated prompt with OpenRouter to generate messages that realistically mimic the slang, emotes, and grammar of other users in the chatroom.
- **Browser Impersonation**: Uses `primp` to send realistic, successful requests to Kick's public APIs.

## Project Structure

```
kick-realistic-chatbot/
├── src/
│   ├── api.py                # FastAPI application entry point.
│   ├── bot_manager.py        # Manages the lifecycle of bot instances.
│   ├── config.py             # Handles configuration and environment variables.
│   ├── kick_api.py           # Interacts with the Kick.com HTTP API.
│   ├── websocket_client.py   # Manages the WebSocket connection to the chat server.
│   ├── llm_generator.py      # Handles interaction with the OpenRouter LLM API.
│   └── main.py               # Contains the core bot running logic.
├── .env                    # Stores environment variables (API keys, etc.).
├── .gitignore              # Specifies files to be ignored by Git.
└── requirements.txt        # Lists the Python project dependencies.
```

## How to Run

1.  **Clone the Repository**

    ```bash
    git clone <repository-url>
    cd kick-realistic-chatbot
    ```

2.  **Create an Environment File**

    Create a `.env` file in the root of the project and add your OpenRouter API key:

    ```env
    # .env
    OPENROUTER_API_KEY="YOUR_OPENROUTER_API_KEY_HERE"
    ```

3.  **Install Dependencies**

    Create a virtual environment and install the required packages.

    ```bash
    # Create and activate a virtual environment
    python -m venv venv
    source venv/bin/activate  # On Windows, use `venv\Scripts\activate`

    # Install dependencies
    pip install -r requirements.txt
    ```

4.  **Run the API Server**

    ```bash
    uvicorn src.api:app --reload
    ```
    The API server will start, and you can access the interactive documentation at `http://127.0.0.1:8000/docs`.

## API Endpoints

The API provides the following endpoints to manage the chatbots:

#### `POST /bots/{channel_name}/start`

Starts a new chatbot for a given channel. The bot will monitor the channel and become active when the stream is live.

-   **URL Params**: `channel_name` (string, required) - The Kick channel name.
-   **Body**: 
    ```json
    {
      "messages_per_minute": 20,
      "sender_count": 10
    }
    ```
-   **Success Response**: `202 Accepted`
-   **Failure Response**: `409 Conflict` if a bot for that channel is already running.

#### `POST /bots/{channel_name}/stop`

Stops a running chatbot for a given channel.

-   **URL Params**: `channel_name` (string, required) - The Kick channel name.
-   **Success Response**: `200 OK`
-   **Failure Response**: `404 Not Found` if no bot is running for that channel.

#### `GET /bots/{channel_name}`

Retrieves the current status of a specific bot.

-   **URL Params**: `channel_name` (string, required) - The Kick channel name.
-   **Success Response**: `200 OK` with a body like `{"status": "running"}`. Status can be `initializing`, `running`, `offline`, `api_error`, etc.
-   **Failure Response**: `404 Not Found`.

#### `GET /bots`

Lists all currently managed bots and their statuses.

-   **Success Response**: `200 OK` with a body like `{"bots": {"channel1": "running", "channel2": "offline"}}`.

## Running with Docker

You can also run the application inside a Docker container.

1.  **Build the Docker Image**

    From the root of the project, run the following command:
    ```bash
    docker build -t kick-chatbot-api .
    ```

2.  **Run the Docker Container**

    Make sure you have your `.env` file with the `OPENROUTER_API_KEY` in the root of the project. This file is used by the container to get the necessary credentials.

    Run the container with the following command:
    ```bash
    docker run --rm -p 8000:8000 --env-file .env -t kick-chatbot-api
    ```
    - `--rm`: Automatically removes the container when it exits.
    - `-p 8000:8000`: Maps port 8000 on your local machine to port 8000 in the container.
    - `--env-file .env`: Loads the environment variables from your `.env` file into the container.

    The API will be accessible at `http://localhost:8000`. 