```markdown
# ENS API Documentation

## 1. Overview

This API provides access to ENS (Ethereum Name Service) domain data and functionality, including domain retrieval, minting dynamic NFTs, and user management. It's designed for developers to integrate ENS data into their applications and services.

## 2. Authentication Details

This API utilizes API keys for authentication.  Each request must include an `X-API-Key` header with your unique API key.  Contact support@example.com to obtain an API key.  No other authentication mechanisms are supported.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.ens`

## 4. Endpoints

### 4.1 GET /api/domains

*   **Method:** `GET`
*   **Path:** `/api/domains`
*   **Description:** Retrieves a list of all registered ENS domains.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON array of domain objects.
*   **Example Request:**
    `GET https://api.example.ens/api/domains`
*   **Example Response:**

    ```json
    [
      {
        "id": "example.eth",
        "name": "example",
        "registrant": "0x...",
        "expiry": "2024-12-31",
        "creation_date": "2023-01-01",
        "status": "active"
      },
      {
        "id": "another.eth",
        "name": "another",
        "registrant": "0x...",
        "expiry": "2024-06-30",
        "creation_date": "2023-03-15",
        "status": "active"
      }
    ]
    ```

### 4.2 GET /api/domains/:domainId

*   **Method:** `GET`
*   **Path:** `/api/domains/:domainId` (Replace `:domainId` with the actual domain ID, e.g., `/api/domains/example.eth`)
*   **Description:** Retrieves details for a specific ENS domain.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON object containing domain details.
*   **Example Request:**
    `GET https://api.example.ens/api/domains/example.eth`
*   **Example Response:**

    ```json
    {
      "id": "example.eth",
      "name": "example",
      "registrant": "0x...",
      "expiry": "2024-12-31",
      "creation_date": "2023-01-01",
      "status": "active"
    }
    ```

### 4.3 POST /api/mint

*   **Method:** `POST`
*   **Path:** `/api/mint`
*   **Description:** Mints a dynamic NFT linked to an ENS domain.  This endpoint requires a valid ENS domain ID and a unique NFT name.
*   **Request Parameters/Body:**
    *   `domainId` (string, required): The ID of the ENS domain to mint the NFT to.
    *   `nftName` (string, required): The name of the NFT to be created.
*   **Response Format:** JSON object indicating the success or failure of the minting operation.
*   **Example Request:**
    `POST https://api.example.ens/api/mint`
    `Content-Type: application/json`
    `X-API-Key: YOUR_API_KEY`
    `{
      "domainId": "example.eth",
      "nftName": "MyAwesomeNFT"
    }`
*   **Example Response (Success):**
    `{
      "status": "success",
      "message": "NFT minted successfully",
      "nftId": "0x..."
    }`

*   **Example Response (Failure):**
    `{
      "status": "error",
      "message": "Invalid domain ID or NFT name"
    }`

### 4.4 GET /api/users

*   **Method:** `GET`
*   **Path:** `/api/users`
*   **Description:** Retrieves a list of registered users.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON array of user objects.
*   **Example Request:**
    `GET https://api.example.ens/api/users`
*   **Example Response:**

    ```json
    [
      {
        "userId": "user123",
        "username": "john.doe",
        "email": "john.doe@example.com"
      },
      {
        "userId": "user456",
        "username": "jane.smith",
        "email": "jane.smith@example.com"
      }
    ]
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid input parameters   | Validate request body and parameters |
| 401      | Unauthorized - Invalid API key          | Provide a valid API key            |
| 404      | Not Found - Resource not found           | Verify resource ID and endpoint      |
| 500      | Internal Server Error                    | Contact support@example.com       |
| 429      | Too Many Requests - Rate Limit Exceeded | Implement retry logic with exponential backoff |


## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.

*   **Requests per minute:** 60
*   **Burst Limit:** 120 requests (allows for short bursts up to the limit)
*   **Reset Time:** 1 minute

Exceeding the rate limit will result in a 429 Too Many Requests error.  Please implement appropriate retry logic with exponential backoff when handling 429 errors.  Detailed rate limit usage can be found in the API response headers (e.g., `X-RateLimit-Limit`, `X-RateLimit-Remaining`, `X-RateLimit-Reset`).
```