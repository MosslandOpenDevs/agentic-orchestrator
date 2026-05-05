```markdown
# Portfolio Rebalancing API Documentation

## 1. Overview

This API provides tools for managing and optimizing investment portfolios. It allows users to retrieve real-time security prices, generate rebalancing recommendations, and view their portfolio holdings.  The API is designed for integration with investment platforms and applications.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain an API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.exampleportfolio.com`

## 4. Endpoints

### 4.1. GET /api/security-prices

*   **Method:** GET
*   **Path:** /api/security-prices
*   **Description:** Retrieves real-time security prices from DTCC and other data sources.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/security-prices
    ```
*   **Example Response:**
    ```json
    [
      {
        "symbol": "AAPL",
        "price": 170.34,
        "timestamp": "2023-10-27T10:30:00Z"
      },
      {
        "symbol": "MSFT",
        "price": 330.12,
        "timestamp": "2023-10-27T10:30:00Z"
      }
    ]
    ```

### 4.2. POST /api/rebalance

*   **Method:** POST
*   **Path:** /api/rebalance
*   **Description:** Generates a rebalancing recommendation for a user's portfolio based on their risk tolerance, investment goals, and current market conditions.
*   **Request Parameters/Body:**
    *   `userId` (string, required): The ID of the user whose portfolio to rebalance.
    *   `riskTolerance` (string, required): The user's risk tolerance (e.g., "conservative", "moderate", "aggressive").
    *   `investmentGoals` (string, required): The user’s investment goals (e.g., "retirement", "growth", "income").
    *   `timeHorizon` (integer, optional): The user’s investment time horizon in years (e.g., 5, 10, 20). Defaults to 10.
*   **Response Format:** JSON
*   **Example Request:**
    ```json
    POST /api/rebalance
    Content-Type: application/json

    {
      "userId": "user123",
      "riskTolerance": "moderate",
      "investmentGoals": "growth",
      "timeHorizon": 10
    }
    ```
*   **Example Response:**
    ```json
    {
      "recommendationId": "recom-456",
      "timestamp": "2023-10-27T10:30:00Z",
      "recommendations": [
        {
          "symbol": "AAPL",
          "quantity": 10,
          "percentage": 20
        },
        {
          "symbol": "MSFT",
          "quantity": 5,
          "percentage": 10
        }
      ],
      "message": "Rebalancing recommendation generated successfully."
    }
    ```

### 4.3. GET /api/portfolio/{userId}

*   **Method:** GET
*   **Path:** /api/portfolio/{userId}
*   **Description:** Retrieves the portfolio positions for a given user.
*   **Request Parameters/Body:** None
*   **Path Parameter:**
    *   `userId` (string, required): The ID of the user whose portfolio to retrieve.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/portfolio/user123
    ```
*   **Example Response:**
    ```json
    {
      "userId": "user123",
      "positions": [
        {
          "symbol": "AAPL",
          "quantity": 100,
          "averagePrice": 170.00,
          "totalValue": 17000.00
        },
        {
          "symbol": "MSFT",
          "quantity": 50,
          "averagePrice": 330.00,
          "totalValue": 16500.00
        }
      ]
    }
    ```

## 5. Error Codes and Handling

| Code      | Description                               | Action                               |
|-----------|-------------------------------------------|-------------------------------------|
| 400        | Bad Request - Invalid input data.           | Validate request parameters.         |
| 401        | Unauthorized - Invalid API key.           | Provide a valid API key.             |
| 404        | Not Found - Resource not found.           | Verify the resource ID is correct.   |
| 500        | Internal Server Error - Server error.      | Contact support for assistance.     |
| 429        | Too Many Requests - Rate limit exceeded. | Implement retry logic with exponential backoff. |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure service availability.

*   **Requests per Minute:** 100
*   **Default Timeout:** 5 seconds
*   **Retry-After Header:**  If a 429 error is returned, the `Retry-After` header will indicate the number of seconds to wait before retrying the request.  Example: `Retry-After: 60` (wait 60 seconds).
```
