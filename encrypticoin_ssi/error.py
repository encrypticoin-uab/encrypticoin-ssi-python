from typing import Optional


class IntegrationError(Exception):
    pass


class BackoffError(IntegrationError):
    pass


class SignatureValidationError(IntegrationError):
    pass


class TrackingSessionReset(IntegrationError):
    def __init__(self, old_session: Optional[int], new_session: int):
        IntegrationError.__init__(self, old_session, new_session)

    @property
    def old_session(self) -> Optional[int]:
        return self.args[0]

    @property
    def new_session(self) -> int:
        return self.args[1]
