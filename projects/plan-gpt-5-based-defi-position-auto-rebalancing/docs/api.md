```markdown
# NFT Portfolio & Prediction API Documentation

## 1. Overview

This API provides access to NFT portfolio data, real-time market data, and GPT-5 powered NFT prediction capabilities. It allows users to retrieve their NFT holdings, analyze market trends, and gain insights into potential NFT investments.

## 2. Authentication Details

All API endpoints require an API key for authentication.  This key should be passed in the `X-API-Key` header of each request.  You can obtain your API key by registering an account through our platform.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with the actual base URL)

## 4. API Endpoints

### 4.1. GET /api/nft/portfolio

*   **Method:** `GET`
*   **Path:** `/api/nft/portfolio`
*   **Description:** Retrieves a user's NFT portfolio holdings.
*   **Request Parameters/Body:**
    *   `user_id` (required): The ID of the user whose portfolio is being requested.
*   **Response Format:** JSON
    ```json
    {
      "user_id": "user123",
      "portfolio": [
        {
          "nft_id": "nft456",
          "name": "Cool NFT",
          "token_name": "COOL",
          "token_symbol": "COOL",
          "quantity": 5,
          "price": 150.00,
          "last_updated": "2024-10-27T10:00:00Z"
        },
        {
          "nft_id": "nft789",
          "name": "Another NFT",
          "token_name": "ANOTHER",
          "token_symbol": "ANOTHER",
          "quantity": 10,
          "price": 75.50,
          "last_updated": "2024-10-27T10:01:00Z"
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/nft/portfolio HTTP/1.1
    X-API-Key: YOUR_API_KEY
    User-Agent: curl/7.79.1
    ```
*   **Example Response:** (See JSON response above)

### 4.2. GET /api/nft/marketdata

*   **Method:** `GET`
*   **Path:** `/api/nft/marketdata`
*   **Description:** Retrieves real-time market data for an NFT.
*   **Request Parameters/Body:**
    *   `nft_id` (required): The ID of the NFT for which market data is requested.
*   **Response Format:** JSON
    ```json
    {
      "nft_id": "nft456",
      "name": "Cool NFT",
      "token_name": "COOL",
      "token_symbol": "COOL",
      "current_price": 165.25,
      "volume_24h": 12345.67,
      "floor_price": 140.00,
      "last_updated": "2024-10-27T10:02:00Z"
    }
    ```
*   **Example Request:**
    ```
    GET /api/nft/marketdata HTTP/1.1
    X-API-Key: YOUR_API_KEY
    User-Agent: curl/7.79.1
    ```
*   **Example Response:** (See JSON response above)

### 4.3. POST /api/gpt5/predict

*   **Method:** `POST`
*   **Path:** `/api/gpt5/predict`
*   **Description:** Generates a GPT-5 prediction for an NFT.
*   **Request Parameters/Body:**
    *   `nft_id` (required): The ID of the NFT for which to generate a prediction.
    *   `prediction_type` (optional, default: "price"): The type of prediction to generate (e.g., "price", "volume").
*   **Response Format:** JSON
    ```json
    {
      "nft_id": "nft456",
      "prediction_type": "price",
      "prediction": 175.00,
      "confidence": 0.85,
      "timestamp": "2024-10-27T10:03:00Z"
    }
    ```
*   **Example Request:**
    ```
    POST /api/gpt5/predict HTTP/1.1
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "nft_id": "nft456",
      "prediction_type": "price"
    }
    ```
*   **Example Response:** (See JSON response above)

### 4.4. GET /api/nft/metadata

*   **Method:** `GET`
*   **Path:** `/api/nft/metadata`
*   **Description:** Retrieves metadata for an NFT.
*   **Request Parameters/Body:**
    *   `nft_id` (required): The ID of the NFT for which metadata is requested.
*   **Response Format:** JSON
    ```json
    {
      "nft_id": "nft456",
      "name": "Cool NFT",
      "token_name": "COOL",
      "token_symbol": "COOL",
      "description": "A cool NFT for cool people.",
      "image_url": "https://example.com/cool_nft.png",
      "attributes": [
        {
          "trait_type": "Background",
          "value": "Blue"
        },
        {
          "trait_type": "Eyes",
          "value": "Green"
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/nft/metadata HTTP/1.1
    X-API-Key: YOUR_API_KEY
    User-Agent: curl/7.79.1
    ```
*   **Example Response:** (See JSON response above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                                     |
| :------ | :--------------------------------------- | :----------------------------------------- |
| 400      | Bad Request - Invalid Input              | Check request parameters for errors.        |
| 401      | Unauthorized - Missing or Invalid API Key | Provide a valid API key in the `X-API-Key` header. |
| 404      | Not Found - Resource Not Found            | Verify the `nft_id` or `user_id` is correct.   |
| 500      | Internal Server Error                    | Contact support for assistance.            |
| 429      | Too Many Requests - Rate Limit Exceeded | Implement retry logic with exponential backoff. |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for short bursts)
*   **Headers:** Rate limiting information is provided in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed in the current time window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current time window.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```