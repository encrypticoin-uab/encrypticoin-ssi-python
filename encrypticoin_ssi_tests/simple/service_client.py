import aiohttp
from aiohttp import CookieJar


class SimpleServiceClientMock:
    def __init__(self, base_url: str = "http://127.0.0.1:8000"):
        self.session = aiohttp.ClientSession(cookie_jar=CookieJar(unsafe=base_url.find("127.0.0.1") >= 0))
        self.base_url = base_url

    async def close(self):
        await self.session.close()

    async def wallet_challenge(self) -> str:
        async with self.session.post(self.base_url + "/wallet-challenge") as r:
            r.raise_for_status()
            return (await r.json())["message"]

    async def submit_signature(self, signature: str) -> str:
        async with self.session.post(self.base_url + "/submit-signature", json={"signature": signature}) as r:
            r.raise_for_status()
            return (await r.json())["address"]

    async def buy(self, item: str) -> dict:
        async with self.session.post(self.base_url + "/buy", json={"item": item}) as r:
            r.raise_for_status()
            return await r.json()
