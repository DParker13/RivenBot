import asyncio
import discord
import logging
from discord import app_commands
from discord.ext import commands, tasks
from PalworldCommands import PalworldCommands
from YoutubeCommands import YoutubeCommands
from OpenAICommands import OpenAICommands


class Riven(commands.Bot):
    audio_queue = asyncio.Queue()
    play_next_song = asyncio.Event()

    def __init__(self, logger, status, ytdl, openai_key):
        commands.Bot.__init__(self, command_prefix='!', intents=discord.Intents.all())

        self.synced = False
        self.logger = logger
        self.game_status = status
        self.add_commands()
        PalworldCommands(client=self, logger=self.logger).add_palworld_commands()
        YoutubeCommands(client=self, logger=self.logger, ytdl=ytdl).add_youtube_commands()
        OpenAICommands(client=self, logger=self.logger, api_key=openai_key).addOpenAICommands()

    async def on_ready(self):
        """
        An asynchronous function that is called when the bot is ready to start receiving events.
        It sets the bot's presence to a game with the specified status, sets up the logs, and prints a message indicating that the bot is online.

        Parameters:
            None

        Returns:
            None
        """
        self.logger.info('Bot is setting up...')

        self.logger.info('Changing status to: ' + str(self.game_status))
        await self.change_presence(status = discord.Status.online, activity=discord.Game(self.game_status))
        self.logger.info('Status changed!')
        
        self.logger.info('Bot is online!')

    async def on_message(self, message):  # event that happens per any message.
        """
        An asynchronous function that is called when a message is received.
        
        Parameters:
            message (discord.Message): The message object representing the received message.
        
        Returns:
            None
        
        Description:
            This function is triggered whenever a message is received. It checks if the message contains the word "beer" in the author's username (case-insensitive) and adds a "🍺" reaction to the message if it does. It then processes any commands in the message.
        """
        if "beer" in str(message.author).lower():
            await message.add_reaction("🍺")

        await self.process_commands(message)

    async def on_voice_state_update(self, member, before, after):
        """
        Asynchronous function that handles voice state updates.

        Args:
            member (discord.Member): The member whose voice state has changed.
            before (discord.VoiceState): The member's voice state before the update.
            after (discord.VoiceState): The member's voice state after the update.

        Returns:
            None

        This function is called whenever a member's voice state changes.
        It checks if the member is not the bot itself and if the member has joined a voice channel.
        If these conditions are met, it starts a loop that checks the bot's voice client's playback status every second.
        If the bot is playing audio, the timeout is reset to 0.
        If the timeout reaches 600 seconds (10 minutes), the bot's song queue is cleared, the bot disconnects from the voice channel, and a message is printed to the logger.
        If the bot is not connected to a voice channel, the loop is broken.

        Note:
            This function assumes that the bot is already connected to a voice channel when a member joins.
        """
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
                    self.empty_queue(Riven.audio_queue)
                    await voice.disconnect()
                    self.logger.info("Bot inactive for too long: leaving channel")
                if not voice.is_connected():
                    break

    async def setup_hook(self):
        """
        Asynchronously starts the audio player task.

        This method is called during the setup phase of the bot. It starts the audio player task, which is responsible for playing audio in the voice channel.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        self.audio_player_task.start()

    def add_commands(self):
        """
        Adds the 'ping' command to the Discord client.

        This function adds the 'ping' command to the Discord client. When the command is called, it returns the latency of the bot in milliseconds.

        Parameters:
            self (object): The instance of the class.
            ctx (Context): The context object representing the invocation context of the command.

        Returns:
            None
        """

        @self.tree.command(name='ping', description='Returns the latency')
        async def ping(interaction: discord.Interaction):
            """
            The ping command returns the latency of the Discord bot.

            Parameters:
                ctx (Context): The invocation context of the command.

            Returns:
                None
            """
            self.logger.trace('Start - Ping Command Called')
            await interaction.response.send_message(f'**Pong!** Latency: {round(self.latency * 1000)}ms')
            self.logger.trace('End - Ping Command Called')

        @self.command(name='sync', description='Syncs the application commands with Discord')
        async def sync(ctx):
            """
            Syncs the application commands with Discord.
        
            This method syncs the application commands with Discord. It retrieves the application commands from the Discord API and syncs them with the bot.
        
            Parameters:
                interaction (discord.Interaction): The interaction object representing the invocation context of the command.
        
            Returns:
                None
            """
            self.logger.trace('Start - Sync Command Called')
            synced = await self.tree.sync()
            await ctx.send(f"Synced {len(synced)} command(s).")
            self.logger.trace('End - Sync Command Called')

    def empty_queue(self, q: asyncio.Queue):
        """
        Empty the given queue by removing all items from it.

        Parameters:
            q (asyncio.Queue): The queue to be emptied.

        Returns:
            None
        """
        self.logger.trace('Start - Empty Queue')
        if not q.empty():
            for _ in range(q.qsize()):
                # Depending on your program, you may want to
                # catch QueueEmpty
                q.get_nowait()
                q.task_done()
        self.logger.trace('End - Empty Queue')

    @tasks.loop(seconds=1)
    async def audio_player_task(self):
        """
        Asynchronously plays audio from a queue in a Discord voice channel.

        This function is a loop that runs every second and checks if there audio in the queue.
        If there are, it retrieves the next audio clip from the queue and plays it in the voice channel.
        If the voice client is not currently playing audio, it starts playing the song.
        If there is no more audio in the queue, it sends a message to the Discord channel indicating that the last song has finished playing.
        If there is more audio in the queue, it sends a message indicating the number of audio clips remaining in the queue.
        The function waits for the next audio clip to finish playing before starting the next one.

        Parameters:
            self (object): The instance of the class.

        Returns:
            None
        """
        try:
            Riven.play_next_song.clear()
            queue_item = await Riven.audio_queue.get()
            interaction = queue_item[0]
            current_video = queue_item[1]
            voice_client = interaction.guild.voice_client
            self.logger.info("Trying to play - " + str(queue_item[1].title))

            try:
                if not voice_client.is_playing():
                    self.logger.trace('Start - Start Audio in Queue')
                    voice_client.play(current_video, after=lambda _: self.loop.call_soon_threadsafe(Riven.play_next_song.set))

                    if Riven.audio_queue.qsize() == 0:
                        self.logger.info(
                            '    Starting Last Audio - ' + str(current_video.title) + ' Queue Size: ' + str(
                                Riven.audio_queue.qsize()))
                        await interaction.followup.send(
                            ':musical_note: **Now playing:** {} :musical_note:'.format(current_video.title))
                    else:
                        self.logger.info(
                            '    Starting Next Song - ' + str(current_video.title) + ' Queue Size: ' + str(
                                Riven.audio_queue.qsize()))
                        await interaction.followup.send(
                            '**Queue: **' + str(Riven.audio_queue.qsize()) + '\n:musical_note: **Now playing:** {} '
                                                                       ':musical_note:'.format(
                                current_video.title))
                    self.logger.info('    Awaiting Next Song...')
                    await Riven.play_next_song.wait()
                else:
                    self.logger.info('!Voice_client Still Playing Audio!')
            except discord.errors.ClientException as e:
                self.logger.error('Error - ' + str(e))
        except AttributeError as e:
            self.logger.error('Error - ' + str(e))
