"""9Router/OpenAI-compatible AI integration."""

from __future__ import annotations

import json
from typing import Any

import requests

from ..config import Settings


def create_insight(settings: Settings, payload: dict[str, Any]) -> dict:
    if not settings.has_ai_config:
        return {"success": False, "error": "AI is not configured", "status_code": 503}

    question = payload.get("question") or "Hãy phân tích ngắn gọn dữ liệu cà phê này."
    data = payload.get("data", {})

    try:
        response = requests.post(
            f"{settings.ai_base_url}/chat/completions",
            headers={
                "Authorization": f"Bearer {settings.ai_api_key}",
                "Content-Type": "application/json",
            },
            json={
                "model": settings.ai_model,
                "messages": [
                    {
                        "role": "system",
                        "content": (
                            "Bạn là chuyên gia phân tích dữ liệu cà phê Việt Nam. "
                            "Trả lời tiếng Việt, ngắn gọn, có số liệu khi dữ liệu đầu vào cung cấp."
                        ),
                    },
                    {"role": "user", "content": f"Câu hỏi: {question}\n\nDữ liệu: {data}"},
                ],
                "temperature": 0.25,
                "max_tokens": 500,
                "stream": False,
            },
            timeout=60,
        )
        response.raise_for_status()
        response.encoding = "utf-8"
        content = _extract_content(response)
    except requests.RequestException as exc:
        return {"success": False, "error": f"AI request failed: {exc}", "status_code": 502}
    except (ValueError, KeyError, IndexError) as exc:
        preview = response.text[:200] if "response" in locals() else ""
        return {
            "success": False,
            "error": f"AI returned an unexpected response: {exc}",
            "response_preview": preview,
            "status_code": 502,
        }

    return {"success": True, "model": settings.ai_model, "insight": content}


def _extract_content(response: requests.Response) -> str:
    content_type = response.headers.get("content-type", "")

    if "text/event-stream" not in content_type:
        body = response.json()
        return body["choices"][0]["message"]["content"]

    chunks: list[str] = []
    for raw_line in response.text.splitlines():
        line = raw_line.strip()
        if not line.startswith("data:"):
            continue
        payload = line.removeprefix("data:").strip()
        if payload == "[DONE]":
            continue
        try:
            event = json.loads(payload)
        except json.JSONDecodeError:
            continue
        for choice in event.get("choices", []):
            delta = choice.get("delta") or {}
            if "content" in delta:
                chunks.append(delta["content"])
            message = choice.get("message") or {}
            if "content" in message:
                chunks.append(message["content"])

    if not chunks:
        raise ValueError("No assistant content found in event stream")
    return "".join(chunks)
