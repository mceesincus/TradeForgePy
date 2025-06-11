\# TradeForgePy - A Generic, Asynchronous Trading API Library



\*\*TradeForgePy\*\* is a high-performance, asynchronous Python library designed to provide a clean, consistent, and provider-agnostic interface for interacting with trading platform APIs. The project includes a ready-to-use FastAPI service that exposes all library features via a modern REST and WebSocket API.



The core objective is to abstract away the specific complexities of each trading provider's API, allowing developers to build robust trading applications, bots, and dashboards on a stable and unified foundation. The first concrete implementation is a full-featured provider for the \*\*TopStepX\*\* platform.



\## ✨ Key Features



\-   \*\*Provider-Agnostic Core:\*\* A generic set of Pydantic models and Abstract Base Classes that define a standard interface for any trading platform.

\-   \*\*Complete TopStepX Provider:\*\* A full implementation of the `TradingPlatformAPI` and `RealTimeStream` interfaces for the TopStepX API, covering all documented REST endpoints and SignalR stream events.

\-   \*\*High-Performance FastAPI Service:\*\* A production-ready web service that exposes the library's functionality, including:

&nbsp;   -   REST endpoints for all account management, order execution, and data retrieval.

&nbsp;   -   A single WebSocket endpoint for streaming all subscribed real-time market and user data.

\-   \*\*Resilient Real-Time Streaming:\*\* The real-time stream handlers are built to be robust, featuring automatic reconnection and re-subscription logic with exponential backoff to handle network disruptions gracefully.

\-   \*\*Fully Asynchronous:\*\* Built from the ground up with `asyncio`, ensuring high throughput and responsiveness for real-time applications.



\## 🏛️ Project Architecture



The project is designed with a clear separation of concerns, making it modular and easy to extend.





.

├── fastapi\_service/ # The user-facing FastAPI application

│ ├── main.py # Defines API endpoints and WebSocket logic

│ └── ...

├── tradeforgepy/

│ ├── core/ # The generic, provider-agnostic core

│ │ ├── enums.py

│ │ ├── interfaces.py # Abstract Base Classes for any provider

│ │ └── models\_generic.py

│ └── providers/

│ └── topstepx/ # The TopStepX-specific implementation

│ ├── client.py # Low-level async HTTP client

│ ├── mapper.py # Maps provider data to generic models

│ ├── provider.py # Implements the core interfaces

│ └── streams.py # SignalR stream management \& resilience

├── examples/ # Example scripts demonstrating library usage

├── tests/ # (Future work) Pytest suite

├── .env.example # Example configuration file

└── requirements.txt



\## 🚀 Getting Started



Follow these steps to get the FastAPI service running locally.



\### 1. Prerequisites



\-   Python 3.11+

\-   Git



\### 2. Installation \& Setup



\*\*A) Clone the repository:\*\*

```bash

git clone https://path/to/your/tradeforgepy/repo.git

cd tradeforgepy



B) Create a virtual environment and install dependencies:



\# Create and activate the virtual environment

python -m venv venv

source venv/bin/activate  # On Windows: venv\\Scripts\\activate



\# Install required packages

pip install -r requirements.txt



3\. Configuration



The service requires API credentials for the trading provider.



A) Create a .env file:

Copy the example configuration file to create your own local version.



cp .env.example .env



B) Edit the .env file:

Open the newly created .env file and fill in your TopStepX credentials.



\# .env



\# Your TopStepX Username

TS\_USERNAME="your\_topstep\_username"



\# Your TopStepX API Key (generate this from your TopStepX dashboard)

TS\_API\_KEY="your\_topstepx\_api\_key"



\# The environment to connect to. Use "DEMO" for practice/testing or "LIVE" for real funds.

\# It is STRONGLY recommended to start with "DEMO".

TS\_ENVIRONMENT="DEMO"



\# (Optional) Default account ID to use for some example scripts

TS\_CAPTURE\_ACCOUNT\_ID="your\_numeric\_account\_id"



4\. Run the Service



With the dependencies installed and configuration set, run the FastAPI service using uvicorn:



uvicorn fastapi\_service.main:app --reload



The API service is now running!



API URL: http://127.0.0.1:8000



Interactive Docs (Swagger UI): http://127.0.0.1:8000/docs



We highly recommend opening the interactive documentation in your browser to explore and test the available REST endpoints.



🛠️ API Usage



The service provides two primary ways to interact with the trading platform: a REST API for request/response actions and a WebSocket for real-time data.



REST API



The REST API provides endpoints for all standard trading operations like fetching accounts, searching for contracts, placing orders, and querying historical data.



The best way to explore all available REST endpoints is through the auto-generated interactive documentation available at http://127.0.0.1:8000/docs when the service is running.



WebSocket Real-Time Stream



For real-time data, connect to the single WebSocket endpoint to receive a stream of market and user-related events.



Endpoint URL: ws://127.0.0.1:8000/ws/stream



Workflow:



Establish a WebSocket connection.



Send a single JSON message to subscribe to desired data feeds.



Begin receiving event messages from the server.



Example Subscription Message:

To subscribe, send a JSON message like this:



{

&nbsp; "action": "subscribe",

&nbsp; "market\_data": {

&nbsp;   "provider\_contract\_ids": \["CON.F.US.MES.M25"],

&nbsp;   "data\_types": \["QUOTE", "DEPTH"]

&nbsp; },

&nbsp; "user\_data": {

&nbsp;   "provider\_account\_ids": \["YOUR\_ACCOUNT\_ID"],

&nbsp;   "data\_types": \["ORDER\_UPDATE", "POSITION\_UPDATE"]

&nbsp; }

}



Example Python Client:



import asyncio

import websockets

import json



async def stream\_client():

&nbsp;   uri = "ws://127.0.0.1:8000/ws/stream"

&nbsp;   async with websockets.connect(uri) as websocket:

&nbsp;       # Define and send subscription message

&nbsp;       subscription\_msg = {

&nbsp;         "action": "subscribe",

&nbsp;         "user\_data": {

&nbsp;           "provider\_account\_ids": \["YOUR\_ACCOUNT\_ID\_HERE"],

&nbsp;           "data\_types": \["ORDER\_UPDATE", "POSITION\_UPDATE"]

&nbsp;         }

&nbsp;       }

&nbsp;       await websocket.send(json.dumps(subscription\_msg))

&nbsp;       print(f"> Sent subscription: {subscription\_msg}")



&nbsp;       # Listen for incoming messages

&nbsp;       while True:

&nbsp;           try:

&nbsp;               message = await websocket.recv()

&nbsp;               data = json.loads(message)

&nbsp;               print(f"< Received event: {data\['event\_type']}")

&nbsp;               print(json.dumps(data\['data'], indent=2))

&nbsp;           except websockets.ConnectionClosed:

&nbsp;               print("Connection closed.")

&nbsp;               break



if \_\_name\_\_ == "\_\_main\_\_":

&nbsp;   asyncio.run(stream\_client())



📋 Project Status \& Known Limitations



The library is feature-complete and stable for all documented API features of the TopStepX provider. The resilience of the real-time stream has been implemented and tested.



Disabled Features



During development and testing, the following advanced order types were found to be unreliable or buggy at the provider API level. To ensure user safety and prevent financial risk, they have been intentionally disabled in this library:



Bracket (OCO) Orders: The provider API lacks a reliable mechanism to cancel the entire order group atomically, creating a risk of orphaned child orders remaining active on the market.



Trailing Stop Orders: The provider API for this order type was found to be non-functional due to a persistent server-side bug in how it processes the trailing value.



These features will not be enabled until the underlying provider API is confirmed to be stable and reliable.



🛣️ Future Work \& Roadmap



The following items are planned for the future development of TradeForgePy:



Comprehensive Test Suite: Build out a full pytest suite with unit and integration tests to ensure long-term stability and prevent regressions.



Generic Configuration: Refactor the configuration system to be fully provider-agnostic, allowing for easy management of credentials for multiple providers.



Implement a New Provider: Add a second provider (e.g., for a crypto or stock brokerage) to validate the generic architecture and demonstrate the library's extensibility.



Add Helper Methods: Introduce higher-level, user-friendly methods to the provider classes (e.g., caching, symbol-based contract lookups) to improve ease of use.



🤝 Contributing



Contributions are welcome! Please feel free to open an issue to report a bug or suggest a feature. If you would like to contribute code, please open an issue first to discuss the proposed changes.



📜 License



This project is licensed under the MIT License. See the LICENSE file for details.s

