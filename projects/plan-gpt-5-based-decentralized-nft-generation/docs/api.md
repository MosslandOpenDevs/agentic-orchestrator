```markdown
# NFT Portfolio and Trading API Documentation

## 1. Overview

This API provides functionalities for managing an NFT portfolio and executing trades based on automated rules. It leverages AI for NFT valuation and allows users to track and trade their NFT holdings.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  You can obtain your API key from the dashboard after registering an account.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1 GET /api/nft/valuation

*   **Method:** `GET`
*   **Path:** `/api/nft/valuation`
*   **Description:** Retrieves the real-time valuation of an NFT based on AI analysis.
*   **Request Parameters/Body:**
    *   `nft_token_address` (required): The Ethereum address of the NFT to be valued. (String)
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/valuation?nft_token_address=0xd8dA6611Ea88Ce2b4c1c79cBC9476438a9B34B37
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "token_address": "0xd8dA6611Ea88Ce2b4c1c79cBC9476438a9B34B37",
      "name": "Bored Ape Yacht Club #1777",
      "valuation": 12500.50,
      "valuation_method": "AI Analysis (Market Trends)",
      "timestamp": "2024-10-27T10:30:00Z"
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Invalid NFT Token Address"
    }
    ```

### 4.2 POST /api/portfolio/add_nft

*   **Method:** `POST`
*   **Path:** `/api/portfolio/add_nft`
*   **Description:** Adds an NFT to a user's portfolio.
*   **Request Parameters/Body:**
    *   `nft_token_address` (required): The Ethereum address of the NFT to be added. (String)
    *   `quantity` (required): The quantity of the NFT to add. (Integer)
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/portfolio/add_nft
    Content-Type: application/json

    {
      "nft_token_address": "0xd8dA6611Ea88Ce2b4c1c79cBC9476438a9B34B37",
      "quantity": 2
    }
    ```
*   **Example Response (Success - 201 Created):**

    ```json
    {
      "message": "NFT added to portfolio successfully",
      "portfolio_id": "user123"
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Invalid NFT Token Address or Quantity"
    }
    ```

### 4.3 GET /api/portfolio/get

*   **Method:** `GET`
*   **Path:** `/api/portfolio/get`
*   **Description:** Retrieves a user's portfolio.
*   **Request Parameters/Body:**
    *   `user_id` (required): The user ID to retrieve the portfolio for. (String)
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/portfolio/get?user_id=user123
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "user_id": "user123",
      "portfolio": [
        {
          "nft_token_address": "0xd8dA6611Ea88Ce2b4c1c79cBC9476438a9B34B37",
          "name": "Bored Ape Yacht Club #1777",
          "quantity": 2,
          "valuation": 25001.00
        },
        {
          "nft_token_address": "0x6E5250E384d99C92a2b8179e844993e674939539",
          "name": "CryptoPunk #622",
          "quantity": 1,
          "valuation": 18000.75
        }
      ]
    }
    ```

### 4.4 POST /api/trade/execute

*   **Method:** `POST`
*   **Path:** `/api/trade/execute`
*   **Description:** Executes a trade based on predefined automation rules.
*   **Request Parameters/Body:**
    *   `user_id` (required): The user ID initiating the trade. (String)
    *   `nft_token_address` (required): The Ethereum address of the NFT to trade. (String)
    *   `trade_type` (required): The type of trade - `BUY` or `SELL`. (String)
    *   `quantity` (required): The quantity of the NFT to trade. (Integer)
    *   `price` (optional): The desired price for the trade. If not provided, the system will use the current market price. (Float)
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/trade/execute
    Content-Type: application/json

    {
      "user_id": "user123",
      "nft_token_address": "0xd8dA6611Ea88Ce2b4c1c79cBC9476438a9B34B37",
      "trade_type": "SELL",
      "quantity": 1,
      "price": 12000.00
    }
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "message": "Trade executed successfully",
      "trade_id": "trade456"
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Invalid Trade Type or Quantity"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.         |
| 401      | Unauthorized - Invalid API key.          |
| 404      | Not Found - Resource not found.          |
| 500      | Internal Server Error - Server error.     |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure service stability.

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Limiting Mechanism:**  Rate limiting is implemented using HTTP status code 429 (Too Many Requests) if the rate limit is exceeded.  The `Retry-After` header will indicate the time to wait before making another request.
```
