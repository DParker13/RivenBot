import asyncio
import discord
from discord.ext import commands, tasks
from os import environ
import youtube_dl

youtube_dl.utils.bug_reports_message = lambda: ''

ytdl_format_options = {
    'format': 'bestaudio/best',
    'outtmpl': '%(extractor)s-%(id)s-%(title)s.%(ext)s',
    'restrictfilenames': True,
    'noplaylist': True,
    'nocheckcertificate': True,
    'ignoreerrors': False,
    'logtostderr': False,
    'quiet': True,
    'no_warnings': True,
    'default_search': 'auto',
    'source_address': '0.0.0.0'  # bind to ipv4 since ipv6 addresses cause issues sometimes
}

ffmpeg_options = {
    'options': '-vn'
}

ytdl = youtube_dl.YoutubeDL(ytdl_format_options)


class YTDLSource(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: ytdl.extract_info(url, download=not stream))

        if 'entries' in data:
            # take first item from a playlist
            data = data['entries'][0]

        filename = data['url'] if stream else ytdl.prepare_filename(data)
        return cls(discord.FFmpegPCMAudio(executable=r"./ffmpeg/bin/ffmpeg.exe", source=filename, **ffmpeg_options), data=data)


client = commands.Bot(command_prefix='!')
status = 'UNO'
queue = []


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(status))
    print('Bot is online!')


@client.event
async def on_message(message):  # event that happens per any message.
    if "beer" in str(message.author).lower():
        await message.add_reaction("🍺")

    await client.process_commands(message)


@client.command(name='ping', help='Returns the latency')
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')


@client.command(name='play', help='Plays music from URL')
async def play(ctx, url):
    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel

    if ctx.guild.voice_client not in ctx.bot.voice_clients:
        await channel.connect()

    guild = ctx.message.guild
    voice_channel = guild.voice_client

    async with ctx.typing():
        player = await YTDLSource.from_url(url, loop=client.loop)

        if not voice_channel.is_playing():
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)
        else:
            voice_channel.stop()
            voice_channel.play(player, after=lambda e: print('Player error: %s' % e) if e else None)

    await ctx.send(':musical_note: **Now playing:** {} :musical_note:'.format(player.title))


@client.command(name='pause', help='Pauses the music')
async def pause(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            await voice_channel.pause()
        else:
            await ctx.send(":exclamation: No music is playing :exclamation:")
    else:
        await ctx.send(':exclamation: Not in a voice channel :exclamation:')


@client.command(name='resume', help='Resumes the current song')
async def resume(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_paused():
            await voice_channel.resume()
        else:
            await ctx.send(":exclamation: Current song is not paused :exclamation:")
    else:
        await ctx.send(':exclamation: Not in a voice channel :exclamation:')


@client.command(name='leave', help='Stops the music and makes me leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        await voice_client.disconnect()
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")


client.run(environ['TOKEN'])
