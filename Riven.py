import asyncio
import discord
import subprocess
from MinecraftCommands import MinecraftCommands
from YoutubeCommands import YoutubeCommands
from discord.ext import commands, tasks
from file_read_backwards import FileReadBackwards


class Riven(commands.Bot):
    songs = asyncio.Queue()
    play_next_song = asyncio.Event()

    def __init__(self, logger, status, yt_pass):
        commands.Bot.__init__(self, command_prefix='!', intents=discord.Intents.all())
        self.logger = logger
        self.status = status
        self.add_commands()
        await MinecraftCommands(client=self, logger=self.logger).add_minecraft_commands()
        await YoutubeCommands(client=self, logger=self.logger, yt_pass=yt_pass).add_youtube_commands()

    async def on_ready(self):
        await self.change_presence(activity=discord.Game(self.status))
        self.logger.setup_logs()
        self.logger.print('Bot is online!')

    async def on_message(self, message):  # event that happens per any message.
        if "beer" in str(message.author).lower():
            await message.add_reaction("🍺")

        await self.process_commands(message)

    async def on_voice_state_update(self, member, before, after):
        if not member.id == self.user.id:
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
                    self.empty_queue(Riven.songs)
                    await voice.disconnect()
                    self.logger.print("Bot inactive for too long: leaving channel")
                if not voice.is_connected():
                    break

    def add_commands(self):
        @self.command(name='ping', help='Returns the latency')
        async def ping(ctx):
            self.logger.print('Start - Ping Command Called')
            await ctx.send(f'**Pong!** Latency: {round(self.latency * 1000)}ms')
            self.logger.print('End - Ping Command Called')

    def empty_queue(self, q: asyncio.Queue):
        self.logger.print('Start - Empty Queue')
        if not q.empty():
            for _ in range(q.qsize()):
                # Depending on your program, you may want to
                # catch QueueEmpty
                q.get_nowait()
                q.task_done()
        self.logger.print('End - Empty Queue')

    async def audio_player_task(self):
        while True:
            try:
                Riven.play_next_song.clear()
                current = await Riven.songs.get()
                current_song = current[1]
                ctx = current[0]
                guild = ctx.message.guild
                voice_channel = guild.voice_client
                self.logger.print("Playing - ", current[1].title)

                try:
                    if not voice_channel.is_playing():
                        self.logger.print('Start - Start Song in Queue')
                        voice_channel.play(current_song, after=self.toggle_next)

                        if Riven.songs.qsize() == 0:
                            self.logger.print(
                                '    Starting Last Song - ' + str(current_song.title) + 'Queue Size: ' + str(
                                    Riven.songs.qsize()))
                            await ctx.send(
                                ':musical_note: **Now playing:** {} :musical_note:'.format(current_song.title))
                            self.logger.print('    Awaiting Last Song...')
                        else:
                            self.logger.print(
                                '    Starting Next Song - ' + str(current_song.title) + 'Queue Size: ' + str(
                                    Riven.songs.qsize()))
                            await ctx.send(
                                '**Queue: **' + str(Riven.songs.qsize()) + '\n:musical_note: **Now playing:** {} '
                                                                           ':musical_note:'.format(
                                    current_song.title))
                            self.logger.print('    Awaiting Next Song...')
                            await Riven.play_next_song.wait()
                except discord.errors.ClientException as e:
                    self.logger.print('Error - ' + str(e))
            except AttributeError as e:
                self.logger.print('Error - ' + str(e))
        self.logger.print('Error - Audio Player Loop Exited!!')

    def toggle_next(self, error):
        self.logger.print('Start - Toggle Next Called')
        self.loop.call_soon_threadsafe(Riven.play_next_song.set)
        self.logger.print('End - Toggle Next Called')

    @tasks.loop(minutes=30)
    async def check_for_players(self, ctx):
        status_proc = subprocess.run('screen -ls', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
        status_str = status_proc.stdout.decode('ascii')
        player_count = 0

        if 'minecraft' in status_str:
            try:
                subprocess.call(r"screen -S minecraft -X stuff '/say Checking for active players... \015 list \015'",
                                shell=True)
                await asyncio.sleep(2)
                subprocess.call('screen -S minecraft -X hardcopy ~/Scripts/Script_Files/player-check.log', shell=True)

                with FileReadBackwards('/home/media-server/Scripts/Script_Files/player-check.log',
                                       encoding='utf-8') as frb:
                    for line in frb:
                        if '/20' in line:
                            i = line.index('/20')
                            player_count = int(line[i - 2:i].strip())
                            self.logger.print(str(player_count))
                            break
                    self.logger.print("Did not find player count!")

                if player_count == 0:
                    self.logger.print("Found no players online - shutting Minecraft server down")
                    subprocess.call(
                        r'screen -S minecraft -X stuff "/say Stopping server in 30 seconds due to lack of players \015"',
                        shell=True)
                    await asyncio.sleep(30)
                    subprocess.call('screen -S minecraft -X stuff "stop\n"', shell=True)
                    await ctx.send("Stopping Minecraft server due to lack of players")
                else:
                    self.logger.print("Players are online: " + str(player_count))
            except FileNotFoundError as ex:
                self.logger.print(ex)
                await ctx.send(str(ex))
                Riven.check_for_players.stop()
        else:
            self.logger.print("Stopping player check")
            Riven.check_for_players.stop()
