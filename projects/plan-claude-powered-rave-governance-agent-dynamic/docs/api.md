```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing portfolios and associated transactions, as well as retrieving market indicator data. It allows users to create, retrieve, and update portfolios, along with their corresponding transactions. This API is designed for integration with financial applications and dashboards.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  You can obtain an API key by registering an account through our developer portal: [https://example.com/developer-portal](https://example.com/developer-portal)  (Replace with your actual portal URL).

## 3. Base URL Configuration

The base URL for all API requests is:

```
https://api.example.com/v1
```

(Replace `https://api.example.com/v1` with your actual base URL)

## 4. Endpoints

### 4.1. GET /api/portfolios

*   **Method:** GET
*   **Path:** /api/portfolios
*   **Description:** Retrieves all portfolios.
*   **Request Parameters:** None
*   **Response Format:** JSON Array
*   **Example Response:**

    ```json
    [
      {
        "id": "portfolio123",
        "name": "My Investments",
        "description": "A portfolio tracking my stock investments.",
        "created_at": "2023-10-26T10:00:00Z",
        "updated_at": "2023-10-27T14:30:00Z"
      },
      {
        "id": "portfolio456",
        "name": "Retirement Fund",
        "description": "Savings for retirement.",
        "created_at": "2023-10-25T08:00:00Z",
        "updated_at": "2023-10-27T10:00:00Z"
      }
    ]
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/v1/portfolios -H "X-API-Key: YOUR_API_KEY"
    ```


### 4.2. GET /api/portfolios/:portfolioId

*   **Method:** GET
*   **Path:** /api/portfolios/:portfolioId
*   **Description:** Retrieves a specific portfolio by ID.
*   **Request Parameters:**
    *   `portfolioId` (Path Parameter): The unique identifier of the portfolio.
*   **Response Format:** JSON
*   **Example Response:**

    ```json
    {
      "id": "portfolio123",
      "name": "My Investments",
      "description": "A portfolio tracking my stock investments.",
      "created_at": "2023-10-26T10:00:00Z",
      "updated_at": "2023-10-27T14:30:00Z"
    }
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/v1/portfolios/portfolio123 -H "X-API-Key: YOUR_API_KEY"
    ```

### 4.3. POST /api/portfolios

*   **Method:** POST
*   **Path:** /api/portfolios
*   **Description:** Creates a new portfolio.
*   **Request Parameters:**
    *   `name` (Body Parameter): The name of the portfolio (required).
    *   `description` (Body Parameter): A description of the portfolio (optional).
*   **Response Format:** JSON (representing the newly created portfolio)
*   **Example Request Body:**

    ```json
    {
      "name": "New Portfolio",
      "description": "A portfolio for testing purposes."
    }
    ```
*   **Example Response:**

    ```json
    {
      "id": "portfolio789",
      "name": "New Portfolio",
      "description": "A portfolio for testing purposes.",
      "created_at": "2023-10-28T12:00:00Z",
      "updated_at": "2023-10-28T12:00:00Z"
    }
    ```
*   **Example Request:**
    ```bash
    curl -X POST -H "X-API-Key: YOUR_API_KEY" -H "Content-Type: application/json" -d '{"name": "New Portfolio", "description": "A portfolio for testing purposes."}' https://api.example.com/v1/portfolios
    ```

### 4.4. GET /api/transactions/:portfolioId

*   **Method:** GET
*   **Path:** /api/transactions/:portfolioId
*   **Description:** Retrieves all transactions for a specific portfolio.
*   **Request Parameters:**
    *   `portfolioId` (Path Parameter): The unique identifier of the portfolio.
*   **Response Format:** JSON Array
*   **Example Response:**

    ```json
    [
      {
        "id": "transaction1",
        "portfolio_id": "portfolio123",
        "transaction_date": "2023-10-27",
        "description": "Stock Purchase - AAPL",
        "amount": -100.00,
        "type": "buy"
      },
      {
        "id": "transaction2",
        "portfolio_id": "portfolio123",
        "transaction_date": "2023-10-28",
        "description": "Dividend Payment",
        "amount": 5.00,
        "type": "dividend"
      }
    ]
    ```
*   **Example Request:**
    ```bash
    curl -X GET https://api.example.com/v1/transactions/portfolio123 -H "X-API-Key: YOUR_API_KEY"
    ```

### 4.5. GET /api/marketIndicators

*   **Method:** GET
*   **Path:** /api/marketIndicators
*   **Description:** Retrieves market indicator data.
*   **Request Parameters:** None
*   **Response Format:** JSON
*   **Example Response:**

    ```json
    {
      "date": "2023-10-28",
      "close_price": 4500.25,
      "volume": 123456789,
      "market_trend": "bullish"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Response Format   |
| :------ | :--------------------------------------- | :---------------- |
| 400      | Bad Request - Invalid input data         | JSON with error details |
| 401      | Unauthorized - Invalid API key          | JSON with error details |
| 403      | Forbidden - Insufficient permissions     | JSON with error details |
| 404      | Not Found - Resource not found           | JSON with error details |
| 500      | Internal Server Error                    | JSON with error details |

All error responses will include a descriptive error message.  Detailed error logs are available for developers.

## 6. Rate Limiting

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:** Rate limit information is returned in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
*   **Exceeding Limits:**  If the rate limit is exceeded, the API will return a 429 (Too Many Requests) error.
```