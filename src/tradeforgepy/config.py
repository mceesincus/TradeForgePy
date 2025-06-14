# tradeforgepy/config.py
import os
import re
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from pathlib import Path
from typing import Literal, Optional, Dict, Any
from dotenv import load_dotenv

def _find_dotenv() -> Optional[Path]:
    """
    Find the .env file by searching upward from the current file's location.
    
    This robust method ensures that settings are loaded correctly for both:
    1. Development: Running scripts from anywhere within the project (e.g., /examples).
    2. Installed package: When the library is installed via pip and used in another project.
    """
    for directory in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
        potential_path = directory / '.env'
        if potential_path.is_file():
            return potential_path
            
    cwd_path = Path.cwd() / '.env'
    if cwd_path.is_file():
        return cwd_path
        
    return None

class ProviderSettings(BaseModel):
    """
    Defines the generic settings structure for any provider.
    """
    USERNAME: str
    API_KEY: str
    ENVIRONMENT: Literal["LIVE", "DEMO"] = "DEMO"
    
    # Provider-specific URLs. Defaults are set for TopStepX.
    API_URL_DEMO: Optional[str] = "https://gateway-api-demo.s2f.projectx.com"
    API_URL_LIVE: Optional[str] = "https://api.topstepx.com"
    MARKET_HUB_DEMO: Optional[str] = "gateway-rtc-demo.s2f.projectx.com/hubs/market"
    MARKET_HUB_LIVE: Optional[str] = "rtc.topstepx.com/hubs/market"
    USER_HUB_DEMO: Optional[str] = "gateway-rtc-demo.s2f.projectx.com/hubs/user"
    USER_HUB_LIVE: Optional[str] = "rtc.topstepx.com/hubs/user"

class Settings(BaseSettings):
    """
    Manages application settings, loading non-provider-specific values from a .env file.
    The main PROVIDERS dictionary is populated separately.
    """
    model_config = SettingsConfigDict(
        env_file=_find_dotenv(),
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'
    )

    PROVIDERS: Dict[str, ProviderSettings] = Field(default_factory=dict)
    
    # Optional settings for specific use cases (e.g., examples)
    DEFAULT_CAPTURE_CONTRACT_ID: Optional[str] = None
    DEFAULT_CAPTURE_ACCOUNT_ID: Optional[str] = None

def _load_provider_settings_from_env() -> Dict[str, ProviderSettings]:
    """
    Explicitly loads, parses, and validates provider settings from environment variables.
    This function ensures the .env file is loaded before attempting to access the variables.
    """
    # 1. Ensure .env is loaded into the environment
    dotenv_path = _find_dotenv()
    if dotenv_path:
        load_dotenv(dotenv_path=dotenv_path, override=True)

    # 2. Parse variables into a nested dictionary
    provider_configs = {}
    provider_re = re.compile(r"^TRADEFORGE_PROVIDER_([A-Z0-9]+)_(\S+)$")
    
    for key, value in os.environ.items():
        match = provider_re.match(key)
        if match:
            provider_name, setting_key = match.groups()
            if provider_name not in provider_configs:
                provider_configs[provider_name] = {}
            provider_configs[provider_name][setting_key] = value

    # 3. Validate and create ProviderSettings models
    validated_providers = {}
    for name, config in provider_configs.items():
        try:
            validated_providers[name] = ProviderSettings(**config)
        except Exception as e:
            print(f"Warning: Could not initialize settings for provider '{name}': {e}")
            
    return validated_providers

# --- Singleton Initialization ---

# 1. Create the base settings object
settings = Settings()

# 2. Explicitly load and attach the provider-specific settings
settings.PROVIDERS = _load_provider_settings_from_env()