```markdown
# NFT Generator API Documentation

## 1. Overview

This API provides endpoints for generating, retrieving, and minting NFTs on the Polygon blockchain. It allows users to create NFTs based on text prompts, view NFT metadata, and mint new NFTs.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  This key should be obtained during registration.  Without a valid API key, requests will be rejected.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.example.com/v1`  (Replace `https://api.example.com/v1` with your actual base URL)

## 4. Endpoints

### 4.1. POST /api/generate-nft

*   **Method:** POST
*   **Path:** `/api/generate-nft`
*   **Description:** Generates an NFT based on a user-provided prompt.  This endpoint utilizes a generative AI model to create an image and associated metadata for the NFT.
*   **Request Parameters/Body:**

    *   `prompt` (string, required): The text prompt used to generate the NFT.
    *   `description` (string, optional): A more detailed description of the desired NFT.
    *   `style` (string, optional):  The desired art style (e.g., "abstract", "realistic", "pixel art"). Defaults to "default".
*   **Response Format:** JSON

    ```json
    {
      "tokenId": "string", // Unique token ID for the generated NFT
      "metadata": {
        "name": "string",
        "description": "string",
        "image": "string", // URL to the generated image
        "attributes": [
          {
            "trait_type": "string",
            "value": "string"
          }
        ]
      }
    }
    ```
*   **Example Request:**

    ```json
    {
      "prompt": "A majestic unicorn in a forest",
      "style": "fantasy"
    }
    ```

*   **Example Response:**

    ```json
    {
      "tokenId": "0x1234567890abcdef1234567890abcdef12345678",
      "metadata": {
        "name": "Unicorn in the Forest",
        "description": "A beautiful unicorn standing in a magical forest.",
        "image": "https://example.com/unicorn.png",
        "attributes": [
          {
            "trait_type": "Creature",
            "value": "Unicorn"
          },
          {
            "trait_type": "Environment",
            "value": "Forest"
          }
        ]
      }
    }
    ```

### 4.2. GET /api/nft/:tokenId

*   **Method:** GET
*   **Path:** `/api/nft/:tokenId`
*   **Description:** Retrieves NFT metadata by token ID.
*   **Request Parameters:**

    *   `tokenId` (string, required): The unique token ID of the NFT.
*   **Response Format:** JSON

    ```json
    {
      "name": "string",
      "description": "string",
      "image": "string", // URL to the generated image
      "attributes": [
        {
          "trait_type": "string",
          "value": "string"
        }
      ]
    }
    ```
*   **Example Request:**

    ```
    GET /api/nft/0x1234567890abcdef1234567890abcdef12345678
    ```

*   **Example Response:**

    ```json
    {
      "name": "Unicorn in the Forest",
      "description": "A beautiful unicorn standing in a magical forest.",
      "image": "https://example.com/unicorn.png",
      "attributes": [
        {
          "trait_type": "Creature",
          "value": "Unicorn"
        },
        {
          "trait_type": "Environment",
          "value": "Forest"
        }
      ]
    }
    ```

### 4.3. POST /api/mint

*   **Method:** POST
*   **Path:** `/api/mint`
*   **Description:** Mints a new NFT on the Polygon blockchain.
*   **Request Parameters/Body:**

    *   `tokenId` (string, required): The token ID of the NFT to mint.
*   **Response Format:** JSON

    ```json
    {
      "success": true,
      "transactionHash": "string" // Hash of the transaction on the Polygon blockchain
    }
    ```
*   **Example Request:**

    ```json
    {
      "tokenId": "0x1234567890abcdef1234567890abcdef12345678"
    }
    ```

*   **Example Response:**

    ```json
    {
      "success": true,
      "transactionHash": "0x1a2b3c4d5e6f7a8b9c0d1e2f3a4b5c6d7e8f9a0b"
    }
    ```

### 4.4. GET /api/users

*   **Method:** GET
*   **Path:** `/api/users`
*   **Description:** Retrieves a list of users.
*   **Response Format:** JSON

    ```json
    [
      {
        "id": "string",
        "username": "string",
        "email": "string"
      },
      {
        "id": "string",
        "username": "string",
        "email": "string"
      }
    ]
    ```
*   **Example Request:**

    ```
    GET /api/users
    ```

*   **Example Response:**

    ```json
    [
      {
        "id": "user123",
        "username": "john.doe",
        "email": "john.doe@example.com"
      },
      {
        "id": "user456",
        "username": "jane.smith",
        "email": "jane.smith@example.com"
      }
    ]
    ```

## 5. Error Codes and Handling

| Code      | Description                     | HTTP Status Code |
| --------- | ------------------------------- | ---------------- |
| 400        | Bad Request                     | 400              |
| 401        | Unauthorized                    | 401              |
| 404        | Not Found                       | 404              |
| 429        | Too Many Requests               | 429              |
| 500        | Internal Server Error           | 500              |

**Error Response Format:**

```json
{
  "error": "string",
  "code": "string"
}
```

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse.

*   **Limit:** 60 requests per minute per API key.
*   **Headers:** Rate limit information will be returned in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.  Example: `X-RateLimit-Limit: 60, X-RateLimit-Remaining: 15, X-RateLimit-Reset: 1678886400`
```
