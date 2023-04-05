import argparse
from Logger import Logger
from Riven import Riven
from YTDL import YTDL

# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--ytpass", help="Youtube account password")
parser.add_argument("--distoken", help="Discord token")
parser.add_argument("--spotclient", help="Spotify client id")
parser.add_argument("--spotsecret", help="Spotify client secret")
parser.add_argument("--logpath", help="Base path for log files")
parser.add_argument("--enablelogs", help="Set 'True' to enable logs")
parser.add_argument("--status", help="The Discord status that appears under the bot name in Discord app")
args = parser.parse_args()

# Setting constants
YT_PASSWORD = args.ytpass
DIS_TOKEN = args.distoken
SPOT_CLIENT = args.spotclient
SPOT_SECRET = args.spotsecret

logger = Logger(base_path=args.logpath, enable_logs=args.enablelogs)
riven_bot = Riven(logger, args.status, YT_PASSWORD)

riven_bot.loop.create_task(riven_bot.audio_player_task())
riven_bot.run(DIS_TOKEN)
