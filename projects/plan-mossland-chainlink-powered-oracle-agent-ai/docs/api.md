```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing portfolios, retrieving asset data, generating trading strategies, and accessing real-time price data via Chainlink. It’s designed for integration with trading platforms, portfolio tracking applications, and automated trading systems.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain an API key by registering an account on our platform.  Failure to provide a valid API key will result in a `401 Unauthorized` error.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`

(Replace `https://api.example.com` with your actual API base URL)

## 4. Endpoints

### 4.1. GET /api/portfolios

*   **Method:** `GET`
*   **Path:** `/api/portfolios`
*   **Description:** Retrieves a list of all portfolios.
*   **Request Parameters:** None
*   **Response Format:** JSON array of portfolio objects.
    ```json
    [
      {
        "portfolioId": "portfolio123",
        "name": "My Investments",
        "description": "A portfolio focused on tech stocks.",
        "createdAt": "2023-10-26T10:00:00Z"
      },
      {
        "portfolioId": "portfolio456",
        "name": "Crypto Portfolio",
        "description": "Holding various cryptocurrencies.",
        "createdAt": "2023-10-27T14:30:00Z"
      }
    ]
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/api/portfolios -H "X-API-Key: YOUR_API_KEY"
    ```
*   **Example Response:** (See JSON response format above)

### 4.2. POST /api/portfolios

*   **Method:** `POST`
*   **Path:** `/api/portfolios`
*   **Description:** Creates a new portfolio.
*   **Request Parameters/Body:** JSON object containing portfolio details.
    ```json
    {
      "name": "New Portfolio",
      "description": "A newly created portfolio.",
      "assetTypes": ["stock", "crypto"]
    }
    ```
*   **Response Format:** JSON object representing the newly created portfolio, including the `portfolioId`.
    ```json
    {
      "portfolioId": "portfolio789",
      "name": "New Portfolio",
      "description": "A newly created portfolio.",
      "assetTypes": ["stock", "crypto"],
      "createdAt": "2023-10-28T08:15:00Z"
    }
    ```
*   **Example Request:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" -d '{"name": "Test Portfolio", "description": "A test portfolio", "assetTypes": ["stock"]}' https://api.example.com/api/portfolios
    ```
*   **Example Response:** (See JSON response format above)

### 4.3. GET /api/assets/{portfolioId}

*   **Method:** `GET`
*   **Path:** `/api/assets/{portfolioId}`
*   **Description:** Retrieves assets for a specific portfolio.
*   **Request Parameters:**
    *   `portfolioId` (Path Parameter): The ID of the portfolio to retrieve assets for.
*   **Response Format:** JSON array of asset objects within the specified portfolio.
    ```json
    [
      {
        "assetId": "asset1",
        "assetType": "stock",
        "name": "Apple Inc.",
        "quantity": 100,
        "price": 175.25
      },
      {
        "assetId": "asset2",
        "assetType": "crypto",
        "name": "Bitcoin",
        "quantity": 0.5,
        "price": 35000.00
      }
    ]
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/api/assets/portfolio123 -H "X-API-Key: YOUR_API_KEY"
    ```
*   **Example Response:** (See JSON response format above)

### 4.4. GET /api/chainlinkData/{assetType}

*   **Method:** `GET`
*   **Path:** `/api/chainlinkData/{assetType}`
*   **Description:** Retrieves real-time asset price data from Chainlink.
*   **Request Parameters:**
    *   `assetType` (Path Parameter): The type of asset to retrieve data for (e.g., "BTC", "ETH", "SOL").
*   **Response Format:** JSON object containing the latest price data.
    ```json
    {
      "assetType": "BTC",
      "price": 48000.50,
      "timestamp": "2023-10-28T12:00:00Z",
      "lastUpdated": "2023-10-28T11:55:00Z"
    }
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/api/chainlinkData/BTC -H "X-API-Key: YOUR_API_KEY"
    ```
*   **Example Response:** (See JSON response format above)

### 4.5. POST /api/strategies

*   **Method:** `POST`
*   **Path:** `/api/strategies`
*   **Description:** Generates a new strategy using GPT-5.
*   **Request Parameters/Body:** JSON object containing parameters for the strategy generation.
    ```json
    {
      "portfolioId": "portfolio123",
      "assetTypes": ["stock", "crypto"],
      "riskTolerance": "moderate",
      "timeHorizon": "long"
    }
    ```
*   **Response Format:** JSON object containing the generated strategy.  This will likely be a complex JSON structure representing the trading rules.
    ```json
    {
      "strategyId": "strategy1",
      "name": "GPT-5 Strategy",
      "rules": [
        "Buy BTC when the price drops below $34000.",
        "Sell BTC when the price rises above $36000."
      ],
      "createdAt": "2023-10-28T13:00:00Z"
    }
    ```
*   **Example Request:**
    ```bash
    curl -X POST -H "Content-Type: application/json" -H "X-API-Key: YOUR_API_KEY" -d '{"portfolioId": "portfolio123", "assetTypes": ["stock", "crypto"], "riskTolerance": "moderate", "timeHorizon": "long"}' https://api.example.com/api/strategies
    ```
*   **Example Response:** (See JSON response format above)

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.         |
| 401      | Unauthorized - Invalid or missing API key. |
| 403      | Forbidden - Insufficient permissions.     |
| 404      | Not Found - Resource not found.          |
| 500      | Internal Server Error - Server error.      |

All error responses will include a JSON body with a `message` field providing details about the error.  Example:

```json
{
  "code": 400,
  "message": "Invalid portfolioId format."
}
```

## 6. Rate Limiting

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for a short burst of activity)
*   **Reset Time:** 60 seconds

If you exceed the rate limits, you will receive a `429 Too Many Requests` error.  Implement retry logic with exponential backoff to handle these situations gracefully.  Detailed rate limit information will be returned in the response headers: `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset`.
```
