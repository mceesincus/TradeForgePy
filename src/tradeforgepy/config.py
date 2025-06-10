# tradeforgepy/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal, Optional
from pathlib import Path

# --- Robust .env file discovery ---
# This logic finds the project root directory (which contains the 'src' folder)
# and constructs an absolute path to the .env file. This makes the settings
# load correctly regardless of where the script is run from.
try:
    # Path to this config.py file
    _current_file_path = Path(__file__).resolve()
    # Go up directories until we find the project root (assumed to be parent of 'src')
    _project_root = _current_file_path.parent.parent.parent
    _env_path = _project_root / '.env'
    
    if not _env_path.exists():
        # Fallback for when the package might be installed and not in a 'src' layout
        _project_root = Path.cwd()
        _env_path = _project_root / '.env'

except Exception:
    # If path logic fails for any reason, default to the current working directory
    _env_path = Path.cwd() / '.env'


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
        env_file=_env_path,         # Use the absolute path we discovered
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


# Create a singleton instance to be used throughout the application
settings = Settings()