# tradeforgepy/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional

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
        env_file='.env',         # Load from a .env file in the project root
        env_file_encoding='utf-8',
        case_sensitive=True      # Important for variable names like TS_API_KEY
    )

    # Required settings
    TS_USERNAME: str
    TS_API_KEY: str

    # Optional settings with defaults
    TS_ENVIRONMENT: Literal["LIVE", "DEMO"] = "DEMO"
    TS_CAPTURE_CONTRACT_ID: str = "CON.F.US.NQ.M25"
    TS_CAPTURE_ACCOUNT_ID: Optional[str] = None


# Create a singleton instance to be used throughout the application
settings = Settings()