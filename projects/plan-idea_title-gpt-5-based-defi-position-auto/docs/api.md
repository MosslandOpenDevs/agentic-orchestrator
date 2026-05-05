```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides functionality for managing and analyzing a portfolio of assets, leveraging a GPT-5 powered rebalancing engine and real-time asset price data. It allows users to retrieve portfolio details, trigger rebalancing recommendations, and fetch asset prices.

## 2. Authentication Details

This API utilizes API Key authentication.  You must include an `Authorization` header with your API key in every request.

*   **Header:** `Authorization: Bearer YOUR_API_KEY`

    Replace `YOUR_API_KEY` with your actual API key.  API keys can be obtained through the registration process.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`

## 4. API Endpoints

### 4.1. GET /api/portfolio/{portfolioId}

*   **Method:** `GET`
*   **Path:** `/api/portfolio/{portfolioId}`
*   **Description:** Retrieves the portfolio data for a given portfolio ID.
*   **Request Parameters:**
    *   `portfolioId` (Path Parameter):  The unique identifier for the portfolio.  Must be a positive integer.
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "portfolioId": 123,
          "name": "My Portfolio",
          "assets": [
            {"assetAddress": "BTC/USDT", "quantity": 0.5, "currentPrice": 60000},
            {"assetAddress": "ETH/USDT", "quantity": 1.0, "currentPrice": 3000}
          ],
          "totalValue": 180000.00
        }
        ```
*   **Example Request:**
    ```
    GET /api/portfolio/123
    ```
*   **Example Response:** (See JSON example above)

### 4.2. POST /api/rebalance/{portfolioId}

*   **Method:** `POST`
*   **Path:** `/api/rebalance/{portfolioId}`
*   **Description:** Triggers the GPT-5 API to generate a rebalancing recommendation for a given portfolio ID.  This endpoint uses the GPT-5 model to analyze the portfolio and suggest adjustments based on market conditions.
*   **Request Parameters:**
    *   `portfolioId` (Path Parameter): The unique identifier for the portfolio. Must be a positive integer.
*   **Request Body:**  (JSON - Optional.  Can be used to provide specific instructions to GPT-5.  Defaults to standard rebalancing parameters)
    ```json
    {
      "riskTolerance": "moderate",
      "timeHorizon": "1 year",
      "assetClasses": ["crypto", "fiat"]
    }
    ```
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "portfolioId": 123,
          "recommendations": [
            {"assetAddress": "BTC/USDT", "newQuantity": 0.3},
            {"assetAddress": "ETH/USDT", "newQuantity": 1.2}
          ],
          "message": "GPT-5 recommends rebalancing to increase crypto exposure based on your risk tolerance and time horizon."
        }
        ```
*   **Example Request:**
    ```
    POST /api/rebalance/123
    Content-Type: application/json
    Authorization: Bearer YOUR_API_KEY
    Body:
    {
      "riskTolerance": "aggressive",
      "timeHorizon": "6 months"
    }
    ```
*   **Example Response:** (See JSON example above)

### 4.3. GET /api/asset_price/{assetAddress}

*   **Method:** `GET`
*   **Path:** `/api/asset_price/{assetAddress}`
*   **Description:** Retrieves the current price of an asset.
*   **Request Parameters:**
    *   `assetAddress` (Path Parameter): The address of the asset (e.g., "BTC/USDT", "ETH/USDT").  Must be a valid asset pair.
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "assetAddress": "BTC/USDT",
          "price": 60000.00,
          "timestamp": 1678886400
        }
        ```
*   **Example Request:**
    ```
    GET /api/asset_price/BTC/USDT
    ```
*   **Example Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code      | Description                               | Action                               |
|-----------|-------------------------------------------|-------------------------------------|
| 400        | Bad Request - Invalid input data           | Check request body/parameters for errors |
| 401        | Unauthorized - Invalid API Key            | Verify API key is correct            |
| 404        | Not Found - Portfolio or Asset not found   | Verify portfolio ID and asset address |
| 429        | Too Many Requests - Rate Limit Exceeded  | Implement retry logic with exponential backoff |
| 500        | Internal Server Error - Server issue       | Contact support                     |

## 6. Rate Limiting Info

*   **Limit:** 100 requests per minute per API key.
*   **Purpose:**  To prevent abuse and ensure fair usage of the API.
*   **Headers:**  Rate limiting information is returned in the response headers:
    *   `X-RateLimit-Limit`:  The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```