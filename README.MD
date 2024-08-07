# TikTok Module

## Introduction

This is a simple Python module for interacting with the TikTok API by TikWM.

It provides functionality to fetch TikTok video data, download videos, and extract audio from videos.
Perfect for using in telegram bots/userbots, I made it for my bots so you can easily integrate it to your projects.

TikWM Free API limit: 5.000 requests per day for one IP adress.

## Features

-   Fully async [`aiohttp` | `asyncio`].
-   Parse TikTok videos by receiving JSON data.
-   Helps to download videos/images/sounds.
-   Search for videos by keywords and search for hashtags.

## Requirements

```txt
aiohttp==3.8.1
asyncio==3.4.3
tqdm==4.62.3
tenacity==8.2.3
```

## Installation

Just manually copy full code from:
https://raw.githubusercontent.com/damirTAG/TikTok-Module/main/TikTok.py

## How to use?

[See the list of examples here](https://github.com/damirtag/tiktok-module/blob/main/Example.py)

## License

This project is licensed under the MIT License - see the [LICENSE](https://github.com/damirtag/tiktok-module/blob/main/LICENSE.MD) file for details.
