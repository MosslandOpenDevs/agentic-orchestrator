```markdown
# RWA Portfolio API Documentation

## 1. Overview

This API provides access to a portfolio of Real World Assets (RWA) managed through automated rebalancing and analysis. It integrates with Chainlink for real-time price data and leverages GPT-5 for advanced portfolio analysis. This documentation outlines the available endpoints, authentication requirements, and expected response formats.

## 2. Authentication Details

All API requests require an API key passed in the `X-API-Key` header.  You can obtain your API key by registering an account through our portal: [https://your-portal-url.com](https://your-portal-url.com) (Replace with your actual portal URL).

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.rwaportfolio.com`

## 4. Endpoints

### 4.1. GET /api/rwa/assets

*   **Method:** GET
*   **Path:** `/api/rwa/assets`
*   **Description:** Retrieves a list of RWA assets currently held in the portfolio.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    *   **Example Response:**
        ```json
        [
          {
            "asset_id": "RWA-BTC-1",
            "asset_name": "Bitcoin (Wrapped)",
            "asset_type": "BTC",
            "quantity": 10.5,
            "current_price": 30000.00,
            "total_value": 315000.00
          },
          {
            "asset_id": "RWA-ETH-2",
            "asset_name": "Ethereum (Wrapped)",
            "asset_type": "ETH",
            "quantity": 5.2,
            "current_price": 2500.00,
            "total_value": 13000.00
          }
        ]
        ```
*   **Example Request:**
    `GET /api/rwa/assets`
    *   **Headers:**
        `X-API-Key: YOUR_API_KEY`

### 4.2. GET /api/rwa/prices

*   **Method:** GET
*   **Path:** `/api/rwa/prices`
*   **Description:** Retrieves real-time RWA prices from Chainlink.
*   **Request Parameters/Body:** None
*   **Response Format:** JSON
    *   **Example Response:**
        ```json
        {
          "BTC": {
            "price": 30000.00,
            "last_updated": "2023-10-27T10:00:00Z"
          },
          "ETH": {
            "price": 2500.00,
            "last_updated": "2023-10-27T10:00:00Z"
          }
        }
        ```
*   **Example Request:**
    `GET /api/rwa/prices`
    *   **Headers:**
        `X-API-Key: YOUR_API_KEY`

### 4.3. POST /api/rwa/rebalance

*   **Method:** POST
*   **Path:** `/api/rwa/rebalance`
*   **Description:** Initiates the rebalancing algorithm based on the specified risk tolerance.
*   **Request Parameters/Body:**
    *   `risk_tolerance`: (String)  A string representing the desired risk tolerance level.  Possible values: `low`, `medium`, `high`.
*   **Response Format:** JSON
    *   **Example Response (Success):**
        ```json
        {
          "status": "success",
          "message": "Rebalancing initiated successfully.",
          "rebalancing_details": {
            "asset_changes": [
              {"asset_id": "RWA-BTC-1", "change": -1.0},
              {"asset_id": "RWA-ETH-2", "change": 1.5}
            ]
          }
        }
        ```
    *   **Example Response (Failure):**
        ```json
        {
          "status": "error",
          "message": "Failed to initiate rebalancing. Invalid risk tolerance."
        }
        ```
*   **Example Request:**
    `POST /api/rwa/rebalance`
    *   **Headers:**
        `X-API-Key: YOUR_API_KEY`
        `Content-Type: application/json`
    *   **Body:**
        ```json
        {
          "risk_tolerance": "medium"
        }
        ```

### 4.4. POST /api/gpt5/analyze

*   **Method:** POST
*   **Path:** `/api/gpt5/analyze`
*   **Description:** Sends RWA data to GPT-5 for analysis.  This endpoint is used for generating portfolio insights and recommendations.
*   **Request Parameters/Body:**
    *   `asset_data`: (JSON)  A JSON object containing the RWA asset data to be analyzed. This will include asset IDs, quantities, and current prices.
*   **Response Format:** JSON
    *   **Example Response (Success):**
        ```json
        {
          "status": "success",
          "analysis_result": "Based on current market conditions and your risk tolerance, we recommend increasing your exposure to Bitcoin and Ethereum."
        }
        ```
    *   **Example Response (Failure):**
        ```json
        {
          "status": "error",
          "message": "GPT-5 analysis failed.  Check API logs for details."
        }
        ```
*   **Example Request:**
    `POST /api/gpt5/analyze`
    *   **Headers:**
        `X-API-Key: YOUR_API_KEY`
        `Content-Type: application/json`
    *   **Body:**
        ```json
        {
          "asset_data": [
            {
              "asset_id": "RWA-BTC-1",
              "asset_name": "Bitcoin (Wrapped)",
              "quantity": 10.5
            },
            {
              "asset_id": "RWA-ETH-2",
              "asset_name": "Ethereum (Wrapped)",
              "quantity": 5.2
            }
          ]
        }
        ```

## 5. Error Codes and Handling

| Code    | Description                      | Possible Cause                               |
| :------ | :------------------------------- | :------------------------------------------ |
| 400      | Bad Request                      | Invalid request parameters, missing data     |
| 401      | Unauthorized                     | Invalid API key or missing authentication  |
| 403      | Forbidden                        | Insufficient permissions                      |
| 404      | Not Found                        | Endpoint or resource not found                |
| 500      | Internal Server Error            | Server-side error                              |
| 503      | Service Unavailable              | Service unavailable due to maintenance or overload |

## 6. Rate Limiting Info

This API is subject to rate limiting to prevent abuse and ensure stability.

*   **Requests per Minute:** 60 requests
*   **Burst Limit:** 120 requests (allows for a short burst exceeding the normal rate)
*   **Reset Time:** 60 seconds

Exceeding the rate limits will result in a `429 Too Many Requests` error.  Please implement appropriate retry logic with exponential backoff.  Detailed rate limiting information can be found in the API documentation portal.
```
