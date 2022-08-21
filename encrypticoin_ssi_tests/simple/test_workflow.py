import asyncio
import subprocess
import sys

import pytest
from eth_account import Account
from eth_account.messages import encode_defunct

from encrypticoin_ssi_tests.simple.service_client import SimpleServiceClientMock


@pytest.fixture
def server_p():
    # NOTE: Production server must be served over HTTPS, but here it will bind to `http://127.0.0.1:8000`.
    server_p = subprocess.Popen([sys.executable, "-m", "encrypticoin_ssi_tests.simple.service_server"])
    try:
        yield server_p
    finally:
        if server_p.poll() is None:
            server_p.terminate()
            server_p.wait()


@pytest.mark.asyncio
async def test_simple_workflow(server_p):
    # naive wait for the mock server to start
    await asyncio.sleep(1)
    assert server_p.poll() is None

    a = Account()
    wallet0 = a.create()  # crypto wallet of the user

    client0 = SimpleServiceClientMock()  # service-client and session of user
    assert await client0.buy("thing-a") == {"item": "thing-a", "attribution": False}  # buy has no token attribution

    message0 = await client0.wallet_challenge()  # ask the service-server for a wallet-sign challenge message
    # NOTE: Signing the message would be done by the crypto-wallet handler extension of the browser, like MetaMask.
    signature0 = wallet0.sign_message(encode_defunct(message0.encode("utf-8"))).signature.hex()  # sign the message

    assert await client0.submit_signature(signature0) == wallet0.address  # the server shall recover the wallet address

    # server authenticated the wallet for the session, and can grant attribution if the balance reaches a threshold
    assert await client0.buy("thing-b") == {
        "item": "thing-b",
        "address": wallet0.address,
        "balance": "0",
        "decimals": 18,
        "attribution": False,
    }
