from typing import Optional


class ProofMessageFactory:
    """
    Simple crypto-wallet ownership message body creation utility.
    The message to be signed by the client is actually arbitrary, but this is the baseline recommendation for:
        - Having a short human-readable description for transparency.
        - Including an arbitrary identifier managed by the server.
    """

    __slots__ = ("description",)

    def __init__(self, description: str):
        """
        Description should be a concise explanation for the signature request. For example:
            - Wallet ownership proof for token attribution at XY web-shop.
            - Wallet ownership proof for token attribution by linking to account at XY web-shop.
        """
        self.description = description

    def create(self, message_id: str) -> str:
        """
        Use this to produce a message to be sent to the service-client.
        The `message_id` must be secure against multiple use and unauthorized use. To this end, it should be
        a secure random value bound to the session of the user.
        For more information see the "Integration requirements" of `/wallet-by-signed` for more info.
        """
        return "%s\nId: %s" % (self.description, message_id)

    def extract_id(self, maybe_message: str) -> Optional[str]:
        """
        Try to recover the `message_id` from a message.
        """
        id_prefix = "%s\nId: " % (self.description,)
        if maybe_message.startswith(id_prefix):
            return maybe_message[len(id_prefix) :]
