import httpx
import asyncio

async def test():
    async with httpx.AsyncClient() as client:
        r = await client.post('https://tmpfiles.org/api/v1/upload', files={'file': ('test.txt', b'hello world', 'text/plain')})
        print(r.json())

asyncio.run(test())
