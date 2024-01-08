import asyncio

import aiohttp

from encrypticoin_ssi.client import ServerIntegrationClient
from encrypticoin_ssi.error import BackoffError, IntegrationError, TrackingSessionReset


async def main():
    tia = ServerIntegrationClient()
    await tia.setup()
    wallet_balances = {}
    try:
        since = 0
        session = None
        while True:
            try:
                changes = await tia.token_changes(since, session)
            except BackoffError:
                print("Backoff")
                await asyncio.sleep(5)
                continue
            except TrackingSessionReset as e:
                if session is None:
                    session = e.new_session
                    print("Session:", session)
                    continue
                raise e
            except (IntegrationError, aiohttp.ClientError) as e:
                print("Error", e)
                # NOTE: depending on implementation general and unknown errors may abort the collector process
                await asyncio.sleep(5)
                continue
            if not changes:  # no updates
                print("End")
                print("Final:", sorted(wallet_balances.keys()))
                break
                # await asyncio.sleep(5)
                # continue
            for change in changes:
                if change.has_attribution():
                    wallet_balances[change.address] = change.as_float()
                    print(" - add", change.address)
                else:
                    wallet_balances.pop(change.address, None)
                    print(" - rem", change.address)
                since = change.id + 1
    finally:
        await tia.close()


if __name__ == "__main__":
    asyncio.run(main())
