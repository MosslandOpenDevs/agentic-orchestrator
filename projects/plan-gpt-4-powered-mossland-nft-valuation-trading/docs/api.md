```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides access to portfolio, user, and asset data. It's designed to be used by applications needing to manage user accounts, track portfolios, and retrieve asset pricing information.  The API utilizes EIP-712 signatures for user authentication, enhancing security.

## 2. Authentication Details

This API requires authentication for all requests except for the `/api/assets/{asset_id}/price` endpoint.

**EIP-712 Signature Authentication:**

All requests to `/api/users/*` and `/api/portfolios/*` require an `Authorization` header containing an EIP-712 signature.

*   **Signature Generation:**  The signature is generated using a key pair.  The user must sign a specific message (e.g., a JSON payload containing user details) using their private key.  The generated signature is then included in the `Authorization` header.
*   **Signature Format:** `signature = eip712_signature`
*   **Message Format:**  The message used for signature generation is a JSON object.  The exact structure of this message will be provided in the request examples.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`

(Replace `https://api.example.com/v1` with the actual base URL)

## 4. Endpoints

### 4.1 GET /api/users/{user_id}

*   **Method:** `GET`
*   **Path:** `/api/users/{user_id}`
*   **Description:** Retrieves user information based on the provided `user_id`.
*   **Request Parameters/Body:**
    *   `user_id` (path parameter):  The unique identifier of the user.  Must be a valid integer.
*   **Response Format:** JSON
    ```json
    {
      "user_id": 123,
      "username": "john.doe",
      "email": "john.doe@example.com",
      "created_at": "2023-10-26T10:00:00Z"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/users/123`
    *   **Response:**
        ```json
        {
          "user_id": 123,
          "username": "john.doe",
          "email": "john.doe@example.com",
          "created_at": "2023-10-26T10:00:00Z"
        }
        ```

### 4.2 GET /api/portfolios/{portfolio_id}

*   **Method:** `GET`
*   **Path:** `/api/portfolios/{portfolio_id}`
*   **Description:** Retrieves portfolio information based on the provided `portfolio_id`.
*   **Request Parameters/Body:**
    *   `portfolio_id` (path parameter): The unique identifier of the portfolio. Must be a valid integer.
*   **Response Format:** JSON
    ```json
    {
      "portfolio_id": 456,
      "name": "My Investments",
      "user_id": 123,
      "assets": [
        {
          "asset_id": 789,
          "quantity": 10,
          "price": 100.00
        },
        {
          "asset_id": 789,
          "quantity": 5,
          "price": 120.00
        }
      ]
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/portfolios/456`
    *   **Response:**
        ```json
        {
          "portfolio_id": 456,
          "name": "My Investments",
          "user_id": 123,
          "assets": [
            {
              "asset_id": 789,
              "quantity": 10,
              "price": 100.00
            },
            {
              "asset_id": 789,
              "quantity": 5,
              "price": 120.00
            }
          ]
        }
        ```

### 4.3 GET /api/assets/{asset_id}/price

*   **Method:** `GET`
*   **Path:** `/api/assets/{asset_id}/price`
*   **Description:** Retrieves asset price data for the specified `asset_id`.
*   **Request Parameters/Body:**
    *   `asset_id` (path parameter): The unique identifier of the asset. Must be a valid integer.
*   **Response Format:** JSON
    ```json
    {
      "asset_id": 789,
      "symbol": "BTC",
      "price": 60000.00,
      "timestamp": 1698398400
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        `GET /api/assets/789/price`
    *   **Response:**
        ```json
        {
          "asset_id": 789,
          "symbol": "BTC",
          "price": 60000.00,
          "timestamp": 1698398400
        }
        ```

### 4.4 POST /api/users/auth

*   **Method:** `POST`
*   **Path:** `/api/users/auth`
*   **Description:** Handles user authentication via EIP-712 signatures.
*   **Request Parameters/Body:**
    *   `message` (required): A JSON payload containing user details (e.g., `username`, `email`).  The exact structure will be documented in the response.
    *   `signature` (required): The EIP-712 signature for the `message`.
*   **Response Format:** JSON
    ```json
    {
      "user_id": 123,
      "username": "john.doe",
      "email": "john.doe@example.com",
      "status": "authenticated"
    }
    ```
*   **Example Requests/Responses:**

    *   **Request:**
        ```json
        {
          "message": {
            "username": "john.doe",
            "email": "john.doe@example.com"
          },
          "signature": "eab3d7c8f9..."  // Example signature
        }
        ```
    *   **Response:**
        ```json
        {
          "user_id": 123,
          "username": "john.doe",
          "email": "john.doe@example.com",
          "status": "authenticated"
        }
        ```

## 5. Error Codes and Handling

| Code      | Description                               | Response Format        |
|-----------|-------------------------------------------|------------------------|
| 400        | Bad Request - Invalid input data.         | `{"error": "Invalid input"}` |
| 401        | Unauthorized - Authentication failed.    | `{"error": "Unauthorized"}` |
| 404        | Not Found - Resource not found.          | `{"error": "Not Found"}`  |
| 500        | Internal Server Error - Server error.     | `{"error": "Internal Server Error"}` |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse.  The following rate limits are in place:

*   **Requests per minute:** 60 requests per minute per user.
*   **Headers:** Rate limiting information will be provided in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.  For example:
    *   `X-RateLimit-Limit: 60`
    *   `X-RateLimit-Remaining: 35`
    *   `X-RateLimit-Reset: 120`
