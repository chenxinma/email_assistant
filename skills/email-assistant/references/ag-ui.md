# ag_ui Protocol Reference

## Overview

ag_ui (Agent-User Interaction UI) is a unified interface protocol designed for AI agent-user interaction. It provides standardized message format and interaction patterns.

## Protocol Specification

### Supported Features

- **Multi-modal responses**: Text, structured data, tool calls
- **Streaming interaction**: Server-Sent Events for real-time responses
- **Tool integration**: Built-in support for multiple tools including async
- **Session management**: Context-aware continuous dialogue

### Message Format

**Request:**
```json
{
  "query": "查询内容",
  "thread_id": "optional-thread-id",
  "messages": [],
  "model_extra": {},
  "tool_call_id": null
}
```

**SSE Response Events:**
```
data: {"type": "tool_call", "name": "search_emails", "args": {...}}
data: {"type": "tool_result", "result": {...}}
data: {"type": "final_answer", "content": "..."}
data: {"type": "error", "message": "..."}
```

### Integration with Email Assistant

ag_ui is used for:
- Natural language email query processing
- Email search and summarization
- Vector database interaction
- AI-assisted decision flow control

When client makes request to `/` endpoint, system internally uses ag_ui protocol to:
1. Parse query
2. Schedule intelligent tools
3. Stream results back to frontend

## Implementation Details

### Server-Sent Events Format

```
event: message
data: {"type": "...", "payload": {...}}
```

### Content Types

| Accept Header | Response Format |
|---------------|-----------------|
| `text/plain` | Plain text stream |
| `application/json` | JSON response |
| `text/event-stream` | SSE events (default) |
