```markdown
# NFT Valuation & Portfolio API Documentation

## 1. Overview

This API provides endpoints for retrieving NFT valuations, portfolio holdings, and risk assessments. It is designed to integrate with your application for providing users with valuable insights into their NFT investments.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be obtained from the API provider.  Failure to provide a valid API key will result in a 401 Unauthorized error.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with the actual base URL)

## 4. Endpoints

### 4.1. GET /api/nft/valuation

*   **Method:** GET
*   **Path:** /api/nft/valuation
*   **Description:** Retrieves the GPT-5 valuation for a given NFT. This endpoint utilizes a sophisticated model to estimate the market value of an NFT based on various factors.
*   **Request Parameters/Body:**

    *   `nft_id` (string, required): The unique identifier of the NFT.
*   **Response Format:** JSON

    ```json
    {
      "nft_id": "0x...",
      "valuation": 12345.67,
      "valuation_currency": "USD",
      "confidence_level": 0.85,
      "last_updated": "2023-10-27T10:00:00Z"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**

        `GET /api/nft/valuation?nft_id=0x1234567890abcdef1234567890abcdef1234`
    *   **Response (Success - 200 OK):**

        ```json
        {
          "nft_id": "0x1234567890abcdef1234567890abcdef1234",
          "valuation": 67890.23,
          "valuation_currency": "USD",
          "confidence_level": 0.92,
          "last_updated": "2023-10-27T10:30:00Z"
        }
        ```

*   **Error Codes:**
    *   400 Bad Request: Invalid `nft_id` format.
    *   404 Not Found: NFT with the given `nft_id` not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

### 4.2. GET /api/portfolio/holdings

*   **Method:** GET
*   **Path:** /api/portfolio/holdings
*   **Description:** Retrieves the portfolio holdings for a given user.
*   **Request Parameters/Body:**

    *   `user_id` (string, required): The unique identifier of the user.
*   **Response Format:** JSON

    ```json
    {
      "user_id": "user123",
      "holdings": [
        {
          "nft_id": "0x...",
          "name": "My Awesome NFT",
          "quantity": 5,
          "value": 12345.67,
          "value_currency": "USD"
        },
        {
          "nft_id": "0x...",
          "name": "Another NFT",
          "quantity": 10,
          "value": 23456.78,
          "value_currency": "USD"
        }
      ]
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**

        `GET /api/portfolio/holdings?user_id=user123`
    *   **Response (Success - 200 OK):**

        ```json
        {
          "user_id": "user123",
          "holdings": [
            {
              "nft_id": "0x...",
              "name": "My Awesome NFT",
              "quantity": 5,
              "value": 12345.67,
              "value_currency": "USD"
            },
            {
              "nft_id": "0x...",
              "name": "Another NFT",
              "quantity": 10,
              "value": 23456.78,
              "value_currency": "USD"
            }
          ]
        }
        ```

*   **Error Codes:**
    *   400 Bad Request: Invalid `user_id` format.
    *   404 Not Found: User with the given `user_id` not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

### 4.3. GET /api/nft/risk

*   **Method:** GET
*   **Path:** /api/nft/risk
*   **Description:** Calculates the risk assessment for a given NFT. This endpoint analyzes various market data and NFT characteristics to provide a risk score.
*   **Request Parameters/Body:**

    *   `nft_id` (string, required): The unique identifier of the NFT.
*   **Response Format:** JSON

    ```json
    {
      "nft_id": "0x...",
      "risk_score": 0.7,
      "risk_level": "Medium",
      "description": "This NFT exhibits moderate volatility and liquidity risk.",
      "last_calculated": "2023-10-27T09:00:00Z"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**

        `GET /api/nft/risk?nft_id=0x1234567890abcdef1234567890abcdef1234`
    *   **Response (Success - 200 OK):**

        ```json
        {
          "nft_id": "0x1234567890abcdef1234567890abcdef1234",
          "risk_score": 0.65,
          "risk_level": "Low",
          "description": "This NFT shows low volatility and high liquidity.",
          "last_calculated": "2023-10-27T09:30:00Z"
        }
        ```

*   **Error Codes:**
    *   400 Bad Request: Invalid `nft_id` format.
    *   404 Not Found: NFT with the given `nft_id` not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

## 5. Error Codes and Handling

| Code    | Description                      | Handling                               |
| :------ | :------------------------------- | :------------------------------------- |
| 400      | Bad Request                      | Validate input data. Log the error.    |
| 401      | Unauthorized (Invalid API Key) | Verify API key. Redirect to login page. |
| 404      | Not Found                        | Check resource existence. Log error.     |
| 500      | Internal Server Error            | Log detailed error information.        |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:**  Rate limit information will be returned in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time until the rate limit resets (in seconds).
```