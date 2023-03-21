import asyncio
import discord
import yt_dlp
import argparse
import subprocess
import builtins
import datetime
import os.path 
from file_read_backwards import FileReadBackwards
from discord.ext import commands, tasks

yt_dlp.utils.bug_reports_message = lambda: ''

# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--password", help="Youtube account password")
parser.add_argument("--token", help="Discord token")
parser.add_argument("--logs", help="Base path for log files")
args = parser.parse_args()

YT_PASSWORD = args.password
TOKEN = args.token

intents = discord.Intents.default()

# Initialization
client = commands.Bot(command_prefix='!', intents=intents)
status = 'UNO'
songs = asyncio.Queue()
play_next_song = asyncio.Event()
log_file = None
_print = print

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

ytdl = yt_dlp.YoutubeDL(ytdl_format_options)


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
                except yt_dlp.utils.DownloadError as e:
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
                    except yt_dlp.utils.DownloadError as e:
                        print(e)
                        player_list.append(None)

                return player_list

        elif data is not None:
            filename = data['url'] if stream else ytdl.prepare_filename(data)
            try:
                return [cls(discord.FFmpegPCMAudio(filename, **ffmpeg_options),
                            data=data)]
            except yt_dlp.utils.DownloadError as e:
                print(e)
                return None

        print("DATA IS SET TO NONE")
        return None

def setup_logs():
    global log_file
    now = datetime.datetime.now()
    log_exists = True
    iteration = 0
    while(log_exists):
        log_file = str(args.logs) + 'log_' + now.strftime('%Y%m%d_') + str(iteration) + '.log'
        if not os.path.isfile(log_file):
            log_exists = False
            break
        iteration += 1

#Overrides original print function
def print(*args, **kwargs):
    #prints to console
    _print(*args, **kwargs)
    #logs to file
    timestamp = datetime.datetime.now().ctime()
    with open(log_file, "a+") as log:
        _print(timestamp + ' --', *args, file=log, **kwargs)

@client.event
async def on_ready():
    await client.change_presence(activity=discord.Game(status))
    setup_logs()
    print('Bot is online!')


@client.event
async def on_message(message):  # event that happens per any message.
    if "beer" in str(message.author).lower():
        await message.add_reaction("🍺")

    await client.process_commands(message)


@client.event
async def on_voice_state_update(member, before, after):
    if not member.id == client.user.id:
        print("Something went wrong in 'on_voice_state_update'")
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
    print('Start - Ping Command Called')
    await ctx.send(f'**Pong!** Latency: {round(client.latency * 1000)}ms')
    print('End - Ping Command Called')

@client.command(name='skip', help='Skips the current song in the queue')
async def skip(ctx):
    print('Start - Skip Command Called')
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            print("    Skipping current audio!")
            await ctx.send("**Skipping current audio!**")
            print("    Skipping current audio!")
            voice_channel.stop()
        else:
            print("    There is nothing in the queue to skip")
            await ctx.send(r"<:cring:758870529599209502> There is nothing in the queue to skip")
            print("    There is nothing in the queue to skip")
    else:
        print(r"I'm not in a voice channel right now")
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
        print(r"I'm not in a voice channel right now")
    print('End - Skip Command Called')


async def audio_player_task():
    while True:
        try:
            play_next_song.clear()
            current = await songs.get()
            current_song = current[1]
            ctx = current[0]
            guild = ctx.message.guild
            voice_channel = guild.voice_client
            print("Playing - ", current[1].title)

            try:
                if not voice_channel.is_playing():
                    print('Start - Start Song in Queue')
                    voice_channel.play(current_song, after=toggle_next)

                    if songs.qsize() == 0:
                        print('    Starting Last Song - ' + str(current_song.title) + 'Queue Size: ' + str(songs.qsize()))
                        await ctx.send(':musical_note: **Now playing:** {} :musical_note:'.format(current_song.title))
                        print('    Awaiting Last Song...')
                    else:
                        print('    Starting Next Song - ' + str(current_song.title) + 'Queue Size: ' + str(songs.qsize()))
                        await ctx.send('**Queue: **' + str(songs.qsize()) + '\n:musical_note: **Now playing:** {} '
                                                                            ':musical_note:'.format(current_song.title))
                        print('    Awaiting Next Song...')
                        await play_next_song.wait()
            except discord.errors.ClientException as e:
                print('Error - ' + str(e))
        except AttributeError as e:
            print('Error - ' + str(e))
    print('Error - Audio Player Loop Exited!!')

def toggle_next(error):
    print('Start - Toggle Next Called')
    client.loop.call_soon_threadsafe(play_next_song.set)
    print('End - Toggle Next Called')


@client.command(name='startminecraft',
                help='Starts the minecraft server')
async def startminecraft(ctx):
    print('Start - Start Minecraft Command Called')
    statusProc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    statusStr = statusProc.stdout.decode('ascii')

    if 'minecraft' not in statusStr:
        print('    Starting Minecraft Server')
        await ctx.send("Starting Minecraft Server")
        subprocess.call(['sh', '/home/media-server/Scripts/minecraft.sh'])

        # checks for any players within the server to auto shutdown
        # await asyncio.sleep(1800)
        # await check_for_players.start(ctx)
        print('    Started Minecraft Server')
    else:
        await ctx.send("Minecraft server is already running")
        print('    Minecraft server is already running')
    print('End - Start Minecraft Command Called')


@client.command(name='stopminecraft',
                help='Stops the minecraft server (Assuming it is running)')
async def stopminecraft(ctx):
    print('Start - Stop Minecraft Command Called')
    status_proc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    status_str = status_proc.stdout.decode('ascii')

    if 'minecraft' in status_str:
        await ctx.send("Attempting to stop Minecraft Server (Server could still be launching if this command was called too early)")
        check_for_players.stop()
        subprocess.call('screen -S minecraft -X stuff "stop\n"', shell=True)
        print('    Minecraft server stopped')
    else:
        await ctx.send("Minecraft server is not running")
        print('    Minecraft server is not running')
    print('End - Stop Minecraft Command Called')


@tasks.loop(minutes=30)
async def check_for_players(ctx):
    status_proc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
    status_str = status_proc.stdout.decode('ascii')
    player_count = 0

    if 'minecraft' in status_str:
        try:
            subprocess.call(r"screen -S minecraft -X stuff '/say Checking for active players... \015 list \015'", shell=True)
            await asyncio.sleep(2)
            subprocess.call('screen -S minecraft -X hardcopy ~/Scripts/Script_Files/player-check.log', shell=True)

            with FileReadBackwards('/home/media-server/Scripts/Script_Files/player-check.log', encoding='utf-8') as frb:
                for line in frb:
                    if '/20' in line:
                        i = line.index('/20')
                        player_count = int(line[i-2:i].strip())
                        print(str(player_count))
                        break
                print("Did not find player count!")

            if player_count == 0:
                print("Found no players online - shutting Minecraft server down")
                subprocess.call(r'screen -S minecraft -X stuff "/say Stopping server in 30 seconds due to lack of players \015"', shell=True)
                await asyncio.sleep(30)
                subprocess.call('screen -S minecraft -X stuff "stop\n"', shell=True)
                await ctx.send("Stopping Minecraft server due to lack of players")
            else:
                print("Players are online: " + str(player_count))
        except FileNotFoundError as ex:
            print(ex)
            await ctx.send(str(ex))
            check_for_players.stop()
    else:
        print("Stopping player check")
        check_for_players.stop()


@client.command(name='play',
                help='Plays music from Youtube URLs or it will automatically search Youtube for top result',
                pass_context=True)
async def play(ctx, _):
    print('Start - Play Command Called')
    search = ctx.message.content[5:].strip()
    is_url = search.find(r"https://") != -1

    if not ctx.message.author.voice:
        await ctx.send("You are not connected to a voice channel")
        print('    Error - You are not connected to a voice channel')
        return
    else:
        channel = ctx.message.author.voice.channel

    if ctx.guild.voice_client not in ctx.bot.voice_clients:
        await channel.connect()
        print('    Connected Rivenbot to Channel')

    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if is_url is False:
        await ctx.send("**Searching Youtube: **" + search)
        print('    Searching Youtube')

    players = await YTDLSource.from_url(search, loop=client.loop, stream=True)

    if players is not None:
        if not voice_channel.is_playing() and len(players) == 1:
            await ctx.send('**Loading Audio...**')
            print('    Loading Audio...')
        elif not voice_channel.is_playing() and len(players) > 1:
            await ctx.send('**Playlist Being Added to Queue...**')
            print('    Playlist Being Added to Queue...')
        else:
            await ctx.send('**Adding Audio to Queue...**')
            print('    Adding Audio to Queue...')

        if len(players) == 1:
            await songs.put([ctx, players[0]])
        else:
            for current_player in players:
                await songs.put([ctx, current_player])
    else:
        await ctx.send(":exclamation:ERROR:exclamation:: No video formats found!")
        print('    No video formats found!')
    print('End - Play Command Called')

@client.command(name='pause', help='Pauses the audio')
async def pause(ctx):
    print('Start - Pause Command Called')
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_playing():
            voice_channel.pause()
        else:
            await ctx.send(":exclamation: No music is playing :exclamation:")
            print('    No music is playing!')
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
        print(r"    I'm not in a voice channel right now")
    print('End - Pause Command Called')


@client.command(name='resume', help='Resumes the current audio')
async def resume(ctx):
    print('Start - Resume Command Called')
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        if voice_channel.is_paused():
            voice_channel.resume()
        else:
            await ctx.send(":exclamation: Current song is not paused :exclamation:")
            print('    Current song is not paused!')
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
        print(r"    I'm not in a voice channel right now")
    print('End - Resume Command Called')


@client.command(name='leave', help='Stops the music and makes me leave the voice channel')
async def leave(ctx):
    print('Start - Leave Command Called')
    voice_client = ctx.message.guild.voice_client

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        await voice_client.disconnect()
    else:
        await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
        print(r"    I'm not in a voice channel right now")

    empty_queue(songs)
    print('End - Leave Command Called')


@client.command(name='clear', help='Clears the queue and stops the music')
async def clear(ctx):
    print('Start - Clear Command Called')
    guild = ctx.message.guild
    voice_channel = guild.voice_client

    await ctx.send(":exclamation: Clearing Queue! :exclamation:")
    empty_queue(songs)

    if ctx.guild.voice_client in ctx.bot.voice_clients:
        voice_channel.stop()
    print('End - Clear Command Called')


def empty_queue(q: asyncio.Queue):
    print('Start - Empty Queue')
    if not q.empty():
        for _ in range(q.qsize()):
            # Depending on your program, you may want to
            # catch QueueEmpty
            q.get_nowait()
            q.task_done()
    print('End - Empty Queue')


client.loop.create_task(audio_player_task())
client.run(TOKEN)
