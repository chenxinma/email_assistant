---
name: email-assistant
description: Use when interacting with email assistant API for: (1) natural language email queries and summaries, (2) syncing latest emails to local database, (3) handling SSE streaming responses via ag_ui protocol
---

# Email Assistant API Skill

## Overview

This skill provides guidance for interacting with the Email Assistant API - an intelligent email management system built with FastAPI. The API supports natural language email queries, summary generation, and email synchronization.

**Base URL**: `http://127.0.0.1:9000`

**Authentication**: Via configuration file credentials

**Protocol**: ag_ui (Agent-User Interaction UI) with Server-Sent Events streaming

## Quick Reference

| Endpoint | Method | Purpose |
|----------|--------|---------|
| `/` | POST | Natural language email queries via ag_ui |
| `/api/emails/refresh` | POST | Sync latest emails to local database |
| `/docs` | GET | Interactive API documentation |

## Core Workflows

### 1. Email Query and Summary

Use the ag_ui protocol endpoint for intelligent email queries:

```bash
curl -X POST "http://127.0.0.1:9000/" \
  -H "Accept: text/plain" \
  -H "Content-Type: application/json" \
  -d '{"threadId": "test-123", "runId": "run-123", "state": {}, "messages": [{"role": "user", "id": "msg-1", "content": "请总结我今天收到的邮件"}], "tools": [], "context": [], "forwardedProps": {}}'
```

**Request body:**
```json
{
  "threadId": "线程 ID（必需）",
  "runId": "运行 ID（必需）",
  "state": {},
  "messages": [
    {
      "role": "user",
      "id": "消息 ID（必需）",
      "content": "查询内容"
    }
  ],
  "tools": [],
  "context": [],
  "forwardedProps": {}
}
```

**Response types (SSE streaming):**
- Tool calls - email query operations during execution
- Tool results - data returned from operations
- Final answer - AI-generated response
- Error messages - if problems occur

**Accept header options:**
- `text/plain` - Plain text streaming (default)
- `application/json` - JSON format response
- `text/event-stream` - SSE streaming events

### 2. Email Synchronization

Sync recent emails to the local database:

```bash
curl -X POST "http://127.0.0.1:9000/api/emails/refresh?days=7" \
  -H "Content-Type: application/json"
```

**Query parameters:**
- `days` (optional): Number of days to sync (default: 2)

**SSE message types:**
- `"文件夹处理中 INBOX"` - Processing folder
- `"邮件处理中"` - Processing email
- `"邮件处理失败"` - Failed email
- `"邮件属性保存中"` - Saving email properties
- `"邮件刷新成功"` - Sync complete
- `"[DONE]"` - Processing finished

## Implementation

### Python Client Example

```python
import requests
import uuid
import json

BASE_URL = "http://127.0.0.1:9000"

def query_emails(query: str, accept_type: str = "text/plain"):
    """Query emails using natural language."""
    response = requests.post(
        f"{BASE_URL}/",
        headers={
            "Accept": accept_type,
            "Content-Type": "application/json"
        },
        json={
            "threadId": str(uuid.uuid4()),
            "runId": str(uuid.uuid4()),
            "state": {},
            "messages": [
                {"role": "user", "id": str(uuid.uuid4()), "content": query}
            ],
            "tools": [],
            "context": [],
            "forwardedProps": {}
        }
    )
    return response.text

def refresh_emails(days: int = 2):
    """Sync latest emails to local database."""
    response = requests.post(
        f"{BASE_URL}/api/emails/refresh",
        params={"days": days},
        headers={"Content-Type": "application/json"},
        stream=True
    )
    for line in response.iter_lines():
        if line:
            print(line.decode())
```

### ag_ui Protocol Handling

For streaming responses, use SSE-compatible client:

```python
import httpx
import uuid
import asyncio

async def stream_query(query: str):
    async with httpx.AsyncClient() as client:
        async with client.stream(
            "POST",
            "http://127.0.0.1:9000/",
            json={
                "threadId": str(uuid.uuid4()),
                "runId": str(uuid.uuid4()),
                "state": {},
                "messages": [
                    {"role": "user", "id": str(uuid.uuid4()), "content": query}
                ],
                "tools": [],
                "context": [],
                "forwardedProps": {}
            },
            headers={"Accept": "text/event-stream"}
        ) as response:
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    yield line[6:]  # Remove "data: " prefix
```

## Error Handling

| Status Code | Meaning |
|-------------|---------|
| 422 | Invalid request input (JSON validation failed) |
| 500 | Server error (e.g., email search failed) |

**CORS allowed origins:**
- `http://localhost`
- `http://localhost:3000`

## Common Mistakes

1. **Not handling SSE format**: The API returns streaming responses. Use appropriate SSE client or handle line-by-line streaming.

2. **Wrong Accept header**: Specify the correct Accept header for your desired response format. Default is `text/plain`.

3. **Missing Content-Type**: Always include `Content-Type: application/json` for POST requests.

4. **Incomplete request body**: The ag_ui protocol requires all fields: `threadId`, `runId`, `state`, `messages`, `tools`, `context`, `forwardedProps`. Each message must have `id`, `role`, and `content`.

5. **Missing message id**: Each message in the `messages` array must have a unique `id` field.

## Related Documentation

- Full API reference: See [docs/api.md](../../docs/api.md) for complete endpoint details
- ag_ui protocol: See [references/ag-ui.md](references/ag-ui.md) for protocol specification
