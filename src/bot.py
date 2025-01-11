import discord
from discord.ext import commands
import json
import asyncio

# Load config
with open('config.json') as f:
    config = json.load(f)

intents = discord.Intents.default()
intents.message_content = True  # Cho phép bot đọc tin nhắn
intents.guilds = True
intents.voice_states = True  # Cho phép bot xử lý các sự kiện liên quan đến voice
intents.members = True  # Cho phép bot xử lý các sự kiện liên quan đến thành viên

bot = commands.Bot(command_prefix=config['PREFIX'], intents=intents)

async def load_extensions():
    await bot.load_extension('cogs.music')

@bot.event
async def on_ready():
    print(f'Bot is online as {bot.user}')
    for guild in bot.guilds:
        print(f'Connected to guild: {guild.name} (id: {guild.id})')

async def main():
    await load_extensions()
    await bot.start(config['TOKEN'])

asyncio.run(main())