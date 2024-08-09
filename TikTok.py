import aiohttp, asyncio, re, os, warnings, functools, logging

from dataclasses import dataclass
from urllib.parse import urljoin
from typing import Union, Optional, Literal, List
from tqdm import tqdm

@dataclass
class data:
    dir_name: str
    media: Union[str, List[str]]
    type: str

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

        self.logger = logging.getLogger('damirtag-TikTok')
        handler = logging.StreamHandler()
        formatter = logging.Formatter('[damirtag-TikTok:%(funcName)s]: %(levelname)s - %(message)s')
        handler.setFormatter(formatter)
        self.logger.addHandler(handler)
        self.logger.setLevel(logging.INFO)

    def _warn(reason: str = 'This function is NOT used but may be useful'):
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                warnings.warn(
                    f"Warning! Deprecated: {func.__name__}\nReason: {reason}",
                    category=DeprecationWarning,
                    stacklevel=2
                )
                return func(*args, **kwargs)
            return wrapper
        return decorator

    async def close_session(self):
        await self.session.close()

    async def _ensure_data(self, link: str):
        try:
            if self.result is None or self.link != link:
                self.link = link
                self.result = await self.fetch(link)
                self.logger.info("Succesfully ensured data from the link")
        except Exception as e:
            self.logger.error(f'Error occured when tried to get data from tikwm: {e}')

    async def __getimages(self, download_dir: Optional[str] = None):
        download_dir = download_dir or self.result['id']
        os.makedirs(download_dir, exist_ok=True)
        tasks = [self._download_file(url, os.path.join(download_dir, f'image_{i + 1}.jpg')) for i, url in enumerate(self.result['images'])]
        await asyncio.gather(*tasks)
        self.logger.info(f"Images - Downloaded and saved photos to {download_dir}")

        return data(
            dir_name=download_dir,
            media=[os.path.join(download_dir, f'image_{i + 1}.jpg') for i in range(len(self.result['images']))],
            type="images"
        )
        

    async def __getvideo(self, video_filename: Optional[str] = None, hd: bool = False):
        video_url = self.result['hdplay'] if hd else self.result['play']
        video_filename = video_filename or f"{self.result['id']}.mp4"

        async with self.session.get(video_url) as response:
            response.raise_for_status()
            total_size = int(response.headers.get('content-length', 0))
            with open(video_filename, 'wb') as file, tqdm(total=total_size, unit='B', unit_scale=True, desc=video_filename) as pbar:
                async for chunk in response.content.iter_any():
                    file.write(chunk)
                    pbar.update(len(chunk))

        self.logger.info(f"Video - Downloaded and saved video as {video_filename}")

        return data(
            dir_name=os.path.dirname(video_filename),
            media=video_filename,
            type="video"
        )

    async def _makerequest(self, endpoint: str, params: dict) -> dict:
        async with self.session.get(urljoin(self.host, endpoint), params=params, headers=self.headers) as response:
            response.raise_for_status()
            data = await response.json()
            return data.get('data', {})

    @staticmethod
    def get_url(text: str) -> Optional[str]:
        urls = re.findall(r'http[s]?://[^\s]+', text)
        return urls[0] if urls else None

    @_warn()
    async def convert_share_urls(self, url: str) -> Optional[str]:
        url = self.get_url(url)
        if '@' in url:
            return url
        async with self.session.get(url, headers=self.headers, allow_redirects=False) as response:
            if response.status == 301:
                return response.headers['Location'].split('?')[0]
        return None

    @_warn()
    async def get_tiktok_video_id(self, original_url: str) -> Optional[str]:
        original_url = await self.convert_share_urls(original_url)
        matches = re.findall(r'/video|v|photo/(\d+)', original_url)
        return matches[0] if matches else None

    async def fetch(self, link: str) -> dict:
        url = self.get_url(link)
        params = {"url": url, "hd": 1}
        return await self._makerequest(self.data_endpoint, params=params)

    async def search(self, method: Literal["keyword", "hashtag"], keyword: str, count: int = 10, cursor: int = 0) -> list:
        self.logger.info(f"Searching for: {keyword}")
        params = {"keywords": keyword, "count": count, "cursor": cursor}
        endpoint = self.search_videos_keyword_endpoint if method == 'keyword' else self.search_videos_hashtag_endpoint

        try:
            data = await self._makerequest(endpoint, params=params)
            if data:
                total_results_int = f"{len(data.get('videos'))} videos" if method == "keyword" else f"{len(data.get('challenge_list'))} hashtags"
                self.logger.info(f"Found {total_results_int} for query: {keyword}")
                return data.get("videos", []) if method == 'keyword' else data.get("challenge_list", [])
            else:
                raise Exception("Nothing found. Sorry, check params")
        except Exception as e:
            self.logger.error(f"Failed to search: {e}")    

    async def _download_file(self, url: str, path: str):
        async with self.session.get(url) as response:
            response.raise_for_status()
            with open(path, 'wb') as file:
                while chunk := await response.content.read(1024):
                    file.write(chunk)

    async def download_sound(self, link: Union[str], audio_filename: Optional[str] = None, 
                         audio_ext: Optional[str] = ".mp3"):
        await self._ensure_data(link)
        
        if not audio_filename:
            audio_filename = f"{self.result['music_info']['title']}{audio_ext}"
        else:
            audio_filename += audio_ext
        
        await self._download_file(self.result['music_info']['play'], audio_filename)
        self.logger.info(f"Sound - Downloaded and saved sound as {audio_filename}")
        return audio_filename

    async def download(self, link: Union[str], video_filename: Optional[str] = None, hd: bool = False) -> str:
        """
        Asynchronously downloads a TikTok video or photo post.

        Args:
            video_filename (Optional[str]): The name of the file for the TikTok video or photo. If None, the file will be named based on the video or photo ID.
            hd (bool): If True, downloads the video in HD format. Defaults to False.

        Returns:
            dir_name (str): Directory name
            media (Union[str, List[str]]): Full list of downloaded media
            type (str): The type of downloaded objects: Images or video

        Raises:
            Exception: No downloadable content found in the provided link.

        Code example:
            ```python
            import asyncio
            from tiktok import TikTok

            async def main():
                    tiktok = TikTok()
                    video = await tiktok.download("https://www.tiktok.com/@adasf4v/video/7367017049136172320", hd=True)
                    # or
                    photo = await tiktok.download('https://www.tiktok.com/@arcadiabayalpha/photo/7375880582473043232', 'tiktok_images')
                    print(f"Downloaded video: {video.media}")
                    print(f"Images downloaded to: {photo.dir_name}")
                    await tiktok.close_session()

            asyncio.run(main())
            ```
        """
        await self._ensure_data(link)
        if 'images' in self.result:
            self.logger.info("Starting to download images")
            return await self.__getimages(video_filename)
        elif 'hdplay' in self.result or 'play' in self.result:
            self.logger.info("Starting to download video.")
            return await self.__getvideo(video_filename, hd)
        else:
            self.logger.error("No downloadable content found in the provided link.")
            raise Exception("No downloadable content found in the provided link.")

    def _get_video_link(self, unique_id: str, aweme_id: str) -> str:
        return f'https://www.tiktok.com/@{unique_id}/video/{aweme_id}'
    def _get_uploader_link(self, unique_id: str) -> str:
        return f'https://www.tiktok.com/@{unique_id}'

    def construct_caption_posts(self, desc_limit: Optional[int] = None, desc_prefix: str = '💬:', desc_suffix: str = '', 
                                uploader_prefix: str = '👤:', uploader_suffix: str = '') -> str:
        """
        Helpful stuff, like constructing captions for telegram bots, may be useful.
        Uses markdown HTML.

        Args:
            desc_limit (Optional[int]): The maximum length of the description. If provided, the description will be truncated to this length.
            desc_prefix (str): The prefix to add before the description link.
            desc_suffix (str): The suffix to add after the description link.
            uploader_prefix (str): The prefix to add before the uploader link.
            uploader_suffix (str): The suffix to add after the uploader link.

        Returns:
            str: The formatted caption for the TikTok post.
        """
        aweme_id = self.result.get('id', 'N/A')
        nickname = self.result.get('author', {}).get('nickname', 'Unknown')
        unique_id = self.result.get('author', {}).get('unique_id', 'unknown_user')
        title = self.result.get('title', 'No title')
        desc = (title[:desc_limit] + '...') if desc_limit and len(title) > desc_limit else title
        video_link = self._get_video_link(unique_id, aweme_id)
        uploader_link = self._get_uploader_link(unique_id)

        return (f"{desc_prefix} <a href='{video_link}'>{desc}</a>{desc_suffix}\n\n"
                f"{uploader_prefix} <a href='{uploader_link}'>{nickname}</a>{uploader_suffix}")

    def construct_caption_audio(self, audio_prefix: str = '💬:', audio_suffix: str = '') -> str:
        """
        Helpful stuff, like constructing captions for telegram bots, may be useful.
        Uses markdown HTML.

        Args:
            audio_prefix (str): The prefix to add before the audio title link.
            audio_suffix (str): The suffix to add after the audio title link.

        Returns:
            str: The formatted caption for the TikTok audio post.
        """
        aweme_id = self.result.get('id', 'N/A')
        unique_id = self.result.get('author', {}).get('unique_id', 'unknown_user')
        video_link = self._get_video_link(unique_id, aweme_id)
        audio_title = self.result.get('music_info', {}).get('title', 'Unknown audio')

        return f'{audio_prefix} <a href="{video_link}">{audio_title}</a>{audio_suffix}'