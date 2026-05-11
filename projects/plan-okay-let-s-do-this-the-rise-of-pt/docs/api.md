```markdown
# Vault & Asset API Documentation

## 1. Overview

This API provides access to user vaults and associated asset data, as well as integration with a GPT-5 analysis service. It allows users to create, retrieve, update, and analyze data within their vaults.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  This key should be obtained during user registration.  Requests without a valid API key will be rejected with a 401 Unauthorized error.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com`  (Replace with your actual API base URL)

## 4. Endpoints

### 4.1. GET /api/vaults

*   **Method:** `GET`
*   **Path:** `/api/vaults`
*   **Description:** Retrieves a list of all vaults associated with the authenticated user.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each element in the array represents a vault and contains the following fields:
        *   `vaultId` (string): Unique identifier for the vault.
        *   `name` (string): Name of the vault.
        *   `description` (string, optional): A brief description of the vault.
        *   `createdAt` (string): Timestamp of vault creation (ISO 8601 format).
*   **Example Request:**
    ```
    GET /api/vaults
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:**
    ```json
    [
      {
        "vaultId": "vault-123",
        "name": "My First Vault",
        "description": "This is my initial vault.",
        "createdAt": "2023-10-27T10:00:00Z"
      },
      {
        "vaultId": "vault-456",
        "name": "Project Alpha",
        "createdAt": "2023-10-26T15:30:00Z"
      }
    ]
    ```

### 4.2. GET /api/vaults/:vaultId

*   **Method:** `GET`
*   **Path:** `/api/vaults/:vaultId`
*   **Description:** Retrieves a specific vault by its ID.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    *   `vaultId` (string): Unique identifier for the vault.
    *   `name` (string): Name of the vault.
    *   `description` (string, optional): A brief description of the vault.
    *   `createdAt` (string): Timestamp of vault creation (ISO 8601 format).
*   **Example Request:**
    ```
    GET /api/vaults/vault-123
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:**
    ```json
    {
      "vaultId": "vault-123",
      "name": "My First Vault",
      "description": "This is my initial vault.",
      "createdAt": "2023-10-27T10:00:00Z"
    }
    ```

### 4.3. POST /api/vaults

*   **Method:** `POST`
*   **Path:** `/api/vaults`
*   **Description:** Creates a new vault.
*   **Request Parameters/Body:** JSON
    *   `name` (string): Name of the vault.
    *   `description` (string, optional): A brief description of the vault.
*   **Response Format:** JSON
    *   `vaultId` (string): Unique identifier for the newly created vault.
    *   `createdAt` (string): Timestamp of vault creation (ISO 8601 format).
*   **Example Request:**
    ```
    POST /api/vaults
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "name": "New Vault",
      "description": "A newly created vault."
    }
    ```
*   **Example Response:**
    ```json
    {
      "vaultId": "vault-789",
      "name": "New Vault",
      "description": "A newly created vault.",
      "createdAt": "2023-10-27T11:30:00Z"
    }
    ```

### 4.4. PUT /api/vaults/:vaultId

*   **Method:** `PUT`
*   **Path:** `/api/vaults/:vaultId`
*   **Description:** Updates an existing vault.
*   **Request Parameters/Body:** JSON
    *   `name` (string): Name of the vault.
    *   `description` (string, optional): A brief description of the vault.
*   **Response Format:** JSON
    *   `vaultId` (string): Unique identifier for the updated vault.
    *   `name` (string): Name of the vault.
    *   `description` (string, optional): A brief description of the vault.
    *   `createdAt` (string): Timestamp of vault creation (ISO 8601 format).
*   **Example Request:**
    ```
    PUT /api/vaults/vault-123
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "name": "Updated Vault Name",
      "description": "This is the updated description."
    }
    ```
*   **Example Response:**
    ```json
    {
      "vaultId": "vault-123",
      "name": "Updated Vault Name",
      "description": "This is the updated description.",
      "createdAt": "2023-10-27T10:00:00Z"
    }
    ```

### 4.5. GET /api/assets

*   **Method:** `GET`
*   **Path:** `/api/assets`
*   **Description:** Retrieves asset data.  This endpoint currently returns placeholder data.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each element in the array represents an asset and contains the following fields:
        *   `assetId` (string): Unique identifier for the asset.
        *   `name` (string): Name of the asset.
        *   `value` (number): Value of the asset.
*   **Example Request:**
    ```
    GET /api/assets
    X-API-Key: YOUR_API_KEY
    ```
*   **Example Response:**
    ```json
    [
      {
        "assetId": "asset-1",
        "name": "Stock A",
        "value": 100.50
      },
      {
        "assetId": "asset-2",
        "name": "Stock B",
        "value": 50.25
      }
    ]
    ```

### 4.6. POST /api/gpt-analysis

*   **Method:** `POST`
*   **Path:** `/api/gpt-analysis`
*   **Description:** Sends data to GPT-5 for analysis and returns the response.
*   **Request Parameters/Body:** JSON
    *   `text` (string): The text to be analyzed by GPT-5.
    *   `prompt` (string, optional):  A custom prompt to guide the analysis.
*   **Response Format:** JSON
    *   `response` (string): The response from the GPT-5 analysis.
    *   `timestamp` (string): Timestamp of the response.
*   **Example Request:**
    ```
    POST /api/gpt-analysis
    X-API-Key: YOUR_API_KEY
    Content-Type: application/json

    {
      "text": "Analyze this text for sentiment.",
      "prompt": "Focus on identifying positive and negative sentiment."
    }
    ```
*   **Example Response:**
    ```json
    {
      "response": "The text expresses a generally positive sentiment, with several instances of enthusiasm and optimism.",
      "timestamp": "2023-10-27T12:00:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code   | Description                               |
| :----- | :---------------------------------------- |
| 400     | Bad Request - Invalid input data.          |
| 401     | Unauthorized - Invalid API key.          |
| 404     | Not Found - Resource not found.           |
| 500     | Internal Server Error - Server error.     |

## 6. Rate Limiting

This API is subject to rate limiting to prevent abuse.  The rate limit is 60 requests per minute per API key.  If you exceed the rate limit, you will receive a 429 Too Many Requests error.  The response headers will include information about the remaining rate limit and the time until the rate limit resets.
```
