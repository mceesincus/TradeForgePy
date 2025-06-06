# C:\work\TradeForgePy\examples\01a_test_direct_auth.py
import asyncio
import logging
import os
from dotenv import load_dotenv
import httpx

# --- Path Setup ---
import sys
project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# --- Basic Logging Setup ---
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

TS_API_URL_DEMO = "https://gateway-api-demo.s2f.projectx.com"
TS_API_URL_LIVE = "https://api.topstepx.com"

async def run_direct_auth_test():
    """Tests authentication by making a direct httpx call, bypassing our client class."""
    logger.info("--- [Example 01a] Running Direct Authentication Test ---")

    load_dotenv(os.path.join(project_root, '.env'))
    
    username = os.getenv("TS_USERNAME")
    api_key = os.getenv("TS_API_KEY")
    environment = os.getenv("TS_ENVIRONMENT", "DEMO").upper()

    if not username or not api_key:
        logger.error("TS_USERNAME and TS_API_KEY must be set in your .env file.")
        return

    api_base_url = TS_API_URL_DEMO if environment == "DEMO" else TS_API_URL_LIVE
    auth_url = f"{api_base_url}/api/Auth/loginKey"
    payload = {"userName": username, "apiKey": api_key}

    logger.info(f"Attempting DIRECT auth to: {auth_url}")
    logger.info(f"Using payload: { {'userName': username, 'apiKey': '...key_hidden...'} }")

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(auth_url, json=payload, timeout=10)
            logger.info(f"Direct call received HTTP status: {response.status_code}")
            
            # Print raw response text for inspection
            print("\n--- RAW RESPONSE TEXT ---")
            print(response.text)
            print("-------------------------\n")

            response.raise_for_status()
            data = response.json()
            
            if data.get("success") and data.get("token"):
                logger.info(">>> DIRECT AUTHENTICATION SUCCEEDED! Token received.")
                print(f"Token: {data['token'][:10]}...")
            else:
                logger.error(f">>> DIRECT AUTHENTICATION FAILED. Server Response: {data}")

        except httpx.HTTPStatusError as e:
            logger.error(f"HTTP error during direct authentication: {e.response.status_code} - {e.response.text}", exc_info=True)
        except Exception as e:
            logger.error(f"Error during direct auth test: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(run_direct_auth_test())