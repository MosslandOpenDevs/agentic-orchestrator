```markdown
# Billions Network API Documentation

## 1. Overview

This document outlines the Billions Network API, providing access to real-time market data, a GPT-5 prompt API, and portfolio data retrieval. The API is designed for developers to integrate Billions Network data and functionality into their applications.

## 2. Authentication Details

Currently, the Billions Network API does not require authentication for all endpoints. However, future versions may implement API keys or OAuth 2.0 for enhanced security and usage tracking.  Please check the API status page for any changes.

## 3. Base URL Configuration

The base URL for all Billions Network API endpoints is:

`https://api.billionsnetwork.com`

## 4. Endpoints

### 4.1. GET /api/billions/nft/data

*   **Method:** GET
*   **Path:** `/api/billions/nft/data`
*   **Description:** Retrieves real-time market data for Billions Network assets. This endpoint provides data such as price, volume, market cap, and trading volume for various assets.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/billions/nft/data
    ```
*   **Example Response:**
    ```json
    {
      "assets": [
        {
          "symbol": "BNT",
          "name": "Billions Token",
          "price": 123.45,
          "volume": 123456789.00,
          "market_cap": 12345678900.00,
          "change_24h": 1.23
        },
        {
          "symbol": "BLN",
          "name": "Billions Network Native",
          "price": 56.78,
          "volume": 987654321.00,
          "market_cap": 56789012345.00,
          "change_24h": -0.87
        }
      ]
    }
    ```

### 4.2. GET /api/gpt5/prompt

*   **Method:** GET
*   **Path:** `/api/gpt5/prompt`
*   **Description:** Sends a prompt to the GPT-5 API and receives a response. This endpoint allows you to interact with a GPT-5 model for various text-based tasks.
*   **Request Parameters/Body:**
    *   `prompt`: (string, required) The text prompt to send to the GPT-5 model.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/gpt5/prompt?prompt=Write a short poem about the Billions Network.
    ```
*   **Example Response:**
    ```json
    {
      "response": "In realms of code, a network bright,\nBillions Network shines with digital light.\nTransactions flow, a vibrant stream,\nBuilding a future, a hopeful dream."
    }
    ```

### 4.3. GET /api/portfolio/data

*   **Method:** GET
*   **Path:** `/api/portfolio/data`
*   **Description:** Retrieves portfolio data. This endpoint retrieves data related to a user's portfolio, including holdings and balances.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/portfolio/data
    ```
*   **Example Response:**
    ```json
    {
      "user_id": "user123",
      "total_portfolio_value": 12345678.90,
      "holdings": [
        {
          "asset_symbol": "BNT",
          "quantity": 100,
          "current_value": 12345.67
        },
        {
          "asset_symbol": "BLN",
          "quantity": 50,
          "current_value": 6678.90
        }
      ]
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :---------------------------------------- |
| 400      | Bad Request - Invalid input parameters.    |
| 401      | Unauthorized - Authentication failed.     |
| 404      | Not Found - Resource not found.           |
| 500      | Internal Server Error - Server error.      |
| 503      | Service Unavailable - The service is temporarily unavailable. |

**Handling:**  Implement proper error handling in your application to gracefully handle these errors.  The response body will typically contain a more detailed error message.

## 6. Rate Limiting Info

The Billions Network API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per minute:** 60 requests per minute per IP address.
*   **Burst Limit:** A 5-minute burst limit is allowed, exceeding which will result in rate limiting.
*   **Rate Limit Headers:** The API will return the remaining rate limit in the `X-RateLimit-Remaining` header and the reset time in the `X-RateLimit-Reset` header.  Example: `X-RateLimit-Remaining: 59, X-RateLimit-Reset: 1678886400`

Please refer to the API status page for any changes to rate limiting policies.
```