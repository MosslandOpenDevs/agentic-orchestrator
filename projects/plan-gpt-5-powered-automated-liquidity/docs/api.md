```markdown
# Billions Network API Documentation

## 1. Overview

This API provides access to data and functionality related to the Billions Network, including token price, NFT portfolio management, and AI-powered portfolio rebalancing suggestions.  It leverages external services like CoinGecko/CoinMarketCap for cryptocurrency price data and GPT-5 for advanced analysis.

## 2. Authentication Details

Currently, this API does not require authentication for most endpoints. However, future versions may require API keys for increased security and usage tracking.  All requests are sent over HTTPS.

## 3. Base URL Configuration

The base URL for all API endpoints is:

`https://api.billionsnetwork.com`

## 4. Endpoints

### 4.1. GET /api/billions/price

*   **Method:** GET
*   **Path:** /api/billions/price
*   **Description:** Retrieves the current price of the Billions Network token (BNT).
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
*   **Example Request:**
    `GET /api/billions/price`
*   **Example Response:**
    ```json
    {
      "symbol": "BNT",
      "price": 123.45,
      "last_updated": "2023-10-27T10:00:00Z"
    }
    ```

### 4.2. GET /api/nft/portfolio/{portfolioId}

*   **Method:** GET
*   **Path:** /api/nft/portfolio/{portfolioId}
*   **Description:** Retrieves the NFT portfolio data for a given portfolio ID.
*   **Request Parameters/Body:** None
*   **Path Parameters:**
    *   `portfolioId`: (string) The unique identifier for the portfolio.
*   **Response Format:** JSON
*   **Example Request:**
    `GET /api/nft/portfolio/123`
*   **Example Response:**
    ```json
    {
      "portfolioId": "123",
      "userId": "user123",
      "nft_holdings": [
        {
          "tokenId": "NFT001",
          "name": "Digital Artwork 1",
          "nftType": "Digital Art",
          "quantity": 5,
          "price": 100.00
        },
        {
          "tokenId": "NFT002",
          "name": "Collectible Item 2",
          "nftType": "Collectible",
          "quantity": 10,
          "price": 50.00
        }
      ]
    }
    ```

### 4.3. POST /api/gpt/prompt

*   **Method:** POST
*   **Path:** /api/gpt/prompt
*   **Description:** Sends a prompt to the GPT-5 API for portfolio rebalancing decisions.  This endpoint utilizes a GPT-5 integration for advanced analysis and recommendations.
*   **Request Parameters/Body:**
    *   `portfolioId`: (string) The unique identifier for the portfolio.
    *   `prompt`: (string) The prompt to send to the GPT-5 API.  Example: "Suggest a portfolio rebalancing strategy for portfolio ID 123, considering current market conditions and the user's risk tolerance."
*   **Response Format:** JSON
*   **Example Request:**
    `POST /api/gpt/prompt`
    `Content-Type: application/json`
    `{
      "portfolioId": "123",
      "prompt": "Suggest a portfolio rebalancing strategy for portfolio ID 123, considering current market conditions and the user's risk tolerance."
    }`
*   **Example Response:**
    ```json
    {
      "status": "success",
      "gptResponse": "Based on the current market conditions and a moderate risk tolerance, I recommend shifting 20% of your portfolio from NFTs of type 'Collectible' to NFTs of type 'Digital Art'.",
      "timestamp": "2023-10-27T10:05:00Z"
    }
    ```

### 4.4. GET /api/coinmarketcap/price/{symbol}

*   **Method:** GET
*   **Path:** /api/coinmarketcap/price/{symbol}
*   **Description:** Retrieves the current price of a cryptocurrency from CoinGecko/CoinMarketCap.
*   **Request Parameters/Body:** None
*   **Path Parameters:**
    *   `symbol`: (string) The cryptocurrency symbol (e.g., "BTC", "ETH").
*   **Response Format:** JSON
*   **Example Request:**
    `GET /api/coinmarketcap/price/BTC`
*   **Example Response:**
    ```json
    {
      "symbol": "BTC",
      "price": 45000.00,
      "last_updated": "2023-10-27T10:01:00Z"
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid Input             | Check request parameters and body.     |
| 404      | Not Found - Resource Not Found          | Verify the resource ID is correct.   |
| 500      | Internal Server Error                   | Contact API support.                 |
| 429      | Too Many Requests - Rate Limit Exceeded | Implement retry logic with exponential backoff. |

## 6. Rate Limiting Info

The API is rate-limited to prevent abuse and ensure fair usage.

*   **Requests per Minute:** 60 requests per minute per IP address.
*   **Default Delay:**  If the rate limit is exceeded, a 60-second delay will be applied to subsequent requests.
*   **Monitoring:** Rate limit usage can be monitored through API usage logs (currently not publicly accessible, but available upon request for developers).
```