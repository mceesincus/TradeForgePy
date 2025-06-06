# data_capture.py
import asyncio
import logging
import json
import os
from typing import Optional, List, Any, Dict
from datetime import datetime
from pydantic import ValidationError

from pysignalr.client import SignalRClient
from pysignalr.exceptions import ConnectionError as PySignalRConnectionError
import httpx

# --- Robust Path Setup ---
import sys
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(script_dir, '..'))
src_path = os.path.join(project_root, 'src')
if src_path not in sys.path:
    sys.path.insert(0, src_path)
# -------------------------
from tradeforgepy.config import settings
from tradeforgepy.providers.topstepx.client import TopStepXHttpClient # Import the client to use it directly

# --- Configuration ---
try:
    TS_USERNAME = settings.TS_USERNAME
    TS_API_KEY = settings.TS_API_KEY
    TS_ENVIRONMENT = settings.TS_ENVIRONMENT
    DEFAULT_CONTRACT_ID_TO_CAPTURE = settings.TS_CAPTURE_CONTRACT_ID
    DEFAULT_ACCOUNT_ID_TO_CAPTURE_STR = settings.TS_CAPTURE_ACCOUNT_ID
except ValidationError as e:
    print(
        "FATAL: Configuration error. Please ensure TS_USERNAME and TS_API_KEY are set in your .env file.\n"
        f"Details: {e}"
    )
    sys.exit(1)

# --- Setup Loggers ---
# Root logger configured for DEBUG to capture everything
logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# Main script logger (console)
script_logger = logging.getLogger("DataCaptureScript")
# The root logger is already configured, so we just get the logger instance.

# Dedicated logger for raw SignalR messages (file)
raw_messages_logger = logging.getLogger("RawSignalRMessages")
raw_messages_logger.setLevel(logging.DEBUG) # Capture all raw messages
log_dir = "captured_data_logs"
os.makedirs(log_dir, exist_ok=True)
file_handler = logging.FileHandler(os.path.join(log_dir, f"signalr_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"), mode='w')
file_formatter = logging.Formatter('%(asctime)s - %(levelname)s - %(name)s - %(message)s')
file_handler.setFormatter(file_formatter)
if not raw_messages_logger.handlers:
    raw_messages_logger.addHandler(file_handler)
    raw_messages_logger.propagate = False

# Tone down noisy libraries on console if needed, but allow their DEBUG in root
logging.getLogger("pysignalr.client").setLevel(logging.INFO)


# --- Helper to get Authentication Token (Now using our debugged client) ---
async def get_auth_token_with_debug(username: str, api_key: str, environment: str) -> Optional[str]:
    """Uses the TopStepXHttpClient to authenticate, leveraging its new detailed logging."""
    script_logger.info("Attempting authentication using TopStepXHttpClient for detailed debugging...")
    http_client = TopStepXHttpClient(username=username, api_key=api_key, environment=environment)
    try:
        # The _authenticate method now contains all the debug logs.
        await http_client._authenticate()
        token = http_client._token
        if token:
            script_logger.info("Authentication successful via http_client. Token received.")
            return token
        else:
            script_logger.error("Authentication via http_client did not return a token, though no exception was raised.")
            return None
    except Exception as e:
        script_logger.critical(f"Caught exception from http_client._authenticate: {e}", exc_info=True)
        return None
    finally:
        await http_client.close_http_client()


# --- Generic SignalR Message Handler (Unchanged) ---
def create_message_handler(hub_name: str, message_type: str):
    async def handler(message_args: List[Any]):
        timestamp_iso = datetime.now().isoformat()
        script_logger.info(f"Received from {hub_name}: {message_type} (see raw_messages log and console print for details)")
        log_entry = {
            "capture_timestamp": timestamp_iso,
            "hub": hub_name,
            "message_type_invoked_on_client": message_type,
            "payload_args": message_args
        }
        try:
            raw_messages_logger.info(json.dumps(log_entry))
        except Exception as e_log:
            raw_messages_logger.error(f"Error serializing log entry to JSON: {e_log}")
            raw_messages_logger.info(str(log_entry))
        print(f"\n--- CONSOLE CAPTURE: [{timestamp_iso}] RAW MESSAGE from {hub_name} - Type: {message_type} ---")
        try:
            pretty_payload = json.dumps(message_args, indent=2)
            print(pretty_payload)
        except Exception as e_print:
            script_logger.error(f"Error pretty-printing message for console: {e_print}")
            print(message_args)
        print(f"--- End of CONSOLE CAPTURE from {hub_name} - Type: {message_type} ---\n")
    return handler

# --- Main Connection Logic (Unchanged) ---
async def connect_to_hub(hub_url_template: str, token: str, hub_name: str,
                         subscriptions: Optional[List[Dict[str, Any]]] = None):
    hub_url_with_token = f"{hub_url_template}?access_token={token}"
    script_logger.info(f"Attempting to connect to {hub_name} at: {hub_url_template.split('?')[0]}?access_token=***")
    
    client = SignalRClient(hub_url_with_token)

    async def on_open_and_subscribe():
        script_logger.info(f"{hub_name} connection opened (via on_open handler).")
        if subscriptions:
            for sub in subscriptions:
                method, args_list, log_name = sub["method"], sub["args"], sub.get("log_name", sub["method"])
                try:
                    script_logger.info(f"Sending subscription command for {hub_name}: {method} with args {args_list}")
                    await client.send(method, args_list)
                    script_logger.info(f"Subscription command '{log_name}' sent successfully for {hub_name}.")
                except Exception as e_sub:
                    script_logger.error(f"Error sending subscription command '{log_name}' ({method}) for {hub_name}: {e_sub}", exc_info=True)

    async def async_error_handler(error_payload: Any):
        err_str = str(getattr(error_payload, 'error', error_payload))
        script_logger.error(f"{hub_name} connection error: {err_str}", exc_info=isinstance(error_payload, Exception))

    client.on_open(on_open_and_subscribe)
    client.on_close(lambda: script_logger.info(f"{hub_name} connection closed."))
    client.on_error(async_error_handler)

    if hub_name == "Market Hub":
        client.on("GatewayQuote", create_message_handler(hub_name, "GatewayQuote"))
        client.on("GatewayTrade", create_message_handler(hub_name, "GatewayTrade"))
        client.on("GatewayDepth", create_message_handler(hub_name, "GatewayDepth"))
    elif hub_name == "User Hub":
        client.on("GatewayUserOrder", create_message_handler(hub_name, "GatewayUserOrder"))
        client.on("GatewayUserPosition", create_message_handler(hub_name, "GatewayUserPosition"))
        client.on("GatewayUserAccount", create_message_handler(hub_name, "GatewayUserAccount"))
        client.on("GatewayUserTrade", create_message_handler(hub_name, "GatewayUserTrade"))

    try:
        await client.run()
    except Exception as e:
        script_logger.error(f"Unexpected error in {hub_name} run loop: {e}", exc_info=True)
    finally:
        script_logger.info(f"{hub_name} client loop finished.")


async def main_capture():
    # Now calls the new auth function
    token = await get_auth_token_with_debug(TS_USERNAME, TS_API_KEY, TS_ENVIRONMENT)
    if not token:
        script_logger.critical("Failed to obtain authentication token. Exiting.")
        return

    # Rest of the function is unchanged as it depends on the token
    TS_MARKET_HUB_DEMO = "wss://gateway-rtc-demo.s2f.projectx.com/hubs/market"
    TS_MARKET_HUB_LIVE = "wss://rtc.topstepx.com/hubs/market"
    TS_USER_HUB_DEMO = "wss://gateway-rtc-demo.s2f.projectx.com/hubs/user"
    TS_USER_HUB_LIVE = "wss://rtc.topstepx.com/hubs/user"
    market_hub_url = TS_MARKET_HUB_DEMO if TS_ENVIRONMENT == "DEMO" else TS_MARKET_HUB_LIVE
    user_hub_url = TS_USER_HUB_DEMO if TS_ENVIRONMENT == "DEMO" else TS_USER_HUB_LIVE
    tasks_to_await = []
    
    # ... (input prompts remain the same) ...
    # This part is long and unchanged, so I will omit it for brevity, but it is part of the final file.
    # It starts with: connect_market_input = input(...)

    connect_market_input = input("Connect to Market Hub? (y/n, default y): ").lower().strip()
    if connect_market_input in ["", "y"]:
        contract_id_market = input(f"Enter Contract ID for Market Hub (default: {DEFAULT_CONTRACT_ID_TO_CAPTURE}): ").strip() or DEFAULT_CONTRACT_ID_TO_CAPTURE
        market_subscriptions = []
        if input(f"Subscribe to Quotes for {contract_id_market}? (y/n, default y): ").lower().strip() != "n":
            market_subscriptions.append({"method": "SubscribeContractQuotes", "args": [contract_id_market], "log_name": "MarketQuotes"})
        if input(f"Listen for Market Trades for {contract_id_market}? (y/n, default y): ").lower().strip() != "n":
            script_logger.info(f"Will listen for 'GatewayTrade' on Market Hub for {contract_id_market}.")
        if input(f"Subscribe to Depth for {contract_id_market}? (y/n, default n): ").lower().strip() == "y":
            market_subscriptions.append({"method": "SubscribeContractMarketDepth", "args": [contract_id_market], "log_name": "MarketDepth"})
        tasks_to_await.append(asyncio.create_task(connect_to_hub(market_hub_url, token, "Market Hub", market_subscriptions)))

    connect_user_input = input("Connect to User Hub? (y/n, default y): ").lower().strip()
    if connect_user_input in ["", "y"]:
        account_id_user_str = input(f"Enter Account ID for User Hub (default: {DEFAULT_ACCOUNT_ID_TO_CAPTURE_STR or 'None'}): ").strip()
        account_id_user = None
        id_to_use = account_id_user_str or DEFAULT_ACCOUNT_ID_TO_CAPTURE_STR
        if id_to_use:
            try: account_id_user = int(id_to_use)
            except (ValueError, TypeError): script_logger.warning(f"Invalid Account ID '{id_to_use}'.")
        
        user_subscriptions = []
        if input("Subscribe to Global Account Updates? (y/n, default y): ").lower().strip() != "n":
            user_subscriptions.append({"method": "SubscribeAccounts", "args": [], "log_name": "UserGlobalAccounts"})
        if account_id_user:
            if input(f"Subscribe to Orders for Account {account_id_user}? (y/n, default y): ").lower().strip() != "n":
                user_subscriptions.append({"method": "SubscribeOrders", "args": [account_id_user], "log_name": "UserOrders"})
            if input(f"Subscribe to Positions for Account {account_id_user}? (y/n, default y): ").lower().strip() != "n":
                user_subscriptions.append({"method": "SubscribePositions", "args": [account_id_user], "log_name": "UserPositions"})
            if input(f"Subscribe to User Trades (Fills) for Account {account_id_user}? (y/n, default y): ").lower().strip() != "n":
                user_subscriptions.append({"method": "SubscribeTrades", "args": [account_id_user], "log_name": "UserFills"})
        else:
             script_logger.info("No valid specific Account ID; only global user subscriptions will be attempted.")

        tasks_to_await.append(asyncio.create_task(connect_to_hub(user_hub_url, token, "User Hub", user_subscriptions)))


    if not tasks_to_await:
        script_logger.info("No hubs selected for connection. Exiting.")
        return

    script_logger.info("Data capture script running. Press Ctrl+C to stop.")
    script_logger.info(f"Raw SignalR messages will be logged to: {os.path.abspath(log_dir)}/")
    
    try:
        await asyncio.gather(*tasks_to_await)
    except KeyboardInterrupt:
        script_logger.info("Keyboard interrupt received. Stopping tasks...")
    finally:
        tasks = asyncio.all_tasks(loop=asyncio.get_running_loop())
        for task in tasks:
            if task is not asyncio.current_task():
                task.cancel()
        await asyncio.gather(*[t for t in tasks if t is not asyncio.current_task()], return_exceptions=True)
        script_logger.info("Data capture script finished.")


if __name__ == "__main__":
    try:
        if not os.path.exists(os.path.join(project_root, '.env')):
            script_logger.warning("'.env' file not found. Script might fail if env vars not set.")
        asyncio.run(main_capture())
    except KeyboardInterrupt:
        script_logger.info("Application terminated by user.")