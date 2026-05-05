```markdown
# DeFi Portfolio Recommender API Documentation

## 1. Overview

This API provides functionalities for managing DeFi portfolios and generating rebalancing recommendations. It leverages GPT-5 to provide intelligent portfolio suggestions based on user-defined goals and risk tolerance.  This documentation outlines the available endpoints, authentication requirements, and expected response formats.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain your API key by registering an account on our platform.

## 3. Base URL Configuration

The base URL for all API requests is:

```
https://api.example.com
```

(Replace `https://api.example.com` with the actual base URL of your API)

## 4. Endpoints

### 4.1. GET /api/assets

*   **Method:** GET
*   **Path:** `/api/assets`
*   **Description:** Retrieves a list of available DeFi assets supported by the system.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each element in the array represents a DeFi asset.
    *   Example:
        ```json
        [
          { "id": "BTC", "name": "Bitcoin", "symbol": "BTC", "description": "The first and most well-known cryptocurrency." },
          { "id": "ETH", "name": "Ethereum", "symbol": "ETH", "description": "The leading blockchain platform." },
          { "id": "USDT", "name": "Tether USD", "symbol": "USDT", "description": "A stablecoin pegged to the US Dollar." }
        ]
        ```
*   **Example Request:**
    ```
    GET /api/assets
    ```
*   **Example Response:** (See JSON example above)

### 4.2. GET /api/portfolios/{portfolioId}

*   **Method:** GET
*   **Path:** `/api/portfolios/{portfolioId}`
*   **Description:** Retrieves the portfolio data for a specific portfolio ID.
*   **Request Parameters/Body:**
    *   `portfolioId` (Path Parameter): The unique identifier for the portfolio.  Must be a valid integer.
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "id": "portfolio123",
          "name": "My Crypto Portfolio",
          "userId": "user456",
          "assets": [
            { "assetId": "BTC", "quantity": 0.5, "price": 30000 },
            { "assetId": "ETH", "quantity": 1.2, "price": 2000 }
          ],
          "totalValue": 75000.00
        }
        ```
*   **Example Request:**
    ```
    GET /api/portfolios/portfolio123
    ```
*   **Example Response:** (See JSON example above)

### 4.3. POST /api/recommendations

*   **Method:** POST
*   **Path:** `/api/recommendations`
*   **Description:** Generates a rebalancing recommendation for a portfolio using GPT-5.
*   **Request Parameters/Body:**
    *   `portfolioId` (Required): The unique identifier for the portfolio.  Must be a valid integer.
    *   `riskTolerance` (Required):  A string representing the user's risk tolerance (e.g., "low", "medium", "high").
    *   `investmentHorizon` (Optional): A string representing the investment horizon (e.g., "short-term", "long-term"). Defaults to "medium".
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "id": "recommendation789",
          "portfolioId": "portfolio123",
          "recommendation": "Based on your risk tolerance and investment horizon, we recommend increasing your allocation to ETH and decreasing your allocation to BTC.",
          "assetChanges": [
            { "assetId": "BTC", "change": -0.1, "percentageChange": -10.0 },
            { "assetId": "ETH", "change": 0.3, "percentageChange": 30.0 }
          ],
          "totalValueChange": 15000.00
        }
        ```
*   **Example Request:**
    ```
    POST /api/recommendations
    Content-Type: application/json

    {
      "portfolioId": "portfolio123",
      "riskTolerance": "medium",
      "investmentHorizon": "long-term"
    }
    ```
*   **Example Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code      | Description                               | Action                               |
|-----------|-------------------------------------------|-------------------------------------|
| 400        | Bad Request - Invalid input data          | Check request body for errors.       |
| 401        | Unauthorized - Invalid API key           | Provide a valid API key in the header. |
| 403        | Forbidden - Insufficient permissions    | Ensure you have the necessary rights. |
| 404        | Not Found - Resource not found            | Verify the ID or path is correct.    |
| 500        | Internal Server Error - Unexpected error | Contact support for assistance.     |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure service stability.  The rate limit is 100 requests per minute per API key.  If you exceed the rate limit, you will receive a 429 (Too Many Requests) error.  You can implement retry logic with exponential backoff to handle temporary rate limiting.  Detailed rate limit information will be returned in the response headers:

*   `X-RateLimit-Limit`:  The maximum number of requests allowed in the current window.
*   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
*   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```
