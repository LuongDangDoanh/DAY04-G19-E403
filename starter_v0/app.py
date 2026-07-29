from __future__ import annotations

import json
import os
from datetime import datetime
from pathlib import Path

import streamlit as st

from chat import (
    ROOT,
    assistant_tool_message,
    now_iso,
    run_model_tool_loop,
    tool_results_message,
    trim_history,
    write_transcript,
)
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version

load_lab_env(ROOT)

st.set_page_config(page_title="Research Agent", page_icon="", layout="wide")
st.title("Research Agent")

ARTIFACTS_DIR = ROOT / "artifacts"

if "messages" not in st.session_state:
    st.session_state.messages = []
if "history" not in st.session_state:
    st.session_state.history = []
if "transcript_id" not in st.session_state:
    ts = datetime.now().strftime("%Y%m%dT%H%M%S%f")
    st.session_state.transcript_id = f"ui_{ts}"
if "transcript_turns" not in st.session_state:
    st.session_state.transcript_turns = []

with st.sidebar:
    st.header("Configuration")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.text_input("Version", "v3")
    model = st.text_input("Model (optional)", "")
    max_rounds = st.slider("Max tool rounds", 1, 10, 4)

    if st.button("Reset conversation"):
        st.session_state.messages = []
        st.session_state.history = []
        st.rerun()

    st.divider()
    st.caption(f"Transcript: {st.session_state.transcript_id}")

system_prompt_path = ARTIFACTS_DIR / "system_prompt.md"
tools_path = ARTIFACTS_DIR / "tools.yaml"
system_prompt = system_prompt_path.read_text(encoding="utf-8")
tool_declarations = load_tool_declarations(tools_path)
openai_tools = to_openai_tools(tool_declarations)

artifact_version = build_artifact_version(version, system_prompt_path, tools_path)

with st.sidebar:
    st.divider()
    st.caption(f"Artifact: {artifact_version.artifact_version}")
    st.caption(f"Prompt hash: {artifact_version.prompt_hash[:12]}...")
    st.caption(f"Tools hash: {artifact_version.tools_hash[:12]}...")

for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "tool_events" in msg and msg["tool_events"]:
            with st.expander("Tool trace", expanded=False):
                for event in msg["tool_events"]:
                    result = event.get("result", {})
                    error = result.get("error")
                    status = "error" if error else "ok"
                    st.code(f"{event['tool']}({json.dumps(event.get('args', {}), ensure_ascii=False)})")
                    if error:
                        st.error(f"{error}: {result.get('message', '')}")
                    else:
                        st.code(json.dumps(result, ensure_ascii=False, indent=2)[:500])

if prompt := st.chat_input("Ask me anything..."):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with st.chat_message("user"):
        st.markdown(prompt)

    provider = make_provider(provider_name)
    selected_model = model or getattr(provider, "default_model", None)
    msgs = [
        {"role": "system", "content": system_prompt},
        *trim_history(st.session_state.history, 5),
        {"role": "user", "content": prompt},
    ]

    turn_record = {
        "turn_index": len(st.session_state.transcript_turns) + 1,
        "started_at": now_iso(),
        "user": prompt,
        "status": "started",
        "assistant_text": None,
        "rounds": [],
        "tool_events": [],
    }

    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            try:
                result = run_model_tool_loop(
                    provider=provider,
                    messages=msgs,
                    tools=openai_tools,
                    model=selected_model,
                    max_tool_rounds=max_rounds,
                )

                assistant_text = result["assistant_text"]
                tool_events = result.get("tool_events", [])
                rounds = result.get("rounds", [])

                st.markdown(assistant_text)
                if tool_events:
                    with st.expander("Tool trace", expanded=True):
                        for event in tool_events:
                            res = event.get("result", {})
                            error = res.get("error")
                            status = "error" if error else "ok"
                            st.code(f"{event['tool']}({json.dumps(event.get('args', {}), ensure_ascii=False)})")
                            if error:
                                st.error(f"{error}: {res.get('message', '')}")
                            else:
                                short = json.dumps(res, ensure_ascii=False, indent=2)[:500]
                                st.code(short)

                turn_record.update(result)
                st.session_state.messages.append({
                    "role": "assistant",
                    "content": assistant_text,
                    "tool_events": tool_events,
                })
                st.session_state.history.append({"role": "user", "content": prompt})
                st.session_state.history.append({"role": "assistant", "content": assistant_text})

            except Exception as exc:
                err_msg = f"{type(exc).__name__}: {str(exc)}"
                st.error(err_msg)
                turn_record.update({"status": "provider_error", "error": err_msg})
                st.session_state.messages.append({"role": "assistant", "content": f"Error: {err_msg}"})

        turn_record["ended_at"] = now_iso()
        st.session_state.transcript_turns.append(turn_record)

        transcript_dir = ROOT / "transcripts"
        transcript_dir.mkdir(parents=True, exist_ok=True)
        transcript_path = transcript_dir / f"{st.session_state.transcript_id}.transcript.json"
        transcript = {
            "transcript_id": st.session_state.transcript_id,
            **artifact_version_dict(artifact_version),
            "provider": provider_name,
            "model": selected_model,
            "system_prompt": str(system_prompt_path),
            "tools": str(tools_path),
            "created_at": st.session_state.transcript_turns[0]["started_at"] if st.session_state.transcript_turns else now_iso(),
            "updated_at": now_iso(),
            "turns": st.session_state.transcript_turns,
        }
        write_transcript(transcript_path, transcript)
