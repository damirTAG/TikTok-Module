# TikTok Module

## Introduction

This is a simple Python module for interacting with the TikTok API. It provides functionality to fetch TikTok video data, download videos, and extract audio from videos.
Perfect for using in telegram bots/userbots

## Features

-   Fully async
-   Fetch TikTok video data including video/image details, user information, and sound details.
-   Download TikTok videos/images directly from the API.
-   Extract audio from TikTok videos and save them as MP3 files.
-   Search for videos by keywords and search for hashtags

## Requirements

See <a href='https://github.com/damirTAG/TikTok-Module/blob/main/requirements.txt'>requirements.txt</a>

## Installation

You can install this project directly from GitHub using pip. Run the following command in your terminal:

```bash
pip install git+https://github.com/damirTAG/TikTok-Module.git
```

## [Usage](https://github.com/damirtag/tiktok-module/blob/main/Example.py)

### Download Images

```py
import asyncio
from TikTok import TikTok


# Download Images from link
async def main(link: str) -> dict:
    try:
        tt = TikTok()
        await tt.init(link)

        await tt.download_photos('TikTok post image')
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main(link=input("TikTok link: ")))
```

### Download Video

```py
import asyncio
from TikTok import TikTok

async def main(link: str) -> dict:
    try:
        tt = TikTok()
        await tt.init(link)

        await tt.download_video('my installed tiktok video')
        # Download in HD
        await tt.download_video('my installed tiktok video in HD', hd=True)
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main(link=input("TikTok link: ")))
```

### Get raw JSON data

```py
import asyncio
from TikTok import TikTok

async def main(link: str) -> dict:
    try:
        tt = TikTok()
        await tt.init(link)

        data = await tt.fetch(link)
        print(data)
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main(link=input("TikTok link: ")))
```

### Search method

```py
import asyncio
from TikTok import TikTok

async def main():
    try:
        tt = TikTok()

        by_keyword = await tt.search('keyword', 'bleach', 3)
        print('Data by searching video (keyword):\n')
        print(by_keyword)

        by_hashtag = await tt.search('hashtag', 'jojo')
        print('Data searching for hashtags (challenges):\n')
        print(by_hashtag)
    except Exception as e:
        print(f'error: {e}')

asyncio.run(main())
```

## Contributing

Contributions are welcome! Feel free to open issues or pull requests to improve the TikTok module. Please ensure that your contributions align with the project's coding standards and guidelines.

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/damirtag/tiktok-module/blob/main/LICENSE.MD) file for details.
