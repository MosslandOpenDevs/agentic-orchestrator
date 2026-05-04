```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for retrieving and managing positions across Aave and Compound protocols, as well as managing Agent Receipts.  It's designed to facilitate portfolio tracking and management for users interacting with these DeFi protocols.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.  Contact your platform administrator to obtain a valid API key.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`  (Replace with your actual API URL)

## 4. Endpoints

### 4.1. GET /api/aave/positions

*   **Method:** `GET`
*   **Path:** `/api/aave/positions`
*   **Description:** Retrieves Aave positions for a given portfolio.
*   **Request Parameters:**
    *   `portfolio_id` (string, required): The ID of the portfolio to retrieve Aave positions for.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": [
        {
          "asset": "DAI",
          "amount": 100,
          "borrowRate": 0.01,
          "interestRate": 0.05
        },
        {
          "asset": "USDC",
          "amount": 50,
          "borrowRate": 0.005,
          "interestRate": 0.04
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/aave/positions?portfolio_id=portfolio123
    ```
*   **Example Response:** (See JSON response above)

### 4.2. GET /api/compound/positions

*   **Method:** `GET`
*   **Path:** `/api/compound/positions`
*   **Description:** Retrieves Compound positions for a given portfolio.
*   **Request Parameters:**
    *   `portfolio_id` (string, required): The ID of the portfolio to retrieve Compound positions for.
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": [
        {
          "asset": "cDAI",
          "amount": 200,
          "borrowRate": 0.015,
          "interestRate": 0.06
        },
        {
          "asset": "cUSDC",
          "amount": 100,
          "borrowRate": 0.01,
          "interestRate": 0.055
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/compound/positions?portfolio_id=portfolio456
    ```
*   **Example Response:** (See JSON response above)

### 4.3. GET /api/agentReceipts

*   **Method:** `GET`
*   **Path:** `/api/agentReceipts`
*   **Description:** Retrieves all Agent Receipts.
*   **Request Parameters:** None
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": [
        {
          "receipt_id": "receipt1",
          "agent_address": "0x...",
          "amount": 1000,
          "timestamp": "2023-10-27T10:00:00Z"
        },
        {
          "receipt_id": "receipt2",
          "agent_address": "0x...",
          "amount": 500,
          "timestamp": "2023-10-27T11:00:00Z"
        }
      ]
    }
    ```
*   **Example Request:**
    ```
    GET /api/agentReceipts
    ```
*   **Example Response:** (See JSON response above)

### 4.4. POST /api/agentReceipts

*   **Method:** `POST`
*   **Path:** `/api/agentReceipts`
*   **Description:** Creates a new Agent Receipt.
*   **Request Body:** JSON
    ```json
    {
      "agent_address": "0x...",
      "amount": 1000,
      "timestamp": "2023-10-27T12:00:00Z"
    }
    ```
*   **Response Format:** JSON
    ```json
    {
      "status": "success",
      "data": {
        "receipt_id": "new_receipt_id"
      }
    }
    ```
*   **Example Request:**
    ```
    POST /api/agentReceipts
    Content-Type: application/json

    {
      "agent_address": "0x...",
      "amount": 1000,
      "timestamp": "2023-10-27T12:00:00Z"
    }
    ```
*   **Example Response:** (See JSON response above)

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters     | Validate request parameters          |
| 401      | Unauthorized - Invalid API key           | Provide a valid API key             |
| 404      | Not Found - Resource not found            | Verify the portfolio ID or receipt ID |
| 500      | Internal Server Error - Server issue     | Contact support                     |
| 503      | Service Unavailable - Server overloaded | Retry request later                 |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.  The following limits apply:

*   **Requests per minute:** 60 requests
*   **Burst limit:** 120 requests (This is a temporary buffer, exceeding this will result in rate limiting)

Rate limiting is implemented using HTTP status code 429 (Too Many Requests).  The `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers will be included in the response to indicate the current rate limit status.  Example:

```
X-RateLimit-Limit: 60
X-RateLimit-Remaining: 45
X-RateLimit-Reset: 120
```
```
