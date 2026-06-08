```markdown
# NFT Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing NFT positions, retrieving risk profiles, accessing real-time market data, and triggering automated rebalancing strategies. It's designed to be integrated into a user's portfolio management system, providing a centralized source of information and control.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain your API key by registering an account on our platform.  This key is used for authorization and tracking usage.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.exampleportfolio.com/v1`

(Replace `https://api.exampleportfolio.com/v1` with the actual base URL of your API.)

## 4. API Endpoints

### 4.1. GET /api/nftPositions

*   **Method:** `GET`
*   **Path:** `/api/nftPositions`
*   **Description:** Retrieves all NFT positions for a given user.
*   **Request Parameters/Body:**
    *   `user_id` (required): The unique identifier of the user.  (Integer or String)
*   **Response Format:** JSON
    ```json
    {
      "user_id": 123,
      "positions": [
        {
          "asset_id": "NFT-001",
          "quantity": 5,
          "purchase_price": 100.00,
          "current_price": 120.00,
          "profit": 20.00
        },
        {
          "asset_id": "NFT-002",
          "quantity": 10,
          "purchase_price": 50.00,
          "current_price": 60.00,
          "profit": 10.00
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/nftPositions HTTP/1.1
    X-API-Key: YOUR_API_KEY
    user_id=123
    ```
*   **Example Response:** (See JSON response above)

### 4.2. GET /api/riskProfiles

*   **Method:** `GET`
*   **Path:** `/api/riskProfiles`
*   **Description:** Retrieves the risk profile for a given user.
*   **Request Parameters/Body:**
    *   `user_id` (required): The unique identifier of the user. (Integer or String)
*   **Response Format:** JSON
    ```json
    {
      "user_id": 123,
      "risk_profile": "Aggressive",
      "risk_tolerance": "High",
      "investment_horizon": "Short"
    }
    ```
*   **Example Request:**
    ```
    GET /api/riskProfiles HTTP/1.1
    X-API-Key: YOUR_API_KEY
    user_id=123
    ```
*   **Example Response:** (See JSON response above)

### 4.3. GET /api/marketData/{asset}

*   **Method:** `GET`
*   **Path:** `/api/marketData/{asset}`
*   **Description:** Retrieves real-time market data for a given DeFi asset.
*   **Request Parameters/Body:**
    *   `asset` (required): The symbol of the DeFi asset (e.g., "ETH", "BTC"). (String)
*   **Response Format:** JSON
    ```json
    {
      "asset": "ETH",
      "price": 3700.50,
      "volume": 123456789.00,
      "change_percent": 0.05,
      "last_updated": "2023-10-27T10:00:00Z"
    }
    ```
*   **Example Request:**
    ```
    GET /api/marketData/ETH HTTP/1.1
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON response above)

### 4.4. POST /api/rebalance

*   **Method:** `POST`
*   **Path:** `/api/rebalance`
*   **Description:** Triggers the GPT-5 agent to generate a rebalancing strategy.
*   **Request Parameters/Body:**
    *   `user_id` (required): The unique identifier of the user. (Integer or String)
    *   `risk_profile` (optional): The user's risk profile (e.g., "Conservative", "Moderate", "Aggressive"). (String)
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "message": "Rebalancing strategy generated successfully.",
      "strategy": {
        "asset_allocation": {
          "ETH": 0.3,
          "BTC": 0.2,
          "USDT": 0.5
        },
        "recommendation": "Rebalance portfolio to align with aggressive risk profile."
      }
    }
    ```
*   **Example Request:**
    ```
    POST /api/rebalance HTTP/1.1
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "user_id": 123,
      "risk_profile": "Aggressive"
    }
    ```
*   **Example Response:** (See JSON response above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters   | Validate request body and parameters |
| 401      | Unauthorized - Invalid API key           | Provide a valid API key             |
| 404      | Not Found - Resource not found           | Check asset ID or user ID           |
| 500      | Internal Server Error - Server issue     | Contact support                     |
| 503      | Service Unavailable - Service is down    | Retry later                        |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for a short burst of activity)
*   **Reset Time:** 60 seconds

Exceeding the rate limits will result in a `429 Too Many Requests` error.  The response headers will include `Retry-After` to indicate when the rate limit will be reset.  Detailed rate limiting information is available in the API documentation.
```