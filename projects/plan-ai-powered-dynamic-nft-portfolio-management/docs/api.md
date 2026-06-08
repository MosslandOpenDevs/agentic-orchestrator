```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides functionalities for managing portfolios, retrieving asset prices, and handling user authentication. It leverages EIP-712 signatures for secure user authentication. The API is designed for efficient portfolio tracking and asset management.

## 2. Authentication Details

This API utilizes EIP-712 signatures for authentication.  Clients must generate a signed message containing the user's address, portfolio ID, and the requested operation.  This signed message is then included in the request header `x-signature`.  The server verifies the signature against the public key to authenticate the request.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`

Replace `https://api.example.com/v1` with your actual API base URL.

## 4. Endpoints

### 4.1. GET /api/portfolio/{portfolioId}

*   **Method:** GET
*   **Path:** `/api/portfolio/{portfolioId}`
*   **Description:** Retrieves portfolio data for a given portfolio ID.
*   **Request Parameters/Body:**
    *   `portfolioId` (Path Parameter): The unique identifier of the portfolio.  Must be a valid integer.
*   **Response Format:** JSON
    ```json
    {
      "portfolioId": "string",
      "userId": "string",
      "name": "string",
      "assets": [
        {
          "assetId": "string",
          "quantity": "number",
          "price": "number"
        }
      ],
      "totalValue": "number"
    }
    ```
*   **Example Request:**
    ```
    GET /api/portfolio/123
    ```
*   **Example Response:**
    ```json
    {
      "portfolioId": "123",
      "userId": "user123",
      "name": "My Portfolio",
      "assets": [
        {
          "assetId": "BTC",
          "quantity": 10.5,
          "price": 65000
        },
        {
          "assetId": "ETH",
          "quantity": 5,
          "price": 3500
        }
      ],
      "totalValue": 347500.0
    }
    ```

### 4.2. POST /api/portfolio/create

*   **Method:** POST
*   **Path:** `/api/portfolio/create`
*   **Description:** Creates a new portfolio.
*   **Request Parameters/Body:**
    *   `userId` (Body Parameter): The unique identifier of the user creating the portfolio.  Must be a valid string.
    *   `name` (Body Parameter): The name of the portfolio.  Must be a valid string.
*   **Response Format:** JSON
    ```json
    {
      "portfolioId": "string",
      "userId": "string",
      "name": "string"
    }
    ```
*   **Example Request:**
    ```
    POST /api/portfolio/create
    Content-Type: application/json

    {
      "userId": "user123",
      "name": "New Portfolio"
    }
    ```
*   **Example Response:**
    ```json
    {
      "portfolioId": "456",
      "userId": "user123",
      "name": "New Portfolio"
    }
    ```

### 4.3. GET /api/asset/price/{assetId}

*   **Method:** GET
*   **Path:** `/api/asset/price/{assetId}`
*   **Description:** Retrieves the current price of an asset.
*   **Request Parameters/Body:**
    *   `assetId` (Path Parameter): The unique identifier of the asset.  Must be a valid string.
*   **Response Format:** JSON
    ```json
    {
      "assetId": "string",
      "price": "number"
    }
    ```
*   **Example Request:**
    ```
    GET /api/asset/price/BTC
    ```
*   **Example Response:**
    ```json
    {
      "assetId": "BTC",
      "price": 65000.0
    }
    ```

### 4.4. POST /api/user/auth

*   **Method:** POST
*   **Path:** `/api/user/auth`
*   **Description:** Handles user authentication using EIP-712 signatures.
*   **Request Parameters/Body:**
    *   `portfolioId` (Body Parameter): The ID of the portfolio.
    *   `operation` (Body Parameter): The operation to perform (e.g., "create_portfolio", "view_portfolio").
    *   `signature` (Body Parameter): The EIP-712 signature.
*   **Response Format:** JSON
    ```json
    {
      "userId": "string",
      "success": true
    }
    ```
*   **Example Request:**
    ```
    POST /api/user/auth
    Content-Type: application/json

    {
      "portfolioId": "123",
      "operation": "view_portfolio",
      "signature": "..."
    }
    ```
*   **Example Response:**
    ```json
    {
      "userId": "user123",
      "success": true
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.         |
| 401      | Unauthorized - Invalid signature.       |
| 404      | Not Found - Resource not found.         |
| 500      | Internal Server Error - Server error.     |

**Error Response Format:**

```json
{
  "code": "integer",
  "message": "string"
}
```

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse.  The rate limit is 100 requests per minute per user.  Exceeding the rate limit will result in a 429 (Too Many Requests) error.

*   **Limit:** 100 requests per minute per user.
*   **Header:** `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`  (These headers will be returned with rate-limited responses).
```
