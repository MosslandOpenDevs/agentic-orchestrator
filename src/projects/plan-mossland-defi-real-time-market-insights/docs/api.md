# API Documentation Overview

This document provides comprehensive information about the available endpoints for sentiment analysis and security alerts submission.

## Authentication Details

All requests to this API require an `API-Key` header with a valid token obtained from our authentication system.

## Base URL Configuration

The base URL for all API calls is `https://api.example.com`.

---

## GET /api/sentiment-analysis

### Description

Fetches sentiment analysis results for a user based on their recent activities or posts.

### Request Parameters

- **User-ID**: Required. The unique identifier of the user whose data you want to analyze.
  - Type: String
  - Example: `123456`

### Response Format

```json
{
    "user_id": "string",
    "sentiment_score": float,
    "analysis_date": "YYYY-MM-DD"
}
```

### Example Request

```http
GET /api/sentiment-analysis?User-ID=123456 HTTP/1.1
Host: api.example.com
API-Key: your_api_key_here
```

### Example Response

```json
{
    "user_id": "123456",
    "sentiment_score": 0.8,
    "analysis_date": "2023-09-27"
}
```

---

## POST /api/security-alerts

### Description

Submits a new security alert to the system.

### Request Body

```json
{
    "alert_type": "string",
    "description": "string",
    "severity_level": int,
    "reported_by_user_id": "string"
}
```

- **alert_type**: Required. Type of security alert.
  - Example: `"phishing"`
- **description**: Required. Description of the alert.
  - Example: `"Suspicious login attempt from an unknown device."`
- **severity_level**: Required. The severity level of the alert (1 to 5).
  - Example: `3`
- **reported_by_user_id**: Optional. ID of the user reporting the alert.
  - Example: `"789012"`

### Response Format

```json
{
    "alert_id": "string",
    "status": "string"
}
```

### Example Request

```http
POST /api/security-alerts HTTP/1.1
Host: api.example.com
Content-Type: application/json
API-Key: your_api_key_here

{
    "alert_type": "phishing",
    "description": "Suspicious login attempt from an unknown device.",
    "severity_level": 3,
    "reported_by_user_id": "789012"
}
```

### Example Response

```json
{
    "alert_id": "ALRT-001",
    "status": "received"
}
```

---

## Error Codes and Handling

| Code | Description               |
|------|---------------------------|
| 401  | Unauthorized              |
| 403  | Forbidden                 |
| 404  | Not Found                 |
| 500  | Internal Server Error     |

### Rate Limiting Information

- **GET /api/sentiment-analysis**: Up to 60 requests per minute.
- **POST /api/security-alerts**: Up to 30 requests per minute.