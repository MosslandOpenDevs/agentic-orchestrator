```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing and rebalancing a portfolio of assets. It allows users to retrieve portfolio data, initiate rebalancing processes, and obtain information about individual assets. This documentation outlines the available endpoints, request/response formats, and error handling procedures.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain a valid API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`

## 4. Endpoints

### 4.1. GET /api/portfolio/{portfolioId}

*   **Method:** GET
*   **Path:** `/api/portfolio/{portfolioId}`
*   **Description:** Retrieves portfolio data for a given portfolio ID.
*   **Request Parameters:**
    *   `portfolioId` (path parameter):  The unique identifier for the portfolio.  Must be an integer.
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "portfolioId": 123,
          "name": "Growth Portfolio",
          "totalValue": 150000.00,
          "assets": [
            {
              "assetId": 456,
              "name": "Apple Inc.",
              "quantity": 100,
              "price": 175.00
            },
            {
              "assetId": 789,
              "name": "Microsoft Corp.",
              "quantity": 50,
              "price": 300.00
            }
          ]
        }
        ```
*   **Example Request:**

    ```
    GET /api/portfolio/123
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON example above)

### 4.2. POST /api/rebalance

*   **Method:** POST
*   **Path:** `/api/rebalance`
*   **Description:** Initiates a rebalancing process for a portfolio. This endpoint requires a JSON payload specifying the desired asset allocation.
*   **Request Parameters:**
    *   **Body:** JSON
        *   `portfolioId` (required): The unique identifier for the portfolio.  Must be an integer.
        *   `targetAllocation` (required):  A JSON object defining the desired asset allocation.  This should be a percentage breakdown for each asset. Example: `{"Apple Inc.": 20, "Microsoft Corp.": 30}`.
*   **Response Format:** JSON
    *   Success Response:
        ```json
        {
          "status": "success",
          "message": "Rebalancing initiated successfully.",
          "rebalanceId": "RB-20231027-001"
        }
        ```
    *   Error Response (Example):
        ```json
        {
          "status": "error",
          "message": "Invalid target allocation.  Percentages must sum to 100."
        }
        ```
*   **Example Request:**

    ```
    POST /api/rebalance
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "portfolioId": 123,
      "targetAllocation": {
        "Apple Inc.": 20,
        "Microsoft Corp.": 30
      }
    }
    ```
*   **Example Response:** (Successful Rebalance - See JSON example above)

### 4.3. GET /api/asset/{assetId}

*   **Method:** GET
*   **Path:** `/api/asset/{assetId}`
*   **Description:** Retrieves asset data for a given asset ID.
*   **Request Parameters:**
    *   `assetId` (path parameter): The unique identifier for the asset. Must be an integer.
*   **Response Format:** JSON
    *   Example:
        ```json
        {
          "assetId": 456,
          "name": "Apple Inc.",
          "ticker": "AAPL",
          "currentPrice": 175.00,
          "lastTradeDate": "2023-10-27"
        }
        ```
*   **Example Request:**

    ```
    GET /api/asset/456
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request                              | Invalid request body or parameters.  Check the request details for specific error messages. |
| 401      | Unauthorized                             | Invalid or missing API key.           |
| 404      | Not Found                               | Portfolio or asset not found.         |
| 422      | Unprocessable Entity                     | Request body is invalid (e.g., incorrect data types). |
| 500      | Internal Server Error                    | An unexpected error occurred on the server. |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per API key.
*   **Headers:** Rate limit information will be returned in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```