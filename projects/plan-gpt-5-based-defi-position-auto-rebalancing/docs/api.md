```markdown
# NFT Portfolio & Rebalancing API Documentation

## 1. Overview

This API provides endpoints for managing an NFT portfolio and generating rebalancing strategies. It allows users to retrieve their portfolio data, access Rain stablecoin market data, and create new rebalancing strategies.  This API is designed to be used by developers building applications that interact with our NFT platform and require dynamic portfolio adjustments.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  You can obtain your API key from the platform dashboard.  Ensure your API key is kept confidential.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/nft/portfolio

*   **Method:** `GET`
*   **Path:** `/api/nft/portfolio`
*   **Description:** Retrieves a user's NFT portfolio data, including holdings, values, and performance metrics.
*   **Request Parameters/Body:**
    *   `user_id` (required): The unique identifier for the user.  (Integer)
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/portfolio?user_id=123
    ```
*   **Example Response:**

    ```json
    {
      "user_id": 123,
      "portfolio_value": 12345.67,
      "total_assets": 12345.67,
      "holdings": [
        {
          "nft_id": "NFT001",
          "name": "Example NFT",
          "token_address": "0x...",
          "quantity": 10,
          "current_price": 123.45,
          "value": 1234.50
        },
        {
          "nft_id": "NFT002",
          "name": "Another NFT",
          "token_address": "0x...",
          "quantity": 5,
          "current_price": 246.90,
          "value": 1234.50
        }
      ],
      "performance": {
        "daily_change": 0.05,
        "weekly_change": 0.10,
        "monthly_change": 0.20
      }
    }
    ```

### 4.2. GET /api/marketdata/rain

*   **Method:** `GET`
*   **Path:** `/api/marketdata/rain`
*   **Description:** Retrieves Rain stablecoin market data, including price, volume, and order book information.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/marketdata/rain
    ```
*   **Example Response:**

    ```json
    {
      "symbol": "RAIN",
      "price": 1.00,
      "volume_24h": 1234567.89,
      "high_24h": 1.05,
      "low_24h": 0.95,
      "order_book": [
        {"price": 1.02, "quantity": 1000},
        {"price": 1.01, "quantity": 2000},
        {"price": 1.00, "quantity": 3000}
      ]
    }
    ```

### 4.3. POST /api/rebalance

*   **Method:** `POST`
*   **Path:** `/api/rebalance`
*   **Description:** Generates a new portfolio rebalancing strategy based on user-defined parameters.
*   **Request Parameters/Body:**

    *   `user_id` (required): The unique identifier for the user. (Integer)
    *   `risk_tolerance` (required):  A numerical value representing the user's risk tolerance (1-5, 1 being most conservative, 5 being most aggressive). (Integer)
    *   `investment_horizon` (required): The investment horizon in days. (Integer)
    *   `nft_whitelist` (optional): An array of NFT IDs to include in the rebalancing strategy. If not provided, all NFTs will be considered. (Array of Strings)
*   **Response Format:** JSON
*   **Example Request:**

    ```json
    POST /api/rebalance
    Content-Type: application/json

    {
      "user_id": 456,
      "risk_tolerance": 3,
      "investment_horizon": 30,
      "nft_whitelist": ["NFT001", "NFT003"]
    }
    ```
*   **Example Response:**

    ```json
    {
      "status": "success",
      "strategy_id": "STR001",
      "rebalancing_recommendations": [
        {
          "nft_id": "NFT001",
          "action": "buy",
          "quantity": 2,
          "percentage": 10
        },
        {
          "nft_id": "NFT002",
          "action": "sell",
          "quantity": 1,
          "percentage": 5
        }
      ],
      "strategy_notes": "This strategy aims for a balanced portfolio based on your risk tolerance and investment horizon, focusing on NFTs in the whitelist."
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Response Body                               |
| :------ | :---------------------------------------- | :----------------------------------------- |
| 400      | Bad Request - Invalid input data          | `{"error": "Invalid input data"}`            |
| 401      | Unauthorized - Invalid API key           | `{"error": "Invalid API key"}`             |
| 403      | Forbidden - User does not have permission | `{"error": "Forbidden: Insufficient permissions"}` |
| 404      | Not Found - Resource not found            | `{"error": "Resource not found"}`           |
| 500      | Internal Server Error                    | `{"error": "Internal server error"}`        |

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per minute:** 60 requests
*   **Burst Limit:**  A burst of 120 requests is allowed, after which the rate limit resets.
*   **Rate Limit Headers:**  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response to indicate the current rate limit status.  Example: `X-RateLimit-Limit: 60, X-RateLimit-Remaining: 54, X-RateLimit-Reset: 1678886400` (Timestamp in seconds).  Exceeding the rate limit will result in a 429 (Too Many Requests) error.
```