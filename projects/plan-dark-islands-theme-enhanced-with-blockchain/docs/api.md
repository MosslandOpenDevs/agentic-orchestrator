# API Documentation

## Overview

This document provides comprehensive details about the endpoints available for interacting with our user settings and blockchain interaction logging services.

## Authentication

All requests to this API require an authentication token, which should be included in the `Authorization` header of each request as a Bearer Token. Example: `Authorization: Bearer YOUR_ACCESS_TOKEN`.

## Base URL Configuration

The base URL for all endpoints is:
```
https://api.example.com
```

---

### GET /api/user-settings/{userId}

#### Description
Retrieve user settings for a specific user.

#### Request Parameters
- **Path Parameter**
  - `{userId}`: The unique identifier of the user whose settings are to be retrieved. (Required)

#### Response Format
```json
{
    "id": "user123",
    "theme": "dark",
    "notificationsEnabled": true,
    "timezone": "UTC"
}
```

#### Example Request/Response
**Request:**
```http
GET /api/user-settings/user123 HTTP/1.1
Host: api.example.com
Authorization: Bearer YOUR_ACCESS_TOKEN
```

**Response:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
    "id": "user123",
    "theme": "dark",
    "notificationsEnabled": true,
    "timezone": "UTC"
}
```

---

### POST /api/blockchain-interaction

#### Description
Log a new blockchain interaction performed by the user.

#### Request Body
```json
{
    "userId": "user123",
    "interactionType": "transfer",
    "details": {
        "fromAddress": "0xabc...",
        "toAddress": "0xdef...",
        "amount": 5.7,
        "currency": "ETH"
    }
}
```

#### Response Format
```json
{
    "status": "success",
    "message": "Interaction logged successfully."
}
```

#### Example Request/Response
**Request:**
```http
POST /api/blockchain-interaction HTTP/1.1
Host: api.example.com
Authorization: Bearer YOUR_ACCESS_TOKEN
Content-Type: application/json

{
    "userId": "user123",
    "interactionType": "transfer",
    "details": {
        "fromAddress": "0xabc...",
        "toAddress": "0xdef...",
        "amount": 5.7,
        "currency": "ETH"
    }
}
```

**Response:**
```json
HTTP/1.1 200 OK
Content-Type: application/json

{
    "status": "success",
    "message": "Interaction logged successfully."
}
```

---

## Error Codes and Handling

- **400 Bad Request**: The request was malformed or missing required parameters.
- **401 Unauthorized**: Authentication failed. Please check your access token.
- **500 Internal Server Error**: An unexpected error occurred on the server.

## Rate Limiting Information

Each endpoint is rate-limited to 60 requests per minute (RPM) for each authenticated user. If you exceed this limit, your subsequent API calls will be blocked until the next minute.