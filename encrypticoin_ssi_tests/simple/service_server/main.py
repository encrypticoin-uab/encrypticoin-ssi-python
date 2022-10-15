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
from encrypticoin_ssi.error import SignatureValidationError, IntegrationError
from encrypticoin_ssi.message import ProofMessageFactory

tia = ServerIntegrationClient()
msg_factory = ProofMessageFactory("Wallet ownership proof for token attribution at SimpleTest web-shop.")


async def _on_startup():
    await tia.setup()


async def _on_shutdown():
    await tia.close()


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
    # NOTE: In this test, the session gets the address permanently. In a production system, either it must be tied to
    # the current action (purchase) or there must be some expiration implemented to force the service-client to
    # re-validate their wallet-ownership frequently.
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
    if address:
        try:
            tb = await tia.token_balance(address)
        except (IntegrationError, aiohttp.ClientError):
            raise HTTPException(500)
        sale["attribution"] = tb.has_attribution()
        # NOTE: The following are returned for testing purposes only. In a production system, these are not necessary
        # to be returned to the service-client and may be sensitive for the user to be displayed in the browser.
        sale["address"] = tb.address
        sale["balance"] = tb.balance
        sale["decimals"] = tb.decimals
    else:
        sale["attribution"] = False
    return JSONResponse(sale)


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
    ],
)
