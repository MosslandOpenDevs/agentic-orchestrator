```markdown
# ENS API Documentation

## 1. Overview

This API provides access to ENS (Ethereum Name Service) domain information, NFT minting capabilities, and Claude generated assets. It allows developers to integrate ENS domain data into their applications and utilize dynamic NFTs linked to those domains.

## 2. Authentication Details

Currently, this API does not require authentication for most endpoints. However, future versions may require API keys for certain operations.  Check the API provider's documentation for updates.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`  (Replace `https://api.example.com/v1` with the actual base URL)

## 4. Endpoints

### 4.1. GET /api/domains

*   **Method:** `GET`
*   **Path:** `/api/domains`
*   **Description:** Retrieves a list of all ENS domains.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON array of domain objects.
    *   Each object contains:
        *   `name`: (string) The ENS domain name (e.g., `myname.eth`).
        *   `tokenId`: (string) The associated ERC-721 token ID.
        *   `owner`: (string) The address that owns the domain.
        *   `createdAt`: (string) Timestamp of domain creation.
*   **Example Request:**
    `GET /api/domains`
*   **Example Response:**

    ```json
    [
      {
        "name": "myname.eth",
        "tokenId": "0x1234567890abcdef1234567890abcdef12345678",
        "owner": "0xAbCdEf01234567890AbCdEf0123456789",
        "createdAt": "2023-10-27T10:00:00Z"
      },
      {
        "name": "anothername.eth",
        "tokenId": "0x9876543210abcdef9876543210abcdef98765432",
        "owner": "0xEfCdAb01234567890EfCdAb0123456789",
        "createdAt": "2023-10-26T18:30:00Z"
      }
    ]
    ```

### 4.2. GET /api/domains/:domainId

*   **Method:** `GET`
*   **Path:** `/api/domains/:domainId`
*   **Description:** Retrieves details for a specific ENS domain.
*   **Request Parameters/Body:**
    *   `:domainId`: (string) The ENS domain name to retrieve.
*   **Response Format:** JSON object containing domain details.
    *   Same fields as the `/api/domains` endpoint response.
*   **Example Request:**
    `GET /api/domains/myname.eth`
*   **Example Response:**

    ```json
    {
      "name": "myname.eth",
      "tokenId": "0x1234567890abcdef1234567890abcdef12345678",
      "owner": "0xAbCdEf01234567890AbCdEf0123456789",
      "createdAt": "2023-10-27T10:00:00Z"
    }
    ```

### 4.3. POST /api/mint

*   **Method:** `POST`
*   **Path:** `/api/mint`
*   **Description:** Mints a new dynamic NFT linked to an ENS domain.
*   **Request Parameters/Body:**
    *   `domain`: (string) The ENS domain name to mint the NFT for.
    *   `metadata`: (JSON)  Metadata for the NFT (e.g., name, description, image URL).
*   **Response Format:** JSON object indicating the success or failure of the minting operation.
    *   `success`: (boolean) True if the minting was successful, false otherwise.
    *   `tokenId`: (string) The newly minted ERC-721 token ID if successful.
*   **Example Request:**
    `POST /api/mint`
    `Content-Type: application/json`
    `{
      "domain": "myname.eth",
      "metadata": {
        "name": "My Dynamic NFT",
        "description": "A cool NFT linked to my ENS domain.",
        "image": "https://example.com/image.png"
      }
    }`
*   **Example Response (Success):**
    `{
      "success": true,
      "tokenId": "0xNewTokenID"
    }`

*   **Example Response (Failure):**
    `{
      "success": false,
      "error": "Domain already exists"
    }`

### 4.4. GET /api/claude/assets

*   **Method:** `GET`
*   **Path:** `/api/claude/assets`
*   **Description:** Retrieves Claude generated assets.  This endpoint is currently a placeholder and may return different data based on Claude's output.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON array of Claude generated assets.
    *   Each object contains:
        *   `assetType`: (string) The type of asset (e.g., "image", "text").
        *   `assetData`: (string) The generated asset data.
*   **Example Request:**
    `GET /api/claude/assets`
*   **Example Response:**

    ```json
    [
      {
        "assetType": "text",
        "assetData": "This is a Claude generated text asset."
      },
      {
        "assetType": "image",
        "assetData": "data:image/png;base64,iVBORw0KGgoAAA..."  // Placeholder base64 image data
      }
    ]
    ```

## 5. Error Codes and Handling

| Code      | Description                               |
|-----------|-------------------------------------------|
| 400        | Bad Request - Invalid input data.          |
| 404        | Not Found - Resource not found.           |
| 500        | Internal Server Error - Server error.      |
| 429        | Too Many Requests - Rate limit exceeded. |

**Error Response Format:**

```json
{
  "error": "Error message"
}
```

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.

*   **Requests per Minute:** 60 requests per minute.
*   **Burst Limit:** A burst limit of 120 requests per minute is allowed, but exceeding this will result in rate limiting.
*   **Reset Time:** Rate limits reset every 60 seconds.

Consult the API provider's documentation for more detailed rate limiting information.
```
