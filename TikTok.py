import aiohttp
import asyncio
import re
import os
import platform
import shutil
import warnings
import functools

from urllib.parse import urljoin
from typing import Union, Optional, Literal
from tqdm import tqdm


def deprecated(reason: str = "This function is deprecated and may be removed in future versions."):
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            warnings.warn(
                f"{func.__name__} is deprecated: {reason}",
                category=DeprecationWarning,
                stacklevel=2
            )
            return func(*args, **kwargs)
        return wrapper
    return decorator

class TikTok:
    def __init__(self, host: Optional[str] = None):
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) '
                          'Version/4.0.4 Mobile/7B334b Safari/531.21.10'
        }
        self.host = host or "https://www.tikwm.com/"
        self.session = aiohttp.ClientSession()

        self.data_endpoint = "api"
        self.search_videos_keyword_endpoint = "api/feed/search"
        self.search_videos_hashtag_endpoint = "api/challenge/search"

        self.link = None
        self.result = None

        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def close_session(self):
        await self.session.close()

    async def init(self, link: Optional[str] = None):
        self.link = link
        self.result = await self.fetch(link)

    async def _makerequest(self, endpoint: str, params: dict) -> dict:
        async with self.session.get(urljoin(self.host, endpoint), params=params, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('data', {})

    @staticmethod
    def get_url(text: str) -> Optional[str]:
        urls = re.findall(r'http[s]?://[^\s]+', text)
        return urls[0] if urls else None

    @deprecated('This function is NOT used but may be useful')
    async def convert_share_urls(self, url: str) -> Optional[str]:
        url = self.get_url(url)
        if '@' in url:
            return url
        async with self.session.get(url, headers=self.headers, allow_redirects=False) as response:
            if response.status == 301:
                return response.headers['Location'].split('?')[0]
        return None

    @deprecated('This function is NOT used but may be useful')
    async def get_tiktok_video_id(self, original_url: str) -> Optional[str]:
        original_url = await self.convert_share_urls(original_url)
        matches = re.findall(r'/video|v|photo/(\d+)', original_url)
        return matches[0] if matches else None

    async def fetch(self, link: str) -> dict:
        url = self.get_url(link)
        params = {"url": url, "hd": 1}
        return await self._makerequest(self.data_endpoint, params=params)

    async def search(self, method: Literal["keyword", "hashtag"], keyword: str, count: int = 10, cursor: int = 0) -> list:
        params = {"keywords": keyword, "count": count, "cursor": cursor}
        endpoint = self.search_videos_keyword_endpoint if method == 'keyword' else self.search_videos_hashtag_endpoint
        data = await self._makerequest(endpoint, params=params)
        return data.get("videos", []) if method == 'keyword' else data.get("challenge_list", [])

    async def _download_file(self, url: str, path: str):
        async with self.session.get(url) as response:
            response.raise_for_status()
            with open(path, 'wb') as file:
                while chunk := await response.content.read(1024):
                    file.write(chunk)

    @deprecated('You can use download() instead')
    async def download_photos(self, download_dir: Optional[str] = None):
        download_dir = download_dir or self.result['id']
        os.makedirs(download_dir, exist_ok=True)
        tasks = [self._download_file(url, os.path.join(download_dir, f'image_{i + 1}.jpg')) for i, url in enumerate(self.result['images'])]
        await asyncio.gather(*tasks)
        return download_dir

    async def download_sound(self, audio_filename: Optional[str] = None):
        audio_filename = audio_filename or f"{self.result['music_info']['title']}.mp3"
        await self._download_file(self.result['music_info']['play'], audio_filename)

    async def download(self, video_filename: Optional[str] = None, hd: bool = False):
        """
        Async function to download a TikTok video or a photo post.

        This function can handle both video posts and photo posts. If the provided
        TikTok link is a video, it will download the video. If the link is a photo
        post, it will download all photos associated with the post.

        Args:
            video_filename (Optional[str]): Name of the TikTok video file. If None,
                                                the file will be named based on the video ID.
            hd (Optional[bool]): If True, downloads the video in HD format. Defaults to False.

        Returns:
            str: The filename of the downloaded video or the directory containing photos.

        Raises:
            Exception: If the download fails.

        Example usage:

        ```python
        import asyncio
        from tiktok import TikTok

        async def main():
            tiktok = TikTok()
            await tiktok.init('https://www.tiktok.com/@adasf4v/video/7367017049136172320')
            video_filename = await tiktok.download(hd=True)
            # or
            await tiktok.init('https://www.tiktok.com/@arcadiabayalpha/photo/7375880582473043232')
            photo_filename = await tiktok.download('tiktok images')
            print(f"Downloaded to: {video_filename}")
            print(f"Images downloaded to: {photo_filename}")
            await tiktok.close_session()

        asyncio.run(main())
        ```
        """
        if 'images' in self.result:
            download_dir = video_filename or self.result['id']
            os.makedirs(download_dir, exist_ok=True)
            tasks = [self._download_file(url, os.path.join(download_dir, f'image_{i + 1}.jpg')) for i, url in enumerate(self.result['images'])]
            await asyncio.gather(*tasks)
            print(f"[TikTok:photos] | Downloaded and saved photos to {download_dir}")
            return download_dir
        elif 'hdplay' in self.result or 'play' in self.result:
            video_url = self.result['hdplay'] if hd else self.result['play']
            if video_filename is None:
                video_filename = f"@damirtag сигмо {self.result['id']}.mp4"
            
            async with self.session.get(video_url) as response:
                response.raise_for_status()  # Raise an error for bad status
                total_size = int(response.headers.get('content-length', 0))
                with open(video_filename, 'wb') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc=video_filename) as pbar:
                    async for chunk in response.content.iter_any():
                        file.write(chunk)
                        pbar.update(len(chunk))
                print(f"[TikTok:video] | Downloaded and saved as {video_filename}")
                return video_filename
        else:
            raise Exception("No downloadable content found in the provided link.")

    def construct_caption_posts(self, desc_limit: Optional[int] = None) -> str:
        aweme_id = self.result['id']
        nickname = self.result['author']['nickname']
        unique = self.result['author']['unique_id']
        desc = (self.result['title'] or 'No title')[:desc_limit] + '...' if desc_limit and len(self.result['title']) > desc_limit else self.result['title']
        video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'
        uploader_link = f'https://www.tiktok.com/@{unique}'
        return f"💬: <a href='{video_link}'>{desc}</a>\n\n👤: <a href='{uploader_link}'>{nickname}</a>"

    def construct_caption_audio(self) -> str:
        aweme_id = self.result['id']
        unique = self.result['author']['unique_id']
        video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'
        audio_title = self.result['music_info']['title']
        return f'💬: <a href="{video_link}"> {audio_title}</a>'

    def cleanup(self):
        if hasattr(self, 'download_dir') and os.path.exists(self.download_dir):
            shutil.rmtree(self.download_dir)
        if hasattr(self, 'video_filename') and os.path.exists(self.video_filename):
            os.remove(self.video_filename)
        if hasattr(self, 'audio_filename') and os.path.exists(self.audio_filename):
            os.remove(self.audio_filename)

    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close_session()
        self.cleanup()

    def __del__(self):
        self.cleanup()


# Example usage:
async def main():
    async with TikTok() as tiktok:
        await tiktok.init('https://www.tiktok.com/@adasf4v/video/7367017049136172320')
        video_filename = await tiktok.download(hd=True)
        print(f"Downloaded to: {video_filename}")
        # or
        await tiktok.init('https://www.tiktok.com/@arcadiabayalpha/photo/7375880582473043232')
        photo_filename = await tiktok.download('tiktok images')
        print(f"Images downloaded to: {photo_filename}")
        del tiktok

# Run the example
asyncio.run(main())
