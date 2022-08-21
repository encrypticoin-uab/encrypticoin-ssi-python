from decimal import Decimal

from encrypticoin_ssi.balance import TokenBalance
from encrypticoin_ssi.balance_change import TokenBalanceChange
from encrypticoin_ssi.message import ProofMessageFactory


def test_token_balance_object():
    tb = TokenBalance("addr", "125", 18)
    assert tb.as_integer() == 0
    assert tb.as_float() == 1.25e-16
    assert tb.as_decimal() == Decimal("1.25e-16")
    tb = TokenBalance("addr", "125", 2)
    assert tb.as_integer() == 1
    assert tb.as_float() == 1.25
    assert tb.as_decimal() == Decimal("1.25")
    tb = TokenBalance("addr", "125000000000000", 18)
    assert tb.as_integer() == 0
    assert tb.as_float() == 0.000125
    assert tb.as_decimal() == Decimal("0.000125")
    tb = TokenBalance("addr", "901000250000000000037", 18)
    assert tb.as_integer() == 901
    assert tb.as_float() == 901.00025
    assert tb.as_decimal() == Decimal("901.000250000000000037")
    tb = TokenBalance("addr", "901000250000000000037", 20)
    assert tb.as_integer() == 9
    assert tb.as_float() == 9.0100025
    assert tb.as_decimal() == Decimal("9.01000250000000000037")
    tb = TokenBalance("addr", "999090000000000000", 18)
    assert tb.as_integer() == 0
    assert tb.as_float() == 0.99909
    assert tb.as_decimal() == Decimal("0.99909")

    assert issubclass(TokenBalanceChange, TokenBalance)


def test_message_factory():
    desc = "Wallet ownership proof for token attribution by linking to account at XY Company."
    pmf = ProofMessageFactory(desc)
    assert pmf.description == desc
    msg = "%s\nId: id" % (desc,)
    assert pmf.create("id") == msg
    assert pmf.extract_id(msg) == "id"
    assert pmf.extract_id("asd") is None
    assert pmf.extract_id("asd\nId: id") is None
