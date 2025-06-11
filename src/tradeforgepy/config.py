# tradeforgepy/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional
from pathlib import Path

def _find_dotenv() -> Optional[Path]:
    """
    Find the .env file by searching upward from the current file's location.
    
    This robust method ensures that settings are loaded correctly for both:
    1. Development: Running scripts from anywhere within the project (e.g., /examples).
    2. Installed Package: When the library is installed via pip and used in another project.
    """
    # Start from this file's directory and search in parent directories
    for directory in [Path(__file__).resolve().parent] + list(Path(__file__).resolve().parents):
        potential_path = directory / '.env'
        if potential_path.is_file():
            return potential_path
            
    # As a final fallback for unusual execution contexts, check the current working directory.
    # This is crucial for when the package is installed and a user runs their script.
    cwd_path = Path.cwd() / '.env'
    if cwd_path.is_file():
        return cwd_path
        
    return None

class Settings(BaseSettings):
    """
    Manages application settings, loading from a .env file and environment variables.
    - TS_USERNAME: Your TopStepX username.
    - TS_API_KEY: Your TopStepX API key.
    - TS_ENVIRONMENT: The trading environment, 'LIVE' or 'DEMO'.
    - TS_CAPTURE_CONTRACT_ID: Default contract ID for the data capture script.
    - TS_CAPTURE_ACCOUNT_ID: Default account ID for the data capture script.
    """
    model_config = SettingsConfigDict(
        env_file=_find_dotenv(),    # Use the robust discovery function
        env_file_encoding='utf-8',
        case_sensitive=True,
        extra='ignore'              # Ignore extra variables from the old .env file
    )

    # Required settings
    TS_USERNAME: str
    TS_API_KEY: str

    # Optional settings with defaults
    TS_ENVIRONMENT: Literal["LIVE", "DEMO"] = "DEMO"
    TS_CAPTURE_CONTRACT_ID: str = "CON.F.US.NQ.M25"
    TS_CAPTURE_ACCOUNT_ID: Optional[str] = None
    
    # --- TopStepX URLs ---
    # These can be overridden in the .env file for testing or if URLs change.
    TS_API_URL_DEMO: str = "https://gateway-api-demo.s2f.projectx.com"
    TS_API_URL_LIVE: str = "https://api.topstepx.com"
    TS_MARKET_HUB_DEMO: str = "gateway-rtc-demo.s2f.projectx.com/hubs/market"
    TS_MARKET_HUB_LIVE: str = "rtc.topstepx.com/hubs/market"
    TS_USER_HUB_DEMO: str = "gateway-rtc-demo.s2f.projectx.com/hubs/user"
    TS_USER_HUB_LIVE: str = "rtc.topstepx.com/hubs/user"


# Create a singleton instance to be used throughout the application
settings = Settings()