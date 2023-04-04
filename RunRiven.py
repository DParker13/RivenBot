import argparse
from Logger import Logger
from Riven import Riven


# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--ytpass", help="Youtube account password")
parser.add_argument("--distoken", help="Discord token")
parser.add_argument("--logpath", help="Base path for log files")
parser.add_argument("--enablelogs", help="Set 'True' to enable logs")
parser.add_argument("--status", help="The Discord status that appears under the bot name in Discord app")
args = parser.parse_args()

# Setting constants
YT_PASSWORD = args.ytpass
DIS_TOKEN = args.distoken

logger = Logger(base_path=args.logpath, enable_logs=args.enablelogs)
riven_bot = Riven(logger, args.status, YT_PASSWORD)

riven_bot.client.loop.create_task(riven_bot.audio_player_task())
riven_bot.client.run(DIS_TOKEN)