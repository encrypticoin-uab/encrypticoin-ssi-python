from encrypticoin_ssi_tests.simple.service_client import SimpleServiceClientMock


class TrackingServiceClientMock(SimpleServiceClientMock):
    async def debug_wallet_changes(self) -> dict:
        async with self.session.get(self.base_url + "/debug-wallet-changes") as r:
            r.raise_for_status()
            return await r.json()
