```markdown
# NFT Portfolio API Documentation

## 1. Overview

This API provides endpoints for managing NFT portfolios, retrieving transaction data, generating risk assessments, and accessing cryptocurrency price data.  It is designed to be used by developers building applications for NFT portfolio tracking and risk management.

## 2. Authentication Details

All API endpoints require an API key passed in the `X-API-Key` header.  You can obtain an API key by registering an account through our developer portal: [https://example.com/developer-portal](https://example.com/developer-portal) (Replace with actual URL).

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com` (Replace with actual URL)

## 4. Endpoints

### 4.1 GET /api/nftCollections

*   **Method:** `GET`
*   **Path:** `/api/nftCollections`
*   **Description:** Retrieves a list of NFT collections.
*   **Request Parameters/Body:**
    *   `limit`: (Optional, Integer) -  Maximum number of collections to return. Defaults to 10.  Maximum value: 100.
    *   `offset`: (Optional, Integer) -  Offset for pagination. Defaults to 0.
*   **Response Format:** JSON
    ```json
    [
      {
        "collectionId": "string",
        "name": "string",
        "symbol": "string",
        "description": "string",
        "imageURL": "string"
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
        "description": "The first NFT project.",
        "imageURL": "https://example.com/punk.png"
      },
      {
        "collectionId": "0x456",
        "name": "BoredApe",
        "symbol": "Apes",
        "description": "A collection of bored apes.",
        "imageURL": "https://example.com/ape.png"
      }
    ]
    ```

### 4.2 GET /api/nftTransactions/{portfolioId}

*   **Method:** `GET`
*   **Path:** `/api/nftTransactions/{portfolioId}`
*   **Description:** Retrieves NFT transactions for a specific portfolio.
*   **Request Parameters/Body:**
    *   `portfolioId`: (Required, String) - The ID of the portfolio.
    *   `limit`: (Optional, Integer) - Maximum number of transactions to return. Defaults to 10.  Maximum value: 100.
    *   `offset`: (Optional, Integer) - Offset for pagination. Defaults to 0.
*   **Response Format:** JSON
    ```json
    {
      "transactions": [
        {
          "transactionId": "string",
          "nftId": "string",
          "portfolioId": "string",
          "timestamp": "string (ISO 8601)",
          "type": "buy/sell",
          "quantity": "integer",
          "price": "number",
          "assetSymbol": "string"
        },
        ...
      ],
      "totalCount": "integer"
    }
    ```
*   **Example Request:**
    ```
    GET /api/nftTransactions/portfolio123?limit=5&offset=0
    ```
*   **Example Response:**
    ```json
    {
      "transactions": [
        {
          "transactionId": "tx12345",
          "nftId": "0x678",
          "portfolioId": "portfolio123",
          "timestamp": "2023-10-27T10:00:00Z",
          "type": "buy",
          "quantity": 2,
          "price": 150.00,
          "assetSymbol": "ETH"
        }
      ],
      "totalCount": 1
    }
    ```

### 4.3 POST /api/riskAssessment

*   **Method:** `POST`
*   **Path:** `/api/riskAssessment`
*   **Description:** Generates a risk assessment for a portfolio using GPT-5.
*   **Request Parameters/Body:**
    *   `portfolioId`: (Required, String) - The ID of the portfolio.
    *   `assetIds`: (Required, Array of Strings) - An array of NFT IDs within the portfolio.
*   **Response Format:** JSON
    ```json
    {
      "riskScore": "number (0-100)",
      "riskCategory": "high/medium/low",
      "assessmentDetails": "string (GPT-5 generated explanation)"
    }
    ```
*   **Example Request:**
    ```
    POST /api/riskAssessment
    Content-Type: application/json

    {
      "portfolioId": "portfolio456",
      "assetIds": ["0x901", "0x902"]
    }
    ```
*   **Example Response:**
    ```json
    {
      "riskScore": 75,
      "riskCategory": "medium",
      "assessmentDetails": "Based on the current market volatility and the portfolio's concentration in high-risk assets, the risk score is 75, categorized as medium. Further diversification is recommended."
    }
    ```

### 4.4 GET /api/priceData/{symbol}

*   **Method:** `GET`
*   **Path:** `/api/priceData/{symbol}`
*   **Description:** Retrieves price data for a given cryptocurrency symbol.
*   **Request Parameters/Body:**
    *   `symbol`: (Required, String) - The cryptocurrency symbol (e.g., ETH, BTC).
*   **Response Format:** JSON
    ```json
    {
      "symbol": "string",
      "price": "number",
      "lastUpdated": "string (ISO 8601)"
    }
    ```
*   **Example Request:**
    ```
    GET /api/priceData/ETH
    ```
*   **Example Response:**
    ```json
    {
      "symbol": "ETH",
      "price": 3500.50,
      "lastUpdated": "2023-10-27T11:30:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                        | Response Format      |
| :------ | :--------------------------------- | :------------------- |
| 400      | Bad Request - Invalid input data   | JSON with error details |
| 401      | Unauthorized - Invalid API key     | JSON with error details |
| 404      | Not Found - Resource not found     | JSON with error details |
| 429      | Too Many Requests - Rate limit exceeded | JSON with error details |
| 500      | Internal Server Error             | JSON with error details |

All error responses will include a `message` field with a human-readable error description.

## 6. Rate Limiting

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Headers:** Rate limit information will be returned in the following headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```