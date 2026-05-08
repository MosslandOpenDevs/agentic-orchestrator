```markdown
# NFT Portfolio API Documentation

## 1. Overview

This API provides access to data and functionality related to NFT portfolios, including collection information, transaction history, risk assessments, and real-time price data.  It leverages GPT-5 for advanced risk analysis.

## 2. Authentication Details

All API endpoints require an API key for authentication. This key should be passed in the `X-API-Key` header of each request.  You can obtain an API key by registering an account through our platform.

## 3. Base URL Configuration

The base URL for all API requests is:

```
https://api.example.com/v1
```

(Replace `https://api.example.com/v1` with the actual base URL of your API)

## 4. API Endpoints

### 4.1. GET /api/nftCollections

*   **Method:** GET
*   **Path:** /api/nftCollections
*   **Description:** Retrieves a list of NFT collections.
*   **Request Parameters/Body:**
    *   `limit` (optional, integer):  Maximum number of collections to return (default: 10, max: 100).
    *   `offset` (optional, integer):  Offset for pagination (default: 0).
*   **Response Format:** JSON
    ```json
    [
      {
        "collectionId": "string",
        "name": "string",
        "symbol": "string",
        "description": "string",
        "totalNFTs": "integer",
        "createdDate": "string"
      },
      ...
    ]
    ```
*   **Example Request:**
    ```
    GET /api/nftCollections?limit=10&offset=0
    ```
*   **Example Response:**
    ```json
    [
      {
        "collectionId": "0x123",
        "name": "CryptoPunks",
        "symbol": "Punks",
        "description": "The first officially recognized collection of 10,000 unique pixel punk characters.",
        "totalNFTs": 10000,
        "createdDate": "2017-07-19T00:00:00Z"
      }
    ]
    ```

### 4.2. GET /api/nftTransactions

*   **Method:** GET
*   **Path:** /api/nftTransactions
*   **Description:** Retrieves a list of NFT transactions for a given portfolio.
*   **Request Parameters/Body:**
    *   `portfolioId` (required, string): The ID of the portfolio for which to retrieve transactions.
    *   `limit` (optional, integer): Maximum number of transactions to return (default: 10, max: 100).
    *   `offset` (optional, integer): Offset for pagination (default: 0).
*   **Response Format:** JSON
    ```json
    {
      "transactions": [
        {
          "transactionId": "string",
          "nftId": "string",
          "collectionId": "string",
          "portfolioId": "string",
          "transactionType": "buy/sell",
          "timestamp": "string",
          "price": "number",
          "quantity": "integer"
        },
        ...
      ],
      "totalCount": "integer"
    }
    ```
*   **Example Request:**
    ```
    GET /api/nftTransactions?portfolioId=0x456&limit=5&offset=0
    ```
*   **Example Response:**
    ```json
    {
      "transactions": [
        {
          "transactionId": "tx123",
          "nftId": "0x789",
          "collectionId": "0x123",
          "portfolioId": "0x456",
          "transactionType": "buy",
          "timestamp": "2023-10-27T10:00:00Z",
          "price": 1.5,
          "quantity": 1
        }
      ],
      "totalCount": 1
    }
    ```

### 4.3. POST /api/riskAssessment

*   **Method:** POST
*   **Path:** /api/riskAssessment
*   **Description:** Generates a risk assessment for a given portfolio using GPT-5.
*   **Request Parameters/Body:**
    *   `portfolioId` (required, string): The ID of the portfolio to assess.
*   **Response Format:** JSON
    ```json
    {
      "riskScore": "number",
      "riskLevel": "low/medium/high",
      "assessmentSummary": "string",
      "gpt5Analysis": "string"
    }
    ```
*   **Example Request:**
    ```
    POST /api/riskAssessment
    Content-Type: application/json

    {
      "portfolioId": "0x789"
    }
    ```
*   **Example Response:**
    ```json
    {
      "riskScore": 0.75,
      "riskLevel": "medium",
      "assessmentSummary": "Portfolio shows moderate risk due to concentration in high-volatility assets.",
      "gpt5Analysis": "GPT-5 analysis indicates a significant correlation between the portfolio's holdings and the broader cryptocurrency market.  Further diversification is recommended."
    }
    ```

### 4.4. GET /api/nftPriceData

*   **Method:** GET
*   **Path:** /api/nftPriceData
*   **Description:** Retrieves real-time NFT price data.
*   **Request Parameters/Body:**
    *   `nftId` (optional, string): The ID of the NFT for which to retrieve price data. If not provided, returns price data for all NFTs.
*   **Response Format:** JSON
    ```json
    [
      {
        "nftId": "string",
        "name": "string",
        "collectionId": "string",
        "price": "number",
        "volume": "number",
        "lastUpdated": "string"
      },
      ...
    ]
    ```
*   **Example Request:**
    ```
    GET /api/nftPriceData?nftId=0x123
    ```
*   **Example Response:**
    ```json
    [
      {
        "nftId": "0x123",
        "name": "CryptoPunk #1",
        "collectionId": "0x123",
        "price": 250000.00,
        "volume": 1000.00,
        "lastUpdated": "2023-10-27T10:30:00Z"
      }
    ]
    ```

## 5. Error Codes and Handling

| Code      | Description                               |
|-----------|-------------------------------------------|
| 400        | Bad Request - Invalid input data.          |
| 401        | Unauthorized - Invalid API key.           |
| 404        | Not Found - Resource not found.           |
| 429        | Too Many Requests - Rate limit exceeded. |
| 500        | Internal Server Error - Server error.       |

All error responses will include a JSON body with details about the error.  For example:

```json
{
  "error": "400",
  "message": "Invalid portfolio ID provided."
}
```

## 6. Rate Limiting Info

The API is rate limited to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Headers:** The API will return rate limit headers in the response:
    *   `X-RateLimit-Limit`:  The maximum number of requests allowed in the current window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```