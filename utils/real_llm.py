"""LLM thật qua OpenAI Responses API.

Module này giữ cùng contract với ``utils.mock_llm.ask_llm`` để luồng hiện tại
vẫn dùng được Redis, rate limit, cost guard và structured logging. API key chỉ
được đọc từ biến môi trường, không ghi vào source code.
"""

from __future__ import annotations

import os
from functools import lru_cache


def _usage_value(usage, name: str) -> int:
    """Đọc usage từ object của SDK hoặc dict trong response."""
    if usage is None:
        return 0
    value = usage.get(name) if isinstance(usage, dict) else getattr(usage, name, 0)
    return int(value or 0)


def _price_per_1k(name: str) -> float:
    """Đọc giá cấu hình theo 1.000 token; mặc định 0 nếu chưa cấu hình."""
    return float(os.getenv(name, "0"))


@lru_cache(maxsize=1)
def _get_client():
    """Tạo OpenAI client khi request đầu tiên thực sự cần gọi LLM."""
    from openai import OpenAI

    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        raise RuntimeError("OPENAI_API_KEY chưa được cấu hình")
    return OpenAI(api_key=api_key)


def ask_llm(question: str, history: list[dict] | None = None) -> dict:
    """Gọi LLM thật và trả về cùng format với mock LLM hiện tại."""
    messages = [
        {
            "role": "system",
            "content": (
                "Bạn là trợ lý kỹ thuật của Day12 Agent. "
                "Trả lời rõ ràng, hữu ích và ưu tiên tiếng Việt."
            ),
        }
    ]

    for turn in history or []:
        role = turn.get("role")
        if role in {"user", "assistant"}:
            messages.append(
                {"role": role, "content": str(turn.get("content", ""))}
            )
    messages.append({"role": "user", "content": question})

    max_output_tokens = int(os.getenv("OPENAI_MAX_OUTPUT_TOKENS", "512"))
    response = _get_client().responses.create(
        model=os.getenv("OPENAI_MODEL", "gpt-5"),
        input=messages,
        max_output_tokens=max_output_tokens,
    )

    answer = (response.output_text or "").strip()
    if not answer:
        raise RuntimeError("LLM trả về câu trả lời rỗng")

    usage = getattr(response, "usage", None)
    tokens_in = _usage_value(usage, "input_tokens")
    tokens_out = _usage_value(usage, "output_tokens")
    cost_usd = round(
        tokens_in / 1000 * _price_per_1k("OPENAI_INPUT_PRICE_PER_1K")
        + tokens_out / 1000 * _price_per_1k("OPENAI_OUTPUT_PRICE_PER_1K"),
        8,
    )

    return {
        "answer": answer,
        "tokens_in": tokens_in,
        "tokens_out": tokens_out,
        "cost_usd": cost_usd,
    }
