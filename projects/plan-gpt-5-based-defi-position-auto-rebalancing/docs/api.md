```markdown
# Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing users, portfolios, assets, and retrieving asset price data. It's designed to facilitate the creation and management of investment portfolios, allowing users to track their holdings and access real-time asset prices.

## 2. Authentication Details

All endpoints requiring authentication utilize JSON Web Tokens (JWT).

*   **Registration:** The `/api/users/auth/register` endpoint requires a valid email and password.
*   **Login:** The `/api/users/auth/login` endpoint requires a valid email and password to generate a JWT.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com` (Replace with your actual API base URL)

## 4. Endpoints

### 4.1. GET /api/users/{user_id}

*   **Method:** GET
*   **Path:** `/api/users/{user_id}`
*   **Description:** Retrieves user information based on the provided `user_id`.
*   **Request Parameters:**
    *   `user_id` (Path Parameter):  The unique identifier for the user.  Integer required.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/users/123
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "id": 123,
      "email": "user@example.com",
      "username": "testuser",
      "created_at": "2023-10-26T10:00:00Z"
    }
    ```

### 4.2. GET /api/portfolios/{portfolio_id}

*   **Method:** GET
*   **Path:** `/api/portfolios/{portfolio_id}`
*   **Description:** Retrieves portfolio information based on the provided `portfolio_id`.
*   **Request Parameters:**
    *   `portfolio_id` (Path Parameter): The unique identifier for the portfolio. Integer required.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/portfolios/456
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "id": 456,
      "name": "My Investments",
      "user_id": 123,
      "created_at": "2023-10-25T14:30:00Z"
    }
    ```

### 4.3. GET /api/assets/price/{asset_id}

*   **Method:** GET
*   **Path:** `/api/assets/price/{asset_id}`
*   **Description:** Retrieves price data for a specific asset based on the provided `asset_id`.
*   **Request Parameters:**
    *   `asset_id` (Path Parameter): The unique identifier for the asset. Integer required.
*   **Response Format:** JSON
*   **Example Request:**
    ```
    GET /api/assets/price/789
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "id": 789,
      "symbol": "AAPL",
      "name": "Apple Inc.",
      "price": 175.25,
      "last_updated": "2023-10-26T11:15:00Z"
    }
    ```

### 4.4. POST /api/users/auth/register

*   **Method:** POST
*   **Path:** `/api/users/auth/register`
*   **Description:** Registers a new user.
*   **Request Body:** JSON
    *   `email` (Required): User's email address. String required.
    *   `password` (Required): User's password. String required.
*   **Response Format:** JSON
    *   **201 Created:**  Successful registration. Returns the newly created user object.
    *   **400 Bad Request:**  Invalid input data.
*   **Example Request:**
    ```
    POST /api/users/auth/register
    Content-Type: application/json

    {
      "email": "newuser@example.com",
      "password": "securepassword"
    }
    ```
*   **Example Response (201 Created):**
    ```json
    {
      "id": 987,
      "email": "newuser@example.com",
      "username": "newuser",
      "created_at": "2023-10-26T12:00:00Z"
    }
    ```

### 4.5. POST /api/users/auth/login

*   **Method:** POST
*   **Path:** `/api/users/auth/login`
*   **Description:** Authenticates a user and returns a JWT.
*   **Request Body:** JSON
    *   `email` (Required): User's email address. String required.
    *   `password` (Required): User's password. String required.
*   **Response Format:** JSON
    *   **200 OK:** Successful login. Returns the JWT.
    *   **401 Unauthorized:** Invalid credentials.
*   **Example Request:**
    ```
    POST /api/users/auth/login
    Content-Type: application/json

    {
      "email": "user@example.com",
      "password": "password123"
    }
    ```
*   **Example Response (200 OK):**
    ```json
    {
      "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJ1c2VyX2lkIjoxMjMsImV4cCI6MTY5MjU2NTk1Nhs.example_jwt_token"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                       | Response Format |
| :------ | :-------------------------------- | :-------------- |
| 400      | Bad Request - Invalid input data | JSON            |
| 401      | Unauthorized - Invalid credentials | JSON            |
| 404      | Not Found - Resource not found     | JSON            |
| 500      | Internal Server Error             | JSON            |

## 6. Rate Limiting

The API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 100 requests per minute per IP address.
*   **Headers:** Rate limiting information will be returned in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed in the current window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```