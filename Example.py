import asyncio
from TikTok import TikTok


# Download Images from link
async def main(link: str) -> dict:
    try:
        tt_module = TikTok(link)
        await tt_module.initialize()

        await tt_module.download_photos()
        print('Images downloaded successfully')
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main(link=input("TikTok link: ")))