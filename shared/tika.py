import os

from aiohttp import ClientSession


async def tika_ocr(data):
    async with ClientSession(
        base_url=os.getenv('TIKA', 'http://127.0.0.1:9998'),
        headers={'X-Tika-OCRLanguage': 'pol+eng'}
    ) as client:
        async with client.put(
            '/tika/text',
            data=data,
        ) as response:
            payload: dict = await response.json()

    return payload.pop('X-TIKA:content').strip(), payload
