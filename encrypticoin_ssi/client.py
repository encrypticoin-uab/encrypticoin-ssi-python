from typing import List, Tuple, Dict, Any

import aiohttp

from encrypticoin_ssi.balance import TokenBalance
from encrypticoin_ssi.balance_change import TokenBalanceChange
from encrypticoin_ssi.error import BackoffError, SignatureValidationError, IntegrationError


class ServerIntegrationClient:
    """
    Lightweight client to the integration REST API.
    """

    __slots__ = ("session", "url_base")

    def __init__(self, session: aiohttp.ClientSession = None, domain: str = "etalon.cash", api_path: str = "/tia"):
        self.session = session
        self.url_base = "https://%s%s" % (domain, api_path)

    async def setup(self):
        if self.session is None:
            self.session = aiohttp.ClientSession()

    async def close(self):
        await self.session.close()
        self.session = None

    async def wallet_by_signed(self, message: str, signature: str) -> str:
        """
        Query the API server for the validation and recovery of the crypto-wallet address that has signed the message.
        The recovered address (if successfully retrieved) is in checksum format.
        """
        async with self.session.post(
            self.url_base + "/wallet-by-signed", json={"message": message, "signature": signature}
        ) as r:
            if r.status == 429:
                raise BackoffError()
            elif r.status == 400:  # This indicates client error or invalid arguments.
                raise SignatureValidationError()
            elif r.status != 200:
                raise IntegrationError()
            try:
                result = await r.json()
            except (TypeError, ValueError):
                raise IntegrationError()
            if not isinstance(result, dict) or not isinstance(result.get("address"), str):
                raise IntegrationError()
            return result["address"]

    async def token_balance(self, address: str) -> TokenBalance:
        """
        Get the balance of tokens in the crypto-wallet by address.
        The address value is case-sensitive, it must be in proper checksum format.
        """
        async with self.session.post(self.url_base + "/token-balance", json={"address": address}) as r:
            if r.status == 429:
                raise BackoffError()
            elif r.status != 200:
                raise IntegrationError()
            try:
                result = await r.json()
                return TokenBalance(address, result["balance"], result["decimals"])
            except (AttributeError, TypeError, ValueError):
                raise IntegrationError()

    async def token_changes(self, since: int) -> List[TokenBalanceChange]:
        """
        Get the token balance changes from the `since` number.
        The next query shall be made with `changes[-1].id + 1`, or repeated with `since` if no changes were retrieved.
        """
        async with self.session.post(self.url_base + "/token-changes", json={"since": since}) as r:
            if r.status == 429:
                raise BackoffError()
            elif r.status != 200:
                raise IntegrationError()
            changes = []
            try:
                result = await r.json()
                decimals = int(result["decimals"])
                for change in result["changes"]:
                    changes.append(TokenBalanceChange(change["id"], change["address"], change["balance"], decimals))
            except (AttributeError, TypeError, ValueError):
                raise IntegrationError()
            return changes

    async def contract_info(self) -> Dict[str, Any]:
        """
        Get some info about the contract. The returned keys are currently `contract_address` and `block_number`.
        """
        async with self.session.get(self.url_base + "/contract-info") as r:
            if r.status == 429:
                raise BackoffError()
            elif r.status != 200:
                raise IntegrationError()
            try:
                return await r.json()
            except (TypeError, ValueError):
                raise IntegrationError()
