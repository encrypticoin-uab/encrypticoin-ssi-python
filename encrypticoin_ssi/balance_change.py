from encrypticoin_ssi.balance import TokenBalance


class TokenBalanceChange(TokenBalance):
    __slots__ = ("id",)

    def __init__(self, id_: int, address: str, balance: str, decimals: int):
        TokenBalance.__init__(self, address, balance, decimals)
        self.id = id_
