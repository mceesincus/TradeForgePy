# ==============================================================================
# tradeforgepy/tradeforgepy/exceptions/__init__.py
# ==============================================================================
class TradeForgeError(Exception):
    """Base exception for the TradeForgePy library."""
    pass

class ConfigurationError(TradeForgeError):
    """Raised for configuration-related issues."""
    pass

class AuthenticationError(TradeForgeError):
    """Raised for authentication failures with the provider."""
    pass

class ConnectionError(TradeForgeError):
    """Raised for network or stream connection problems."""
    pass

class APILimitError(TradeForgeError):
    """Raised when the provider's API rate limits are exceeded."""
    pass

class OperationFailedError(TradeForgeError):
    """
    Raised when a requested operation (e.g., placing an order) fails at the provider level.
    Contains provider-specific error details if available.
    """
    def __init__(self, message: str, provider_error_code=None, provider_error_message=None):
        super().__init__(message)
        self.provider_error_code = provider_error_code
        self.provider_error_message = provider_error_message

    def __str__(self):
        base = super().__str__()
        details = []
        if self.provider_error_code is not None:
            details.append(f"ProviderCode: {self.provider_error_code}")
        if self.provider_error_message is not None:
            details.append(f"ProviderMsg: {self.provider_error_message}")
        return f"{base} ({', '.join(details)})" if details else base

class NotFoundError(TradeForgeError):
    """Raised when a requested resource (e.g., contract, order) is not found."""
    pass

class InvalidParameterError(TradeForgeError):
    """Raised when invalid parameters are provided for an operation."""
    pass