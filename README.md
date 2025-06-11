TradeForgePy - API Documentation

This document provides comprehensive documentation for the TradeForgePy FastAPI service. It is designed for developers who wish to use this service as a backend for trading applications, dashboards, or bots.

Table of Contents

Overview

Getting Started

2.1. Prerequisites

2.2. Installation

2.3. Configuration

2.4. Running the Service

Core Concepts & Data Models

REST API Endpoints

4.1. Accounts

4.2. Contracts

4.3. Positions

4.4. Orders

4.5. History

Real-Time Data Streaming (WebSocket)

5.1. Connection Workflow

5.2. Subscription Message

5.3. Streamed Event Format

Error Handling

1. Overview

TradeForgePy is a generic, provider-agnostic Python library designed to offer a clean, consistent, and asynchronous interface for interacting with various trading platform APIs. The project's core philosophy is to separate a generic core from provider-specific implementations, allowing for easy expansion and maintenance.

This document details the API for the FastAPI service built on top of the TradeForgePy library. The service provides a robust set of RESTful endpoints and a real-time WebSocket stream for all core trading functionalities.

The first and currently implemented provider is for the TopStepX platform.

2. Getting Started

Follow these steps to set up and run the TradeForgePy API service on your local machine.

2.1. Prerequisites

Python 3.11 or higher

Git

2.2. Installation

Clone the Repository

git clone https://path/to/your/tradeforgepy/repo.git
cd TradeForgePy


Install Dependencies
It is highly recommended to use a virtual environment.

python -m venv venv
source venv/bin/activate  # On Windows, use `venv\Scripts\activate`
pip install -r requirements.txt
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END
2.3. Configuration

The service requires API credentials to connect to the trading provider (TopStepX). These are configured via a .env file in the project's root directory.

Create the .env file:
Create a file named .env in the root of the TradeForgePy project.

Add Configuration:
Copy the following template into your .env file and replace the placeholder values with your actual TopStepX credentials.

# .env file

# Your TopStepX Username
TS_USERNAME="your_topstep_username"

# Your TopStepX API Key (generate this from your TopStepX dashboard)
TS_API_KEY="your_topstepx_api_key"

# The environment to connect to. Use "DEMO" for practice/testing or "LIVE" for real funds.
# It is STRONGLY recommended to start with "DEMO".
TS_ENVIRONMENT="DEMO"

# (Optional) Default account ID to use for some example/utility scripts
TS_CAPTURE_ACCOUNT_ID="your_numeric_account_id"
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Dotenv
IGNORE_WHEN_COPYING_END
2.4. Running the Service

Once configured, you can run the FastAPI service using uvicorn. From the project's root directory, run:

uvicorn fastapi_service.main:app --reload
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Bash
IGNORE_WHEN_COPYING_END

The service will start and be available at http://127.0.0.1:8000.

You can access the interactive API documentation (provided by FastAPI/Swagger) at http://127.0.0.1:8000/docs. This is a valuable tool for exploring and testing the API endpoints directly from your browser.

3. Core Concepts & Data Models

All API responses use a consistent set of generic data models. Understanding these is key to using the API.

Account: Represents a trading account, including its ID, balance, and status.

Contract: Represents a tradable instrument (e.g., a futures contract like MESM5), including its ID, symbol, tick size, and value.

Position: Represents an open position in a specific contract for an account, including quantity and average entry price.

Order: Represents a pending or historical order, including its ID, status (e.g., WORKING, FILLED), side, size, and prices.

Trade: Represents a single fill or execution, detailing the price, quantity, and time of a trade.

All models include a provider_name field (e.g., "TopStepX") and a provider_specific_data field containing the raw, unmodified data from the provider's API for further inspection if needed.

4. REST API Endpoints

The following endpoints are available for querying data and executing actions.

4.1. Accounts
GET /accounts

Retrieves a list of all active trading accounts associated with the configured credentials.

Response 200 OK

[
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_account_id": "8391036",
    "account_name": "TS-0012345",
    "balance": 150105.75,
    "currency": "USD",
    "buying_power": null,
    "cash_balance": null,
    "margin_balance": null,
    "can_trade": true,
    "is_active": true
  }
]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
4.2. Contracts
GET /contracts/search

Searches for tradable contracts.

Query Parameters:

query (string, required): The search text (e.g., "MES", "NQ", "E-mini").

Response 200 OK

[
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_contract_id": "CON.F.US.MES.M25",
    "symbol": "MESM5",
    "exchange": "CME",
    "asset_class": "FUTURES",
    "description": "Micro E-mini S&P 500: Jun 2025",
    "tick_size": 0.25,
    "tick_value": 1.25,
    "price_currency": "USD",
    "multiplier": 5,
    "min_order_size": null,
    "max_order_size": null,
    "is_tradable": true,
    "expiration_date_utc": null,
    "underlying_symbol": null
  }
]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
GET /contracts/{provider_contract_id}

Retrieves detailed information for a single contract by its unique provider ID.

Path Parameters:

provider_contract_id (string, required): The unique ID of the contract (e.g., "CON.F.US.MES.M25").

Response 200 OK

{
  "provider_name": "TopStepX",
  "provider_specific_data": { "... raw data ..." },
  "provider_contract_id": "CON.F.US.MES.M25",
  "symbol": "MESM5",
  "exchange": "CME",
  "asset_class": "FUTURES",
  "description": "Micro E-mini S&P 500: Jun 2025",
  "tick_size": 0.25,
  "tick_value": 1.25,
  "price_currency": "USD",
  "multiplier": 5,
  "is_tradable": true
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
4.3. Positions
GET /positions

Retrieves a list of all open positions for a specific account.

Query Parameters:

account_id (string, required): The provider_account_id for which to fetch positions.

Response 200 OK

[
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MES.M25",
    "quantity": 2,
    "average_entry_price": 5150.25,
    "unrealized_pnl": null
  },
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MNQ.M25",
    "quantity": -1,
    "average_entry_price": 18100.5,
    "unrealized_pnl": null
  }
]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
POST /positions/close

Submits a market order to close all or part of an existing position.

Request Body:

{
  "provider_account_id": "8391036",
  "provider_contract_id": "CON.F.US.MES.M25",
  "size_to_close": 1
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END

size_to_close (float, optional): If provided, closes only that many contracts. If omitted, the entire position for that contract is closed.

Response 200 OK

{
  "provider_name": "TopStepX",
  "order_id_acknowledged": true,
  "provider_order_id": null,
  "initial_order_status": "PENDING_SUBMIT",
  "message": "Close position request submitted."
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
4.4. Orders
GET /orders/open

Retrieves a list of all open (working) orders for a specific account.

Query Parameters:

account_id (string, required): The provider_account_id.

Response 200 OK

[
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_order_id": "123456789",
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MES.M25",
    "order_type": "LIMIT",
    "order_side": "BUY",
    "original_size": 1,
    "status": "WORKING",
    "limit_price": 5100.0,
    "stop_price": null,
    "filled_size": 0,
    "average_fill_price": null,
    "time_in_force": "GTC",
    "created_at_utc": "2025-06-11T12:30:00Z",
    "updated_at_utc": "2025-06-11T12:30:01Z",
    "commission": null,
    "reason_text": null
  }
]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
POST /orders/place

Places a new order.

Request Body:

{
  "provider_account_id": "8391036",
  "provider_contract_id": "CON.F.US.MES.M25",
  "order_type": "LIMIT",
  "order_side": "BUY",
  "size": 1,
  "limit_price": 5100.0,
  "stop_price": null
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END

order_type can be MARKET, LIMIT, STOP_MARKET, or STOP_LIMIT.

limit_price is required for LIMIT and STOP_LIMIT orders.

stop_price is required for STOP_MARKET and STOP_LIMIT orders.

Response 200 OK

{
  "provider_name": "TopStepX",
  "order_id_acknowledged": true,
  "provider_order_id": "123456790",
  "initial_order_status": "PENDING_SUBMIT",
  "message": "Order submitted successfully."
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
POST /orders/cancel/{provider_order_id}

Cancels an open order.

Path Parameters:

provider_order_id (string, required): The ID of the order to cancel.

Query Parameters:

account_id (string, required): The provider_account_id that owns the order.

Response 200 OK

{
  "provider_name": "TopStepX",
  "success": true,
  "message": "Cancellation request submitted."
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
4.5. History
GET /history/trades

Retrieves the trade history (fills) for an account within a given time range.

Query Parameters:

account_id (string, required): The provider_account_id.

start_time (string, required): The start of the time range in ISO 8601 format (e.g., 2025-06-11T00:00:00Z).

end_time (string, required): The end of the time range in ISO 8601 format.

Response 200 OK

[
  {
    "provider_name": "TopStepX",
    "provider_specific_data": { "... raw data ..." },
    "provider_trade_id": "987654",
    "provider_order_id": "123456780",
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MES.M25",
    "price": 5150.25,
    "quantity": 1,
    "side": "BUY",
    "timestamp_utc": "2025-06-11T14:05:10Z",
    "commission": 2.12,
    "pnl": 0.0
  }
]
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
5. Real-Time Data Streaming (WebSocket)

The service provides a single WebSocket endpoint for streaming real-time market and user data. This eliminates the need for constant polling.

Endpoint URL: ws://127.0.0.1:8000/ws/stream

5.1. Connection Workflow

Connect: Establish a WebSocket connection to the endpoint. The underlying library will handle authentication and maintaining a resilient connection.

Subscribe: Send a single JSON message to the server to subscribe to the data feeds you need.

Receive Events: The server will start pushing event messages to you as they occur. If the connection drops, the library will attempt to reconnect and re-subscribe automatically.

5.2. Subscription Message

To subscribe, send a JSON message with the following structure:

{
  "action": "subscribe",
  "market_data": {
    "provider_contract_ids": [
      "CON.F.US.MES.M25",
      "CON.F.US.MNQ.M25"
    ],
    "data_types": ["QUOTE", "DEPTH", "TRADE"]
  },
  "user_data": {
    "provider_account_ids": ["8391036"],
    "data_types": ["ORDER_UPDATE", "POSITION_UPDATE", "USER_TRADE", "ACCOUNT_UPDATE"]
  }
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END

action: Must be "subscribe".

market_data: (Optional) Subscribes to public market data.

provider_contract_ids: A list of contract IDs.

data_types: A list containing one or more of QUOTE, TRADE, or DEPTH.

user_data: (Optional) Subscribes to private account data.

provider_account_ids: A list of account IDs.

data_types: A list containing one or more of ORDER_UPDATE, POSITION_UPDATE, ACCOUNT_UPDATE, or USER_TRADE.

5.3. Streamed Event Format

All messages received from the server will be JSON objects with two top-level keys: event_type and data.

Quote Event

event_type: "QUOTE"

{
  "event_type": "QUOTE",
  "data": {
    "provider_name": "MarketStream",
    "provider_contract_id": "CON.F.US.MES.M25",
    "timestamp_utc": "2025-06-11T15:00:01.123Z",
    "bid_price": 5150.25,
    "ask_price": 5150.50,
    "last_price": 5150.50
  }
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
Order Update Event

event_type: "ORDER_UPDATE"

{
  "event_type": "ORDER_UPDATE",
  "data": {
    "provider_name": "UserStream",
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MES.M25",
    "timestamp_utc": "2025-06-11T15:00:02.456Z",
    "order_data": {
      "provider_order_id": "123456790",
      "status": "FILLED",
      "filled_size": 1,
      "average_fill_price": 5150.50
    }
  }
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END
Position Update Event

event_type: "POSITION_UPDATE"

{
  "event_type": "POSITION_UPDATE",
  "data": {
    "provider_name": "UserStream",
    "provider_account_id": "8391036",
    "provider_contract_id": "CON.F.US.MES.M25",
    "timestamp_utc": "2025-06-11T15:00:02.457Z",
    "position_data": {
      "quantity": 1,
      "average_entry_price": 5150.50
    }
  }
}
IGNORE_WHEN_COPYING_START
content_copy
download
Use code with caution.
Json
IGNORE_WHEN_COPYING_END

Other event types (TRADE, DEPTH, USER_TRADE, ACCOUNT_UPDATE) follow a similar, consistent structure.

6. Error Handling

The API uses standard HTTP status codes:

200 OK: The request was successful.

404 Not Found: The requested resource (e.g., a specific contract or order) could not be found.

422 Unprocessable Entity: The request was syntactically correct, but contained semantic errors (e.g., missing a required field in a POST body). The response body will contain details.

500 Internal Server Error: An unexpected error occurred on the server, often related to an issue communicating with the provider's API. The response body may contain error details.