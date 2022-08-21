class IntegrationError(Exception):
    pass


class BackoffError(IntegrationError):
    pass


class SignatureValidationError(IntegrationError):
    pass
