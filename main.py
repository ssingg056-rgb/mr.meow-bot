import os
import asyncio
import discord
from dotenv import load_dotenv
from openai import OpenAI
from flask import Flask
from threading import Thread

# --- FLASK KEEP-ALIVE SERVER ---
app = Flask('')

@app.route('/')
def home():
    return "Mr. Meow is online!"

def run():
    port = int(os.getenv("PORT", 10000))
    app.run(host='0.0.0.0', port=port)

def keep_alive():
    t = Thread(target=run)
    t.daemon = True
    t.start()

keep_alive()
# -------------------------------

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

# Replace with your copied Discord User ID!
OWNER_ID = 1521196096465010719  

THINKING_EMOJI = "<a:loading:1529087869124350024>"

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

        msg_content = message.content.strip()
        msg_lower = msg_content.lower()

        # --- REMOTE PUPPET COMMAND (OWNER ONLY via DM or Server) ---
        if msg_lower.startswith('mr.meow send '):
            if message.author.id != OWNER_ID:
                await message.reply("You aren't my master!")
                return

            # Format: mr.meow send <TARGET_ID> <TEXT>
            parts = msg_content.split(' ', 3)
            if len(parts) < 4:
                await message.reply("Usage: `mr.meow send <ID> <message>`")
                return

            target_id_str = parts[2]
            text_to_send = parts[3]

            try:
                target_id = int(target_id_str)
            except ValueError:
                await message.reply("Invalid ID! It must be numbers.")
                return

            # 1. Try sending to a channel
            channel = self.get_channel(target_id)
            if channel is None:
                try:
                    channel = await self.fetch_channel(target_id)
                except Exception:
                    channel = None

            if channel:
                try:
                    await channel.send(text_to_send)
                    await message.reply(f"Sent message to channel `{channel.name}`!")
                    return
                except Exception as e:
                    await message.reply(f"Failed to send to channel: {e}")
                    return

            # 2. If not a channel, try sending to a user DM
            try:
                user = await self.fetch_user(target_id)
                await user.send(text_to_send)
                await message.reply(f"Sent DM to `{user.name}`!")
            except Exception as e:
                await message.reply(f"Could not find channel or send DM to user ID: {e}")
            
            return

        # Check if message is a reply to the bot
        is_reply_to_bot = False
        if message.reference and message.reference.resolved:
            is_reply_to_bot = message.reference.resolved.author == self.user

        # --- AI CHAT RESPONSE ---
        if 'mr.meow' in msg_lower or is_reply_to_bot:
            user_prompt = msg_lower.replace('mr.meow', '').strip()

            if not user_prompt:
                user_prompt = "Hello!"

            thinking_msg = await message.reply(f"{THINKING_EMOJI} *Thinking...*")

            try:
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
                                    "You were created and programmed exclusively by Certified Chad. "
                                    "NEVER say you were made by Google, OpenAI, Meta, or any company—always state that your creator made you. "
                                    "Keep your answers brief, casual, and paced naturally like a real Discord user."
                                )
                            },
                            {"role": "user", "content": user_prompt}
                        ]
                    )
                )

                bot_reply = response.choices[0].message.content
                await thinking_msg.edit(content=bot_reply)

            except Exception as e:
                print(f"Error handling message: {e}")
                await thinking_msg.edit(content="Meow! Something went wrong processing that request.")

intents = discord.Intents.default()
intents.message_content = True

client = Client(intents=intents)
client.run(DISCORD_TOKEN)