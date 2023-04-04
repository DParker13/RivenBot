import asyncio
import discord
import yt_dlp


class YTDLSource(discord.PCMVolumeTransformer):
    yt_dlp.utils.bug_reports_message = lambda: ''
    ffmpeg_options = {
        'options': '-vn'
    }

    def __init__(self, source, *, data, volume=0.5, yt_password):
        super().__init__(source, volume)
        self.data = data
        self.title = data.get('title')
        self.url = data.get('url')
        self.YT_PASSWORD = yt_password

        ytdl_format_options = {
            'username': 'meepmeep04@gmail.com',
            'password': self.YT_PASSWORD,
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

    @classmethod
    async def from_url(cls, self, url, *, loop=None, stream=False):
        loop = loop or asyncio.get_event_loop()
        data = await loop.run_in_executor(None, lambda: self.ytdl.extract_info(url, download=not stream))

        # Checks if the link is a playlist
        if 'entries' in data:
            if len(data['entries']) == 1:
                # take first item from a playlist
                data = data['entries'][0]

                filename = data['url'] if stream else self.ytdl.prepare_filename(data)
                try:
                    return [cls(discord.FFmpegPCMAudio(filename, **YTDLSource.ffmpeg_options),
                                data=data)]
                except yt_dlp.utils.DownloadError as e:
                    print(e)
                    return None
            else:
                player_list = list()
                while len(data['entries']) != 0:
                    current_data = data['entries'].pop(0)

                    filename = current_data['url'] if stream else self.ytdl.prepare_filename(current_data)
                    try:
                        player_list.append(cls(discord.FFmpegPCMAudio(filename, **YTDLSource.ffmpeg_options),
                                               data=current_data))
                    except yt_dlp.utils.DownloadError as e:
                        print(e)
                        player_list.append(None)

                return player_list

        elif data is not None:
            filename = data['url'] if stream else self.ytdl.prepare_filename(data)
            try:
                return [cls(discord.FFmpegPCMAudio(filename, **YTDLSource.ffmpeg_options),
                            data=data)]
            except yt_dlp.utils.DownloadError as e:
                print(e)
                return None

        print("DATA IS SET TO NONE")
        return None