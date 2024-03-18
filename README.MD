# TikTok Module

## Introduction

This is a simple Python module for interacting with the TikTok API. It provides functionality to fetch TikTok video data, download videos, and extract audio from videos.
Perfect for using in telegram bots/userbots

## Features

-   Fetch TikTok video data including video details, user information, and music details.
-   Download TikTok videos directly from the API.
-   Extract audio from TikTok videos and save them as MP3 files.

## Requirements

-   Python 3.6+
-   aiohttp library

## [Usage](https://github.com/damirtag/tiktok-module/blob/main/Example.py)
```py
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
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to improve the TikTok module. Please ensure that your contributions align with the project's coding standards and guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/damirtag/tiktok-module/blob/main/LICENSE.MD) file for details.
