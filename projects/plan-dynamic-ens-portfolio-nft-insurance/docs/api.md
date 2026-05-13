```markdown
# Mossland NFT API Documentation

## 1. Overview

This API provides access to data related to Mossland NFTs, holders, portfolios, and valuations. It allows developers to integrate Mossland data into their applications, providing users with insights into NFT ownership, portfolio performance, and asset valuations.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain an API key by registering your application at [https://your-mossland-platform.com/api/register](https://your-mossland-platform.com/api/register).  Replace `https://your-mossland-platform.com/api/register` with the actual registration URL.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.mossland.com`

Replace `https://api.mossland.com` with the actual API URL if it changes.

## 4. Endpoints

### 4.1. GET /api/nftholders

*   **Method:** GET
*   **Path:** /api/nftholders
*   **Description:** Retrieves a list of all NFT holders.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    *   Each object in the array represents an NFT holder.
    *   Example:
        ```json
        [
          {
            "userId": "user123",
            "tokenId": "mossland1",
            "quantity": 1
          },
          {
            "userId": "user456",
            "tokenId": "mossland2",
            "quantity": 2
          }
        ]
        ```
*   **Example Request:**
    `GET /api/nftholders`
*   **Example Response:** (See JSON example above)

### 4.2. GET /api/nftholders/:userId

*   **Method:** GET
*   **Path:** /api/nftholders/:userId
*   **Description:** Retrieves a specific NFT holder by ID.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Object
    *   Returns details of the NFT holder.
    *   Example:
        ```json
        {
          "userId": "user123",
          "tokenId": "mossland1",
          "quantity": 1
        }
        ```
*   **Example Request:**
    `GET /api/nftholders/user123`
*   **Example Response:** (See JSON example above)

### 4.3. GET /api/nft/:tokenId

*   **Method:** GET
*   **Path:** /api/nft/:tokenId
*   **Description:** Retrieves information about a specific Mossland NFT.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Object
    *   Returns details about the NFT.
    *   Example:
        ```json
        {
          "tokenId": "mossland1",
          "name": "Mossland Plot 1",
          "description": "A beautiful plot of land in the Mossland region.",
          "imageURL": "https://example.com/mossland1.png",
          "metadataURL": "https://example.com/mossland1.json"
        }
        ```
*   **Example Request:**
    `GET /api/nft/mossland1`
*   **Example Response:** (See JSON example above)

### 4.4. GET /api/portfolios/:userId

*   **Method:** GET
*   **Path:** /api/portfolios/:userId
*   **Description:** Retrieves a specific portfolio by user ID.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Object
    *   Returns details about the portfolio.
    *   Example:
        ```json
        {
          "userId": "user123",
          "portfolioName": "My Mossland Portfolio",
          "assets": [
            {
              "tokenId": "mossland1",
              "quantity": 1
            },
            {
              "tokenId": "mossland2",
              "quantity": 2
            }
          ]
        }
        ```
*   **Example Request:**
    `GET /api/portfolios/user123`
*   **Example Response:** (See JSON example above)

### 4.5. POST /api/portfolios

*   **Method:** POST
*   **Path:** /api/portfolios
*   **Description:** Creates a new portfolio.
*   **Request Parameters/Body:** JSON Object
    *   `userId`: (Required) The ID of the user creating the portfolio.
    *   `portfolioName`: (Required) The name of the portfolio.
    *   `assets`: (Optional) An array of asset tokens to include in the portfolio.
    *   Example:
        ```json
        {
          "userId": "user789",
          "portfolioName": "New Portfolio",
          "assets": [
            {
              "tokenId": "mossland3",
              "quantity": 3
            }
          ]
        }
        ```
*   **Response Format:** JSON Object (Contains the newly created portfolio details, including the ID)
    *   Example:
        ```json
        {
          "portfolioId": "portfolio123",
          "userId": "user789",
          "portfolioName": "New Portfolio",
          "assets": [
            {
              "tokenId": "mossland3",
              "quantity": 3
            }
          ]
        }
        ```
*   **Example Request:**
    `POST /api/portfolios` with the JSON body above.
*   **Example Response:** (See JSON example above)

### 4.6. GET /api/valuations/:tokenId

*   **Method:** GET
*   **Path:** /api/valuations/:tokenId
*   **Description:** Retrieves valuation data for a specific NFT.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Object
    *   Returns the latest valuation data.
    *   Example:
        ```json
        {
          "tokenId": "mossland1",
          "valuation": 15000,
          "valuationDate": "2023-10-27T10:00:00Z"
        }
        ```
*   **Example Request:**
    `GET /api/valuations/mossland1`
*   **Example Response:** (See JSON example above)

## 5. Error Codes and Handling

| Code    | Description                               |
| :------ | :--------------------------------------- |
| 400      | Bad Request - Invalid input data.          |
| 401      | Unauthorized - Invalid or missing API key. |
| 404      | Not Found - Resource not found.           |
| 500      | Internal Server Error - Server error.      |

**Error Response Format:**

```json
{
  "error": "Error message"
}
```

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse and ensure fair usage.

*   **Limit:** 60 requests per minute per API key.
*   **Headers:** Rate limit information will be returned in the `X-RateLimit-Limit`, `X-RateLimit-Remaining`, and `X-RateLimit-Reset` headers.
    *   `X-RateLimit-Limit`:  The maximum number of requests allowed in the current window.
    *   `X-RateLimit-Remaining`: The number of requests remaining in the current window.
    *   `X-RateLimit-Reset`: The time (in seconds) until the rate limit resets.
```
