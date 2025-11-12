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
ffmpeg-python
```

## Installation

Just manually copy full code from:
https://raw.githubusercontent.com/damirTAG/TikTok-Module/main/TikTok.py

## Usage

[See the list of examples here](https://github.com/damirtag/tiktok-module/blob/main/Example.py)

### In Telegram bot libraries example usage:

#### Telethon Example

```python
from telethon import TelegramClient, events
from tiktok import TikTok

# Initialize your Telegram client
api_id = 'your_api_id'
api_hash = 'your_api_hash'
bot_token = 'your_bot_token'

client = TelegramClient('bot_session', api_id, api_hash).start(bot_token=bot_token)
tiktok = TikTok()

@client.on(events.NewMessage(pattern='/tt'))
async def handle_tiktok_command(event):
    try:
        # Get TikTok link from message
        tiktok_link = event.text.split()[1]

        # Download the TikTok content
        result = await tiktok.download(tiktok_link, hd=True)

        # Send the downloaded content
        if result.type == 'video':
            await client.send_file(
                event.chat_id,
                result.media[0],
                caption=f"Downloaded from: {tiktok_link}"
            )
        else:  # Photos
            for photo in result.media:
                await client.send_file(
                    event.chat_id,
                    result.media,
                    caption=f"Downloaded from: {tiktok_link}",
                    reply_to=event.message.id,
                    force_document=False,
                    allow_cache=False
                )

    except Exception as e:
        await event.reply(f"Error downloading TikTok content: {str(e)}")

# Run the client
client.run_until_disconnected()
```

#### Aiogram Example

```python
from aiogram import Bot, Dispatcher, types
from aiogram.filters.command import Command
from tiktok import TikTok
import asyncio

# Initialize bot and dispatcher
bot = Bot(token='your_bot_token')
dp = Dispatcher()
tiktok = TikTok()

@dp.message(Command('tt'))
async def handle_tiktok_command(message: types.Message):
    try:
        # Get TikTok link from message
        command_parts = message.text.split()
        if len(command_parts) != 2:
            await message.reply("Please provide a TikTok link after the command")
            return

        tiktok_link = command_parts[1]

        # Send "processing" message
        processing_msg = await message.reply("Downloading TikTok content...")

        # Download the TikTok content
        result = await tiktok.download(tiktok_link, hd=True)

        # Send the downloaded content
        if result.type == 'video':
            await message.reply_video(
                video=types.FSInputFile(result.media[0]),
                caption=f"Downloaded from: {tiktok_link}"
            )
        else:  # Photos
            media_group = []
            for photo in result.media:
                media_group.append(
                    types.InputMediaPhoto(
                        media=types.FSInputFile(photo)
                    )
                )
            # Set caption for the first photo
            if media_group:
                media_group[0].caption = f"Downloaded from: {tiktok_link}"

            await message.reply_media_group(media=media_group)

        # Delete processing message
        await processing_msg.delete()

    except Exception as e:
        await message.reply(f"Error downloading TikTok content: {str(e)}")

async def main():
    await dp.start_polling(bot)

if __name__ == '__main__':
    asyncio.run(main())
```
