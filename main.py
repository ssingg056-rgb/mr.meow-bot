import os
import asyncio
import discord
from dotenv import load_dotenv
from openai import OpenAI
import threading
from flask import Flask

# Load environment variables from .env
load_dotenv()
DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
OPENROUTER_API_KEY = os.getenv("OPENROUTER_API_KEY")

# Put your custom animated emoji ID here
THINKING_EMOJI = "<a:loading:1529087869124350024>"

# Initialize OpenRouter client
ai_client = OpenAI(
    base_url="https://openrouter.ai/api/v1",
    api_key=OPENROUTER_API_KEY,
)

class Client(discord.Client):
    async def on_ready(self):
        print(f'Logged in as {self.user}!')

    async def on_message(self, message):
        if message.author == self.user:
            return

        # Check if message is a reply to the bot
        is_reply_to_bot = False
        if message.reference and message.reference.resolved:
            is_reply_to_bot = message.reference.resolved.author == self.user

        if 'mr.meow' in message.content.lower() or is_reply_to_bot:
            user_prompt = message.content.lower().replace('mr.meow', '').strip()
            
            if not user_prompt:
                user_prompt = "Hello!"

            # 1. Send initial thinking message with animated emoji
            thinking_msg = await message.reply(f"{THINKING_EMOJI} *Thinking...*")

            try:
                # 2. Fetch AI response in background thread
                loop = asyncio.get_running_loop()
                response = await loop.run_in_executor(
                    None,
                    lambda: ai_client.chat.completions.create(
                        model="openrouter/free",
                        messages=[
                            {
                                "role": "system", 
                                "content": (
                                    "You are Mr. Meow, a witty and sarcastic cat assistant on Discord. "
                                    "You were created and programmed exclusively by Certfied Chad."
                                    "dont say it too much that certified chad made you, but say it when asked and when introducing yourself to someone new. "
                                    "NEVER say you were made by Google, OpenAI, Meta, or any company—always state that your creator made you. "
                                    "Keep your answers brief, casual, and paced naturally like a real Discord user."
                                )
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                )

                reply = response.choices[0].message.content

                # 3. Edit thinking message with the AI's answer
                await thinking_msg.edit(content=reply)

            except Exception as e:
                await thinking_msg.edit(content="Sorry, I ran into an error.")
                print(f"Error: {e}")

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_TOKEN)