import aiohttp, aiofiles, re, asyncio, os, shutil
from typing import Union, Optional
import platform

class TikTok:
    def __init__(self):
        self.headers = {
            'Accept-language': 'en',
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) '
                        'Version/4.0.4 Mobile/7B334b Safari/531.21.102011-10-16 20:23:10'
        }

        self.link = None
        self.result = None

        if platform.system() == 'Windows':
            asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

    async def init(self, link: Union[str] = None):
        """
        Initialize tiktok module client
        Note:
            Mandatory function to initialize tiktok module.
        
        Args:
            link (:obj:`str`): Link provided by user
        """
        self.link = link
        self.result = await self.fetch(self.link)

        

    @staticmethod
    def get_url(text: str) -> Union[str, None]:
        try:
            url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)

            if len(url) > 0:
                return url[0]
        except Exception as e:
            print('Error in get_url:', e)
            return None

    async def convert_share_urls(self, url: str):
        if '@' in url:
                print("this link is original, so it can't be formatted: {}".format(url))
                return url
        else:
            print('converting tiktok link...')
            try:
                    async with aiohttp.ClientSession() as session:
                        async with session.get(url, headers=self.headers, allow_redirects=False) as response:
                            if response.status == 301:
                                url = response.headers['Location'].split('?')[0] if '?' in response.headers[
                                    'Location'] else \
                                    response.headers['Location']
                                print('obtaining the original link successfully, the original link is: {}'.format(url))
                                return url
            except Exception as e:
                    print('could not get original link!')
                    print(e)
                    return None

    async def get_tiktok_video_id(self, original_url: str) -> Union[str, None]:
        """
        Returns: tiktok video id
        """
        try:
            original_url = await self.convert_share_urls(original_url)

            matches = re.findall('/(video|v|photo)/(\d+)', original_url)
            if matches:
                video_id = matches[0][1]
                return video_id
            else:
                print("No TikTok video ID found in the URL:", original_url)
                return None
        except Exception as e:
            print('Error getting TikTok video ID:', e)
            return None


    async def fetch(self, link: str) -> Union[str, None]:
        """
        Returns: RAW JSON TikTok API data
        """
        try:
            aweme_id = await self.get_tiktok_video_id(link)
            print(f'TikTok video id: {aweme_id}')
            url = f'https://api22-normal-c-useast2a.tiktokv.com/aweme/v1/feed/?aweme_id={aweme_id}'
                # print(url)
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        json = await response.json()
                        data = json['aweme_list'][0]

                        return(data)
                    else:
                        raise Exception('Failed to fetch')
        except Exception as e:
            raise e

    async def download_image(self, session, image_url, i, download_dir, media_dict):
        async with session.get(image_url) as response:
            if response.status == 200:
                image_data = await response.read()

                file_name = f'image_{i + 1}.jpg'
                file_path = f'{download_dir}/{file_name}'

                os.makedirs(os.path.dirname(file_path), exist_ok=True)

                with open(file_path, 'wb') as file:
                    file.write(image_data)

                print(f"Image {i + 1} downloaded and saved as '{file_path}'")
                media_dict[i] = file_path
            else:
                print(
                    f"Failed to download image {i + 1}. Status code: {response.status}")

    async def download_photos(self, download_dir: Optional[str] = None):
        """
        Async func to download photos (can be used with download_sound() )

        Args:
            download_dir (:obj:`str`): Where to store downloaded images (if None, then stores in video id named folder)
        """
        if download_dir == None:
            self.download_dir = self.result['aweme_id']
        else:
            self.download_dir = download_dir

        image_list = self.result['image_post_info']['images']
        images = []
        for image in image_list:
            display_image = image['display_image']['url_list'][0]
            if display_image:
                images.append(display_image)
        media_dict = {}
        async with aiohttp.ClientSession() as session:
            tasks = []
            for i, image_url in enumerate(images):
                tasks.append(asyncio.ensure_future(self.download_image(
                    session, image_url, i, download_dir, media_dict)))

            await asyncio.gather(*tasks)

        sorted_media = {k: v for k, v in sorted(
            media_dict.items(), key=lambda item: item[0])}
        return list(sorted_media.values())

    async def download_sound(self, audio_filename: Optional[str] = None):
        """
        Downloads sound from video/post

        Args:
            audio_filename(:obj:`str`): Name of the tiktok sound file (if None, then stores in sound name file),
        
        Returns: 
            file name.
        """
        if audio_filename == None:
            self.audio_filename = f"{self.result['music']['title']}.mp3"
        else:
            self.audio_filename = f'{audio_filename}.mp3'

        audio_url = self.result['music']['play_url']['url_list']
        cleaned_string = audio_url[0]

        async with aiohttp.ClientSession() as audio_session:
            async with audio_session.get(cleaned_string) as audio_response:
                if audio_response.status == 200:
                    audio_filename = self.audio_filename
                    audio_data = await audio_response.read()

                    with open(audio_filename, "wb") as audio_file:
                        audio_file.write(audio_data)
                        print("Sound downloaded successfully.")
                    return audio_filename
                else:
                    print(f"Error: {audio_response.status}")

    def construct_caption_posts(self):
        """
        Basic function to construct caption for some data |
        Returns: aweme id(video id), User nickname and unique id (username), video description and link
        """

        aweme_id = self.result['aweme_id']
        nickname = self.result['author']['nickname']
        unique = self.result['author']['unique_id']
        desc = self.result['desc'] if self.result['desc'] else 'No title'
        try:
            # video_url = result['video_data']['nwm_video_url_HQ']
            video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'
        except KeyError:
            video_url = None


        uploader_link = f'https://www.tiktok.com/@{unique}'

        image_caption = f"💬: <a href='{video_link}'>{desc}</a>\n\n👤: <a href='{uploader_link}'>{nickname}</a>"

        return f"{image_caption}"


    def construct_caption_audio(self):
        """
        same as construct_caption_posts but for audio
        """

        aweme_id = self.result['aweme_id']
        unique = self.result['author']['unique_id']
        video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'

        audio_title = self.result['music']['title']
        audio_caption = f'💬: <a href="{video_link}"> {audio_title}</a>'

        return f"{audio_caption}"

    async def download_video(self, video_filename: Optional[str] = None):
        """
        Async function to download tiktok video 

        Args:
            video_filename(:obj:`str`): Name of the tiktok video file (if None, then stores in video id named file)
        """
        video_url = self.result['video']['play_addr']['url_list'][0]
        if video_filename == None:
            self.video_filename = f"@damirtag sigma {self.result['aweme_id']}.mp4"
        else:
            self.video_filename = f'{video_filename}.mp4'

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status == 200:
                    with open(self.video_filename, 'wb') as f:
                        async for chunk in response.content.iter_any():
                            f.write(chunk)

                    print(f"Video downloaded and saved as {self.video_filename}")
                    return self.video_filename
                else:
                    return f"Failed to download the video. HTTP status: {response.status}"          
    

    def __del_photos__(self):
        shutil.rmtree(self.download_dir)
        print("[TikTok:photos] | %s has been removed successfully" % self.download_dir)
    def __del_video__(self):
        os.remove(self.video_filename)
        print("[TikTok:video] | %s has been removed successfully" % self.local_filename)
    def __del_sound__(self):
        os.remove(self.audio_filename)
        print("[TikTok:sound] | %s has been removed successfully" % self.audio_filename)
