import os
import asyncio
import discord
from dotenv import load_dotenv
from openai import OpenAI
import threading
from flask import Flask

# Load environment variables from local .env if running locally
load_dotenv()

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Custom animated emoji
THINKING_EMOJI = "<a:loading:1529087869124350024>"

# Initialize OpenRouter client
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

# Discord Bot Setup
intents = discord.Intents.default()
intents.message_content = True
client = discord.Client(intents=intents)

# Flask Web Server to satisfy Render port check
app = Flask(__name__)

@app.route("/")
def home():
    return "Mr. Meow is alive and running!"

def run_flask():
    # Render assigns its own PORT environment variable dynamically
    port = int(os.getenv("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

@client.event
async def on_ready():
    print(f"Logged in as {client.user}")

@client.event
async def on_message(message):
    # Ignore messages sent by the bot itself
    if message.author == client.user:
        return

    # Respond when mentioned or in direct messages
    if client.user.mentioned_in(message) or isinstance(message.channel, discord.DMChannel):
        try:
            # Add thinking reaction
            await message.add_reaction("🤔")

            # Call OpenRouter API
            response = ai_client.chat.completions.create(
                model="openrouter/free",
                messages=[
                    {"role": "system", "content": "You are Mr. Meow, a helpful assistant that even generates code, you can help with ANYTHING!, messages are 2-3 sentences long, and you are very friendly and helpful. You are a cat."},
                    {"role": "user", "content": message.content}
                ]
            )

            bot_reply = response.choices[0].message.content
            await message.reply(bot_reply)

        except Exception as e:
            print(f"Error handling message: {e}")
            await message.reply("Meow! Something went wrong processing that request.")

# Start Flask web server in a separate thread
threading.Thread(target=run_flask, daemon=True).start()

# Start Discord Bot
client.run(DISCORD_TOKEN)