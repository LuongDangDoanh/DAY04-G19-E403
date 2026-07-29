from __future__ import annotations

import argparse
import json
import os
from datetime import datetime
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Any
from urllib.parse import urlparse

import requests

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from tools._shared import TIMEOUT
from versioning import build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS_DIR = ROOT / "artifacts"
TRANSCRIPTS_DIR = ROOT / "transcripts"


def json_response(handler: SimpleHTTPRequestHandler, status: int, payload: dict[str, Any]) -> None:
    body = json.dumps(payload, ensure_ascii=False, default=str).encode("utf-8")
    handler.send_response(status)
    handler.send_header("Content-Type", "application/json; charset=utf-8")
    handler.send_header("Content-Length", str(len(body)))
    handler.end_headers()
    handler.wfile.write(body)


def telegram_send_message(token: str, chat_id: int | str, text: str) -> dict[str, Any]:
    response = requests.post(
        f"https://api.telegram.org/bot{token}/sendMessage",
        json={
            "chat_id": chat_id,
            "text": text[:3900],
            "disable_web_page_preview": True,
        },
        timeout=TIMEOUT,
    )
    response.raise_for_status()
    return response.json()


class ResearchUiHandler(SimpleHTTPRequestHandler):
    server: "ResearchUiServer"

    def __init__(self, *args: Any, **kwargs: Any) -> None:
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self) -> None:
        path = urlparse(self.path).path
        if path == "/":
            self.send_response(302)
            self.send_header("Location", "/ui/index.html")
            self.end_headers()
            return
        super().do_GET()

    def do_POST(self) -> None:
        path = urlparse(self.path).path
        if path == "/api/chat":
            self.handle_api_chat()
            return
        if path == "/telegram/webhook":
            self.handle_telegram_webhook()
            return
        json_response(self, 404, {"error": "not_found"})

    def handle_api_chat(self) -> None:
        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            payload = json.loads(raw.decode("utf-8") or "{}")
            user_text = str(payload.get("message") or "").strip()
            history = payload.get("history") or []
            if not user_text:
                json_response(self, 400, {"error": "missing_message"})
                return
            if not isinstance(history, list):
                history = []

            clean_history = self.clean_history(history)
            result = self.server.run_agent(user_text, clean_history)
            transcript_record = self.server.append_transcript(
                source="ui",
                user_text=user_text,
                history=clean_history,
                result=result,
            )
            json_response(self, 200, {
                "answer": result.get("assistant_text", ""),
                "status": result.get("status"),
                "rounds": result.get("rounds", []),
                "tool_events": result.get("tool_events", []),
                "request_text": user_text,
                "response_text": result.get("assistant_text", ""),
                "transcript_id": self.server.transcript_id,
                "transcript_path": str(self.server.transcript_path),
                "transcript": transcript_record,
                "artifact_version": self.server.artifact_version_map["artifact_version"],
            })
        except Exception as exc:
            json_response(self, 500, {
                "error": type(exc).__name__,
                "message": str(exc),
            })

    def handle_telegram_webhook(self) -> None:
        expected_secret = self.server.telegram_webhook_secret
        if expected_secret:
            actual_secret = self.headers.get("X-Telegram-Bot-Api-Secret-Token", "")
            if actual_secret != expected_secret:
                json_response(self, 401, {"ok": False, "error": "invalid_secret"})
                return

        try:
            content_length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(content_length)
            update = json.loads(raw.decode("utf-8") or "{}")
            message = update.get("message") or update.get("edited_message") or {}
            chat = message.get("chat") or {}
            chat_id = chat.get("id")
            text = str(message.get("text") or "").strip()
            if not chat_id or not text:
                json_response(self, 200, {"ok": True, "ignored": True})
                return

            result = self.server.run_agent(text, self.server.telegram_histories.get(str(chat_id), []))
            self.server.append_transcript(
                source="telegram",
                user_text=text,
                history=self.server.telegram_histories.get(str(chat_id), []),
                result=result,
                chat_id=str(chat_id),
            )
            answer = result.get("assistant_text") or "Agent không trả về nội dung."
            self.server.telegram_histories.setdefault(str(chat_id), [])
            self.server.telegram_histories[str(chat_id)].extend([
                {"role": "user", "content": text},
                {"role": "assistant", "content": answer},
            ])
            self.server.telegram_histories[str(chat_id)] = trim_history(
                self.server.telegram_histories[str(chat_id)],
                self.server.history_window,
            )

            if not self.server.telegram_bot_token:
                json_response(self, 500, {"ok": False, "error": "missing_telegram_token"})
                return
            telegram_send_message(self.server.telegram_bot_token, chat_id, answer)
            json_response(self, 200, {"ok": True, "status": result.get("status")})
        except Exception as exc:
            json_response(self, 500, {
                "ok": False,
                "error": type(exc).__name__,
                "message": str(exc),
            })

    @staticmethod
    def clean_history(history: list[Any]) -> list[dict[str, str]]:
        clean_history: list[dict[str, str]] = []
        for item in history:
            if not isinstance(item, dict):
                continue
            role = item.get("role")
            content = item.get("content")
            if role in {"user", "assistant"} and isinstance(content, str):
                clean_history.append({"role": role, "content": content})
        return clean_history

    def do_DELETE(self) -> None:
        path = urlparse(self.path).path
        if path != "/telegram/webhook":
            json_response(self, 404, {"error": "not_found"})
            return
        try:
            self.server.telegram_histories.clear()
            json_response(self, 200, {"ok": True, "message": "telegram history cleared"})
        except Exception as exc:
            json_response(self, 500, {
                "error": type(exc).__name__,
                "message": str(exc),
            })


class ResearchUiServer(ThreadingHTTPServer):
    def __init__(
        self,
        server_address: tuple[str, int],
        *,
        provider_name: str,
        model: str | None,
        history_window: int,
        max_tool_rounds: int,
    ) -> None:
        load_lab_env(ROOT)
        self.provider = make_provider(provider_name)
        self.model = model
        self.history_window = history_window
        self.max_tool_rounds = max_tool_rounds
        self.system_prompt = (ARTIFACTS_DIR / "system_prompt.md").read_text(encoding="utf-8")
        self.artifact_version_info = build_artifact_version("v5", ARTIFACTS_DIR / "system_prompt.md", ARTIFACTS_DIR / "tools.yaml")
        self.artifact_version_map = {
            "version": self.artifact_version_info.version,
            "artifact_version": self.artifact_version_info.artifact_version,
            "prompt_hash": self.artifact_version_info.prompt_hash,
            "tools_hash": self.artifact_version_info.tools_hash,
        }
        declarations = load_tool_declarations(ARTIFACTS_DIR / "tools.yaml")
        self.openai_tools = to_openai_tools(declarations)
        self.telegram_bot_token = os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.telegram_webhook_secret = os.getenv("TELEGRAM_WEBHOOK_SECRET", "")
        self.telegram_histories: dict[str, list[dict[str, str]]] = {}
        self.transcripts_dir = TRANSCRIPTS_DIR
        self.transcripts_dir.mkdir(parents=True, exist_ok=True)
        self.transcript_id = "_".join([
            safe_slug("ui"),
            safe_slug(provider_name),
            datetime.now().strftime("%Y%m%dT%H%M%S%f"),
        ])
        self.transcript_path = self.transcripts_dir / f"{self.transcript_id}.transcript.json"
        self.artifact_version = None
        self.transcript: dict[str, Any] = {
            "transcript_id": self.transcript_id,
            "source": "ui",
            "provider": provider_name,
            "model": model,
            **self.artifact_version_map,
            "created_at": now_iso(),
            "updated_at": now_iso(),
            "turns": [],
        }
        super().__init__(server_address, ResearchUiHandler)

    def run_agent(self, user_text: str, history: list[dict[str, str]] | None = None) -> dict[str, Any]:
        messages = [
            {"role": "system", "content": self.system_prompt},
            *trim_history(history or [], self.history_window),
            {"role": "user", "content": user_text},
        ]
        return run_model_tool_loop(
            provider=self.provider,
            messages=messages,
            tools=self.openai_tools,
            model=self.model,
            max_tool_rounds=self.max_tool_rounds,
        )

    def append_transcript(
        self,
        *,
        source: str,
        user_text: str,
        history: list[dict[str, str]] | None,
        result: dict[str, Any],
        chat_id: str | None = None,
    ) -> dict[str, Any]:
        turn = {
            "turn_index": len(self.transcript["turns"]) + 1,
            "source": source,
            "chat_id": chat_id,
            "started_at": now_iso(),
            "user": user_text,
            "history": trim_history(history or [], self.history_window),
            "status": result.get("status"),
            "assistant_text": result.get("assistant_text"),
            "rounds": result.get("rounds", []),
            "tool_events": result.get("tool_events", []),
            "ended_at": now_iso(),
        }
        self.transcript["turns"].append(turn)
        self.transcript["updated_at"] = now_iso()
        self.transcript["last_turn"] = turn
        self.transcript_path.write_text(json.dumps(self.transcript, ensure_ascii=False, indent=2, default=str), encoding="utf-8")
        return turn


def main() -> None:
    load_lab_env(ROOT)
    parser = argparse.ArgumentParser(description="Serve Research Agent UI and chat API.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=5173)
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "gemini"], default=os.getenv("AGENT_PROVIDER", "openrouter"))
    parser.add_argument("--model", default=os.getenv("AGENT_MODEL") or None)
    parser.add_argument("--history-window", type=int, default=5)
    parser.add_argument("--max-tool-rounds", type=int, default=4)
    args = parser.parse_args()

    server = ResearchUiServer(
        (args.host, args.port),
        provider_name=args.provider,
        model=args.model,
        history_window=args.history_window,
        max_tool_rounds=args.max_tool_rounds,
    )
    print(f"Research UI running at http://{args.host}:{args.port}/ui/index.html")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()


if __name__ == "__main__":
    main()
