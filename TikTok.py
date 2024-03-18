import aiohttp, re, asyncio, os, shutil
from typing import Union

class TikTok:
    def __init__(self, link: str) -> None:
        self.link = link
        self.headers = {
            'Accept-language': 'en',
            'User-Agent': 'Mozilla/5.0 (iPad; U; CPU OS 3_2 like Mac OS X; en-us) AppleWebKit/531.21.10 (KHTML, like Gecko) '
                        'Version/4.0.4 Mobile/7B334b Safari/531.21.102011-10-16 20:23:10'
        }
        self.result = None
        self.download_dir = None
        self.local_filename = None
        self.file_name = None

    async def initialize(self):
        self.result = await self.fetch(self.link)
        self.download_dir = self.result['aweme_list'][0]['aweme_id']
        self.local_filename = f"{self.result['aweme_list'][0]['aweme_id']}.mp4"
        self.file_name = f"audio/{self.result['aweme_list'][0]['music']['title']}.mp3"

    @staticmethod
    def get_url(text: str) -> Union[str, None]:
        try:
            url = re.findall('http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\(\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', text)

            if len(url) > 0:
                return url[0]
        except Exception as e:
            print('Error in get_url:', e)
            return None

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

    async def download_photos(self):
        """
        Async func to download photos (can be user with download_sound() )
        """
        download_dir = self.download_dir

        image_list = self.result['aweme_list'][0]['image_post_info']['images']
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

    async def download_sound(self):
        """
        Downloads sound from video/post \n
        Return file name!
        """
        audio_url = self.result['aweme_list'][0]['music']['play_url']['url_list']
        cleaned_string = audio_url[0]

        async with aiohttp.ClientSession() as audio_session:
            async with audio_session.get(cleaned_string) as audio_response:
                if audio_response.status == 200:
                    file_name = self.file_name
                    audio_data = await audio_response.read()

                    with open(file_name, "wb") as audio_file:
                        audio_file.write(audio_data)
                        print("Sound downloaded successfully.")
                    return file_name
                else:
                    print(f"Error: {audio_response.status}")

    def construct_caption_posts(self):
        """
        Basic function to construct caption for some data | \n
        Returns: aweme id(video id), User nickname and unique id (username), video description and link
        """
        aweme_id = self.result['aweme_list'][0]['aweme_id']
        nickname = self.result['aweme_list'][0]['author']['nickname']
        unique = self.result['aweme_list'][0]['author']['unique_id']
        desc = self.result['aweme_list'][0]['desc'] if self.result['aweme_list'][0]['desc'] else 'No title'
        try:
            # video_url = result['video_data']['nwm_video_url_HQ']
            video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'
        except KeyError:
            video_url = None


        uploader_link = f'https://www.tiktok.com/@{unique}'

        image_caption = f"💬: ({video_link}) | {desc}\n\n👤:({uploader_link}) | {nickname}</a>"

        return f"{image_caption}"


    def construct_caption_audio(self):
        """
        same as construct_caption_posts but for audio
        """
        aweme_id = self.result['aweme_list'][0]['aweme_id']
        unique = self.result['aweme_list'][0]['author']['unique_id']
        video_link = f'https://www.tiktok.com/@{unique}/video/{aweme_id}'

        audio_title = self.result['aweme_list'][0]['music']['title']
        audio_caption = f'💬: <a href="{video_link}"> {audio_title}</a>'

        return f"{audio_caption}"

    async def download_video(self):
        video_url = self.result['aweme_list'][0]['video']['play_addr']['url_list'][0]

        async with aiohttp.ClientSession() as session:
            async with session.get(video_url) as response:
                if response.status == 200:
                    with open(self.local_filename, 'wb') as f:
                        async for chunk in response.content.iter_any():
                            f.write(chunk)

                    print(f"Video downloaded and saved as {self.local_filename}")
                    return self.local_filename
                else:
                    return f"Failed to download the video. HTTP status: {response.status}"

                
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

    async def fetch(self, link):
        """
        Gets tiktok link and then returns raw json data list from API
        """
        try:
            conv_link = await self.convert_share_urls(link)
            match = re.search(r'/(\d+)$', conv_link)
            if match:
                aweme_id = match.group(1)
                print(aweme_id)
                url = f'https://api22-normal-c-useast2a.tiktokv.com/aweme/v1/feed/?aweme_id={aweme_id}'
                print(url)
                async with aiohttp.ClientSession() as session:
                    async with session.get(url) as response:
                        if response.status == 200:
                            data = await response.json()

                            return(data)
                        else:
                            raise Exception('Failed to fetch')
            else:
                print("No match found")
        except Exception as e:
            return e
        
    def __del_photos__(self):
        shutil.rmtree(self.download_dir)
        print("Photos | %s has been removed successfully" % self.download_dir)
    def __del_video__(self):
        os.remove(self.local_filename)
        print("Video | %s has been removed successfully" % self.local_filename)
    def __del_sound__(self):
        os.remove(self.file_name)
        print("Sound | %s has been removed successfully" % self.file_name)

            

