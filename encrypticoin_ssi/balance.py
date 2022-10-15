from decimal import Decimal


class TokenBalance:
    __slots__ = ("address", "balance", "decimals")

    def __init__(self, address: str, balance: str, decimals: int):
        self.address = address
        self.balance = balance
        self.decimals = decimals

    def has_attribution(self) -> bool:
        """
        Whether the wallet has enough tokens for attribution or not.
        """
        return bool(self.as_integer())

    def as_integer(self) -> int:
        """
        Balance of "whole" tokens.
        """
        tmp = self.balance[: -self.decimals]
        if tmp:
            return int(tmp)
        return 0

    def as_float(self) -> float:
        """
        Limited precision balance of the token.
        """
        return float(self.as_decimal())

    def as_decimal(self) -> Decimal:
        """
        Exact precision balance of the token.
        """
        return Decimal(self.balance) / 10**self.decimals
