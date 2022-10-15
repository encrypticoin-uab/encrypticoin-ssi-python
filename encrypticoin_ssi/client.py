from typing import List, Dict, Any, Optional

import aiohttp

from encrypticoin_ssi.balance import TokenBalance
from encrypticoin_ssi.balance_change import TokenBalanceChange
from encrypticoin_ssi.error import BackoffError, SignatureValidationError, IntegrationError


class ServerIntegrationClient:
    """
    Lightweight client to the integration REST API.
    """

    __slots__ = ("session", "proxy_address", "url_base")

    @classmethod
    def create_url_base(cls, domain: str = "etalon.cash", api_path: str = "/tia"):
        return "https://%s%s" % (domain, api_path)

    def __init__(
        self,
        session: aiohttp.ClientSession = None,
        domain: str = "etalon.cash",
        api_path: str = "/tia",
        proxy_address: Optional[str] = None,
    ):
        self.session = session
        self.url_base = self.create_url_base(domain, api_path)
        self.proxy_address = proxy_address

    async def setup(self, session: aiohttp.ClientSession = None):
        """
        A customized session may be provided for use.
        """
        if self.session is None:
            if session is None:
                session = aiohttp.ClientSession()
            self.session = session

    async def close(self):
        await self.session.close()
        self.session = None

    async def wallet_by_signed(self, message: str, signature: str) -> str:
        """
        Query the API server for the validation and recovery of the crypto-wallet address that has signed the message.
        The recovered address (if successfully retrieved) is in checksum format.
        """
        async with self.session.post(
            self.url_base + "/wallet-by-signed",
            json={"message": message, "signature": signature},
            proxy=self.proxy_address,
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
        async with self.session.post(
            self.url_base + "/token-balance", json={"address": address}, proxy=self.proxy_address
        ) as r:
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
        Call this periodically (every 10-20 seconds) to get the changes incrementally.
        The next query shall be made with `changes[-1].id + 1`, or repeated with `since` if no changes were retrieved.
        """
        async with self.session.post(
            self.url_base + "/token-changes", json={"since": since}, proxy=self.proxy_address
        ) as r:
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
        Get some info about the contract.
        The returned keys are currently `contract_address`, `block_number` and `decimals`.
        """
        async with self.session.get(self.url_base + "/contract-info", proxy=self.proxy_address) as r:
            if r.status == 429:
                raise BackoffError()
            elif r.status != 200:
                raise IntegrationError()
            try:
                return await r.json()
            except (TypeError, ValueError):
                raise IntegrationError()
