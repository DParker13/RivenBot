import subprocess


class MinecraftCommands:

    def __init__(self, client, logger):
        self.client = client
        self.logger = logger

    def add_minecraft_commands(self):
        @self.client.command(name='startminecraft',
                             help='Starts the minecraft server')
        async def startminecraft(ctx):
            self.logger.print('Start - Start Minecraft Command Called')
            status_proc = subprocess.run('/home/media-server/Scripts/minecraft-status.sh', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            status_str = status_proc.stdout.decode('utf-8')

            if '"running": false' in status_str:
                self.logger.print('    Starting Minecraft Server')
                await ctx.send("Starting Minecraft Server")
                subprocess.call('/home/media-server/Scripts/minecraft-start.sh', shell=True)

                self.logger.print('    Started Minecraft Server')
            else:
                await ctx.send("Minecraft server is already running")
                self.logger.print('    Minecraft server is already running')
            self.logger.print('End - Start Minecraft Command Called')

        @self.client.command(name='stopminecraft',
                             help='Stops the minecraft server (Assuming it is running)')
        async def stopminecraft(ctx):
            self.logger.print('Start - Stop Minecraft Command Called')
            status_proc = subprocess.run('/home/media-server/Scripts/minecraft-status.sh', shell=True, stdout=subprocess.PIPE, stdin=subprocess.PIPE)
            status_str = status_proc.stdout.decode('utf-8')

            if '"running": true' in status_str:
                await ctx.send(
                    "Attempting to stop Minecraft Server (Server could still be launching if this command was called too early)")
                self.client.check_for_players.stop()
                subprocess.call('/home/media-server/Scripts/minecraft-stop.sh', shell=True)
                self.logger.print('    Minecraft server stopped')
            else:
                await ctx.send("Minecraft server is not running")
                self.logger.print('    Minecraft server is not running')
            self.logger.print('End - Stop Minecraft Command Called')
