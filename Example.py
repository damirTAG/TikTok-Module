import asyncio
from TikTok import TikTok  # Assuming your TikTok class is implemented in 'TikTok.py' or you can name it as you want

async def main():
    # Initialize TikTok instance
    tiktok = TikTok()

    # Example 1: Download video
    try:
        await tiktok.init('https://www.tiktok.com/@p1lotless/video/7382314053496098053')
        video = await tiktok.download(hd=True)
        print(f"Downloaded video: {video.media}")
    except Exception as e:
        print(f"Error downloading video: {e}")

    # Example 2: Download photos
    try:
        await tiktok.init('https://www.tiktok.com/@arcadiabayalpha/photo/7375880582473043232')
        photo = await tiktok.download('tiktok_images1')
        print(f"Images downloaded to: {photo.dir_name}")
    except Exception as e:
        print(f"Error downloading photos: {e}")

    # Example 3: Search videos by keyword
    try:
        keyword = 'funny'
        videos = await tiktok.search(method="keyword", keyword=keyword, count=5)
        print(f"Found {len(videos)} videos for keyword '{keyword}':")
        for idx, video in enumerate(videos, start=1):
            print(f"{idx}. {video['title']}\n{video['play']}")
    except Exception as e:
        print(f"Error searching videos: {e}")

    # Example 4: Search hashtags
    try:
        hashtag = 'dance'
        challenges = await tiktok.search(method="hashtag", keyword=hashtag, count=5)
        print(f"Found {len(challenges)} challenges for hashtag '{hashtag}':")
        for idx, challenge in enumerate(challenges, start=1):
            print(f"{idx}. #{challenge['cha_name']}\nUser count: {challenge['user_count']}\nView count: {challenge['view_count']}")
    except Exception as e:
        print(f"Error searching hashtags: {e}")

    await tiktok.close_session()
    print("Session closed.")

if __name__ == "__main__":
    asyncio.run(main())
