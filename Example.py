import asyncio
from TikTok import TikTok


# Download Images from link
async def main(link: str) -> dict:
    try:
        tt_module = TikTok()
        await tt_module.init(link)

        await tt_module.download_photos('TikTok post image')
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main(link=input("TikTok link: ")))