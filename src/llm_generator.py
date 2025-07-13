import primp
import json
from . import config

class LlmApiError(Exception):
    """Custom exception for LLM API errors."""
    pass

def _build_prompt(chat_history: list[dict]) -> str:
    """Builds a prompt from a list of chat messages."""
    history_str = "\n".join([f"<{msg['sender']}> {msg['content']}" for msg in chat_history])
    
    prompt = f"""You are a chatter in a Kick.com live stream. Your goal is to blend in perfectly with the other users.
To do this, you will generate a list of realistic messages based on the recent chat history provided below.

**Recent Chat History (last {config.MESSAGE_COLLECTION_SECONDS} seconds):**
---
{history_str}
---

**Your Task:**
Analyze the chat history above to understand the conversation's topic, tone, and style. Then, generate a list of exactly 100 new chat messages that a real user would likely send in this context.

**Instructions for Realism:**
1.  **Mimic the Style:** Pay close attention to the slang, emotes, capitalization, punctuation, and even the grammar of the other chatters. If they use a lot of emotes like "KEKW" or "Pog," you should too. If they type in all lowercase, you should too.
2.  **Stay Relevant:** Your messages must be relevant to the ongoing conversation or events in the stream.
3.  **Be Diverse:** Generate a mix of messages. Some can be reactions (e.g., "LUL," "no way," "hesRight"), some can be questions about what's happening, and others can be simple comments.
4.  **Match Message Lengths:** Pay close attention to the length of the messages in the chat history. Your generated messages should have a similar mix of lengths. If the chat history includes longer sentences and comments, make sure to include some in your output instead of only generating short, one-word reactions.
5.  **Be a Chatter, Not an Assistant:** Do NOT act like an AI. Do not be overly helpful or use formal language. You are just another user in the chat.
6.  **Be honest to the tone:** If the chat is edgy, rude, or politically incorrect, your messages can reflect that. Real chatters are unfiltered — blend in, even if the tone is chaotic or borderline offensive.
7.  **Don't be too clever:** Many chatters repeat what others say or write low-effort, copy-paste style comments. Repetition is okay and even expected.
8.  **Embrace chat imperfections:** Feel free to use bad grammar, all lowercase, weird punctuation, or misspellings if it fits the tone. Many users are fast-typing or not native English speakers.
9.  **Include common Kick chat behaviors:** Spam short emotes ("KEKW", "TriKool"), react to usernames ("based Real_Hawk"), joke about race/politics/religion if the chat does, or respond with internet slang like "cope", "seethe", or "L + ratio".
10. **Use Emotes Correctly and Frequently:** The chat history will contain emotes in a special format like `[emote:37226:KEKW]`. You **MUST** replicate this exact format when using emotes. Look for them in the history and use them frequently in your own messages to blend in.

**What Not to Do:**
- ❌ DO NOT: Use full proper sentences with clean grammar.
- ❌ DO NOT: Explain anything.
- ❌ DO NOT: Say "As an AI" or write like you're contributing insight.
- ❌ DO NOT: Write emote names as plain text (e.g., `KEKW`). Always use the full `[emote:ID:NAME]` format.

**Output Format:**

Example of a valid response:
["lol true", "what just happened??", "[emote:37226:KEKW]", "that was sick", "[emote:37227:LULW]"]
"""
    return prompt

def generate_messages(chat_history: list[dict]) -> list[str]:
    """
    Generates a list of chat messages using an LLM.

    Args:
        chat_history: A list of recent chat message dictionaries.

    Returns:
        A list of generated message strings.
    """
    if not chat_history:
        return []

    prompt = _build_prompt(chat_history)
    
    headers = {
        "Authorization": f"Bearer {config.OPENROUTER_API_KEY}",
        "Content-Type": "application/json"
    }
    
    body = {
        "model": "google/gemini-2.5-flash",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "response_format": {"type": "json_object"} # Ask for JSON output
    }

    try:
        print("Generating messages with OpenRouter...")
        client = primp.Client(timeout=60)
        resp = client.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            json=body
        )

        if resp.status_code != 200:
            raise LlmApiError(f"OpenRouter API returned status {resp.status_code}: {resp.text}")

        response_data = resp.json()
        raw_content = response_data.get("choices", [{}])[0].get("message", {}).get("content", "[]")
        
        # The content should be a JSON string, which needs to be parsed
        generated_messages = json.loads(raw_content)

        if not isinstance(generated_messages, list) or not all(isinstance(m, str) for m in generated_messages):
             raise LlmApiError(f"LLM output was not a valid JSON array of strings. Got: {generated_messages}")

        print(f"Successfully generated {len(generated_messages)} messages.")
        return generated_messages

    except json.JSONDecodeError as e:
        raise LlmApiError(f"Failed to decode JSON from OpenRouter response: {e}") from e
    except Exception as e:
        raise LlmApiError(f"An unexpected error occurred during message generation: {e}") from e 