```markdown
# NFT Generator API Documentation

## 1. Overview

This API provides functionalities for generating, retrieving, and minting NFTs. It utilizes the Polygon blockchain for minting operations. This documentation outlines the available endpoints, authentication methods, request/response formats, and potential error handling.

## 2. Authentication Details

All API requests require an API key in the `X-API-Key` header.  This key must be provided for all requests.  You can obtain your API key from the [API Key Management Portal](https://your-api-key-portal.com).  Failure to provide a valid API key will result in a `401 Unauthorized` error.

## 3. Base URL Configuration

The base URL for all API requests is:

```
https://api.yournftproject.com
```

## 4. API Endpoints

### 4.1. POST /api/generate-nft

*   **Method:** POST
*   **Path:** /api/generate-nft
*   **Description:** Generates a new NFT based on a user-provided prompt. This endpoint utilizes a generative AI model to create an image and associated metadata.
*   **Request Parameters/Body:**

    *   `prompt` (string, required): The text prompt used to generate the NFT.  Example: "A futuristic cyberpunk cat wearing sunglasses."
    *   `description` (string, optional):  A more detailed description of the NFT.
    *   `traits` (array, optional): An array of traits to influence the generation.  (e.g., ["cyberpunk", "cat", "sunglasses"]) -  Limited to a predefined set of traits.
*   **Response Format:** JSON

    ```json
    {
      "tokenId": "string", // Unique token ID of the generated NFT
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
      "prompt": "A majestic unicorn in a magical forest",
      "traits": ["unicorn", "magic", "forest"]
    }
    ```
*   **Example Response:**

    ```json
    {
      "tokenId": "0x1234567890abcdef1234567890abcdef1234",
      "metadata": {
        "name": "Magical Unicorn",
        "description": "A beautiful unicorn roaming through a magical forest.",
        "image": "https://example.com/unicorn.png",
        "attributes": [
          {
            "trait_type": "unicorn",
            "value": "magical"
          },
          {
            "trait_type": "magic",
            "value": "forest"
          },
          {
            "trait_type": "forest",
            "value": "magical"
          }
        ]
      }
    }
    ```

### 4.2. GET /api/nft/:tokenId

*   **Method:** GET
*   **Path:** /api/nft/:tokenId
*   **Description:** Retrieves NFT metadata by its token ID.
*   **Request Parameters:**

    *   `tokenId` (string, required): The unique token ID of the NFT.
*   **Response Format:** JSON

    ```json
    {
      "metadata": {
        "name": "string",
        "description": "string",
        "image": "string",
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

    ```
    GET /api/nft/0x1234567890abcdef1234567890abcdef1234
    ```
*   **Example Response:**

    ```json
    {
      "metadata": {
        "name": "Magical Unicorn",
        "description": "A beautiful unicorn roaming through a magical forest.",
        "image": "https://example.com/unicorn.png",
        "attributes": [
          {
            "trait_type": "unicorn",
            "value": "magical"
          },
          {
            "trait_type": "magic",
            "value": "forest"
          },
          {
            "trait_type": "forest",
            "value": "magical"
          }
        ]
      }
    }
    ```

### 4.3. POST /api/mint

*   **Method:** POST
*   **Path:** /api/mint
*   **Description:** Mints an NFT on the Polygon blockchain.  This requires a valid `tokenId` (obtained from the `/api/generate-nft` endpoint) and sufficient Polygon network funds.
*   **Request Parameters/Body:**

    *   `tokenId` (string, required): The token ID of the NFT to mint.
    *   `recipient` (string, required): The Polygon address to which the NFT will be transferred.
*   **Response Format:** JSON

    ```json
    {
      "transactionHash": "string", // Hash of the transaction on the Polygon blockchain
      "status": "string", // "success" or "failure"
      "message": "string" //  Details about the transaction
    }
    ```
*   **Example Request:**

    ```json
    {
      "tokenId": "0x1234567890abcdef1234567890abcdef1234",
      "recipient": "0xYourPolygonAddress"
    }
    ```
*   **Example Response (Success):**

    ```json
    {
      "transactionHash": "0x...",
      "status": "success",
      "message": "NFT minted successfully!"
    }
    ```

*   **Example Response (Failure):**

    ```json
    {
      "transactionHash": "0x...",
      "status": "failure",
      "message": "Insufficient funds to mint NFT."
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Possible Causes                               |
| :------ | :--------------------------------------- | :------------------------------------------- |
| 400      | Bad Request                              | Invalid request body, missing required parameters |
| 401      | Unauthorized                             | Invalid or missing API key                     |
| 404      | Not Found                               | Token ID does not exist                       |
| 429      | Too Many Requests                        | Rate limiting exceeded                         |
| 500      | Internal Server Error                    | Server-side error                              |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.  The following rate limits are enforced:

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Generation Requests per Minute:** 10 generation requests per minute per API key.

If you exceed the rate limits, you will receive a `429 Too Many Requests` error.  Implement retry logic with exponential backoff to handle these situations gracefully.  Consult the API Key Management Portal for potential rate limit increases based on your usage.
```