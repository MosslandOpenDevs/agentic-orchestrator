```markdown
# NFT & DeFi Portfolio Management API Documentation

## 1. Overview

This API provides tools for managing and analyzing an NFT and DeFi portfolio. It allows users to retrieve their NFT positions, access real-time DeFi data, generate rebalancing strategies, and send data for analysis using a GPT-5 model.  This API is designed for integration with a user interface or other applications seeking to manage a user's crypto portfolio.

## 2. Authentication Details

All API endpoints require an API key for authentication. This key should be passed in the `X-API-Key` header of each request.

*   **Key Generation:** API keys can be generated through a secure process (details omitted for brevity – contact support for key generation).
*   **Security:**  Treat your API key as a password.  Do not share it publicly or commit it to version control.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.exampleportfolio.com/v1`

(Replace `https://api.exampleportfolio.com/v1` with the actual base URL)

## 4. API Endpoints

### 4.1 GET /api/nftPositions

*   **Method:** `GET`
*   **Path:** `/api/nftPositions`
*   **Description:** Retrieves all NFT positions for a given user.
*   **Request Parameters/Body:**
    *   `user_id` (required, string): The unique identifier for the user.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/nftPositions?user_id=user123
    ```
*   **Example Response (200 OK):**
    ```json
    [
      {
        "nft_name": "CoolCat #123",
        "contract_address": "0x...",
        "quantity": 5,
        "price_usd": 1500.00,
        "last_updated": "2023-10-27T10:00:00Z"
      },
      {
        "nft_name": "PixelPanda #456",
        "contract_address": "0x...",
        "quantity": 10,
        "price_usd": 75.00,
        "last_updated": "2023-10-27T10:00:00Z"
      }
    ]
    ```

### 4.2 GET /api/defiData/{protocol}

*   **Method:** `GET`
*   **Path:** `/api/defiData/{protocol}`
*   **Description:** Retrieves real-time DeFi data for a specified protocol.
*   **Request Parameters/Body:**
    *   `protocol` (required, string): The DeFi protocol to retrieve data for (e.g., "Uniswap", "Aave", "Chainlink").
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/defiData/Uniswap
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "protocol": "Uniswap",
      "liquidity_pools": [
        {"token_a": "ETH", "token_b": "DAI", "total_value": 10000000.00},
        {"token_a": "USDC", "token_b": "DAI", "total_value": 5000000.00}
      ],
      "timestamp": "2023-10-27T10:00:00Z"
    }
    ```

### 4.3 POST /api/rebalance

*   **Method:** `POST`
*   **Path:** `/api/rebalance`
*   **Description:** Generates a rebalancing strategy based on the current NFT positions and risk profile.
*   **Request Parameters/Body:**
    *   `user_id` (required, string): The unique identifier for the user.
    *   `risk_profile` (required, string):  The user's risk profile (e.g., "conservative", "moderate", "aggressive").
    *   `investment_amount` (optional, number): The amount to invest in the rebalancing strategy. Defaults to user's portfolio value.
*   **Response Format:** JSON
*   **Example Request:**
    ```json
    POST /api/rebalance
    {
      "user_id": "user123",
      "risk_profile": "moderate",
      "investment_amount": 10000
    }
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "strategy_name": "Moderate Rebalance",
      "recommendations": [
        {"protocol": "Aave", "asset": "ETH", "amount": 2000},
        {"protocol": "Uniswap", "asset": "DAI", "amount": 1000}
      ],
      "timestamp": "2023-10-27T10:00:00Z"
    }
    ```

### 4.4 GET /api/gpt5/analyze

*   **Method:** `GET`
*   **Path:** `/api/gpt5/analyze`
*   **Description:** Sends data to the GPT-5 API for analysis.  This endpoint is used for advanced portfolio analysis and insights.
*   **Request Parameters/Body:**
    *   `user_id` (required, string): The unique identifier for the user.
    *   `data` (required, string):  A JSON string containing the portfolio data to be analyzed (e.g., NFT positions, DeFi holdings, transaction history).
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/gpt5/analyze?user_id=user123&data={"nft_positions": [...], "defi_holdings": [...]}
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "analysis_type": "Portfolio Risk Assessment",
      "results": "Your portfolio is moderately risky. Consider diversifying...",
      "timestamp": "2023-10-27T10:00:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters   | Validate request body and parameters |
| 401      | Unauthorized - Invalid API key          | Provide a valid API key            |
| 404      | Not Found - Resource not found           | Verify endpoint and parameters      |
| 429      | Too Many Requests - Rate Limit Exceeded | Implement retry logic with exponential backoff |
| 500      | Internal Server Error                    | Contact support for assistance       |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure stability.

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Burst Handling:**  A short burst of requests (e.g., 10 requests in 10 seconds) will be tolerated, but sustained high-volume requests will be throttled.
*   **Rate Limit Headers:** The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response to indicate the current rate limit status.
```
