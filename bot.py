import discord
from discord.ext import commands
import re
import asyncio
import datetime
import os
from dotenv import load_dotenv

load_dotenv()
TOKEN = os.getenv('DISCORD_BOT_TOKEN')

# Votre code du bot ici
@bot.command()
@commands.check(is_owner)
async def restart(ctx):
    await ctx.send("Le bot va redémarrer.")
    await bot.close()
    os.execv(sys.executable, ['python'] + sys.argv)
    
bot.run(TOKEN)
