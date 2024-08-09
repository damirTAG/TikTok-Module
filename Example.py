import asyncio
from TikTok import TikTok  # Assuming your TikTok class is implemented in 'TikTok.py' or you can name it as you want

async def main():
    # Initialize TikTok instance
    tiktok = TikTok()

    # Example 1: Download video
    try:
        await tiktok.download('https://www.tiktok.com/@p1lotless/video/7382314053496098053', hd=True)
    except Exception as e:
        print(f"Error downloading video: {e}")

    # Example 2: Download photos and sound
    try:
        await tiktok.download('https://www.tiktok.com/@dx_r13/photo/7398188624526724358', 'example-data/tiktok_images1')
        await tiktok.download_sound('https://www.tiktok.com/@dx_r13/photo/7398188624526724358', 'example-data/goofy ahh sound')
    except Exception as e:
        print(f"Error downloading photos: {e}")

    # Example 3: Search videos by keyword
    try:
        keyword = 'funny'
        videos = await tiktok.search(method="keyword", keyword=keyword, count=5)
        for idx, video in enumerate(videos, start=1):
            print(f"{idx}. {video['title']}\n{video['play']}")
    except Exception as e:
        print(f"Error searching videos: {e}")

    # Example 4: Search hashtags
    try:
        hashtag = 'dance'
        challenges = await tiktok.search(method="hashtag", keyword=hashtag, count=5)
        for idx, challenge in enumerate(challenges, start=1):
            print(f"{idx}. #{challenge['cha_name']}\nUser count: {challenge['user_count']}\nView count: {challenge['view_count']}")
    except Exception as e:
        print(f"Error searching hashtags: {e}")

    await tiktok.close_session()
    print("Session closed.")

if __name__ == "__main__":
    asyncio.run(main())
