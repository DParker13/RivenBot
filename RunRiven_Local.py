import asyncio
import discord
import youtube_dl
from discord.ext import commands, tasks
from os import environ

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
token = ""


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
        return cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options,
                                          executable=r"D:\danie\Documents\GitHub\RivenBot\ffmpeg\bin\ffmpeg.exe"),
                   data=data)


client = commands.Bot(command_prefix='!')
status = 'UNO'
songs = asyncio.Queue()
play_next_song = asyncio.Event()


@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(status))
    print('Bot is online!')


@client.event
async def on_message(message):  # event that happens per any message.
    if "beer" in str(message.author).lower():
        await message.add_reaction("🍺")

    await client.process_commands(message)


@client.event
async def on_voice_state_update(member, before, after):
    if not member.id == client.user.id:
        return

    elif before.channel is None:
        voice = after.channel.guild.voice_client
        time = 0
        while True:
            await asyncio.sleep(1)
            time = time + 1
            if voice.is_playing():
                time = 0
            if time == 600:
                await voice.disconnect()
                print("Bot inactive for too long: leaving channel")
            if not voice.is_connected():
                break


@client.command(name='ping', help='Returns the latency')
async def ping(ctx):
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')


@client.command(name='skip', help='Skips the current song in the queue')
async def skip(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if voice_channel.is_playing():
        voice_channel.stop()
        toggle_next(None)
    else:
        await ctx.send(r"<:cring:758870529599209502> There is nothing in the queue to skip")


async def audio_player_task():
    while True:
        try:
            play_next_song.clear()
            current = await songs.get()
            current_song = current[1]
            ctx = current[0]
            guild = ctx.message.guild
            voice_channel = guild.voice_client
            print("Playing:", current[1].title)

            voice_channel.play(current_song, after=toggle_next)
            if songs.qsize() == 0:
                await ctx.send(':musical_note: **Now playing:** {} :musical_note:'.format(current_song.title))
            else:
                await ctx.send('Queue: ' + songs.qsize() + '\n:musical_note: **Now playing:** {} :musical_note:'.format(
                    current_song.title))

            await play_next_song.wait()
        except AttributeError as e:
            print(e)


def toggle_next(error):
    client.loop.call_soon_threadsafe(play_next_song.set)


@client.command(name='play', help='Plays music from URL', pass_context=True)
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

    if not voice_channel.is_playing():
        await ctx.send('**Loading Audio...**')
    else:
        await ctx.send('**Adding Audio to Queue...**')
    player = await YTDLSource.from_url(url, loop=client.loop, stream=True)
    await songs.put([ctx, player])


@client.command(name='pause', help='Pauses the music')
async def pause(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            voice_channel.pause()
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
            voice_channel.resume()
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


@client.command(name='clear', help='Clears the queue and stops the music')
async def clear(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    await ctx.send(":exclamation: Clearing Queue! :exclamation:")
    empty_queue(songs)
    voice_channel.stop()


def empty_queue(q: asyncio.Queue):
    if not q.empty():
        for _ in range(q.qsize()):
            # Depending on your program, you may want to
            # catch QueueEmpty
            q.get_nowait()
            q.task_done()


client.loop.create_task(audio_player_task())
client.run(token)
