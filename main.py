import discord
from discord.ext import commands, tasks
import youtube_dl

client = commands.Bot(command_prefix="!")

status = ["Having a beer with the boys"]

@client.event
async def on_ready():
    print('Bot is online!')

@client.command(name="ping", help="This command returns the latency")
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')

client.run('ODg3NTE5OTkxNjQ4MzU4NDMy.YUFVZw.tN14Fpdn8qXivfy4cZdGdurOQwM')