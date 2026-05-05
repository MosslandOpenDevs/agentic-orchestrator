```markdown
# Secure Portfolio Rebalancing API

## 1. Overview

This API provides tools for managing and executing investment strategies, leveraging real-time security data and blockchain technology. It allows users to generate rebalancing recommendations, execute trades on the Ethereum blockchain, and retrieve real-time security prices.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be obtained through a secure registration process.  The API key is used for authorization and rate limiting.  Contact support@secureportfolio.com to obtain an API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.secureportfolio.com/v1`

## 4. Endpoints

### 4.1. GET /api/security-prices

*   **Method:** `GET`
*   **Path:** `/api/security-prices`
*   **Description:** Retrieves real-time security prices from DTCC and other sources.  Supports fetching prices for various asset classes (Stocks, Bonds, Commodities).
*   **Request Parameters/Body:**
    *   `asset_class` (optional, string): Filter by asset class (e.g., "stocks", "bonds", "commodities").  If not provided, all asset classes are returned.
    *   `symbol` (optional, string): Filter by security symbol (e.g., "AAPL", "GOOG").
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/security-prices?asset_class=stocks&symbol=AAPL
    ```
*   **Example Response:**
    ```json
    [
      {
        "symbol": "AAPL",
        "asset_class": "stocks",
        "price": 175.34,
        "timestamp": "2023-10-27T10:00:00Z"
      },
      {
        "symbol": "MSFT",
        "asset_class": "stocks",
        "price": 330.12,
        "timestamp": "2023-10-27T10:00:00Z"
      }
    ]
    ```

### 4.2. POST /api/rebalance

*   **Method:** `POST`
*   **Path:** `/api/rebalance`
*   **Description:** Generates a rebalancing recommendation for a user based on their portfolio holdings and risk tolerance.
*   **Request Parameters/Body:**
    *   `user_id` (required, string): The unique identifier for the user.
    *   `risk_tolerance` (required, string): The user's risk tolerance level (e.g., "low", "medium", "high").
    *   `portfolio_holdings` (required, JSON):  A JSON object representing the user's current portfolio holdings.  Example:
        ```json
        {
          "AAPL": 100,
          "MSFT": 50,
          "GOOG": 25
        }
        ```
*   **Response Format:** JSON
*   **Example Request:**
    ```
    POST /api/rebalance
    Content-Type: application/json

    {
      "user_id": "user123",
      "risk_tolerance": "medium",
      "portfolio_holdings": {
        "AAPL": 100,
        "MSFT": 50,
        "GOOG": 25
      }
    }
    ```
*   **Example Response:**
    ```json
    {
      "user_id": "user123",
      "recommendation": {
        "AAPL": 50,
        "MSFT": 75,
        "GOOG": 25,
        "rebalancing_reason": "Adjust portfolio to align with medium risk tolerance."
      }
    }
    ```

### 4.3. POST /api/execute-trade

*   **Method:** `POST`
*   **Path:** `/api/execute-trade`
*   **Description:** Executes a trade on the Ethereum blockchain using a smart contract.  This endpoint requires the user to have a connected Ethereum wallet.
*   **Request Parameters/Body:**
    *   `user_id` (required, string): The unique identifier for the user.
    *   `asset_symbol` (required, string): The symbol of the asset to trade (e.g., "ETH").
    *   `quantity` (required, integer): The number of units to trade.
    *   `trade_type` (required, string): The type of trade ("buy" or "sell").
    *   `smart_contract_address` (required, string): The address of the smart contract to execute the trade against.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    POST /api/execute-trade
    Content-Type: application/json

    {
      "user_id": "user456",
      "asset_symbol": "ETH",
      "quantity": 1.5,
      "trade_type": "buy",
      "smart_contract_address": "0x1234567890ABCdef01234567890abcdef"
    }
    ```
*   **Example Response:**
    ```json
    {
      "user_id": "user456",
      "asset_symbol": "ETH",
      "quantity": 1.5,
      "trade_type": "buy",
      "transaction_hash": "0xabcdef1234567890abcdef1234567890abcdef",
      "status": "pending"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input data        | Validate request parameters and body. |
| 401      | Unauthorized - Invalid API key         | Ensure API key is correct and valid. |
| 403      | Forbidden - Insufficient permissions   | Check user permissions.            |
| 404      | Not Found - Resource not found           | Verify endpoint and resource exist.  |
| 500      | Internal Server Error - Server issue     | Contact support@secureportfolio.com. |
| 503      | Service Unavailable - Service down       | Retry request later.                |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure service availability.  The rate limit is 100 requests per minute per API key.  Exceeding this limit will result in a 429 Too Many Requests error.

*   **Limit:** 100 requests per minute
*   **Header:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset` (returned with each response)
```
