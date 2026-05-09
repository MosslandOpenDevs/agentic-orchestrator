```markdown
# ENS Dynamic NFT API Documentation

## 1. Overview

This API provides endpoints for interacting with the ENS (Ethereum Name Service) dynamic NFT ecosystem. It allows users to retrieve information about ENS domains, mint dynamic NFTs linked to those domains, and retrieve details about NFTs and users. This API is designed to be a foundational component for building applications that leverage the integration between ENS and dynamic NFTs.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  This key must be provided for every request.  Contact your administrator to obtain a valid API key.  The API key is used to authenticate and authorize requests.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`  (Replace `https://api.example.com/v1` with the actual base URL)

## 4. Endpoints

### 4.1. GET /api/ens/domains/{domainId}

*   **Method:** GET
*   **Path:** `/api/ens/domains/{domainId}`
*   **Description:** Retrieves information about a specific ENS domain.  The `{domainId}` is a path parameter representing the unique identifier of the ENS domain.
*   **Request Parameters/Body:**
    *   `domainId` (string, required): The ID of the ENS domain to retrieve.  This should be a valid ENS domain identifier.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/ens/domains/0x1234567890abcdef1234567890abcdef12345678
    ```
*   **Example Response (200 OK):**

    ```json
    {
      "domainId": "0x1234567890abcdef1234567890abcdef12345678",
      "name": "example.eth",
      "nftId": "0x9876543210fedcba9876543210fedcba98765432",
      "mintedAt": "2023-10-27T10:00:00Z",
      "metadata": {
        "description": "A dynamic NFT linked to example.eth",
        "image": "https://example.com/image.png"
      }
    }
    ```
*   **Error Codes:**
    *   404 Not Found: Domain not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

### 4.2. POST /api/nft/mint

*   **Method:** POST
*   **Path:** `/api/nft/mint`
*   **Description:** Mints a dynamic NFT linked to an ENS domain.
*   **Request Parameters/Body:**

    ```json
    {
      "domainId": "0x1234567890abcdef1234567890abcdef12345678",
      "metadata": {
        "description": "A new dynamic NFT",
        "image": "https://example.com/new_image.png"
      }
    }
    ```
    *   `domainId` (string, required): The ID of the ENS domain to link the NFT to.
    *   `metadata` (object, required):  A JSON object containing the metadata for the NFT. This can include a description and an image URL.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    POST /api/nft/mint
    Content-Type: application/json

    {
      "domainId": "0x1234567890abcdef1234567890abcdef12345678",
      "metadata": {
        "description": "My awesome NFT",
        "image": "https://example.com/my_nft.jpg"
      }
    }
    ```
*   **Example Response (201 Created):**

    ```json
    {
      "nftId": "0x9876543210fedcba9876543210fedcba98765432",
      "domainId": "0x1234567890abcdef1234567890abcdef12345678",
      "mintedAt": "2023-10-27T10:05:00Z"
    }
    ```
*   **Error Codes:**
    *   400 Bad Request: Invalid request body.
    *   404 Not Found: Domain not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

### 4.3. GET /api/nft/{nftId}

*   **Method:** GET
*   **Path:** `/api/nft/{nftId}`
*   **Description:** Retrieves information about a specific NFT. The `{nftId}` is a path parameter representing the unique identifier of the NFT.
*   **Request Parameters/Body:**
    *   `nftId` (string, required): The ID of the NFT to retrieve.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/nft/0x9876543210fedcba9876543210fedcba98765432
    ```
*   **Example Response (200 OK):**

    ```json
    {
      "nftId": "0x9876543210fedcba9876543210fedcba98765432",
      "domainId": "0x1234567890abcdef1234567890abcdef12345678",
      "mintedAt": "2023-10-27T10:05:00Z",
      "metadata": {
        "description": "My awesome NFT",
        "image": "https://example.com/my_nft.jpg"
      }
    }
    ```
*   **Error Codes:**
    *   404 Not Found: NFT not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

### 4.4. GET /api/users/{userId}

*   **Method:** GET
*   **Path:** `/api/users/{userId}`
*   **Description:** Retrieves information about a specific user. The `{userId}` is a path parameter representing the unique identifier of the user.
*   **Request Parameters/Body:**
    *   `userId` (string, required): The ID of the user to retrieve.
*   **Response Format:** JSON
*   **Example Request:**

    ```
    GET /api/users/user123
    ```
*   **Example Response (200 OK):**

    ```json
    {
      "userId": "user123",
      "username": "john.doe",
      "email": "john.doe@example.com"
    }
    ```
*   **Error Codes:**
    *   404 Not Found: User not found.
    *   500 Internal Server Error: An unexpected error occurred on the server.

## 5. Error Codes and Handling

| Code    | Description                        | Handling                               |
| :------ | :--------------------------------- | :------------------------------------- |
| 400      | Bad Request                        | Validate request body and parameters. |
| 401      | Unauthorized (Invalid API Key)     | Provide a valid API key.                |
| 404      | Not Found                          | Verify the resource exists.             |
| 500      | Internal Server Error              | Log the error and contact support.      |
| 429      | Too Many Requests (Rate Limited)  | Implement retry logic with exponential backoff. |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Headers:** Rate limit information is provided in the response headers:
    *   `X-RateLimit-Limit`: The maximum number of requests allowed.
    *   `X-RateLimit-Remaining`: The number of requests remaining.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```