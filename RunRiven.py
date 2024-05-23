import argparse
import discord
import yt_dlp
import asyncio
import json

from Logger import Logger
from Riven import Riven

# Command line arguments
parser = argparse.ArgumentParser(description='Discord bot for the Soft Tacos')
parser.add_argument("--ytpass", help="Youtube account password")
parser.add_argument("--distoken", help="Discord token")
parser.add_argument("--openaikey", help="OpenAI Secret Key")
parser.add_argument("--status", help="The Discord status that appears under the bot name in Discord app")
args = parser.parse_args()

# Setting constants
YT_PASSWORD = args.ytpass
DIS_TOKEN = args.distoken
OPENAI_KEY = args.openaikey

# Load the CONFIG.JSON file
with open('/home/media-server/Documents/GitHub/RivenBot/config.json') as f:
    config = json.load(f)

# Setup youtube-dlp
ytdl_options = config['ytdl_format_options']
ytdl_options['password'] = YT_PASSWORD

ytdl = yt_dlp.YoutubeDL(ytdl_options)
ffmpeg_options = config['ffmpeg_options']

yt_dlp.utils.bug_reports_message = lambda: ''

class YTDL(discord.PCMVolumeTransformer):
    def __init__(self, source, *, data, volume=0.5):
        """
        Initializes a new instance of the YTDL class.

        Args:
            source (AudioSource): The audio source for the YTDL instance.
            data (dict): A dictionary containing the data for the YTDL instance.
                It should have the following keys:
                    - 'title' (str): The title of the audio source.
                    - 'url' (str): The URL of the audio source.
            volume (float, optional): The volume of the audio source. Defaults to 0.5.
        """
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')

    @classmethod
    async def from_url(cls, url, *, loop=None, stream=True):
        """
        Asynchronously creates a list of `YTDL` objects from a given URL.
        
        Args:
            url (str): The URL of the video or playlist to extract information from.
            loop (asyncio.AbstractEventLoop, optional): The event loop to use for the asynchronous operations. If not provided, the default event loop will be used.
            stream (bool, optional): Whether to stream the video or not. Defaults to False.
        
        Returns:
            Union[List[YTDL], None]: A list of `YTDL` objects if the URL is a playlist with multiple entries, a single `YTDL` object if the URL is a single video, or None if the URL is invalid or an error occurs during the extraction process.
        """
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


logger = Logger(base_path=config['logging']['base_path'], enable_logs=config['logging']['enable_logs'], log_level=config['logging']['log_level'])
riven_bot = Riven(logger, args.status, YTDL, OPENAI_KEY)
riven_bot.run(DIS_TOKEN)
