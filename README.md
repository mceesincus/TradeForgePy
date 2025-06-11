TradeForgePy - A Generic, Asynchronous Trading API Library



!\[alt text](https://img.shields.io/badge/version-0.1.0--alpha-blue)





!\[alt text](https://img.shields.io/badge/python-3.11+-blue.svg)





!\[alt text](https://img.shields.io/badge/license-MIT-green.svg)



A modern, provider-agnostic Python library for interacting with trading platform APIs, offering a clean, consistent interface for both REST API calls and real-time data streaming.



Core Objective



TradeForgePy aims to simplify the development of custom trading tools, bots, and analytics dashboards by abstracting away the specific implementation details of various trading platforms. By providing a unified set of interfaces and data models, developers can write code once and potentially switch between different brokerage or platform providers with minimal changes.



This library is built from the ground up with asyncio to be highly performant and non-blocking, making it ideal for real-time, event-driven trading applications.



Key Features



Asynchronous-First: Built entirely with asyncio and httpx for high-performance, non-blocking I/O suitable for real-time financial applications.



Provider-Agnostic Architecture: A generic core defines the standard interfaces and data models. Specific platforms are implemented as providers, ensuring consistent code for the end-user.



Unified REST and Streaming: Provides a single, cohesive provider object for handling both historical data/account management (REST) and live market/user data (WebSockets/SignalR).



Type-Safe: Leverages Pydantic extensively for robust data validation, clear schemas, and an improved developer experience with auto-completion.



Extensible by Design: The provider model makes it straightforward to add support for new trading platforms by simply implementing the core interfaces.



Clean Data Models: Offers a set of generic, easy-to-understand Pydantic models (Account, Order, Contract, Trade, etc.) for all common trading entities.



Project Status



✅ Generic Core: The core interfaces, enums, and generic data models are complete and stable.



✅ TopStepX Provider - REST API: The TopStepXProvider has a complete and validated implementation for all REST API endpoints, including authentication, account/position/order management, and historical data retrieval.



🟡 TopStepX Provider - Real-Time Streams: The streaming connection and foundational message handling are implemented. Mappers for market data (Quotes, Depth) and account updates are complete. Mappers for user trading events (OrderUpdate, UserTrade, PositionUpdate) are pending finalization with live data.



🔜 Next Steps:



Finalize the remaining real-time stream event mappers for the TopStepX provider.



Build a FastAPI service to expose the library's functionality over a web API.



Add a second provider implementation (e.g., Tradovate, Bybit) to validate the generic architecture.



Installation



This project uses modern Python packaging. A new dependency, pydantic-settings, is required.



\# Ensure you have the required dependencies

pip install httpx pysignalr-client pydantic pydantic-settings



\# For now, the project can be run directly from the source.

\# A setup.py or pyproject.toml will be added for pip installation later.

\# git clone https://your-repo-url/TradeForgePy.git

\# cd TradeForgePy



Configuration



The library uses a .env file in the project root for configuration, managed by pydantic-settings. Create a file named .env in the root of the project directory.



.env.example



Copy the following into your .env file and replace the placeholder values with your actual credentials.



\# .env file for TradeForgePy



\# == Core API Credentials (Required) ==

TS\_USERNAME="your\_topstepx\_username"

TS\_API\_KEY="your\_topstepx\_api\_key"



\# == Environment Selection (Required) ==

\# Set to "LIVE" for the production TopStepX environment, or "DEMO" for the demo environment.

TS\_ENVIRONMENT="LIVE"



\# == Default values for Capture/Test Scripts ==

\# Use a liquid contract like ESU4 (E-mini S\&P) or NQU4 (E-mini Nasdaq) for testing.

TS\_CAPTURE\_CONTRACT\_ID="ESU4"

TS\_CAPTURE\_ACCOUNT\_ID="your\_numeric\_live\_account\_id"

&nbsp;

Quick Start: REST API Usage



This example demonstrates how to instantiate the provider, connect, and fetch your account details.



import asyncio

import logging

from tradeforgepy.providers.topstepx import TopStepXProvider

from tradeforgepy.exceptions import TradeForgeError



\# Basic logging setup

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')



async def main():

&nbsp;   """

&nbsp;   A simple example to connect to the provider and fetch account data.

&nbsp;   """

&nbsp;   provider = None

&nbsp;   try:

&nbsp;       # Provider automatically loads credentials from your .env file

&nbsp;       provider = TopStepXProvider()



&nbsp;       # Establish connection and authenticate

&nbsp;       await provider.connect()

&nbsp;       logging.info("Successfully connected to the provider.")



&nbsp;       # Fetch all tradable accounts

&nbsp;       accounts = await provider.get\_accounts()



&nbsp;       if not accounts:

&nbsp;           logging.warning("No tradable accounts found.")

&nbsp;           return



&nbsp;       logging.info(f"Found {len(accounts)} tradable account(s):")

&nbsp;       for acc in accounts:

&nbsp;           print("\\n--- Generic Account Model ---")

&nbsp;           # The output is a clean, generic Pydantic model

&nbsp;           print(acc.model\_dump\_json(indent=2))



&nbsp;   except TradeForgeError as e:

&nbsp;       logging.error(f"An error occurred: {e}", exc\_info=True)

&nbsp;   finally:

&nbsp;       if provider:

&nbsp;           await provider.disconnect()

&nbsp;           logging.info("Provider disconnected.")



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(main())



Advanced Usage: Real-Time Streams



This example shows how to subscribe to real-time market and user data streams.



import asyncio

import logging

import sys



from tradeforgepy.providers.topstepx import TopStepXProvider

from tradeforgepy.core.models\_generic import GenericStreamEvent

from tradeforgepy.core.enums import MarketDataType, UserDataType, StreamConnectionStatus

from tradeforgepy.config import settings # For easily accessing test settings

from tradeforgepy.exceptions import TradeForgeError



\# Setup logging

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger(\_\_name\_\_)



async def run\_stream\_example():

&nbsp;   """

&nbsp;   Connects to the TopStepX real-time streams and prints incoming events.

&nbsp;   """

&nbsp;   provider = TopStepXProvider() # Loads config from .env



&nbsp;   # 1. Define your event handlers

&nbsp;   async def on\_event\_received(event: GenericStreamEvent):

&nbsp;       logger.info(f"EVENT: {event.event\_type.value}")

&nbsp;       print(event.model\_dump\_json(indent=2))



&nbsp;   async def on\_status\_changed(status: StreamConnectionStatus, reason: str):

&nbsp;       logger.info(f"STATUS -> {status.value}. Reason: {reason}")



&nbsp;   async def on\_error\_received(error: Exception):

&nbsp;       logger.error(f"STREAM ERROR: {error}", exc\_info=True)



&nbsp;   try:

&nbsp;       # 2. Register handlers with the provider

&nbsp;       provider.on\_event(on\_event\_received)

&nbsp;       provider.on\_status\_change(on\_status\_changed)

&nbsp;       provider.on\_error(on\_error\_received)



&nbsp;       # 3. Connect the underlying HTTP client (for auth)

&nbsp;       await provider.connect()



&nbsp;       # 4. Subscribe to desired data streams

&nbsp;       account\_id = settings.TS\_CAPTURE\_ACCOUNT\_ID

&nbsp;       contract\_id = settings.TS\_CAPTURE\_CONTRACT\_ID

&nbsp;       

&nbsp;       logger.info(f"Subscribing to Market Data for {contract\_id}...")

&nbsp;       await provider.subscribe\_market\_data(

&nbsp;           provider\_contract\_ids=\[contract\_id],

&nbsp;           data\_types=\[MarketDataType.QUOTE, MarketDataType.DEPTH]

&nbsp;       )



&nbsp;       logger.info(f"Subscribing to User Data for Account {account\_id}...")

&nbsp;       await provider.subscribe\_user\_data(

&nbsp;           provider\_account\_ids=\[account\_id],

&nbsp;           data\_types=\[UserDataType.ACCOUNT\_UPDATE, UserDataType.ORDER\_UPDATE]

&nbsp;       )



&nbsp;       # 5. Run forever to process messages

&nbsp;       logger.info("Starting stream... Press Ctrl+C to stop.")

&nbsp;       await provider.run\_forever()



&nbsp;   except TradeForgeError as e:

&nbsp;       logger.error(f"A library error occurred: {e}")

&nbsp;   except asyncio.CancelledError:

&nbsp;       logger.info("Main task cancelled.")

&nbsp;   finally:

&nbsp;       logger.info("Disconnecting provider...")

&nbsp;       await provider.disconnect()



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   if sys.platform == "win32":

&nbsp;       asyncio.set\_event\_loop\_policy(asyncio.WindowsSelectorEventLoopPolicy())

&nbsp;   try:

&nbsp;       asyncio.run(run\_stream\_example())

&nbsp;   except KeyboardInterrupt:

&nbsp;       logger.info("Script stopped by user.")

&nbsp;

Architectural Overview



The library is designed in layers to maximize code reuse and maintainability. The flow of information for a typical REST API call is as follows:



sequenceDiagram

&nbsp;   participant User as User Code

&nbsp;   participant Provider as TopStepXProvider

&nbsp;   participant Client as TopStepXHttpClient

&nbsp;   participant Mapper as providers/topstepx/mapper.py

&nbsp;   participant API as TopStepX API



&nbsp;   User->>+Provider: await get\_accounts()

&nbsp;   Provider->>+Client: await ts\_get\_accounts()

&nbsp;   Client->>+API: POST /api/Account/search

&nbsp;   API-->>-Client: JSON Response

&nbsp;   Client-->>-Provider: Returns TSAccountSearchResponse (Pydantic Model)

&nbsp;   Provider->>+Mapper: map\_ts\_accounts\_to\_generic(response)

&nbsp;   Mapper-->>-Provider: Returns List\[GenericAccount]

&nbsp;   Provider-->>-User: Returns List\[GenericAccount]



tradeforgepy/core/: The public-facing part of the library. It contains:



interfaces.py: Abstract Base Classes (TradingPlatformAPI, RealTimeStream) that define the required methods for any provider.



models\_generic.py: The provider-agnostic Pydantic models (Account, Order, Trade, etc.) that are consumed by the end-user.



enums.py: A comprehensive set of generic enums (OrderSide, OrderStatus, etc.).



tradeforgepy/providers/topstepx/: A self-contained implementation for the TopStepX platform.



provider.py: The main TopStepXProvider class that implements the core interfaces.



client.py: A low-level TopStepXHttpClient that handles authentication, token management, and all direct HTTP requests to the API. It returns provider-specific Pydantic models.



streams.py: Internal handlers for managing the SignalR WebSocket connections.



mapper.py: The crucial "translation layer" that maps data between the provider-specific models and the generic core models.



schemas\_ts.py: Pydantic models that exactly match the JSON request/response schemas of the TopStepX API, generated from their OpenAPI specification.



Contributing



Contributions are welcome! This project is in its early stages, and there is much to do. Please follow this general workflow:



Fork the repository.



Create a new feature branch (git checkout -b feature/your-feature-name).



Make your changes. Please adhere to the existing architecture.



Add or update tests for your changes.



Ensure your code passes linting and type-checking (black, isort, mypy).



Submit a pull request with a clear description of your changes.



Roadmap



Phase 1: Finalize Streaming



Capture live data for GatewayUserOrder, GatewayUserTrade, and GatewayUserPosition.



Implement the final stream event mappers in mapper.py.



Add comprehensive tests for the streaming functionality.



Phase 2: Build FastAPI Service



Expose TradingPlatformAPI methods via REST endpoints.



Expose RealTimeStream functionality via WebSocket endpoints.



Implement authentication for the service.



Phase 3: Add New Providers



Implement a provider for a crypto exchange (e.g., Bybit, Binance).



Implement a provider for another futures platform (e.g., Tradovate).



License



This project is licensed under the MIT License. See the LICENSE file for details.

