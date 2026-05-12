```markdown
# NFT Rebalancing Protocol API Documentation

## 1. Overview

This API provides endpoints for managing and triggering the NFT rebalancing algorithm within the protocol. It interacts with Chainlink price feeds for accurate asset valuations and allows for automated rebalancing of NFT collateral to optimize returns.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for all requests.  Contact your system administrator to obtain a valid API key.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/nftCollateral

*   **Method:** `GET`
*   **Path:** `/api/nftCollateral`
*   **Description:** Retrieves all NFT collateral data associated with the protocol. This includes asset holdings, current valuations, and other relevant information.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each object in the array represents a single collateral asset.
    *   Example:
        ```json
        [
          {
            "assetId": "ETH",
            "quantity": 100,
            "valuation": 15000.00,
            "lastUpdated": "2023-10-27T10:00:00Z"
          },
          {
            "assetId": "USDC",
            "quantity": 5000,
            "valuation": 5000.00,
            "lastUpdated": "2023-10-27T10:00:00Z"
          }
        ]
        ```
*   **Example Request:**

    ```
    GET /api/nftCollateral
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON example above)

### 4.2. GET /api/priceFeeds

*   **Method:** `GET`
*   **Path:** `/api/priceFeeds`
*   **Description:** Retrieves current price feeds from Chainlink for supported assets. This is used by the rebalancing algorithm to determine accurate valuations.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each object represents a price feed for a specific asset.
    *   Example:
        ```json
        [
          {
            "assetId": "ETH",
            "price": 1800.50,
            "timestamp": 1698400000,
            "source": "Chainlink"
          },
          {
            "assetId": "USDC",
            "price": 1.00,
            "timestamp": 1698400000,
            "source": "Chainlink"
          }
        ]
        ```
*   **Example Request:**

    ```
    GET /api/priceFeeds
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON example above)

### 4.3. POST /api/rebalance

*   **Method:** `POST`
*   **Path:** `/api/rebalance`
*   **Description:** Triggers the rebalancing algorithm. This initiates the process of adjusting NFT collateral holdings based on current price feeds.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    *   Successful rebalancing will return a success message.
    *   Example:
        ```json
        {
          "status": "success",
          "message": "Rebalancing initiated successfully."
        }
        ```
*   **Example Request:**

    ```
    POST /api/rebalance
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters   | Check request body/parameters for errors |
| 401      | Unauthorized - Invalid API Key          | Provide a valid API Key in header    |
| 404      | Not Found - Endpoint or resource not found | Verify endpoint and resource existence |
| 500      | Internal Server Error                    | Contact system administrator         |
| 503      | Service Unavailable - Chainlink issues  | Retry request later                  |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure stability.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:** Rate limiting information will be returned in the response headers:
    *   `X-RateLimit-Limit`:  The maximum number of requests allowed in the current window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
    *   `X-RateLimit-Reset`: The timestamp (in Unix epoch seconds) when the rate limit resets.
```