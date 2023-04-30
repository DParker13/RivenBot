import argparse
import discord
import yt_dlp
import asyncio

from Logger import Logger
from Riven import Riven

# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--ytpass", help="Youtube account password")
parser.add_argument("--distoken", help="Discord token")
parser.add_argument("--openaikey", help="OpenAI Secret Key")
parser.add_argument("--chatpath", help="OpenAI chat file path")
parser.add_argument("--logpath", help="Base path for log files")
parser.add_argument("--enablelogs", help="Set 'True' to enable logs")
parser.add_argument("--status", help="The Discord status that appears under the bot name in Discord app")
args = parser.parse_args()

# Setting constants
YT_PASSWORD = args.ytpass
DIS_TOKEN = args.distoken
OPENAI_KEY = args.openaikey
CHAT_PATH = args.chatpath

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
ytdl = yt_dlp.YoutubeDL(ytdl_format_options)
yt_dlp.utils.bug_reports_message = lambda: ''
ffmpeg_options = {
    'options': '-vn'
}


class YTDL(discord.PCMVolumeTransformer):
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


logger = Logger(base_path=args.logpath, enable_logs=args.enablelogs)
riven_bot = Riven(logger, discord.Status.online, YTDL, OPENAI_KEY, CHAT_PATH)
riven_bot.run(DIS_TOKEN)
