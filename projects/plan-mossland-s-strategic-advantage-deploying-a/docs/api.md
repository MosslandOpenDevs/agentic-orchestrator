```markdown
# NFT & DeFi Portfolio Management API Documentation

## 1. Overview

This API provides a comprehensive suite of tools for managing an NFT portfolio within a DeFi ecosystem. It allows users to track NFT valuations, adjust positions in yield farms, view holdings, and retrieve asset prices. This API is designed for developers integrating portfolio management functionality into their applications.

## 2. Authentication Details

All API requests require an API key for authentication.  This key should be included in the `X-API-Key` header of each request.  You can obtain your API key from the [API Key Management Portal](https://your-api-key-portal.com).  This portal allows you to generate, revoke, and monitor API usage.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`

## 4. Endpoints

### 4.1. GET /api/nft/valuation

*   **Method:** `GET`
*   **Path:** `/api/nft/valuation`
*   **Description:** Retrieves the real-time valuation of a specified NFT.
*   **Request Parameters:**
    *   `nft_address` (required): The Ethereum address of the NFT to be valued.  (String)
*   **Response Format:** JSON
    *   `valuation` (Number): The current valuation of the NFT in USD.
    *   `timestamp` (Number): Unix timestamp of the valuation.
    *   `source` (String):  The data source used for the valuation (e.g., Chainlink, CoinGecko).
*   **Example Request:**
    ```
    GET /api/nft/valuation?nft_address=0xd8dA6611E982AC22B8670b47A58E04b8837c75Ea
    ```
*   **Example Response:**
    ```json
    {
      "valuation": 15000.75,
      "timestamp": 1678886400,
      "source": "Chainlink"
    }
    ```

### 4.2. POST /api/yieldfarm/adjust

*   **Method:** `POST`
*   **Path:** `/api/yieldfarm/adjust`
*   **Description:** Adjusts NFT positions in DeFi protocols based on yield farming strategies.  This endpoint requires a detailed strategy definition.
*   **Request Body:** JSON
    *   `strategy_id` (required): The ID of the yield farming strategy to execute. (String)
    *   `nft_address` (required): The Ethereum address of the NFT to adjust. (String)
    *   `amount` (required): The amount of the NFT to adjust (positive for buy, negative for sell). (Number)
    *   `protocol_address` (required): The address of the DeFi protocol. (String)
*   **Response Format:** JSON
    *   `status` (Boolean): Indicates success or failure.
    *   `message` (String):  A descriptive message about the operation.
    *   `transaction_hash` (String, optional): The transaction hash if the operation was successful.
*   **Example Request:**
    ```json
    {
      "strategy_id": "strat_123",
      "nft_address": "0xd8dA6611E982AC22B8670b47A58E04b8837c75Ea",
      "amount": -1.5,
      "protocol_address": "0x878866e682e4359573438698752192a8412c6184"
    }
    ```
*   **Example Response (Success):**
    ```json
    {
      "status": true,
      "message": "NFT position adjusted successfully.",
      "transaction_hash": "0x1234567890abcdef1234567890abcdef12345678"
    }
    ```
*   **Example Response (Failure):**
    ```json
    {
      "status": false,
      "message": "Failed to adjust NFT position.  Insufficient funds."
    }
    ```

### 4.3. GET /api/user/holdings

*   **Method:** `GET`
*   **Path:** `/api/user/holdings`
*   **Description:** Retrieves a user's NFT holdings.
*   **Request Parameters:**
    *   `user_id` (required): The unique identifier for the user. (String)
*   **Response Format:** JSON
    *   `holdings` (Array): An array of NFT holdings.
        *   `nft_address` (String): The Ethereum address of the NFT.
        *   `name` (String): The name of the NFT.
        *   `token_id` (String): The token ID of the NFT.
        *   `quantity` (Number): The quantity of the NFT held.
        *   `value` (Number): The current value of the NFT holdings in USD.
*   **Example Request:**
    ```
    GET /api/user/holdings?user_id=user_123
    ```
*   **Example Response:**
    ```json
    [
      {
        "nft_address": "0xd8dA6611E982AC22B8670b47A58E04b8837c75Ea",
        "name": "Bored Ape Yacht Club #123",
        "token_id": "123",
        "quantity": 1,
        "value": 20000.00
      },
      {
        "nft_address": "0x694792d3F885E388A647F2796647716E7F124F8e",
        "name": "CryptoPunks #456",
        "token_id": "456",
        "quantity": 2,
        "value": 15000.00
      }
    ]
    ```

### 4.4. GET /api/asset/price

*   **Method:** `GET`
*   **Path:** `/api/asset/price`
*   **Description:** Retrieves the current price of an asset.
*   **Request Parameters:**
    *   `asset_symbol` (required): The symbol of the asset (e.g., ETH, BTC). (String)
*   **Response Format:** JSON
    *   `symbol` (String): The asset symbol.
    *   `price` (Number): The current price of the asset in USD.
    *   `timestamp` (Number): Unix timestamp of the price.
*   **Example Request:**
    ```
    GET /api/asset/price?asset_symbol=ETH
    ```
*   **Example Response:**
    ```json
    {
      "symbol": "ETH",
      "price": 3800.50,
      "timestamp": 1678886400
    }
    ```

## 5. Error Codes and Handling

| Code      | Description                               |
|-----------|-------------------------------------------|
| 400        | Bad Request - Invalid input parameters.     |
| 401        | Unauthorized - Invalid or missing API key. |
| 404        | Not Found - Resource not found.            |
| 429        | Too Many Requests - Rate limit exceeded.   |
| 500        | Internal Server Error - Server error.       |

All error responses will include a JSON body with a `message` field providing details about the error.

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure fair usage.  The following rate limits apply:

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Burst Limit:**  A burst limit of 120 requests per minute is allowed for short periods.  Exceeding this limit will result in a 429 Too Many Requests error.

You can monitor your API usage and request a rate limit increase through the [API Key Management Portal](https://your-api-key-portal.com).
```
