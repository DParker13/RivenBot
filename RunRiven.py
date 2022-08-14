import asyncio
import discord
import youtube_dl
import argparse
import subprocess
from file_read_backwards import FileReadBackwards
from discord.ext import commands, tasks

youtube_dl.utils.bug_reports_message = lambda: ''

# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--password", help="Youtube account password")
parser.add_argument("--token", help="Discord token")
args = parser.parse_args()

YT_PASSWORD = args.password
TOKEN = args.token

# Initialization
client = commands.Bot(command_prefix='!')
status = 'UNO'
songs = asyncio.Queue()
play_next_song = asyncio.Event()

ytdl_format_options = {
    'username': 'meepmeep04@gmail.com',
    'password': YT_PASSWORD,
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
    'source_address': '0.0.0.0',  # bind to ipv4 since ipv6 addresses cause issues sometimes
    'cookiefile': 'cookies.txt'
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

        # Checks if the link is a playlist
        if 'entries' in data:
            if len(data['entries']) == 1:
                # take first item from a playlist
                data = data['entries'][0]

                filename = data['url'] if stream else ytdl.prepare_filename(data)
                try:
                    return [cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                                data=data)]
                except youtube_dl.utils.DownloadError as e:
                    print(e)
                    return None
            else:
                player_list = list()
                while len(data['entries']) != 0:
                    current_data = data['entries'].pop(0)

                    filename = current_data['url'] if stream else ytdl.prepare_filename(current_data)
                    try:
                        player_list.append(cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                                               data=current_data))
                    except youtube_dl.utils.DownloadError as e:
                        print(e)
                        player_list.append(None)

                return player_list

        elif data is not None:
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            try:
                return [cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                            data=data)]
            except youtube_dl.utils.DownloadError as e:
                print(e)
                return None

        print("DATA IS SET TO NONE")
        return None


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
        timeout = 0
        while True:
            await asyncio.sleep(1)
            timeout = timeout + 1
            if voice.is_playing():
                timeout = 0
            if timeout == 600:
                empty_queue(songs)
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

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            await ctx.send("**Skipping current audio!**")
            voice_channel.stop()
        else:
            await ctx.send(r"<:cring:758870529599209502> There is nothing in the queue to skip")
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")


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

            try:
                if not voice_channel.is_playing():
                    voice_channel.play(current_song, after=toggle_next)

                    if songs.qsize() == 0:
                        await ctx.send(':musical_note: **Now playing:** {} :musical_note:'.format(current_song.title))
                    else:
                        await ctx.send('**Queue: **' + str(songs.qsize()) + '\n:musical_note: **Now playing:** {} '
                                                                            ':musical_note:'.format(
                            current_song.title))

                        await play_next_song.wait()
            except discord.errors.ClientException as e:
                print(e)
        except AttributeError as e:
            print(e)


def toggle_next(error):
    client.loop.call_soon_threadsafe(play_next_song.set)

@client.command(name="test")
async def test(ctx):
    await ctx.send("Testing minecraft timeout")
    await check_for_players(ctx)

@client.command(name='startminecraft',
                help='Starts the minecraft server')
async def startminecraft(ctx):
    statusProc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    statusStr = statusProc.stdout.decode('ascii')

    if 'minecraft' not in statusStr:
        await ctx.send("Starting Minecraft Server")
        subprocess.call(['sh', '/home/dan/Scripts/minecraft.sh'])

        # checks for any players within the server to auto shutdown
        asyncio.sleep(600)
        await check_for_players()
    else:
        await ctx.send("Minecraft server is already running")


@client.command(name='stopminecraft',
                help='Stops the minecraft server (Assuming it is running)')
async def stopminecraft(ctx):
    status_proc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    status_str = status_proc.stdout.decode('ascii')

    if 'minecraft' in status_str:
        await ctx.send("Attempting to stop Minecraft Server (Server could still be launching if this command was called too early)")
        subprocess.call('screen -S minecraft -X stuff "stop\n"', shell=True)
    else:
        await ctx.send("Minecraft server is not running")


@tasks.loop(minutes=1)
async def check_for_players(ctx):
    status_proc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    status_str = status_proc.stdout.decode('ascii')
    player_count = None

    if 'minecraft' not in status_str:
        subprocess.call(r"screen -S minecraft -X stuff '/say Checking for active players... \015 list \015'", shell=True)
        subprocess.call('screen -S minecraft -X hardcopy ./player-check.log', shell=True)
        asyncio.sleep(5)

        try:
            with FileReadBackwards('./player-check.log', encoding='utf-8') as frb:
                for line in frb:
                    if '/20' in line:
                        i = line.index('/20')
                        player_count = int(line[i-2:i].strip())

            if player_count is None or player_count == 0:
                subprocess.call(r'screen -S minecraft -X stuff "/say Stopping server in 5 seconds due to lack of players \015"', shell=True)
                asyncio.sleep(5)
                subprocess.call('screen -S minecraft -X stuff "stop\n"', shell=True)
                await ctx.send("Stopping Minecraft server due to lack of players")
        except FileNotFoundError:
            await ctx.send("File not found - player-check.log")
            check_for_players.stop()
    else:
        check_for_players.stop()




@client.command(name='play',
                help='Plays music from Youtube URLs or it will automatically search Youtube for top result',
                pass_context=True)
async def play(ctx, _):
    search = ctx.message.content[5:].strip()
    is_url = search.find(r"https://") != -1

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        return
    else:
        channel = ctx.message.author.voice.channel

    if ctx.guild.voice_client not in ctx.bot.voice_clients:
        await channel.connect()

    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if is_url is False:
        await ctx.send("**Searching Youtube: **" + search)

    players = await YTDLSource.from_url(search, loop=client.loop, stream=True)

    if players is not None:
        if not voice_channel.is_playing() and len(players) == 1:
            await ctx.send('**Loading Audio...**')
        elif not voice_channel.is_playing() and len(players) > 1:
            await ctx.send('**Playlist Being Added to Queue...**')
        else:
            await ctx.send('**Adding Audio to Queue...**')

        if len(players) == 1:
            await songs.put([ctx, players[0]])
        else:
            for current_player in players:
                await songs.put([ctx, current_player])
    else:
        await ctx.send(":exclamation:ERROR:exclamation:: No video formats found!")


@client.command(name='pause', help='Pauses the audio')
async def pause(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            voice_channel.pause()
        else:
            await ctx.send(":exclamation: No music is playing :exclamation:")
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")


@client.command(name='resume', help='Resumes the current audio')
async def resume(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_paused():
            voice_channel.resume()
        else:
            await ctx.send(":exclamation: Current song is not paused :exclamation:")
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")


@client.command(name='leave', help='Stops the music and makes me leave the voice channel')
async def leave(ctx):
    voice_client = ctx.message.guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        await voice_client.disconnect()
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")

    empty_queue(songs)


@client.command(name='clear', help='Clears the queue and stops the music')
async def clear(ctx):
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    await ctx.send(":exclamation: Clearing Queue! :exclamation:")
    empty_queue(songs)

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        voice_channel.stop()


def empty_queue(q: asyncio.Queue):
    if not q.empty():
        for _ in range(q.qsize()):
            # Depending on your program, you may want to
            # catch QueueEmpty
            q.get_nowait()
            q.task_done()


client.loop.create_task(audio_player_task())
client.run(TOKEN)
