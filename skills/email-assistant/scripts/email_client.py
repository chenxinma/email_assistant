#!/usr/bin/env python3
"""
Email Assistant API Client

Simple client for testing and interacting with the Email Assistant API.
"""

import httpx
import asyncio
import sys


BASE_URL = "http://127.0.0.1:9000"


async def stream_query(query: str, accept_type: str = "text/event-stream"):
    """Query emails using natural language with streaming response."""
    async with httpx.AsyncClient(timeout=60.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/",
            json={
                "query": query,
                "thread_id": None,
                "messages": [],
                "model_extra": {},
                "tool_call_id": None,
            },
            headers={"Accept": accept_type},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line.startswith("data: "):
                    print(line[6:])
                elif line:
                    print(line)


async def refresh_emails(days: int = 2):
    """Sync latest emails to local database."""
    async with httpx.AsyncClient(timeout=120.0) as client:
        async with client.stream(
            "POST",
            f"{BASE_URL}/api/emails/refresh",
            params={"days": days},
            headers={"Content-Type": "application/json"},
        ) as response:
            response.raise_for_status()
            async for line in response.aiter_lines():
                if line:
                    print(line)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python email_client.py query <your query>")
        print("  python email_client.py refresh [days]")
        print("\nExamples:")
        print('  python email_client.py query "今天收到的所有邮件摘要"')
        print("  python email_client.py refresh 7")
        sys.exit(1)

    command = sys.argv[1]

    if command == "query":
        if len(sys.argv) < 3:
            print("Error: query requires a query string")
            sys.exit(1)
        query = " ".join(sys.argv[2:])
        asyncio.run(stream_query(query))

    elif command == "refresh":
        days = int(sys.argv[2]) if len(sys.argv) > 2 else 2
        asyncio.run(refresh_emails(days))

    else:
        print(f"Unknown command: {command}")
        sys.exit(1)


if __name__ == "__main__":
    main()
