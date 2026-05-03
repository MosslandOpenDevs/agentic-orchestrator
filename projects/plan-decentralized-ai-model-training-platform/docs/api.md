```markdown
# AI Model Deployment API Documentation

## 1. Overview

This API provides endpoints for managing AI models and user transactions related to model deployments. It allows users to retrieve a list of available models, get details about a specific model, register new users, and create new transactions representing model deployment requests.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  This key must be provided for every request.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`

## 4. Endpoints

### 4.1. GET /api/models

*   **Method:** `GET`
*   **Path:** `/api/models`
*   **Description:** Retrieves a list of available AI models.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    ```json
    [
      {
        "modelId": "model123",
        "name": "GPT-3.5",
        "description": "A powerful language model for various tasks.",
        "version": "1.0",
        "pricing": "Pay-as-you-go"
      },
      {
        "modelId": "model456",
        "name": "Stable Diffusion",
        "description": "An image generation model.",
        "version": "2.1",
        "pricing": "Subscription"
      }
    ]
    ```
*   **Example Requests/Responses:**
    *   **Request:**
        `GET /api/models`
    *   **Response:** (See JSON example above)

### 4.2. GET /api/models/:modelId

*   **Method:** `GET`
*   **Path:** `/api/models/:modelId` (Replace `:modelId` with the actual model ID)
*   **Description:** Retrieves details for a specific AI model.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    ```json
    {
      "modelId": "model123",
      "name": "GPT-3.5",
      "description": "A powerful language model for various tasks.",
      "version": "1.0",
      "pricing": "Pay-as-you-go",
      "deploymentCost": 0.10,
      "maxRequestsPerMinute": 100
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:**
        `GET /api/models/model123`
    *   **Response:** (See JSON example above)

### 4.3. POST /api/users/register

*   **Method:** `POST`
*   **Path:** `/api/users/register`
*   **Description:** Registers a new user.
*   **Request Parameters/Body:** JSON
    ```json
    {
      "username": "newuser",
      "email": "newuser@example.com",
      "password": "securepassword"
    }
    ```
*   **Response Format:** JSON
    *   **Success (201 Created):**
        ```json
        {
          "userId": "user789",
          "username": "newuser",
          "email": "newuser@example.com"
        }
        ```
    *   **Error (400 Bad Request):**
        ```json
        {
          "error": "Invalid input data."
        }
        ```
*   **Example Requests/Responses:**
    *   **Request:**
        `POST /api/users/register` with the JSON body above.
    *   **Response (Success):** (See JSON example above)
    *   **Response (Error):** (See JSON example above)

### 4.4. POST /api/transactions

*   **Method:** `POST`
*   **Path:** `/api/transactions`
*   **Description:** Creates a new transaction (model deployment).
*   **Request Parameters/Body:** JSON
    ```json
    {
      "modelId": "model123",
      "userId": "user789",
      "quantity": 1,
      "region": "us-east-1"
    }
    ```
*   **Response Format:** JSON
    *   **Success (201 Created):**
        ```json
        {
          "transactionId": "transaction123",
          "modelId": "model123",
          "userId": "user789",
          "quantity": 1,
          "region": "us-east-1",
          "status": "pending"
        }
        ```
    *   **Error (400 Bad Request):**
        ```json
        {
          "error": "Invalid request parameters."
        }
        ```
*   **Example Requests/Responses:**
    *   **Request:**
        `POST /api/transactions` with the JSON body above.
    *   **Response (Success):** (See JSON example above)
    *   **Response (Error):** (See JSON example above)

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.         |
| 401      | Unauthorized - Invalid API key.          |
| 404      | Not Found - Resource not found.          |
| 500      | Internal Server Error - Server error.     |

## 6. Rate Limiting Info

The API is rate-limited to 100 requests per minute per API key.  If you exceed this limit, you will receive a `429 Too Many Requests` error.  The response headers will include rate limit information, including the remaining requests and the reset time.  Example: `X-RateLimit-Limit: 100`, `X-RateLimit-Remaining: 75`, `X-RateLimit-Reset: 60`.
```