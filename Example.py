import asyncio
from TikTok import TikTok


# Doing stuff...
async def main(link: str) -> dict:
    try:
        tiktok = TikTok()

        by_keyword = await tiktok.search('keyword', 'bleach', 3)
        print('Data by searching video (keyword):\n')
        print(by_keyword)

        by_hashtag = await tiktok.search('hashtag', 'jojo')
        print('Data searching for hashtags (challenges):\n')
        print(by_hashtag)

        await tiktok.init(link)
            
        # Fetch and print the raw data
        print("Raw TikTok Data:")
        print(tiktok.result)
            
        # Download photos
        try:
            photos = await tiktok.download_photos()
            print("\nDownloaded Photos:")
            print(photos)
        except KeyError:
            print('No photos found, skipping')
            
        # Download sound
        sound = await tiktok.download_sound()
        print("\nDownloaded Sound:")
        print(sound)
            
        # Download video
        try:
            video = await tiktok.download_video()
            print("\nDownloaded Video:")
            print(video)
        except KeyError:
            print('No videos found, skipping')
            
        # Construct captions (WARNING!: in HTML markdown)
        caption_posts = tiktok.construct_caption_posts()
        print("\nConstructed Caption for Posts:")
        print(caption_posts)
            
        caption_audio = tiktok.construct_caption_audio()
        print("\nConstructed Caption for Audio:")
        print(caption_audio)
    finally:
        await tiktok.close_session()

asyncio.run(main(link=input("TikTok link: ")))