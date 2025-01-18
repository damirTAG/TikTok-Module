import asyncio
from TikTok import TikTok, data


async def main():
    async with TikTok() as tt:
        # Download video
        result: data = await tt.download("https://vm.tiktok.com/ZMkHSh5t1/")
        print(f"Downloaded: {result.media}")

        # Download photo post and sound
        result: data = await tt.download(
            'https://www.tiktok.com/@dx_r13/photo/7398188624526724358', 
            'example-data/tiktok_images1'
            )
        print(f'Downloaded photo post to: {result.dir_name}')
        sound_filename = await tt.download_sound(
            'https://www.tiktok.com/@dx_r13/photo/7398188624526724358', 
            'example-data/goofy ahh sound'
            )
        print(f'Downloaded sound as: {sound_filename}')
        
        # Get tiktok post info (raw api response)
        info = await tt.fetch("https://www.tiktok.com/messages?lang=ru-RU")
        if info:
            print(f"Video title: {info.data.get('title', 'No title')}")
            print(f"Video duration: {info.data.get('duration', 0.0)}")
            print(f"Video download link: {info.data.get('play', 'No video link')}")
            print(f"Music download link: {info.data.get('music', 'No music link')}")
        
        # Search videos by keyword
        result = await tt.search(
                'keyword', 
                'jojo 7',
                count=5
            )
        if result:
            for idx, video in enumerate(result, start=1):
                print(f"{idx}. {video['title']}\n{video['play']}")

if __name__ == "__main__":
    asyncio.run(main())