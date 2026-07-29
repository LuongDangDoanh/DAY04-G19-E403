"""Streamlit UI - Research Agent | Day 04 Lab."""
from __future__ import annotations

import json
import sys
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st
import yaml

ROOT = Path(__file__).parent
TRANSCRIPTS_DIR = ROOT / "transcripts"
PROVIDERS = ["deepseek", "openrouter", "openai"]

sys.path.insert(0, str(ROOT))

from agent import ResearchAgent
from env_loader import load_lab_env
from providers import make_provider


load_lab_env(ROOT)


def apply_theme() -> None:
    st.markdown(
        """
        <style>
        :root {
            --bg: #0f1012;
            --panel: #16181c;
            --panel-2: #1c1f24;
            --line: #2a2f38;
            --line-soft: #22262d;
            --text: #f4f4f5;
            --muted: #a1a7b3;
            --subtle: #747b88;
            --accent: #7dd3a8;
            --danger: #ff7b7b;
        }

        .stApp {
            background: var(--bg);
            color: var(--text);
        }

        header[data-testid="stHeader"] {
            background: rgba(15, 16, 18, 0.86);
            border-bottom: 1px solid rgba(255, 255, 255, 0.04);
            backdrop-filter: blur(16px);
        }

        [data-testid="stSidebar"] {
            background: #131519;
            border-right: 1px solid var(--line-soft);
        }

        .block-container {
            max-width: 1060px;
            padding-top: 1.35rem;
            padding-bottom: 7rem;
        }

        .app-header {
            display: flex;
            justify-content: space-between;
            align-items: flex-start;
            gap: 18px;
            margin-bottom: 18px;
            padding-bottom: 16px;
            border-bottom: 1px solid var(--line-soft);
        }

        .app-title {
            margin: 0;
            color: var(--text);
            font-size: 1.45rem;
            font-weight: 650;
            letter-spacing: 0;
        }

        .app-subtitle {
            margin: 5px 0 0;
            color: var(--muted);
            font-size: 0.93rem;
        }

        .status-row {
            display: flex;
            flex-wrap: wrap;
            justify-content: flex-end;
            gap: 8px;
        }

        .status-pill,
        .trace-pill {
            display: inline-flex;
            align-items: center;
            gap: 7px;
            min-height: 30px;
            padding: 5px 10px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.025);
            color: var(--text);
            font-size: 0.8rem;
            white-space: nowrap;
        }

        .status-pill span,
        .trace-pill span {
            color: var(--subtle);
        }

        .empty-state {
            display: grid;
            gap: 10px;
            max-width: 680px;
            margin: 74px auto 42px;
            text-align: center;
        }

        .empty-state strong {
            color: var(--text);
            font-size: 1.16rem;
            font-weight: 650;
        }

        .empty-state p {
            margin: 0;
            color: var(--muted);
            font-size: 0.94rem;
        }

        .tool-list {
            display: grid;
            grid-template-columns: repeat(2, minmax(0, 1fr));
            gap: 7px;
            margin-top: 8px;
        }

        .tool-chip {
            overflow: hidden;
            text-overflow: ellipsis;
            white-space: nowrap;
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            padding: 6px 8px;
            background: rgba(255, 255, 255, 0.02);
            color: var(--muted);
            font-family: ui-monospace, SFMono-Regular, Menlo, Consolas, monospace;
            font-size: 0.78rem;
        }

        .trace-row {
            display: flex;
            flex-wrap: wrap;
            gap: 8px;
            margin: 12px 0 4px;
        }

        div[data-testid="stChatMessage"] {
            border: 1px solid var(--line-soft);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.018);
            padding: 0.85rem 1rem;
            margin-bottom: 0.72rem;
        }

        [data-testid="stChatMessageContent"] p,
        [data-testid="stChatMessageContent"] li {
            line-height: 1.58;
        }

        div[data-testid="stExpander"] {
            border-color: var(--line-soft);
            border-radius: 8px;
            background: rgba(255, 255, 255, 0.012);
        }

        .stButton > button,
        .stDownloadButton > button {
            min-height: 38px;
            border: 1px solid var(--line);
            border-radius: 8px;
            background: var(--panel);
            color: var(--text);
        }

        .stButton > button:hover,
        .stDownloadButton > button:hover {
            border-color: var(--accent);
            color: var(--text);
        }

        .stTextInput input,
        .stSelectbox [data-baseweb="select"] > div {
            border-color: var(--line);
            border-radius: 8px;
            background: var(--panel);
            color: var(--text);
        }

        code {
            border: 1px solid rgba(125, 211, 168, 0.18);
            border-radius: 6px;
            background: rgba(125, 211, 168, 0.08);
            color: #d8f8e5;
        }

        @media (max-width: 760px) {
            .app-header {
                display: block;
            }

            .status-row {
                justify-content: flex-start;
                margin-top: 12px;
            }

            .tool-list {
                grid-template-columns: 1fr;
            }
        }
        </style>
        """,
        unsafe_allow_html=True,
    )


def load_tools() -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    tools_src = yaml.safe_load((ROOT / "artifacts" / "tools.yaml").read_text(encoding="utf-8"))
    tools_list = tools_src if isinstance(tools_src, list) else tools_src.get("tools", [])
    openai_tools = [{"type": "function", "function": tool} for tool in tools_list]
    return tools_list, openai_tools


def init_state() -> None:
    st.session_state.setdefault("msgs", [])
    st.session_state.setdefault("last_transcript", None)


def render_header(provider_name: str, model: str | None, tool_count: int) -> None:
    st.markdown(
        f"""
        <div class="app-header">
            <div>
                <h1 class="app-title">Research Agent</h1>
                <p class="app-subtitle">Prompt engineering and tool calling lab.</p>
            </div>
            <div class="status-row">
                <div class="status-pill"><span>provider</span>{provider_name}</div>
                <div class="status-pill"><span>model</span>{model or "default"}</div>
                <div class="status-pill"><span>tools</span>{tool_count}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def render_tool_chips(tools_list: list[dict[str, Any]]) -> None:
    chips = "".join(
        f'<div class="tool-chip">{tool.get("name", "tool")}</div>'
        for tool in tools_list
    )
    st.markdown(f'<div class="tool-list">{chips}</div>', unsafe_allow_html=True)


def render_trace(tool_calls: list[Any], tool_results: list[dict[str, Any]]) -> None:
    if not tool_calls:
        return

    st.markdown(
        f"""
        <div class="trace-row">
            <div class="trace-pill"><span>tool calls</span>{len(tool_calls)}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    for index, (tool_call, tool_result) in enumerate(zip(tool_calls, tool_results), start=1):
        result = tool_result.get("result", tool_result.get("error", "unknown"))
        args = getattr(tool_call, "args", {})
        name = getattr(tool_call, "name", "tool")
        label = f"{index}. {name}({json.dumps(args, ensure_ascii=False)})"
        with st.expander(label, expanded=False):
            args_col, result_col = st.columns(2)
            with args_col:
                st.caption("Arguments")
                st.json(args)
            with result_col:
                st.caption("Result")
                st.json(result)


def render_history() -> None:
    for message in st.session_state.msgs:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])
            render_trace(message.get("tool_calls", []), message.get("tool_results", []))


def model_history() -> list[dict[str, str]]:
    return [
        {"role": message["role"], "content": message.get("content", "")}
        for message in st.session_state.msgs
        if message.get("role") in {"user", "assistant"}
    ]


def save_transcript(query: str, provider_name: str, model: str | None, run: Any) -> Path:
    TRANSCRIPTS_DIR.mkdir(exist_ok=True)
    timestamp = datetime.now()
    transcript_path = TRANSCRIPTS_DIR / f"{timestamp:%Y%m%d_%H%M%S}.json"
    transcript = {
        "timestamp": timestamp.isoformat(timespec="seconds"),
        "provider": provider_name,
        "model": model,
        "query": query,
        "text": run.text,
        "tool_calls": [
            {"name": tool_call.name, "args": tool_call.args}
            for tool_call in run.tool_calls
        ],
        "tool_results": run.tool_results,
    }
    transcript_path.write_text(
        json.dumps(transcript, ensure_ascii=False, indent=2, default=str),
        encoding="utf-8",
    )
    st.session_state.last_transcript = transcript_path.name
    return transcript_path


def render_sidebar(tools_list: list[dict[str, Any]]) -> tuple[str, Any, str | None, ResearchAgent]:
    with st.sidebar:
        st.markdown("## Agent")
        provider_name = st.selectbox("Provider", PROVIDERS, index=0)
        provider = make_provider(provider_name)
        model = getattr(provider, "default_model", None)
        st.caption(f"Model: {model}")

        clear_col, sample_col = st.columns(2)
        with clear_col:
            if st.button("Clear", use_container_width=True):
                st.session_state.msgs = []
                st.session_state.last_transcript = None
                st.rerun()
        with sample_col:
            if st.button("Sample", use_container_width=True):
                st.session_state.pending_prompt = "Find recent AI research news and cite sources."
                st.rerun()

        st.divider()
        st.markdown("## Tools")
        st.caption(f"{len(tools_list)} tools loaded")
        render_tool_chips(tools_list)

        st.divider()
        st.markdown("## Transcript")
        if st.session_state.last_transcript:
            st.caption(st.session_state.last_transcript)
        else:
            st.caption("No transcript yet.")

    system_prompt = (ROOT / "artifacts" / "system_prompt.md").read_text(encoding="utf-8")
    _, openai_tools = load_tools()
    agent = ResearchAgent(provider, system_prompt=system_prompt, tools=openai_tools, model=model)
    return provider_name, provider, model, agent


def main() -> None:
    st.set_page_config(page_title="Research Agent", page_icon="R", layout="wide")
    apply_theme()
    init_state()

    tools_list, _ = load_tools()
    provider_name, _provider, model, agent = render_sidebar(tools_list)
    render_header(provider_name, model, len(tools_list))

    if not st.session_state.msgs:
        st.markdown(
            """
            <div class="empty-state">
                <strong>Start a research run</strong>
                <p>Ask a question, request a digest, or test a tool boundary.</p>
            </div>
            """,
            unsafe_allow_html=True,
        )

    render_history()

    prompt = st.session_state.pop("pending_prompt", None) or st.chat_input("Ask the research agent")
    if not prompt:
        return

    user_message = {"role": "user", "content": prompt}
    st.session_state.msgs.append(user_message)
    with st.chat_message("user"):
        st.markdown(prompt)

    with st.chat_message("assistant"):
        try:
            with st.spinner("Running agent..."):
                run = agent.run(model_history())

            assistant_text = run.text or "(no text)"
            st.markdown(assistant_text)
            render_trace(run.tool_calls, run.tool_results)
            save_transcript(prompt, provider_name, model, run)
            st.session_state.msgs.append(
                {
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_calls": run.tool_calls,
                    "tool_results": run.tool_results,
                }
            )
        except Exception as exc:
            st.error(f"Provider error: {exc}. Try switching provider in the sidebar.")


if __name__ == "__main__":
    main()
