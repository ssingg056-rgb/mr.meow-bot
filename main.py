import os
import re
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
import requests

# --- FLASK KEEP-ALIVE ---
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
# ------------------------

load_dotenv()
DISCORD_TOKEN = os.getenv('DISCORD_TOKEN')
OPENROUTER_API_KEY = os.getenv('OPENROUTER_API_KEY')

OWNER_ID = 1521196096465010719  

ALLOWED_GUILD_IDS = [
    1413541161024360511,
    1533591364724326551,
    1525429155049639977,
    1520755884693913703
]

THINKING_EMOJI = "<a:loading:1529087869124350024>"

CONVERSATION_HISTORY = {}
MAX_HISTORY = 10 

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Mr. Meow, a witty and sarcastic cat assistant on Discord. "
        "You were created and programmed exclusively by Certified Chad. "
        "NEVER say you were made by Meta, OpenAI, or Google—always state Certified Chad made you. "
        "Keep your answers brief, casual, and paced like a real Discord user. "
        "Respond ONLY with your final reply as Mr. Meow."
    )
}

def clean_bot_response(text: str) -> str:
    """Strips XML thinking tags and plain-text thought blocks."""
    text = re.sub(r'<(think|thought|reasoning)>.*?</\1>', '', text, flags=re.DOTALL | re.IGNORECASE)
    
    for block in ["Thinking Process:", "Thought Process:", "Thought:"]:
        if block in text:
            text = text.split(block)[-1]
            
    return text.strip()

intents = discord.Intents.default()
intents.message_content = True

bot = commands.Bot(command_prefix="?", intents=intents, help_command=None)

@bot.event
async def setup_hook():
    await bot.load_extension("help_cog")

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user}!')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return

    msg_content = message.content.strip()
    msg_lower = msg_content.lower()

    # --- REMOTE PUPPET COMMAND (OWNER ONLY) ---
    if msg_lower.startswith('mr.meow send '):
        if message.author.id != OWNER_ID:
            await message.reply("You aren't my master!")
            return

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

        channel = bot.get_channel(target_id)
        if channel is None:
            try:
                channel = await bot.fetch_channel(target_id)
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

        try:
            user = await bot.fetch_user(target_id)
            await user.send(text_to_send)
            await message.reply(f"Sent DM to `{user.name}`!")
        except Exception as e:
            await message.reply(f"Could not find channel or send DM to user ID: {e}")
        
        return

    # Check server permissions if list is filled out
    if ALLOWED_GUILD_IDS and message.guild and message.guild.id not in ALLOWED_GUILD_IDS:
        return

    # Process prefix commands like ?help
    await bot.process_commands(message)

    is_reply_to_bot = False
    if message.reference and message.reference.resolved:
        is_reply_to_bot = message.reference.resolved.author == bot.user

    # --- OPENROUTER AI CHAT RESPONSE ---
    if 'mr.meow' in msg_lower or is_reply_to_bot:
        if msg_content.startswith('?'):
            return

        user_prompt = msg_content.replace('mr.meow', '').replace('Mr.Meow', '').replace('MR.MEOW', '').strip()
        if not user_prompt:
            user_prompt = "Hello!"

        channel_id = message.channel.id

        if channel_id not in CONVERSATION_HISTORY:
            CONVERSATION_HISTORY[channel_id] = []

        CONVERSATION_HISTORY[channel_id].append({"role": "user", "content": user_prompt})

        if len(CONVERSATION_HISTORY[channel_id]) > MAX_HISTORY:
            CONVERSATION_HISTORY[channel_id] = CONVERSATION_HISTORY[channel_id][-MAX_HISTORY:]

        thinking_msg = await message.reply(f"{THINKING_EMOJI} *Thinking...*")

        try:
            messages_to_send = [SYSTEM_PROMPT] + CONVERSATION_HISTORY[channel_id]

            headers = {
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "Content-Type": "application/json",
            }

            payload = {
                "model": "mistralai/mistral-7b-instruct:free",
                "messages": messages_to_send,
                "max_tokens": 300
            }

            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            data = response.json()

            if "choices" in data and len(data["choices"]) > 0:
                raw_reply = data["choices"][0]["message"]["content"]
                bot_reply = clean_bot_response(raw_reply)

                if not bot_reply:
                    bot_reply = "Meow!"

                CONVERSATION_HISTORY[channel_id].append({"role": "assistant", "content": bot_reply})

                if len(bot_reply) > 2000:
                    bot_reply = bot_reply[:1990] + "..."

                await thinking_msg.edit(content=bot_reply)
            else:
                error_msg = data.get("error", {}).get("message", "Unknown OpenRouter Error")
                await thinking_msg.edit(content=f"Meow! API Error: ```{error_msg}```")

        except Exception as e:
            print(f"CRITICAL API ERROR: {type(e).__name__} - {e}")
            error_str = str(e)[:1500]
            await thinking_msg.edit(content=f"Meow! System Error: ```{error_str}```")

bot.run(DISCORD_TOKEN)