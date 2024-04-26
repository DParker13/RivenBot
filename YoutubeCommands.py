import asyncio
import discord


class YoutubeCommands:
    def __init__(self, client, logger, ytdl):
        """
        Initializes a new instance of the class.

        Args:
            client (object): The client object.
            logger (object): The logger object.
            ytdl (object): The ytdl object.
        """
        self.client = client
        self.logger = logger
        self.ytdl = ytdl

    def add_youtube_commands(self):
        """
        Adds the YouTube commands to the Discord client.

        This function adds the following commands to the Discord client:
        - 'play': Plays music from YouTube URLs or searches YouTube for the top result.
        - 'pause': Pauses the audio.
        - 'resume': Resumes the current audio.
        - 'skip': Skips the current song in the queue.
        - 'leave': Stops the music and makes the bot leave the voice channel.
        - 'clear': Clears the queue and stops the music.

        Parameters:
        - None

        Returns:
        - None
        """
        @self.client.tree.command(name='play',
                                  description='Plays music from Youtube URLs or it will automatically search Youtube for top result')
        async def play(interaction: discord.Interaction, search: discord.app_commands.Range[str, 1, 512]):
            self.logger.print('Start - Play Command Called')
            search = search.strip()
            self.logger.print('search: ' + search)
            is_url = search.find(r"https://") != -1
            self.logger.print('is_url: ' + str(is_url))

            if not interaction.user.voice:
                await interaction.response.send_message("You are not connected to a voice channel")
                self.logger.print('    Error - You are not connected to a voice channel')
                self.logger.print('End - Play Command Called')
                return
            else:
                await interaction.response.defer()
                channel = interaction.user.voice.channel
                self.logger.print('channel: ' + str(channel))

            if interaction.guild.voice_client not in interaction.client.voice_clients:
                self.logger.print('    Connecting Rivenbot to Channel')
                try:
                    await channel.connect(timeout=5)
                except asyncio.TimeoutError:
                    await interaction.followup.send("Unable to connect to your voice channel (Timed out)")
                    self.logger.print('    Failed to connect to the voice channel')
                    return
                self.logger.print('    Connected Rivenbot to Channel')

            voice_client = interaction.guild.voice_client
            self.logger.print("Voice Client (Channel): " + str(voice_client))

            if is_url is False:
                await interaction.followup.send("**Searching Youtube: **" + search)
                self.logger.print('    Searching Youtube')

            players = await self.ytdl.from_url(search, stream=True)
            self.logger.print('players: ' + str(players))

            if players is not None:
                if not voice_client.is_playing() and len(players) == 1:
                    await interaction.followup.send('**Loading Audio...**')
                    self.logger.print('    Loading Audio...')
                elif not voice_client.is_playing() and len(players) > 1:
                    await interaction.followup.send('**Playlist Being Added to Queue...**')
                    self.logger.print('    Playlist Being Added to Queue...')
                else:
                    await interaction.followup.send('**Adding Audio to Queue...**')
                    self.logger.print('    Adding Audio to Queue...')

                if len(players) == 1:
                    await self.client.songs.put([interaction, players[0]])
                else:
                    for current_player in players:
                        await self.client.songs.put([interaction, current_player])
            else:
                await interaction.followup.send(":exclamation:ERROR:exclamation:: No video formats found!")
                self.logger.print('    No video formats found!')
            self.logger.print('End - Play Command Called')

        @self.client.tree.command(name='pause', description='Pauses the audio')
        async def pause(interaction: discord.Interaction):
            """
            Pauses the audio in the voice channel the bot is currently in.

            Parameters:
                interaction (discord.Interaction): The interaction object.

            Returns:
                None

            Raises:
                None

            Description:
                This command pauses the audio that is currently playing in the voice channel that the bot is in.
                If there is no audio playing, it sends a message to the channel indicating that there is no music playing.
                If the bot is not in a voice channel, it sends a message to the channel indicating that it is not in a voice channel.

            Example Usage:
                /pause
            """
            self.logger.print('Start - Pause Command Called')
            voice_channel = interaction.guild.voice_client

            if voice_channel:
                if voice_channel.is_playing():
                    voice_channel.pause()
                    await interaction.response.send_message("Pausing audio!")
                else:
                    await interaction.response.send_message(":exclamation: No music is playing :exclamation:")
                    self.logger.print('    No music is playing!')
            else:
                await interaction.response.send_message(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
            self.logger.print('End - Pause Command Called')


        @self.client.tree.command(name='resume', description='Resumes the current audio')
        async def resume(interaction: discord.Interaction):
            
            self.logger.print('Start - Resume Command Called')
            voice_channel = interaction.guild.voice_client

            if voice_channel:
                if voice_channel.is_paused():
                    voice_channel.resume()
                    await interaction.response.send_message("Resuming audio!")
                else:
                    await interaction.response.send_message(":exclamation: No music is paused :exclamation:")
                    self.logger.print('    No music is paused!')
            else:
                await interaction.response.send_message(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
            self.logger.print('End - Resume Command Called')

        @self.client.tree.command(name='skip', description='Skips the current song in the queue')
        async def skip(interaction: discord.Interaction):
            """
            Skips the current song in the queue.
        
            Parameters:
                interaction (discord.Interaction): The interaction object.
        
            Returns:
                None
        
            Raises:
                None
        
            Description:
                This command skips the current song in the queue.
                If there is no song playing, it sends a message to the channel indicating that there is no music playing.
                If the bot is not in a voice channel, it sends a message to the channel indicating that it is not in a voice channel.
        
            Example Usage:
                /skip
            """
            self.logger.print('Start - Skip Command Called')
            voice_channel = interaction.guild.voice_client
        
            if voice_channel:
                if voice_channel.is_playing():
                    voice_channel.stop()
                    await interaction.response.send_message("Skipped the current song")
                else:
                    await interaction.response.send_message(":exclamation: No music is playing :exclamation:")
                    self.logger.print('    No music is playing!')
            else:
                await interaction.response.send_message(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
            self.logger.print('End - Skip Command Called')

        @self.client.tree.command(name='leave', description='Stops the music and makes me leave the voice channel')
        async def leave(interaction: discord.Interaction):
            """
            Stops the music and makes me leave the voice channel.

            Parameters:
                interaction (discord.Interaction): The interaction object.

            Returns:
                None

            Description:
                This command stops the music and makes the bot leave the voice channel.
                If there is no audio playing, it sends a message to the channel indicating that there is no music playing.
                If the bot is not in a voice channel, it sends a message to the channel indicating that it is not in a voice channel.

            Example Usage:
                /leave
            """
            self.logger.print('Start - Leave Command Called')
            voice_client = interaction.guild.voice_client

            if voice_client:
                self.logger.print('Start - Disconnecting')
                await voice_client.disconnect()
                voice_client.cleanup()
                await interaction.response.send_message("Bye Bye!")
                self.logger.print('End - Disconnecting')
            else:
                await interaction.response.send_message(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")

            self.client.empty_queue(self.client.songs)
            self.logger.print('End - Leave Command Called')

        @self.client.tree.command(name='clear', description='Clears the queue and stops the music')
        async def clear(interaction: discord.Interaction):
            """
            Clears the queue and stops the music.
        
            Parameters:
                interaction (discord.Interaction): The interaction object.
        
            Returns:
                None
        
            Description:
                This command clears the queue and stops the music.
                It sends a message to the channel indicating that the queue is being cleared.
                If there is no audio playing, it sends a message to the channel indicating that there is no music playing.
                If the bot is not in a voice channel, it sends a message to the channel indicating that it is not in a voice channel.
        
            Example Usage:
                /clear
            """
            self.logger.print('Start - Clear Command Called')
            voice_channel = interaction.guild.voice_client
        
            await interaction.response.send_message(":exclamation: Clearing Queue! :exclamation:")
            self.client.empty_queue(self.client.songs)
        
            if voice_channel:
                voice_channel.stop()
                self.logger.print('Queue Cleared!')
            else:
                await interaction.response.send_message(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
        
            self.logger.print('End - Clear Command Called')