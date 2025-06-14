# ==============================================================================
# tradeforgepy/__init__.py
# ==============================================================================
import logging
from typing import Dict, Type

from .config import settings
from .core.interfaces import TradingPlatformAPI
from .exceptions import ConfigurationError
from .providers.topstepx import TopStepXProvider

# Set up a default null handler to avoid "No handler found" warnings.
# The user of the library is responsible for configuring the logging.
logging.getLogger(__name__).addHandler(logging.NullHandler())

# --- Provider Factory ---

PROVIDER_MAP: Dict[str, Type[TradingPlatformAPI]] = {
    "TOPSTEPX": TopStepXProvider,
}
"""A mapping of provider names to their corresponding implementation classes."""


class TradeForgePy:
    """
    A factory class for creating configured trading provider instances.
    """
    @staticmethod
    def create_provider(provider_name: str, **kwargs) -> TradingPlatformAPI:
        """
        Creates and returns a configured provider instance based on the provider name.

        This factory handles the dependency injection of provider-specific settings
        loaded from the environment.

        Args:
            provider_name: The name of the provider to create (e.g., "TopStepX").
            **kwargs: Additional arguments to pass to the provider's constructor,
                      such as 'connect_timeout' or 'cache_ttl_seconds'.

        Returns:
            An initialized instance of a TradingPlatformAPI implementation.

        Raises:
            ConfigurationError: If the requested provider is not supported or if
                                its configuration is missing.
        """
        provider_key = provider_name.upper()
        
        provider_class = PROVIDER_MAP.get(provider_key)
        if not provider_class:
            raise ConfigurationError(
                f"Unsupported provider: '{provider_name}'. "
                f"Available providers: {list(PROVIDER_MAP.keys())}"
            )

        provider_settings = settings.PROVIDERS.get(provider_key)
        if not provider_settings:
            raise ConfigurationError(
                f"Configuration for provider '{provider_name}' not found. "
                f"Ensure environment variables like 'TRADEFORGE_PROVIDER_{provider_key}_USERNAME' are set."
            )

        try:
            # Pass the specific provider settings and any additional kwargs
            return provider_class(settings=provider_settings, **kwargs)
        except Exception as e:
            logging.getLogger(__name__).error(f"Failed to initialize provider '{provider_name}': {e}", exc_info=True)
            raise ConfigurationError(f"Failed to initialize provider '{provider_name}'.") from e