```markdown
# NFT Fraction API Documentation

## 1. Overview

This API provides endpoints for managing NFT fractions, retrieving asset prices, and triggering AI-powered portfolio valuations. It's designed to integrate with a user interface allowing users to view and manage their fractional NFT portfolios.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key should be obtained during user registration.  Failure to provide a valid API key will result in a `401 Unauthorized` error.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.nftfraction.com`

## 4. Endpoints

### 4.1. GET /api/nftfraction/portfolio/:portfolioId

*   **Method:** `GET`
*   **Path:** `/api/nftfraction/portfolio/:portfolioId`
*   **Description:** Retrieves all NFT fractions belonging to a specific portfolio.
*   **Request Parameters:**
    *   `:portfolioId` (Path Parameter):  The unique identifier for the portfolio.  Must be a string.
*   **Response Format:** JSON
*   **Example Response (200 OK):**

    ```json
    [
      {
        "assetId": "0x1234567890abcdef",
        "fractionId": "nftfraction123",
        "assetName": "Bored Ape Yacht Club #420",
        "quantity": 0.5,
        "price": 15000.00,
        "lastUpdated": "2023-10-27T10:00:00Z"
      },
      {
        "assetId": "0xabcdef1234567890",
        "fractionId": "nftfraction456",
        "assetName": "CryptoPunk #789",
        "quantity": 0.25,
        "price": 12000.00,
        "lastUpdated": "2023-10-27T10:05:00Z"
      }
    ]
    ```
*   **Example Request:**

    `GET /api/nftfraction/portfolio/portfolioId123`

### 4.2. POST /api/portfolio/create

*   **Method:** `POST`
*   **Path:** `/api/portfolio/create`
*   **Description:** Creates a new portfolio for a user.
*   **Request Parameters/Body:**

    *   `name` (String, Required): The name of the portfolio.
    *   `userId` (String, Required): The unique identifier for the user.
*   **Response Format:** JSON
*   **Example Response (201 Created):**

    ```json
    {
      "portfolioId": "portfolioId789",
      "name": "My Collection",
      "userId": "userId123"
    }
    ```
*   **Example Request (using `curl`):**

    ```bash
    curl -X POST \
      https://api.nftfraction.com/api/portfolio/create \
      -H 'Content-Type: application/json' \
      -d '{
        "name": "My Test Portfolio",
        "userId": "userId456"
      }'
    ```

### 4.3. GET /api/nftfraction/price/:asset

*   **Method:** `GET`
*   **Path:** `/api/nftfraction/price/:asset`
*   **Description:** Retrieves the current price of an asset.
*   **Request Parameters:**
    *   `:asset` (Path Parameter): The asset identifier (e.g., contract address).  Must be a string.
*   **Response Format:** JSON
*   **Example Response (200 OK):**

    ```json
    {
      "assetId": "0x1234567890abcdef",
      "price": 15500.00,
      "timestamp": "2023-10-27T10:10:00Z"
    }
    ```
*   **Example Request:**

    `GET /api/nftfraction/price/0x1234567890abcdef`

### 4.4. POST /api/ai/valuation

*   **Method:** `POST`
*   **Path:** `/api/ai/valuation`
*   **Description:** Triggers AI valuation of a portfolio.
*   **Request Parameters/Body:**
    *   `portfolioId` (String, Required): The unique identifier for the portfolio.
*   **Response Format:** JSON
*   **Example Response (200 OK):**

    ```json
    {
      "portfolioId": "portfolioId789",
      "valuation": 120000.00,
      "confidence": 0.85,
      "timestamp": "2023-10-27T10:15:00Z"
    }
    ```
*   **Example Request (using `curl`):**

    ```bash
    curl -X POST \
      https://api.nftfraction.com/api/ai/valuation \
      -H 'Content-Type: application/json' \
      -d '{
        "portfolioId": "portfolioId789"
      }'
    ```

## 5. Error Codes and Handling

| Code      | Description                               |
| --------- | ---------------------------------------- |
| 400        | Bad Request - Invalid input data.        |
| 401        | Unauthorized - Invalid API key.          |
| 403        | Forbidden - User does not have permission. |
| 404        | Not Found - Resource not found.          |
| 500        | Internal Server Error - Server error.      |

**Error Response Format:**

```json
{
  "error": "Error message",
  "code": "Error code"
}
```

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allowing for a short burst within the minute limit)
*   **Headers:** Rate limiting information is provided in the response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`
```