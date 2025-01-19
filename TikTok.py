"""
Author: https://github.com/damirTAG
GH repo: https://github.com/damirTAG/TikTok-Module

MIT License

Copyright (c) 2024 Tagilbayev Damir

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in all
copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
SOFTWARE.

"""

import aiohttp, asyncio
import logging, os, re
import ffmpeg

from dataclasses import dataclass, field
from typing import Union, Optional, Literal, List, Dict
from tqdm.asyncio import tqdm


@dataclass
class data:
    dir_name: str
    media: Union[str, List[str]]
    type: str

@dataclass
class metadata(data):
    metadata: Dict[str, Union[int, float]] = field(default_factory=dict)

    @property
    def height(self) -> Optional[int]:
        return self.metadata.get('height')
    @property
    def width(self) -> Optional[int]:
        return self.metadata.get('width')
    @property
    def duration(self) -> Optional[float]:
        return self.metadata.get('duration')

class TikTok:
    def __init__(self, host: Optional[str] = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) '
                          'Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        }
        self.host = host or "https://www.tikwm.com/"
        self.session = None

        self.data_endpoint = "api"
        self.search_videos_keyword_endpoint = "api/feed/search"
        self.search_videos_hashtag_endpoint = "api/challenge/search"

        self.logger = self._setup_logger()
        self.result = None
        self.link = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    def _setup_logger(self):
        logger = logging.getLogger('damirtag.TikTok')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[damirtag-TikTok:%(funcName)s]: %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        if not logger.handlers:
            logger.addHandler(handler)
        logger.setLevel(logging.INFO)
        return logger

    async def _ensure_data(self, link: str):
        if self.result is None or self.link != link:
            self.link = link
            self.result = await self.fetch(link)
            self.logger.info("Successfully ensured data from the link")

    async def _makerequest(self, endpoint: str, params: dict) -> dict:
        async with self.session.get(
                os.path.join(self.host, endpoint),
                params=params, 
                headers=self.headers
            ) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('data', {})

    async def _download_file(self, url: str, path: str):
        async with self.session.get(url) as response:
            response.raise_for_status()
            with open(path, 'wb') as file, tqdm(unit='B', unit_scale=True, desc=os.path.basename(path)) as pbar:
                while chunk := await response.content.read(1024):
                    file.write(chunk)
                    pbar.update(len(chunk))

    @staticmethod
    def get_url(text: str) -> Optional[str]:
        urls = re.findall(r'http[s]?://[^\s]+', text)
        return urls[0] if urls else None

    async def image(self, download_dir: Optional[str] = None):
        download_dir = download_dir or self.result['id']
        os.makedirs(download_dir, exist_ok=True)
        tasks = [
            self._download_file(
                    url, 
                    os.path.join(
                        download_dir, 
                        f'image_{i + 1}.jpg'
                    )
                )
                for i, url in enumerate(self.result['images'])
            ]
        await asyncio.gather(*tasks)
        self.logger.info(f"Images - Downloaded and saved photos to {download_dir}")

        return data(
            dir_name=download_dir,
            media=[
                    os.path.join(
                        download_dir, 
                        f'image_{i + 1}.jpg'
                    ) 
                    for i in range(len(self.result['images']))
                ],
            type="images"
        )

    async def video(self, video_filename: Optional[str] = None, hd: bool = False):
        video_url = self.result['hdplay'] if hd else self.result['play']
        video_filename = video_filename or f"Greetings from @damirtag {self.result['id']}.mp4"

        async with self.session.get(video_url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(video_filename, 'wb') as file, tqdm(
                    total=total_size, 
                    unit='B', 
                    unit_scale=True, 
                    desc=video_filename
                ) as pbar:
                async for chunk in response.content.iter_any():
                    file.write(chunk)
                    pbar.update(len(chunk))

        self.logger.info(f"Video - Downloaded and saved video as {video_filename}")

        # Extract metadata (duration from API, width and height from ffmpeg)
        duration = self.result.get('duration', 0.0)  # Provided by the API
        width, height = self._get_video_dimensions(video_filename)

        return metadata(
            dir_name=os.path.dirname(video_filename),
            media=video_filename,
            type="video",
            metadata={
                'duration': duration,
                'width': width,
                'height': height
            }
        )

    def _get_video_dimensions(self, video_file: str):
        """Extract width and height using ffmpeg."""
        try:
            probe = ffmpeg.probe(video_file)
            video_streams = [stream for stream in probe['streams'] if stream['codec_type'] == 'video']
            if video_streams:
                width = video_streams[0]['width']
                height = video_streams[0]['height']
                return width, height
            else:
                self.logger.error(f"No video streams found in {video_file}")
                return None, None
        except Exception as e:
            self.logger.error(f"Error while extracting video dimensions with ffmpeg: {e}")
            return None, None
        
    async def fetch(self, link: str) -> dict:
        """
        Get tiktok post info (raw api response).

        :param: link(str) = Tiktok video url
        """
        url = self.get_url(link)
        params = {"url": url, "hd": 1}
        return await self._makerequest(self.data_endpoint, params=params)

    async def search(
            self, 
            method: Literal["keyword", "hashtag"], 
            keyword: str, 
            count: int = 10, 
            cursor: int = 0
            ) -> list:
        """
        Search videos by keyword (default search) or hashtag

        Args:
            method (Literal["keyword", "hashtag"]): The search method. Choose between 'keyword' for general video search or 'hashtag' for hashtag-based search.
            keyword (str): The keyword or hashtag to search for. For 'keyword', it can be a phrase or any string. For 'hashtag', prefix with `#` (e.g., '#funny').
            count (int, optional): The number of search results to return. Default is 10.
            cursor (int, optional): The cursor for pagination. Used to fetch subsequent pages of results. Default is 0.

        Returns:
            list: A list of search results returned by the TikTok API.
            Each entry in the list contains metadata for individual videos or hashtags.

            Example response to see: 
                https://tikwm.com/api/feed/search?keywords=jojo7&count=10&cursor=10

        Example:
            If you're searching for videos related to "jojo7" with 10 results:
                result = await search(method="keyword", keyword="jojo7", count=10, cursor=0)

            If you're searching for a specific hashtag like "#funny" with 5 results:
                result = await search(method="hashtag", keyword="funny", count=5, cursor=0)
        """
        self.logger.info(f"Searching for: {keyword}")
        params = {"keywords": keyword, "count": count, "cursor": cursor}
        endpoint = (
            self.search_videos_keyword_endpoint 
            if method == 'keyword' 
            else self.search_videos_hashtag_endpoint
            )

        try:
            data = await self._makerequest(endpoint, params=params)
            if data:
                total_results_int = (
                    f"{len(data.get('videos'))} videos" 
                    if method == "keyword" 
                    else f"{len(data.get('challenge_list'))} hashtags"
                    )
                self.logger.info(f"Found {total_results_int} for query: {keyword}")
                return data.get("videos", []) if method == 'keyword' else data.get("challenge_list", [])
            else:
                raise Exception("Nothing found. Sorry, check params")
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")    

    async def download_sound(
            self, 
            link: Union[str], 
            audio_filename: Optional[str] = None, 
            audio_ext: Optional[str] = ".mp3"
        ):
        await self._ensure_data(link)
        
        if not audio_filename:
            audio_filename = f"{self.result['music_info']['title']}{audio_ext}"
        else:
            audio_filename += audio_ext
        
        await self._download_file(self.result['music_info']['play'], audio_filename)
        self.logger.info(f"Sound - Downloaded and saved sound as {audio_filename}")
        return audio_filename

    async def download(
            self, 
            link: Union[str], 
            video_filename: Optional[str] = None, 
            hd: bool = False
            ) -> str:
        """
        Asynchronously downloads a TikTok video or photo post.

        Args:
            video_filename (Optional[str]): The name of the file for the TikTok video or photo. If None, the file will be named based on the video or photo ID.
            hd (bool): If True, downloads the video in HD format. Defaults to False.
            metadata (bool): if True, returns duration, width and height (only for videos)

        Returns:
            dir_name (Union[str]): Directory name.
            media (List[str]): Full list of downloaded media.
            type (str): The type of downloaded objects: Images or video.
            metadata (dict): {'duration': 13, 'width': 576, 'height': 1024}

        Raises:
            Exception: No downloadable content found in the provided link.

        Base usage code example:
            ```python
            import asyncio
            from tiktok import TikTok

            async def main():
                async with TikTok() as tt:
                    video = await tiktok.download("https://www.tiktok.com/@adasf4v/video/7367017049136172320", hd=True)
                    # or
                    photo = await tiktok.download('https://www.tiktok.com/@arcadiabayalpha/photo/7375880582473043232', 'tiktok_images')
                    print(f"Downloaded video: {video.media}")
                    print(f"Images downloaded to: {photo.dir_name}")
                    await tiktok.close_session()

            asyncio.run(main())
            ```
        
        Telethon usage code example:
            ```python
            from telethon import TelegramClient, events
            from tiktok import TikTok

            # Initialize your Telegram client
            api_id = 'your_api_id'
            api_hash = 'your_api_hash'
            bot_token = 'your_bot_token'

            client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
            tiktok = TikTok()

            @client.on(events.NewMessage(pattern='/tiktok'))
            async def handle_tiktok_command(event):
                try:
                    # Get TikTok link from message
                    tiktok_link = event.text.split()[1]
                    
                    # Download the TikTok content
                    result = await tiktok.download(tiktok_link, hd=True)
                    
                    # Send the downloaded content
                    if result.type == 'video':
                        await client.send_file(
                            event.chat_id,
                            result.media[0],
                            caption=f"Downloaded from: {tiktok_link}"
                        )
                    else:  # Photos
                        for photo in result.media:
                            await client.send_file(
                                event.chat_id,
                                photo,
                                caption=f"Downloaded from: {tiktok_link}"
                            )
                            
                except Exception as e:
                    await event.reply(f"Error downloading TikTok content: {str(e)}")

            # Run the client
            client.run_until_disconnected()
            ```

        Aiogram usage code example:
            ```python
            from aiogram import Bot, Dispatcher, types
            from aiogram.filters.command import Command
            from tiktok import TikTok
            import asyncio

            # Initialize bot and dispatcher
            bot = Bot(token='your_bot_token')
            dp = Dispatcher()
            tiktok = TikTok()

            @dp.message(Command('tiktok'))
            async def handle_tiktok_command(message: types.Message):
                try:
                    # Get TikTok link from message
                    command_parts = message.text.split()
                    if len(command_parts) != 2:
                        await message.reply("Please provide a TikTok link after the command")
                        return
                        
                    tiktok_link = command_parts[1]
                    
                    # Send "processing" message
                    processing_msg = await message.reply("Downloading TikTok content...")
                    
                    # Download the TikTok content
                    result = await tiktok.download(tiktok_link, hd=True)
                    
                    # Send the downloaded content
                    if result.type == 'video':
                        await message.reply_video(
                            video=types.FSInputFile(result.media[0]),
                            caption=f"Downloaded from: {tiktok_link}"
                        )
                    else:  # Photos
                        media_group = []
                        for photo in result.media:
                            media_group.append(
                                types.InputMediaPhoto(
                                    media=types.FSInputFile(photo)
                                )
                            )
                        # Set caption for the first photo
                        if media_group:
                            media_group[0].caption = f"Downloaded from: {tiktok_link}"
                        
                        await message.reply_media_group(media=media_group)
                    
                    # Delete processing message
                    await processing_msg.delete()
                    
                except Exception as e:
                    await message.reply(f"Error downloading TikTok content: {str(e)}")

            async def main():
                await dp.start_polling(bot)

            if __name__ == '__main__':
                asyncio.run(main())
            ```
        """
        await self._ensure_data(link)
        if 'images' in self.result:
            self.logger.info("Starting to download images")
            return await self.image(video_filename)
        elif 'hdplay' in self.result or 'play' in self.result:
            self.logger.info("Starting to download video.")
            return await self.video(video_filename, hd)
        else:
            self.logger.error("No downloadable content found in the provided link.")
            raise Exception("No downloadable content found in the provided link.")