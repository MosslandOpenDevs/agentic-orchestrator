```markdown
# Portfolio Analytics API Documentation

## 1. Overview

This API provides access to various portfolio analytics data sources, including Ethereum market data, Dune Analytics portfolio performance, and a portfolio rebalancing service powered by GPT-5.  It’s designed to provide insights and facilitate informed investment decisions.

## 2. Authentication Details

Currently, this API utilizes API key authentication.  All requests must include an `X-API-Key` header with your unique API key.  Contact your administrator to obtain an API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/marketdata/ethereum

*   **Method:** GET
*   **Path:** /api/marketdata/ethereum
*   **Description:** Retrieves Ethereum market data from Chainlink. This includes current price, 24h price change, volume, and market cap.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/marketdata/ethereum
    ```
*   **Example Response:**

    ```json
    {
      "symbol": "ETH",
      "price": 3500.50,
      "priceChange": 15.25,
      "priceChangePercent": 0.43,
      "volume": 123456789.00,
      "marketCap": 250000000000,
      "lastBlockTime": 1678886400
    }
    ```

### 4.2. GET /api/marketdata/dune

*   **Method:** GET
*   **Path:** /api/marketdata/dune
*   **Description:** Retrieves Dune Analytics data for portfolio performance. This endpoint requires a Dune Analytics portfolio ID.
*   **Request Parameters/Body:**
    *   `portfolio_id` (string, required): The unique ID of the Dune Analytics portfolio.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/marketdata/dune?portfolio_id=dune-portfolio-123
    ```
*   **Example Response:**

    ```json
    {
      "portfolio_id": "dune-portfolio-123",
      "total_assets": 150000.00,
      "total_value": 300000.00,
      "profit_loss": 150000.00,
      "performance_metric": "0.50",
      "last_updated": 1678886400
    }
    ```

### 4.3. POST /api/portfolio/rebalance

*   **Method:** POST
*   **Path:** /api/portfolio/rebalance
*   **Description:** Initiates portfolio rebalancing based on GPT-5 analysis. This endpoint requires a JSON payload containing portfolio holdings.
*   **Request Parameters/Body:**
    *   `holdings` (JSON, required):  A JSON object representing the portfolio holdings.  The format is:
        ```json
        {
          "assets": [
            {"asset": "ETH", "quantity": 10},
            {"asset": "BTC", "quantity": 5}
          ]
        }
        ```
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/portfolio/rebalance
    Content-Type: application/json

    {
      "assets": [
        {"asset": "ETH", "quantity": 10},
        {"asset": "BTC", "quantity": 5}
      ]
    }
    ```
*   **Example Response:**

    ```json
    {
      "status": "success",
      "message": "Portfolio rebalancing initiated successfully.",
      "rebalancing_id": "rebalance-12345"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :---------------------------------------- |
| 400      | Bad Request - Invalid input data.          |
| 401      | Unauthorized - Invalid or missing API key. |
| 404      | Not Found - Resource not found.           |
| 500      | Internal Server Error - Server error.      |

**Error Response Format:**

```json
{
  "error_code": "400",
  "message": "Invalid input data provided."
}
```

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:** Rate limit information is returned in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.

    *   `X-RateLimit-Limit`:  The maximum number of requests allowed in the current window. (e.g., 100)
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current window. (e.g., 85)
    *   `X-RateLimit-Reset`: The Unix timestamp when the rate limit resets. (e.g., 1678893600)

Example:

```
X-RateLimit-Limit: 100
X-RateLimit-Remaining: 85
X-RateLimit-Reset: 1678893600
```
```
