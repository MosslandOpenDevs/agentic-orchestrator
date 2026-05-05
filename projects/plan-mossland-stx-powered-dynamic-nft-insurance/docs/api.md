```markdown
# NFT Portfolio & Valuation API Documentation

## 1. Overview

This API provides endpoints for managing NFT portfolios, retrieving NFT valuations, and exploring NFT fractionalization data. It allows users to track their NFT holdings, create new portfolios, and get AI-powered valuations for individual NFTs.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain your API key from the [API Key Management Portal](https://example.com/api-key-portal).  Ensure your key is kept secure.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`

## 4. Endpoints

### 4.1. GET /api/nft/fractionalization

*   **Method:** `GET`
*   **Path:** `/api/nft/fractionalization`
*   **Description:** Retrieves information about NFT fractionalization opportunities. This endpoint provides details on NFTs currently available for fractional ownership.
*   **Request Parameters/Body:**
    *   `tokenId` (optional, string): Filters results by a specific NFT token ID.
    *   `limit` (optional, integer, default: 20):  Limits the number of results returned per page.
    *   `offset` (optional, integer, default: 0):  Specifies the starting point for pagination.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/nft/fractionalization?tokenId=0x123...&limit=10&offset=0
    ```
*   **Example Response:**
    ```json
    {
      "data": [
        {
          "tokenId": "0x123...",
          "name": "Awesome NFT",
          "fractionSize": 0.5,
          "currentFractionHolders": 100,
          "totalFractionValue": 1000.00
        },
        {
          "tokenId": "0x456...",
          "name": "Another NFT",
          "fractionSize": 0.25,
          "currentFractionHolders": 50,
          "totalFractionValue": 500.00
        }
      ],
      "pagination": {
        "limit": 10,
        "offset": 0,
        "totalItems": 200,
        "totalPages": 10
      }
    }
    ```

### 4.2. GET /api/portfolio/user

*   **Method:** `GET`
*   **Path:** `/api/portfolio/user`
*   **Description:** Retrieves a user's NFT portfolio.
*   **Request Parameters/Body:**
    *   `userId` (required, string): The ID of the user whose portfolio to retrieve.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/portfolio/user?userId=user123
    ```
*   **Example Response:**
    ```json
    {
      "userId": "user123",
      "portfolioId": "portfolio456",
      "totalPortfolioValue": 5000.00,
      "assets": [
        {
          "tokenId": "0x123...",
          "name": "Awesome NFT",
          "quantity": 2,
          "purchasePrice": 2500.00
        },
        {
          "tokenId": "0x456...",
          "name": "Another NFT",
          "quantity": 1,
          "purchasePrice": 2500.00
        }
      ]
    }
    ```

### 4.3. POST /api/portfolio/create

*   **Method:** `POST`
*   **Path:** `/api/portfolio/create`
*   **Description:** Creates a new NFT portfolio for a user.
*   **Request Parameters/Body:**
    *   `userId` (required, string): The ID of the user creating the portfolio.
    *   `portfolioName` (optional, string, default: "New Portfolio"): The name of the portfolio.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    POST /api/portfolio/create
    Content-Type: application/json

    {
      "userId": "user123",
      "portfolioName": "My Cool Portfolio"
    }
    ```
*   **Example Response:**
    ```json
    {
      "portfolioId": "portfolio789",
      "userId": "user123",
      "portfolioName": "My Cool Portfolio",
      "totalPortfolioValue": 0.00
    }
    ```

### 4.4. GET /api/nft/valuation

*   **Method:** `GET`
*   **Path:** `/api/nft/valuation`
*   **Description:** Retrieves the AI-powered valuation of an NFT.
*   **Request Parameters/Body:**
    *   `tokenId` (required, string): The token ID of the NFT to be valued.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/nft/valuation?tokenId=0x123...
    ```
*   **Example Response:**
    ```json
    {
      "tokenId": "0x123...",
      "name": "Awesome NFT",
      "valuation": 3000.00,
      "valuationMethod": "AI-Powered Analysis"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Possible Causes                               |
| :------ | :--------------------------------------- | :------------------------------------------- |
| 400      | Bad Request                               | Invalid request parameters, missing required fields |
| 401      | Unauthorized                             | Invalid API key or missing authentication header |
| 404      | Not Found                                | NFT not found, portfolio not found            |
| 429      | Too Many Requests                        | Rate limiting exceeded                         |
| 500      | Internal Server Error                    | Server-side error                               |

**Error Response Format:**

```json
{
  "error": "Error message",
  "code": "Error code"
}
```

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for short bursts of activity)
*   **Reset Time:** 60 seconds

Exceeding the rate limits will result in a 429 Too Many Requests error.  Implement retry logic with exponential backoff for handling 429 errors.  Consult the API Key Management Portal for monitoring your API usage and potential adjustments to your rate limits.
```
