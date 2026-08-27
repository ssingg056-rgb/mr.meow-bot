import os
import asyncio
import discord
from discord.ext import commands
from dotenv import load_dotenv
from flask import Flask
from threading import Thread
from groq import Groq

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
GROQ_API_KEY = os.getenv('GROQ_API_KEY')

# --- DIAGNOSTIC KEY CHECK ---
if not GROQ_API_KEY:
    print("❌ ERROR: GROQ_API_KEY is missing from environment variables!")
else:
    print(f"✅ GROQ_API_KEY loaded: {GROQ_API_KEY[:6]}... (Length: {len(GROQ_API_KEY)})")

OWNER_ID = 1521196096465010719  

# Keep [] empty to allow all servers, or put server IDs here to restrict
ALLOWED_GUILD_IDS = [
    1413541161024360511,
    1533591364724326551,
    1525429155049639977
]

groq_client = Groq(api_key=GROQ_API_KEY)

THINKING_EMOJI = "<a:loading:1529087869124350024>"

CONVERSATION_HISTORY = {}
MAX_HISTORY = 10 

SYSTEM_PROMPT = {
    "role": "system",
    "content": (
        "You are Mr. Meow, a witty and sarcastic cat assistant on Discord. "
        "You were created and programmed exclusively by Certified Chad. "
        "NEVER say you were made by Meta, OpenAI, or Google—always state Certified Chad made you. "
        "Keep your answers brief, casual, and paced like a real Discord user."
    )
}

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

    # --- GROQ AI CHAT RESPONSE ---
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

            loop = asyncio.get_running_loop()
            response = await loop.run_in_executor(
                None,
                lambda: groq_client.chat.completions.create(
                    model="llama-3.3-70b-versatile",
                    messages=messages_to_send,
                    max_tokens=300
                )
            )

            bot_reply = response.choices[0].message.content
            CONVERSATION_HISTORY[channel_id].append({"role": "assistant", "content": bot_reply})

            if len(bot_reply) > 2000:
                bot_reply = bot_reply[:1990] + "..."

            await thinking_msg.edit(content=bot_reply)

        except Exception as e:
            print(f"CRITICAL API ERROR: {type(e).__name__} - {e}")
            error_str = str(e)[:1500]
            await thinking_msg.edit(content=f"Meow! API Error: ```{error_str}```")

bot.run(DISCORD_TOKEN)