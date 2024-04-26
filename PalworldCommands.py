import subprocess
import os

class PalworldCommands:

    def __init__(self, client, logger):
        self.client = client
        self.logger = logger

    def add_palworld_commands(self):
        # Command to start the service
        start_command = ['sudo', '/bin/systemctl', 'start', 'palworld']

        # Command to stop the service
        stop_command = ['sudo', '/bin/systemctl', 'stop', 'palworld']

        @self.client.command(name='startpalworld',
                             help='Starts the Palworld server')
        async def startpalworld(ctx):
            try:
                self.logger.print('Start - Start Palworld Command Called')
                await ctx.send("Starting Palworld Server")
                subprocess.run(start_command, check=True)
                self.logger.print('End - Start Palworld Command Called')
            except subprocess.CalledProcessError as e:
                self.logger.print(f"Error while checking palworld server status: {e}")
                self.logger.print(f"Error output: {e.stderr}")
            except Exception as e:
                self.logger.print(f"An unexpected error occurred: {e}")

        @self.client.command(name='stoppalworld',
                             help='Stops the Palworld server (Assuming it is running)')
        async def stopPalworld(ctx):
            try:
                self.logger.print('Start - Stop Palworld Command Called')
                await ctx.send("Stopping Palworld Server")
                subprocess.run(stop_command, check=True)
                self.logger.print('End - Stop Palworld Command Called')
            except subprocess.CalledProcessError as e:
                self.logger.print(f"Error while checking palworld server status: {e}")
                self.logger.print(f"Error output: {e.stderr}")
            except Exception as e:
                self.logger.print(f"An unexpected error occurred: {e}")
