import asyncio
import os
import time

import aiohttp
from starlette.applications import Starlette
from starlette.exceptions import HTTPException
from starlette.middleware import Middleware
from starlette.middleware.sessions import SessionMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse
from starlette.routing import Route

from encrypticoin_ssi.client import ServerIntegrationClient
from encrypticoin_ssi.error import BackoffError, IntegrationError, SignatureValidationError, TrackingSessionReset
from encrypticoin_ssi.message import ProofMessageFactory

tia = ServerIntegrationClient()
msg_factory = ProofMessageFactory("Wallet ownership proof for token attribution at TrackingTest web-shop.")
collector_task: asyncio.Task = None
# NOTE: The wallet balances shall be saved and recalled from a persistent storage in a production system.
wallet_balances = dict()


async def _on_startup():
    global collector_task
    await tia.setup()
    collector_task = asyncio.create_task(_collector())


async def _on_shutdown():
    collector_task.cancel()
    try:
        await collector_task
    except asyncio.CancelledError:
        pass
    await tia.close()


async def _collector():
    """
    The token changes collector is implemented as an asynchronous task inside the mock server in this example.

    For a production implementation it should be a separate process on the server side that is run in a single
    instance. The collection index (since) and the wallet balance changes should be persisted in a database.
    """
    since = 0
    session = None
    while True:
        try:
            changes = await tia.token_changes(since, session)
        except BackoffError:
            await asyncio.sleep(5)
            continue
        except TrackingSessionReset as e:  # Change tracking stream reset.
            wallet_balances.clear()
            since = 0
            session = e.new_session
            continue
        except (IntegrationError, aiohttp.ClientError):
            # NOTE: depending on implementation general and unknown errors may abort the collector process
            await asyncio.sleep(5)
            continue
        if not changes:  # no updates
            await asyncio.sleep(5)
            continue
        for change in changes:
            # Depending on the server-system and service requirements, these changes can be recorded into a database.
            # The database updates can propagate the change as events in the specific system and ensure that all
            # services will adapt to the new state: granting or revoking attribution to an account for example.
            wallet_balances[change.address] = change
            since = change.id + 1
            # NOTE: The `session` has to be saved as well with the `since` to continue later.


def wallet_challenge(request: Request):
    # NOTE: The message_id value is protected in the server-side session storage from manipulation, we only need
    # to include a timestamp and make the value unique.
    message_id = "-".join([str(time.time()), os.urandom(16).hex()])
    request.session["message_id"] = message_id
    return JSONResponse({"message": msg_factory.create(message_id)})


async def submit_signature(request: Request):
    params = await request.json()
    if not isinstance(params, dict) or not isinstance(params.get("signature"), str):
        raise HTTPException(400, "signature missing")
    try:
        message_id = request.session.pop("message_id")
    except KeyError:
        raise HTTPException(400, "no message_id set up")
    if float(message_id.partition("-")[0]) + 5 < time.time():
        raise HTTPException(400, "message_id expired")
    try:
        address = await tia.wallet_by_signed(msg_factory.create(message_id), params["signature"])
    except SignatureValidationError:
        raise HTTPException(400, "signature invalid")
    except (IntegrationError, aiohttp.ClientError):
        raise HTTPException(500)
    # NOTE: In this test, the session gets the address permanently. In a production system, it shall be
    # saved to the authenticated user's account (as discussed in the "continuous workflow").
    request.session["address"] = address
    # NOTE: The service-client shall hide some part of the address using an ellipsis for safety if it displays the
    # address. See MetaMask for example.
    return JSONResponse({"address": address})


async def buy(request: Request):
    # NOTE: In this test the "attribution-check" is embedded into the "purchase" step, but in a web-shop it would
    # likely be desired to have it as a separate endpoint as well to see if the wallet provides attribution right
    # after the ownership proof is checked.
    params = await request.json()
    if not isinstance(params, dict) or not isinstance(params.get("item"), str):
        raise HTTPException(400, "item missing")
    sale = {"item": params["item"]}
    address = request.session.get("address")
    # NOTE: Instead of calling the `token-balance` api-server endpoint, the service-server has all the
    # balances at hand by the collector process.
    if address and address in wallet_balances:
        tb = wallet_balances[address]
        sale["attribution"] = tb.has_attribution()
        # NOTE: The following are returned for testing purposes only. In a production system, these are not necessary
        # to be returned to the service-client and may be sensitive for the user to be displayed in the browser.
        sale["address"] = tb.address
        sale["balance"] = tb.balance
        sale["decimals"] = tb.decimals
    else:
        sale["attribution"] = False
    return JSONResponse(sale)


async def debug_wallet_changes(request: Request):
    return JSONResponse({wb.address: wb.balance for wb in wallet_balances.values()})


app = Starlette(
    debug=True,
    on_startup=[_on_startup],
    on_shutdown=[_on_shutdown],
    middleware=[
        # NOTE: Session storage is with random key and no https-only as this is purely for testing functionality.
        Middleware(SessionMiddleware, secret_key=os.urandom(32).hex()),
    ],
    routes=[
        Route("/wallet-challenge", wallet_challenge, methods=["POST"]),
        Route("/submit-signature", submit_signature, methods=["POST"]),
        Route("/buy", buy, methods=["POST"]),
        Route("/debug-wallet-changes", debug_wallet_changes, methods=["GET"]),
    ],
)
