```markdown
# NFT Portfolio API Documentation

## 1. Overview

This API provides tools for NFT portfolio management, including valuation, holdings tracking, market data retrieval, and portfolio optimization. It leverages GPT-5 for advanced NFT valuation and integrates with real-time market data sources.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  You can obtain an API key by registering an account on our platform.  Failure to provide a valid API key will result in a `401 Unauthorized` error.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`

(Replace `https://api.example.com/v1` with the actual base URL.)

## 4. Endpoints

### 4.1. GET /api/nft/valuation

*   **Method:** `GET`
*   **Path:** `/api/nft/valuation`
*   **Description:** Retrieves NFT valuation based on GPT-5 analysis.  This endpoint takes the NFT's metadata (name, description, collection, etc.) and uses GPT-5 to provide an estimated valuation.
*   **Request Parameters/Body:**
    *   `nft_id` (string, required): The unique identifier of the NFT.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/valuation?nft_id=0x1234567890abcdef1234567890abcdef1234
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "nft_id": "0x1234567890abcdef1234567890abcdef1234",
      "valuation": 1500.75,
      "gpt5_analysis": "GPT-5 analysis suggests a valuation based on market trends and rarity scores.  The analysis indicates strong potential due to recent community engagement.",
      "timestamp": "2024-10-27T10:00:00Z"
    }
    ```
*   **Example Response (Error - 400 Bad Request):**

    ```json
    {
      "error": "Invalid NFT ID format"
    }
    ```

### 4.2. GET /api/portfolio/holdings

*   **Method:** `GET`
*   **Path:** `/api/portfolio/holdings`
*   **Description:** Retrieves a user's NFT portfolio holdings.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/portfolio/holdings
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "user_id": "user123",
      "holdings": [
        {
          "nft_id": "0x1234567890abcdef1234567890abcdef1234",
          "name": "Cool NFT",
          "collection": "Awesome Collection",
          "quantity": 3,
          "purchase_price": 500.00,
          "current_price": 600.50
        },
        {
          "nft_id": "0xabcdef0123456789abcdef0123456789",
          "name": "Another NFT",
          "collection": "Different Collection",
          "quantity": 1,
          "purchase_price": 750.25,
          "current_price": 800.00
        }
      ]
    }
    ```

### 4.3. GET /api/market/data

*   **Method:** `GET`
*   **Path:** `/api/market/data`
*   **Description:** Retrieves real-time market data for NFTs.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/market/data
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "nft_id": "0x1234567890abcdef1234567890abcdef1234",
      "name": "Cool NFT",
      "collection": "Awesome Collection",
      "current_price": 650.75,
      "volume_24h": 12345.67,
      "floor_price": 500.00,
      "last_traded_price": "640.00",
      "timestamp": "2024-10-27T10:05:00Z"
    }
    ```

### 4.4. POST /api/portfolio/optimize

*   **Method:** `POST`
*   **Path:** `/api/portfolio/optimize`
*   **Description:** Generates portfolio optimization recommendations.  This endpoint takes a user's portfolio holdings and recommends adjustments to maximize returns based on current market conditions.
*   **Request Parameters/Body:**
    *   `holdings` (JSON array, required): An array of NFT holdings, as described in the `/api/portfolio/holdings` endpoint.
*   **Response Format:** JSON
*   **Example Request:**

    ```json
    POST /api/portfolio/optimize
    {
      "holdings": [
        {
          "nft_id": "0x1234567890abcdef1234567890abcdef1234",
          "name": "Cool NFT",
          "collection": "Awesome Collection",
          "quantity": 3,
          "purchase_price": 500.00,
          "current_price": 650.75
        },
        {
          "nft_id": "0xabcdef0123456789abcdef0123456789",
          "name": "Another NFT",
          "collection": "Different Collection",
          "quantity": 1,
          "purchase_price": 750.25,
          "current_price": 800.00
        }
      ]
    }
    ```
*   **Example Response (Success - 200 OK):**

    ```json
    {
      "recommendations": [
        {
          "nft_id": "0x1234567890abcdef1234567890abcdef1234",
          "action": "Sell",
          "quantity": 1,
          "reason": "Overvalued based on market trends."
        },
        {
          "nft_id": "0xabcdef0123456789abcdef0123456789",
          "action": "Buy",
          "quantity": 2,
          "reason": "Undervalued based on market trends."
        }
      ]
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.         |
| 401      | Unauthorized - Invalid API key.          |
| 403      | Forbidden - Insufficient permissions.   |
| 404      | Not Found - Resource not found.          |
| 500      | Internal Server Error - Server error.    |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.  The following rate limits apply:

*   **Requests per minute:** 60 requests per minute per API key.
*   **Burst Limit:** A burst of up to 120 requests per minute is allowed.  After exceeding this limit, requests will be throttled.

Rate limiting is enforced by HTTP status code 429 (Too Many Requests).  Response headers will include `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` to indicate the rate limit status.
```
