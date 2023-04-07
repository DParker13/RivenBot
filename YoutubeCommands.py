from YTDL import YTDL


class YoutubeCommands:
    vc = None
    def __init__(self, client, logger, yt_pass):
        self.client = client
        self.logger = logger
        self.yt_pass = yt_pass

    def add_youtube_commands(self):
        @self.client.command(name='play',
                             help='Plays music from Youtube URLs or it will automatically search Youtube for top result',
                             pass_context=True)
        async def play(ctx):
            try:
                self.logger.print('Start - Play Command Called')
                search = ctx.message.content[5:].strip()
                is_url = search.find(r"https://") != -1

                if not ctx.message.author.voice:
                    await ctx.send("You are not connected to a voice channel")
                    self.logger.print('    Error - You are not connected to a voice channel')
                    return
                else:
                    channel = ctx.message.author.voice.channel

                if ctx.guild.voice_client not in ctx.bot.voice_clients:
                    self.logger.print('    Connecting Rivenbot to Channel')
                    YoutubeCommands.vc = await channel.connect(timeout=5)
                    self.logger.print('    Connected Rivenbot to Channel')

                guild = ctx.message.guild
                voice_channel = guild.voice_client
                self.logger.print("Voice Channel: " + str(voice_channel))

                if is_url is False:
                    await ctx.send("**Searching Youtube: **" + search)
                    self.logger.print('    Searching Youtube')

                players = await YTDL(source=YoutubeCommands.vc.source, data=None, yt_password=self.yt_pass).add_functions().from_url(search, loop=self.client.loop, stream=True)

                if players is not None:
                    if not voice_channel.is_playing() and len(players) == 1:
                        await ctx.send('**Loading Audio...**')
                        self.logger.print('    Loading Audio...')
                    elif not voice_channel.is_playing() and len(players) > 1:
                        await ctx.send('**Playlist Being Added to Queue...**')
                        self.logger.print('    Playlist Being Added to Queue...')
                    else:
                        await ctx.send('**Adding Audio to Queue...**')
                        self.logger.print('    Adding Audio to Queue...')

                    if len(players) == 1:
                        await self.client.songs.put([ctx, players[0]])
                    else:
                        for current_player in players:
                            await self.client.songs.put([ctx, current_player])
                else:
                    await ctx.send(":exclamation:ERROR:exclamation:: No video formats found!")
                    self.logger.print('    No video formats found!')
                self.logger.print('End - Play Command Called')
            except Exception as e:
                self.logger.print('Error - ' + str(e))

        @self.client.command(name='pause', help='Pauses the audio')
        async def pause(ctx):
            self.logger.print('Start - Pause Command Called')
            guild = ctx.message.guild
            voice_channel = guild.voice_client

            if ctx.guild.voice_client in ctx.bot.voice_clients:
                if voice_channel.is_playing():
                    voice_channel.pause()
                else:
                    await ctx.send(":exclamation: No music is playing :exclamation:")
                    self.logger.print('    No music is playing!')
            else:
                await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
            self.logger.print('End - Pause Command Called')

        @self.client.command(name='resume', help='Resumes the current audio')
        async def resume(ctx):
            self.logger.print('Start - Resume Command Called')
            guild = ctx.message.guild
            voice_channel = guild.voice_client

            if ctx.guild.voice_client in ctx.bot.voice_clients:
                if voice_channel.is_paused():
                    voice_channel.resume()
                else:
                    await ctx.send(":exclamation: Current song is not paused :exclamation:")
                    self.logger.print('    Current song is not paused!')
            else:
                await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")
            self.logger.print('End - Resume Command Called')

        @self.client.command(name='skip', help='Skips the current song in the queue')
        async def skip(ctx):
            self.logger.print('Start - Skip Command Called')
            guild = ctx.message.guild
            voice_channel = guild.voice_client

            if ctx.guild.voice_client in ctx.bot.voice_clients:
                if voice_channel.is_playing():
                    self.logger.print("    Skipping current audio!")
                    await ctx.send("**Skipping current audio!**")
                    self.logger.print("    Skipping current audio!")
                    voice_channel.stop()
                else:
                    self.logger.print("    There is nothing in the queue to skip")
                    await ctx.send(r"<:cring:758870529599209502> There is nothing in the queue to skip")
                    self.logger.print("    There is nothing in the queue to skip")
            else:
                self.logger.print(r"I'm not in a voice channel right now")
                await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"I'm not in a voice channel right now")
            self.logger.print('End - Skip Command Called')

        @self.client.command(name='leave', help='Stops the music and makes me leave the voice channel')
        async def leave(ctx):
            self.logger.print('Start - Leave Command Called')
            voice_client = ctx.message.guild.voice_client

            if ctx.guild.voice_client in ctx.bot.voice_clients:
                self.logger.print('Start - Disconnecting')
                await voice_client.disconnect()
                self.logger.print('End - Disconnecting')
            else:
                await ctx.send(r"<:cring:758870529599209502> I'm not in a voice channel right now")
                self.logger.print(r"    I'm not in a voice channel right now")

            self.client.empty_queue(self.client.songs)
            self.logger.print('End - Leave Command Called')

        @self.client.command(name='clear', help='Clears the queue and stops the music')
        async def clear(ctx):
            self.logger.print('Start - Clear Command Called')
            guild = ctx.message.guild
            voice_channel = guild.voice_client

            await ctx.send(":exclamation: Clearing Queue! :exclamation:")
            self.client.empty_queue(self.client.songs)

            if ctx.guild.voice_client in ctx.bot.voice_clients:
                voice_channel.stop()
            self.logger.print('End - Clear Command Called')
