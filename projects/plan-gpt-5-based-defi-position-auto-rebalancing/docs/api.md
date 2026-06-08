```markdown
# NFT Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing NFT positions, retrieving risk profiles, accessing real-time price data, and triggering automated rebalancing strategies. It is designed to integrate with a user's portfolio management system, providing data and functionality for informed decision-making.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  This key must be provided for every request.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`

## 4. Endpoints

### 4.1. GET /api/nftPositions

*   **Method:** GET
*   **Path:** `/api/nftPositions`
*   **Description:** Retrieves all NFT positions for a given user.
*   **Request Parameters/Body:**
    *   `userId` (required, string): The unique identifier for the user.
*   **Response Format:** JSON
    *   `data`: An array of NFT position objects.
        *   Each position object contains:
            *   `tokenId` (string): The unique identifier of the NFT.
            *   `quantity` (integer): The number of NFTs held.
            *   `assetToken` (string): The token address of the NFT.
            *   `lastTradePrice` (number): The last traded price of the asset.
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        GET /api/nftPositions?userId=user123
        ```

    *   **Response (200 OK):**
        ```json
        {
          "data": [
            {
              "tokenId": "0x1234567890abcdef",
              "quantity": 10,
              "assetToken": "0xabcde...",
              "lastTradePrice": 150.75
            },
            {
              "tokenId": "0x9876543210fedcba",
              "quantity": 5,
              "assetToken": "0xbcdef...",
              "lastTradePrice": 225.50
            }
          ]
        }
        ```

### 4.2. GET /api/riskProfiles

*   **Method:** GET
*   **Path:** `/api/riskProfiles`
*   **Description:** Retrieves the risk profile for a given user.
*   **Request Parameters/Body:**
    *   `userId` (required, string): The unique identifier for the user.
*   **Response Format:** JSON
    *   `data`: A risk profile object.
        *   `riskLevel` (string):  The user's risk level (e.g., "Conservative", "Moderate", "Aggressive").
        *   `assetAllocation` (object):  An object defining the recommended asset allocation based on the risk level.
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        GET /api/riskProfiles?userId=user123
        ```

    *   **Response (200 OK):**
        ```json
        {
          "data": {
            "riskLevel": "Moderate",
            "assetAllocation": {
              "ETH": 0.3,
              "BTC": 0.2,
              "SOL": 0.1
            }
          }
        }
        ```

### 4.3. GET /api/priceData/{assetToken}

*   **Method:** GET
*   **Path:** `/api/priceData/{assetToken}`
*   **Description:** Retrieves real-time price data for a given asset token.
*   **Request Parameters/Body:**
    *   `assetToken` (required, string): The token address of the asset.
*   **Response Format:** JSON
    *   `data`: A price data object.
        *   `price` (number): The current price of the asset.
        *   `volume` (number): The 24-hour trading volume.
        *   `lastUpdated` (string): Timestamp of the last price update (ISO 8601 format).
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        GET /api/priceData/0xabcde...
        ```

    *   **Response (200 OK):**
        ```json
        {
          "data": {
            "price": 300.25,
            "volume": 1234567.89,
            "lastUpdated": "2023-10-27T10:00:00Z"
          }
        }
        ```

### 4.4. POST /api/rebalance

*   **Method:** POST
*   **Path:** `/api/rebalance`
*   **Description:** Triggers the GPT-5 agent to generate a rebalancing strategy.
*   **Request Parameters/Body:**
    *   `userId` (required, string): The unique identifier for the user.
*   **Response Format:** JSON
    *   `data`: A rebalancing strategy object.
        *   `strategy` (string): The generated rebalancing strategy.
        *   `recommendations` (array): An array of recommendations for buying or selling assets.
*   **Example Requests/Responses:**

    *   **Request:**
        ```
        POST /api/rebalance
        Content-Type: application/json

        {
          "userId": "user123"
        }
        ```

    *   **Response (200 OK):**
        ```json
        {
          "data": {
            "strategy": "Aggressive Growth",
            "recommendations": [
              {
                "assetToken": "0xabcde...",
                "action": "Buy",
                "quantity": 5
              },
              {
                "assetToken": "0xbcdef...",
                "action": "Sell",
                "quantity": 2
              }
            ]
          }
        }
        ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters  | Check request body and parameters.   |
| 401      | Unauthorized - Invalid API key          | Provide a valid API key in the header. |
| 404      | Not Found - Resource not found           | Verify the resource ID and endpoint.  |
| 500      | Internal Server Error                    | Contact API support.                |
| 503      | Service Unavailable - API is down       | Retry the request later.            |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse.  The following limits apply:

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Headers:** Rate limit information is returned in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.  Example: `X-RateLimit-Limit: 60`, `X-RateLimit-Remaining: 45`, `X-RateLimit-Reset: 1678886400` (Unix timestamp).  Exceeding the rate limit will result in a 429 Too Many Requests error.
```
