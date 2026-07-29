from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any

from providers.base import Provider, ToolCall
from tools import TOOL_FUNCTIONS


@dataclass
class AgentRun:
    text: str | None
    tool_calls: list[ToolCall] = field(default_factory=list)
    tool_results: list[dict[str, Any]] = field(default_factory=list)


def _json_text(value: Any, *, max_chars: int = 6000) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    if len(text) <= max_chars:
        return text
    return text[:max_chars] + "\n...<truncated>"


def _format_timeline_result(result: dict[str, Any]) -> str | None:
    items = result.get("items")
    screenname = result.get("screenname")
    if not isinstance(items, list) or not items:
        return None

    lines = [f"Recent posts from @{screenname or 'the account'}:"]
    for item in items[:5]:
        if not isinstance(item, dict):
            continue
        title = item.get("title") or item.get("summary") or "(no text)"
        date = item.get("date") or "unknown date"
        url = item.get("url") or ""
        suffix = f" - {url}" if url else ""
        lines.append(f"- {title} ({date}){suffix}")
    return "\n".join(lines)


def _fallback_tool_answer(results: list[dict[str, Any]], response_text: str | None) -> str:
    rendered: list[str] = []
    for event in results:
        result = event.get("result", event.get("error", {}))
        if isinstance(result, dict) and result.get("error"):
            rendered.append(f"{event.get('tool', 'tool')} failed: {result.get('message', result.get('error'))}")
            continue
        if isinstance(result, dict):
            timeline_text = _format_timeline_result(result)
            if timeline_text:
                rendered.append(timeline_text)
                continue
        rendered.append(_json_text(result, max_chars=1200))

    if rendered:
        return "\n\n".join(rendered)
    return response_text or "(no text)"


class ResearchAgent:
    def __init__(
        self,
        provider: Provider,
        *,
        system_prompt: str,
        tools: list[dict[str, Any]] | None = None,
        model: str | None = None,
    ) -> None:
        self.provider = provider
        self.system_prompt = system_prompt
        self.tools = tools or []
        self.model = model

    def run(self, user_messages: list[dict[str, str]], *, tool_choice: Any | None = None) -> AgentRun:
        messages = [{"role": "system", "content": self.system_prompt}, *user_messages]
        response = self.provider.complete(
            messages,
            self.tools,
            model=self.model,
            temperature=0.0,
            tool_choice=tool_choice,
        )
        results: list[dict[str, Any]] = []
        for call in response.tool_calls:
            func = TOOL_FUNCTIONS.get(call.name)
            if not func:
                results.append({"tool": call.name, "error": "unknown_tool"})
                continue
            try:
                result = func(**call.args)
            except Exception as exc:  # keep eval robust; failures are evidence
                result = {"error": type(exc).__name__, "message": str(exc)}
            results.append({"tool": call.name, "args": call.args, "result": result})

        # Best-effort synthesis: answer from tool results without exposing raw JSON.
        final_text = response.text
        if response.tool_calls and results:
            synthesis_messages = [
                *messages,
                {
                    "role": "assistant",
                    "content": response.text or "I used the selected tool(s).",
                },
                {
                    "role": "user",
                    "content": (
                        "TOOL_RESULTS_JSON:\n"
                        f"{_json_text(results)}\n\n"
                        "Answer the user's latest request directly using only these tool results. "
                        "Do not show raw JSON. Keep the same language as the user's latest message. "
                        "If useful, include dates and links."
                    ),
                },
            ]
            try:
                synthesis = self.provider.complete(
                    synthesis_messages,
                    tools=None,
                    model=self.model,
                    temperature=0.2,
                )
                final_text = synthesis.text or _fallback_tool_answer(results, response.text)
            except Exception:
                final_text = _fallback_tool_answer(results, response.text)

        return AgentRun(text=final_text, tool_calls=response.tool_calls, tool_results=results)
