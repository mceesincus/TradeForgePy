# tradeforgepy/providers/topstepx/client.py
import httpx
import asyncio
import json
from typing import Optional, Dict, Any, Union
from datetime import datetime, timedelta
import logging

from pydantic import BaseModel

from .schemas_ts import (
    TSLoginApiKeyRequest, TSLoginResponse, TSValidateResponse,
    TSSearchAccountRequest, TSSearchAccountResponse,
    TSSearchContractRequest, TSSearchContractByIdRequest, TSSearchContractResponse, TSSearchContractByIdResponse,
    TSRetrieveBarRequest, TSRetrieveBarResponse,
    TSPlaceOrderRequest, TSPlaceOrderResponse,
    TSCancelOrderRequest, TSCancelOrderResponse,
    TSModifyOrderRequest, TSModifyOrderResponse,
    TSSearchOrderRequest, TSSearchOrderResponse, TSSearchOpenOrderRequest,
    TSCloseContractPositionRequest, TSPartialCloseContractPositionRequest, TSClosePositionResponse, TSPartialClosePositionResponse,
    TSSearchPositionRequest, TSSearchPositionResponse,
    TSSearchTradeRequest, TSSearchHalfTradeResponse
)
from tradeforgepy.exceptions import AuthenticationError, ConnectionError as TradeForgeConnectionError, OperationFailedError, InvalidParameterError, NotFoundError
from tradeforgepy.utils.time_utils import UTC_TZ
from tradeforgepy.config import ProviderSettings

logger = logging.getLogger(__name__)

# Hardcoded URLs are removed from here. They are now managed in config.py.
TS_TOKEN_LIFETIME_HOURS = 23.5
TS_TOKEN_SAFETY_MARGIN_MINUTES = 30

class TopStepXHttpClient:
    """
    An async HTTP client dedicated to interacting with the TopStepX REST API.
    It manages authentication, token lifecycle, and maps raw responses to
    TopStepX-specific Pydantic models defined in schemas_ts.py.
    """
    _MAX_RETRIES = 3
    _INITIAL_BACKOFF_SEC = 1.0

    def __init__(self, username: str, api_key: str, environment: str = "DEMO",
                 connect_timeout: float = 10.0, read_timeout: float = 30.0,
                 provider_urls: ProviderSettings = None):
        if not username or not api_key:
            raise ValueError("TopStepX username and api_key must be provided.")
        self.username = username
        self.api_key = api_key
        self.environment = environment.upper()

        if not provider_urls:
            raise ValueError("provider_urls must be provided to TopStepXHttpClient.")
        
        self.base_url = provider_urls.API_URL_DEMO if self.environment == "DEMO" else provider_urls.API_URL_LIVE
        
        self.timeout_config = httpx.Timeout(connect_timeout, read=read_timeout)
        self.async_client = httpx.AsyncClient(timeout=self.timeout_config, follow_redirects=True)

        self._token: Optional[str] = None
        self._token_acquired_at: Optional[datetime] = None
        self._token_lifetime = timedelta(hours=TS_TOKEN_LIFETIME_HOURS)
        self._token_safety_margin = timedelta(minutes=TS_TOKEN_SAFETY_MARGIN_MINUTES)
        self._auth_lock = asyncio.Lock()

        logger.info(f"TopStepXHttpClient initialized for {self.environment} environment. User: {self.username}")

    async def _authenticate(self) -> None:
        async with self._auth_lock:
            if self._token and self._token_acquired_at and \
               (datetime.now(UTC_TZ) < self._token_acquired_at + self._token_lifetime - self._token_safety_margin):
                return

            logger.info(f"Authenticating TopStepX user: {self.username}")
            endpoint = "/api/Auth/loginKey"
            request_model = TSLoginApiKeyRequest(userName=self.username, apiKey=self.api_key)
            
            # Use model_dump_json to respect json_encoders config
            content_payload = request_model.model_dump_json()

            try:
                # Use content parameter for pre-encoded string
                response = await self.async_client.post(f"{self.base_url}{endpoint}", content=content_payload, headers={"Content-Type": "application/json"})
                response.raise_for_status()
                auth_response = TSLoginResponse.model_validate(response.json())

                if auth_response.success and auth_response.token:
                    self._token = auth_response.token
                    self._token_acquired_at = datetime.now(UTC_TZ)
                    logger.info("TopStepX auth successful.")
                else:
                    err_msg = f"TopStepX auth failed: {auth_response.errorMessage} (Code: {auth_response.errorCode.value})"
                    raise AuthenticationError(err_msg)
            except Exception as e:
                err_msg = f"Exception during TopStepX auth: {e}"
                logger.error(err_msg, exc_info=True)
                raise AuthenticationError(err_msg) from e

    async def _validate_token(self) -> bool:
        if not self._token: return False
        logger.debug("Validating current TopStepX token.")
        headers = {"Authorization": f"Bearer {self._token}", "Accept": "application/json"}
        try:
            response = await self.async_client.post(f"{self.base_url}/api/Auth/validate", headers=headers)
            if response.status_code == 401: return False
            response.raise_for_status()
            validate_response = TSValidateResponse.model_validate(response.json())
            if validate_response.success:
                if validate_response.newToken: self._token = validate_response.newToken
                self._token_acquired_at = datetime.now(UTC_TZ)
                return True
            return False
        except Exception:
            return False

    async def _ensure_valid_token(self) -> None:
        is_expired = self._token is None or self._token_acquired_at is None or \
            (datetime.now(UTC_TZ) >= (self._token_acquired_at + self._token_lifetime - self._token_safety_margin))
        if is_expired:
            if not await self._validate_token():
                await self._authenticate()

    async def _request(self, method: str, endpoint: str,
                       content_payload: Optional[str] = None,
                       expected_response_model: Optional[type[BaseModel]] = None
                       ) -> Union[Dict[str, Any], BaseModel]:
        await self._ensure_valid_token()
        if not self._token:
            raise AuthenticationError("Request attempted without a valid token.")
        
        headers = {"Authorization": f"Bearer {self._token}", "Content-Type": "application/json"}
        url = f"{self.base_url}{endpoint}"
        last_exception = None
        backoff_sec = self._INITIAL_BACKOFF_SEC

        for attempt in range(self._MAX_RETRIES):
            try:
                response = await self.async_client.request(method, url, headers=headers, content=content_payload)

                if response.status_code == 401:
                    logger.warning("Token expired or invalid (401). Re-authenticating and retrying once.")
                    await self._authenticate()
                    headers["Authorization"] = f"Bearer {self._token}"
                    response = await self.async_client.request(method, url, headers=headers, content=content_payload)

                # Retry on transient server errors (5xx)
                if response.status_code >= 500:
                    response.raise_for_status() # Will raise HTTPStatusError, caught below

                # If we get here, status is likely 2xx or a non-retryable 4xx
                response.raise_for_status()
                response_data = response.json()

                if isinstance(response_data, dict) and response_data.get("success") is False:
                    err_msg = response_data.get("errorMessage", "Unknown API Error")
                    err_code = response_data.get("errorCode")
                    logger.error(f"TopStepX API reported failure at {endpoint}: {err_msg} (Code: {err_code})")
                    raise OperationFailedError(err_msg, provider_error_code=err_code, provider_error_message=err_msg)

                return expected_response_model.model_validate(response_data) if expected_response_model else response_data

            except (httpx.HTTPStatusError, httpx.RequestError) as e:
                # Check if it's a server error (5xx) or a transient request error
                is_server_error = isinstance(e, httpx.HTTPStatusError) and e.response.status_code >= 500
                is_transient_error = isinstance(e, httpx.RequestError)

                if is_server_error or is_transient_error:
                    last_exception = e
                    logger.warning(
                        f"Retryable HTTP error on attempt {attempt + 1}/{self._MAX_RETRIES} for {endpoint}: {e}. "
                        f"Retrying in {backoff_sec:.1f}s..."
                    )
                    await asyncio.sleep(backoff_sec)
                    backoff_sec *= 2  # Exponential backoff
                    continue
                else:
                    # It's a non-retryable client error (4xx) or other status error
                    raise TradeForgeConnectionError(f"HTTP error {e.response.status_code} on {endpoint}: {e.response.text[:200]}") from e
            
            except OperationFailedError:
                raise # Do not retry on logical API failures (e.g., "Insufficient Funds")
            
            except Exception as e:
                # Catch any other unexpected errors
                last_exception = e
                logger.error(f"Unexpected error during request to {endpoint}: {e}", exc_info=True)
                break # Stop retrying on unexpected errors

        # If all retries failed
        raise TradeForgeConnectionError(f"Request to {endpoint} failed after {self._MAX_RETRIES} retries.") from last_exception

    async def ts_get_accounts(self, only_active: bool = True) -> TSSearchAccountResponse:
        payload = TSSearchAccountRequest(onlyActiveAccounts=only_active).model_dump_json()
        return await self._request("POST", "/api/Account/search", content_payload=payload, expected_response_model=TSSearchAccountResponse)

    async def ts_search_contracts(self, search_text: str, live: bool = False) -> TSSearchContractResponse:
        payload = TSSearchContractRequest(searchText=search_text, live=live).model_dump_json()
        return await self._request("POST", "/api/Contract/search", content_payload=payload, expected_response_model=TSSearchContractResponse)

    async def ts_get_contract_by_id(self, contract_id: str) -> TSSearchContractByIdResponse:
        payload = TSSearchContractByIdRequest(contractId=contract_id).model_dump_json()
        return await self._request("POST", "/api/Contract/searchById", content_payload=payload, expected_response_model=TSSearchContractByIdResponse)

    async def ts_get_historical_bars(self, request: TSRetrieveBarRequest) -> TSRetrieveBarResponse:
        payload = request.model_dump_json(by_alias=True, exclude_none=True)
        return await self._request("POST", "/api/History/retrieveBars", content_payload=payload, expected_response_model=TSRetrieveBarResponse)

    async def ts_place_order(self, order_request: TSPlaceOrderRequest) -> TSPlaceOrderResponse:
        payload = order_request.model_dump_json(by_alias=True, exclude_none=True)
        return await self._request("POST", "/api/Order/place", content_payload=payload, expected_response_model=TSPlaceOrderResponse)

    async def ts_cancel_order(self, account_id: int, order_id: int) -> TSCancelOrderResponse:
        payload = TSCancelOrderRequest(accountId=account_id, orderId=order_id).model_dump_json()
        return await self._request("POST", "/api/Order/cancel", content_payload=payload, expected_response_model=TSCancelOrderResponse)

    async def ts_modify_order(self, modify_request: TSModifyOrderRequest) -> TSModifyOrderResponse:
        payload = modify_request.model_dump_json(by_alias=True, exclude_none=True)
        return await self._request("POST", "/api/Order/modify", content_payload=payload, expected_response_model=TSModifyOrderResponse)

    async def ts_search_orders(self, search_request: TSSearchOrderRequest) -> TSSearchOrderResponse:
        payload = search_request.model_dump_json(by_alias=True, exclude_none=True)
        return await self._request("POST", "/api/Order/search", content_payload=payload, expected_response_model=TSSearchOrderResponse)

    async def ts_search_open_orders(self, search_open_request: TSSearchOpenOrderRequest) -> TSSearchOrderResponse:
        payload = search_open_request.model_dump_json()
        return await self._request("POST", "/api/Order/searchOpen", content_payload=payload, expected_response_model=TSSearchOrderResponse)

    async def ts_search_open_positions(self, account_id: int) -> TSSearchPositionResponse:
        payload = TSSearchPositionRequest(accountId=account_id).model_dump_json()
        return await self._request("POST", "/api/Position/searchOpen", content_payload=payload, expected_response_model=TSSearchPositionResponse)

    async def ts_close_contract_position(self, account_id: int, contract_id: str) -> TSClosePositionResponse:
        payload = TSCloseContractPositionRequest(accountId=account_id, contractId=contract_id).model_dump_json()
        return await self._request("POST", "/api/Position/closeContract", content_payload=payload, expected_response_model=TSClosePositionResponse)

    async def ts_partial_close_contract_position(self, account_id: int, contract_id: str, size: int) -> TSPartialClosePositionResponse:
        payload = TSPartialCloseContractPositionRequest(accountId=account_id, contractId=contract_id, size=size).model_dump_json()
        return await self._request("POST", "/api/Position/partialCloseContract", content_payload=payload, expected_response_model=TSPartialClosePositionResponse)

    async def ts_search_trades(self, search_request: TSSearchTradeRequest) -> TSSearchHalfTradeResponse:
        payload = search_request.model_dump_json(by_alias=True, exclude_none=True)
        return await self._request("POST", "/api/Trade/search", content_payload=payload, expected_response_model=TSSearchHalfTradeResponse)

    async def close_http_client(self):
        """Closes the underlying httpx.AsyncClient session."""
        if self.async_client and not self.async_client.is_closed:
            logger.info("Closing TopStepXHttpClient's async client session.")
            await self.async_client.aclose()