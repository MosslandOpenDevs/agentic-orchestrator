```markdown
# RWA Portfolio Management API Documentation

## 1. Overview

This API provides endpoints for managing and simulating a portfolio of RWA (Real World Asset) assets. It leverages a GPT-5 agent to provide portfolio rebalancing recommendations and allows for retrieving portfolio simulation results. This documentation outlines the available endpoints, authentication requirements, and expected response formats.

## 2. Authentication Details

All API requests require an API key passed in the `Authorization` header.

*   **Header:** `Authorization: Bearer <YOUR_API_KEY>`
*   Replace `<YOUR_API_KEY>` with your actual API key.  API keys are generated upon registration and should be treated as confidential.

## 3. Base URL Configuration

The base URL for all API requests is:

`https://api.example.com/v1`  (Replace with the actual base URL)

## 4. API Endpoints

### 4.1. GET /api/rwa/price

*   **Method:** `GET`
*   **Path:** `/api/rwa/price`
*   **Description:** Retrieves the current price of a specified RWA asset.
*   **Request Parameters:**
    *   `asset_id` (required, string): The unique identifier of the RWA asset.
*   **Response Format:** JSON
    *   `{ "asset_id": "string", "price": "number", "currency": "string" }`
*   **Example Request:**
    ```
    GET /api/rwa/price?asset_id=RWA-123
    ```
*   **Example Response:**
    ```json
    {
      "asset_id": "RWA-123",
      "price": 123.45,
      "currency": "USD"
    }
    ```

### 4.2. POST /api/portfolio/rebalance

*   **Method:** `POST`
*   **Path:** `/api/portfolio/rebalance`
*   **Description:** Initiates the rebalancing of the portfolio based on the GPT-5 agent's recommendations.
*   **Request Body:** JSON
    *   `portfolio_id` (required, string): The unique identifier of the portfolio to rebalance.
    *   `rebalance_strategy` (optional, string):  Allows overriding the GPT-5 strategy. Defaults to "GPT-5".
*   **Response Format:** JSON
    *   `{ "status": "success", "message": "Portfolio rebalanced successfully", "new_portfolio_allocation": "object" }`  (Where `new_portfolio_allocation` is a JSON object representing the new asset allocation percentages).
*   **Example Request:**
    ```
    POST /api/portfolio/rebalance
    Content-Type: application/json

    {
      "portfolio_id": "PORT-456",
      "rebalance_strategy": "GPT-5"
    }
    ```
*   **Example Response:**
    ```json
    {
      "status": "success",
      "message": "Portfolio rebalanced successfully",
      "new_portfolio_allocation": {
        "RWA-123": 0.3,
        "RWA-789": 0.2,
        "RWA-012": 0.5
      }
    }
    ```

### 4.3. GET /api/simulation/results

*   **Method:** `GET`
*   **Path:** `/api/simulation/results`
*   **Description:** Retrieves portfolio simulation results.
*   **Request Parameters:**
    *   `simulation_id` (required, string): The unique identifier of the simulation.
*   **Response Format:** JSON
    *   `{ "simulation_id": "string", "start_date": "string", "end_date": "string", "total_return": "number", "peak_value": "number", "drawdown": "number", "results": "array of objects" }`
        *   `results` is an array of objects, each representing a point in time with: `timestamp`, `portfolio_value`, `asset_allocations`.
*   **Example Request:**
    ```
    GET /api/simulation/results?simulation_id=SIM-987
    ```
*   **Example Response:**
    ```json
    {
      "simulation_id": "SIM-987",
      "start_date": "2023-01-01",
      "end_date": "2023-12-31",
      "total_return": 1.5,
      "peak_value": 100000,
      "drawdown": -10,
      "results": [
        { "timestamp": "2023-01-01", "portfolio_value": 95000, "asset_allocations": { "RWA-123": 0.2, "RWA-789": 0.3 } },
        { "timestamp": "2023-06-30", "portfolio_value": 110000, "asset_allocations": { "RWA-123": 0.3, "RWA-789": 0.2 } }
      ]
    }
    ```

## 5. Error Codes and Handling

| Code    | Description                               | Action                               |
| :------ | :--------------------------------------- | :---------------------------------- |
| 400      | Bad Request - Invalid Input              | Check request parameters/body for errors. |
| 401      | Unauthorized - Invalid API Key           | Ensure the API key is correct.       |
| 404      | Not Found - Resource Not Found            | Check the asset ID or simulation ID. |
| 500      | Internal Server Error                    | Contact API support.                |
| 503      | Service Unavailable - API Unavailable   | Retry the request later.            |

## 6. Rate Limiting Info

The API is subject to rate limiting to prevent abuse and ensure stability.

*   **Requests per Minute:** 60 requests per minute per API key.
*   **Exceeded Limit:**  If the rate limit is exceeded, the API will return a `429 Too Many Requests` error.  The response header will include a `Retry-After` value indicating the number of seconds to wait before retrying.
```
