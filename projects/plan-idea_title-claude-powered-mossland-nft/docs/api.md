```markdown
# NFT Portfolio API Documentation

## 1. Overview

This API provides endpoints for managing NFT collections, retrieving cryptocurrency prices, and creating and managing portfolios. It allows users to track their NFT holdings and monitor cryptocurrency prices, providing a comprehensive tool for NFT portfolio management.

## 2. Authentication Details

Currently, this API does not require authentication for read-only operations (GET requests).  For POST and PUT requests (creating and updating portfolios), a Bearer token is required.  Tokens can be obtained through the `/api/auth/token` endpoint (not documented here for brevity, but implemented internally).  Include the token in the `Authorization` header of your requests.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com`

## 4. Endpoints

### 4.1 GET /api/nftCollections

*   **Method:** GET
*   **Path:** `/api/nftCollections`
*   **Description:** Retrieves a list of available NFT collections.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON Array
    ```json
    [
      {
        "collectionId": "0x1234567890abcdef",
        "name": "CryptoPunks",
        "symbol": "Punks",
        "description": "The first officially recognized collection of 10,000 unique pixelpunks.",
        "website": "https://www.cryptopunks.com/"
      },
      {
        "collectionId": "0xfedcba9876543210",
        "name": "Bored Ape Yacht Club",
        "symbol": "BAYC",
        "description": "The original collection of 10,000 Bored Ape NFTs.",
        "website": "https://www.boredapetysclub.com/"
      }
    ]
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/nftCollections`
    *   **Response:** (See JSON response above)

### 4.2 GET /api/priceFeeds/ethereum

*   **Method:** GET
*   **Path:** `/api/priceFeeds/ethereum`
*   **Description:** Retrieves the current price of Ethereum.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    ```json
    {
      "currency": "ETH",
      "price": 2500.50,
      "timestamp": 1678886400
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/priceFeeds/ethereum`
    *   **Response:** (See JSON response above)

### 4.3 POST /api/portfolios

*   **Method:** POST
*   **Path:** `/api/portfolios`
*   **Description:** Creates a new portfolio.
*   **Request Parameters/Body:** JSON
    ```json
    {
      "name": "My Portfolio",
      "description": "A portfolio tracking my NFT investments.",
      "currency": "USD"
    }
    ```
*   **Response Format:** JSON
    *   **Success (201 Created):** Returns the newly created portfolio object.
        ```json
        {
          "portfolioId": "a1b2c3d4e5f6",
          "name": "My Portfolio",
          "description": "A portfolio tracking my NFT investments.",
          "currency": "USD",
          "createdAt": "2023-03-15T10:00:00Z"
        }
        ```
    *   **Error (400 Bad Request):**  If the request body is invalid.
        ```json
        {
          "error": "Invalid request body. 'name' is required."
        }
        ```
*   **Example Requests/Responses:**
    *   **Request:** `POST /api/portfolios` with the JSON body above.
    *   **Response:** (See successful JSON response above)

### 4.4 GET /api/portfolios/:portfolioId

*   **Method:** GET
*   **Path:** `/api/portfolios/:portfolioId` (e.g., `/api/portfolios/a1b2c3d4e5f6`)
*   **Description:** Retrieves a specific portfolio.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    ```json
    {
      "portfolioId": "a1b2c3d4e5f6",
      "name": "My Portfolio",
      "description": "A portfolio tracking my NFT investments.",
      "currency": "USD",
      "createdAt": "2023-03-15T10:00:00Z"
    }
    ```
*   **Example Requests/Responses:**
    *   **Request:** `GET /api/portfolios/a1b2c3d4e5f6`
    *   **Response:** (See JSON response above)

### 4.5 PUT /api/portfolios/:portfolioId

*   **Method:** PUT
*   **Path:** `/api/portfolios/:portfolioId` (e.g., `/api/portfolios/a1b2c3d4e5f6`)
*   **Description:** Updates a specific portfolio.
*   **Request Parameters/Body:** JSON
    ```json
    {
      "name": "Updated Portfolio Name",
      "description": "Updated portfolio description.",
      "currency": "EUR"
    }
    ```
*   **Response Format:** JSON
    *   **Success (200 OK):** Returns the updated portfolio object.
        ```json
        {
          "portfolioId": "a1b2c3d4e5f6",
          "name": "Updated Portfolio Name",
          "description": "Updated portfolio description.",
          "currency": "EUR",
          "createdAt": "2023-03-15T10:00:00Z"
        }
        ```
    *   **Error (400 Bad Request):** If the request body is invalid.
        ```json
        {
          "error": "Invalid request body. 'name' is required."
        }
        ```
*   **Example Requests/Responses:**
    *   **Request:** `PUT /api/portfolios/a1b2c3d4e5f6` with the JSON body above.
    *   **Response:** (See successful JSON response above)

## 5. Error Codes and Handling

| Code    | Description                        | Possible Cause                               |
| :------ | :--------------------------------- | :------------------------------------------ |
| 400      | Bad Request                        | Invalid request body, missing required fields |
| 404      | Not Found                          | Portfolio with the given ID does not exist  |
| 500      | Internal Server Error              | Server-side error                            |
| 401      | Unauthorized                       | Invalid or missing Bearer token              |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse.  The following rate limits apply:

*   **Requests per Minute:** 60 requests per minute per IP address.
*   **Exceeded Limit:** If the rate limit is exceeded, the API will return a 429 (Too Many Requests) error.  Implement retry logic with exponential backoff to handle this situation gracefully.
```
