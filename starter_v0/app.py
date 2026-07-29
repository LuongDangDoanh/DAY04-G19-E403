from __future__ import annotations

import html
import json
import os
import re
from datetime import datetime
from pathlib import Path
from typing import Any

import streamlit as st

from chat import now_iso, run_model_tool_loop, safe_slug, trim_history, write_transcript
from env_loader import load_lab_env
from providers import make_provider
from tools import load_tool_declarations, to_openai_tools
from versioning import artifact_version_dict, build_artifact_version


ROOT = Path(__file__).parent
ARTIFACTS = ROOT / "artifacts"
TRANSCRIPTS = ROOT / "transcripts"
load_lab_env(ROOT)

SCENARIOS = {
    "Research request": "Tin AI hôm nay có gì nổi bật?",
    "Missing information": "Tóm tắt 5 tweet mới nhất giúp mình",
    "Sensitive action": "Đăng bản tin này lên Telegram giúp mình",
}


def clean_for_display(value: Any) -> str:
    text = json.dumps(value, ensure_ascii=False, indent=2, default=str)
    for env_name in ("OPENROUTER_API_KEY", "OPENAI_API_KEY", "TAVILY_API_KEY", "FIRECRAWL_API_KEY", "RAPIDAPI_KEY", "TELEGRAM_BOT_TOKEN"):
        secret = os.getenv(env_name)
        if secret:
            text = text.replace(secret, "[REDACTED]")
    return text


def artifact_context(version: str) -> dict[str, Any]:
    artifact = build_artifact_version(version, ARTIFACTS / "system_prompt.md", ARTIFACTS / "tools.yaml")
    return artifact_version_dict(artifact)


def init_state(version: str) -> None:
    if "session_version" in st.session_state and st.session_state.session_version != version:
        for key in ("history", "turns", "transcript_id", "created_at", "run_count", "last_result", "last_request", "last_transcript_path"):
            st.session_state.pop(key, None)
    st.session_state.session_version = version
    if "history" not in st.session_state:
        st.session_state.history = []
    if "turns" not in st.session_state:
        st.session_state.turns = []
    if "transcript_id" not in st.session_state:
        stamp = datetime.now().strftime("%Y%m%dT%H%M%S%f")
        st.session_state.transcript_id = f"ui_{safe_slug(version)}_{stamp}"
    if "run_count" not in st.session_state:
        st.session_state.run_count = 0


def save_transcript(version: str, provider_name: str, model: str | None) -> Path:
    TRANSCRIPTS.mkdir(parents=True, exist_ok=True)
    transcript_path = TRANSCRIPTS / f"{st.session_state.transcript_id}.transcript.json"
    payload = {
        "transcript_id": st.session_state.transcript_id,
        **artifact_context(version),
        "provider": provider_name,
        "model": model,
        "system_prompt": str(ARTIFACTS / "system_prompt.md"),
        "tools": str(ARTIFACTS / "tools.yaml"),
        "created_at": st.session_state.get("created_at", now_iso()),
        "updated_at": now_iso(),
        "turns": st.session_state.turns,
    }
    write_transcript(transcript_path, payload)
    return transcript_path


def tool_status(result: Any) -> str:
    if isinstance(result, dict) and result.get("error"):
        return "ERROR"
    if isinstance(result, dict) and result.get("awaiting_user"):
        return "WAITING"
    return "PASS"


def render_event(round_index: int, event: dict[str, Any], event_index: int) -> None:
    name = event.get("tool", "unknown_tool")
    result = event.get("result", {})
    status = tool_status(result)
    icon = "✕" if status == "ERROR" else "!" if status == "WAITING" else "✓"
    st.markdown(
        f'<div class="event"><div class="event-head"><span class="event-icon">{icon}</span>'
        f'<span><strong>{html.escape(name)}</strong><small>round {round_index} · status {status.lower()}</small></span>'
        f'<b class="event-status {status.lower()}">{status}</b></div>'
        f'<div class="event-grid"><div><label>args</label><pre>{html.escape(clean_for_display(event.get("args", {})))}</pre></div>'
        f'<div><label>result / error</label><pre>{html.escape(clean_for_display(result))}</pre></div></div></div>',
        unsafe_allow_html=True,
    )


def run_request(user_text: str, version: str, provider_name: str, model: str | None, max_rounds: int) -> None:
    try:
        system_prompt = (ARTIFACTS / "system_prompt.md").read_text(encoding="utf-8")
        declarations = to_openai_tools(load_tool_declarations(ARTIFACTS / "tools.yaml"))
        provider = make_provider(provider_name)
        result = run_model_tool_loop(
            provider=provider,
            messages=[{"role": "system", "content": system_prompt}, *trim_history(st.session_state.history, 5), {"role": "user", "content": user_text}],
            tools=declarations,
            model=model or getattr(provider, "default_model", None),
            max_tool_rounds=max_rounds,
        )
        turn = {
            "turn_index": len(st.session_state.turns) + 1,
            "started_at": now_iso(),
            "ended_at": now_iso(),
            "user": user_text,
            **result,
        }
        st.session_state.turns.append(turn)
        st.session_state.history.extend([{"role": "user", "content": user_text}, {"role": "assistant", "content": result.get("assistant_text", "")}])
        st.session_state.last_result = result
        st.session_state.last_request = user_text
        st.session_state.run_count += 1
        path = save_transcript(version, provider_name, model)
        st.session_state.last_transcript_path = str(path)
    except Exception as exc:
        st.session_state.last_result = {"status": "provider_error", "assistant_text": "Provider error. Inspect details below.", "rounds": [], "tool_events": [], "error": f"{type(exc).__name__}: {exc}"}


st.set_page_config(page_title="Traceboard", page_icon="T", layout="wide", initial_sidebar_state="expanded")
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Be+Vietnam+Pro:wght@400;800&display=swap');
:root{--lav:#E9E3FF;--white:#FFFFFF;--violet:#6C4BFF;--pink:#FF93B8;--ink:#2C2354}
.stApp{background:var(--lav);color:var(--ink);font-family:'Be Vietnam Pro',Arial,sans-serif}
[data-testid="stSidebar"]{background:var(--lav)}
[data-testid="stSidebar"]>div{padding-top:2rem}
h1,h2,h3{font-family:'Be Vietnam Pro',Arial,sans-serif;font-weight:800;letter-spacing:-.05em;color:var(--ink)}
.hero,.panel,.event,.metric{background:var(--white);border-radius:26px;box-shadow:12px 14px 26px rgba(108,75,255,.18),-8px -8px 18px rgba(255,255,255,.9),inset 0 3px 4px rgba(255,255,255,.82);padding:1.4rem}
.hero{padding:2.2rem 2.4rem;margin-bottom:1.2rem}.eyebrow{color:var(--violet);font-size:.72rem;font-weight:800;letter-spacing:.14em;text-transform:uppercase}.hero p{max-width:700px;opacity:.72}
.metric{min-height:100px}.metric b{display:block;font-size:1.35rem}.metric small,.event small{display:block;opacity:.58;font-size:.72rem}
.panel{margin-top:1.1rem}.request{background:var(--lav);border-radius:22px;box-shadow:inset 0 3px 4px rgba(255,255,255,.82);padding:1rem 1.1rem;margin:.8rem 0 1rem}.request label,.event label{display:block;text-transform:uppercase;letter-spacing:.1em;font-size:.65rem;font-weight:800;opacity:.55}.request p{margin:.3rem 0 0;font-weight:800}
.event{padding:1rem 1.1rem;margin:.7rem 0;box-shadow:6px 8px 16px rgba(108,75,255,.11),inset 0 3px 4px rgba(255,255,255,.82)}.event-head{display:flex;align-items:center;gap:.7rem}.event-icon{width:28px;height:28px;display:grid;place-items:center;border-radius:10px;background:var(--violet);color:var(--white);font-weight:800}.event-head>span:nth-child(2){flex:1}.event-status{font-size:.65rem}.event-status.error{color:var(--pink)}.event-status.pass{color:var(--violet)}.event-status.waiting{color:var(--ink)}.event-grid{display:grid;grid-template-columns:1fr 1fr;gap:.7rem;margin:.8rem 0 0}.event pre{white-space:pre-wrap;overflow-wrap:anywhere;background:var(--lav);border-radius:14px;padding:.7rem;font-size:.68rem;color:var(--ink)}.meta{padding:.7rem 0;font-size:.72rem;opacity:.7}.stButton>button{border:0;border-radius:18px;background:var(--white);color:var(--ink);box-shadow:inset 0 3px 4px rgba(255,255,255,.82),7px 8px 15px rgba(108,75,255,.14);font-weight:800}.stButton>button:hover{color:var(--violet);border:0}.stChatInput{border-radius:22px}.scenario-note{font-size:.76rem;opacity:.62}
@media(max-width:700px){.event-grid{grid-template-columns:1fr}.hero{padding:1.4rem}.metric{margin-bottom:.8rem}}
@media(prefers-reduced-motion:reduce){*,*:before,*:after{transition:none!important;animation:none!important}}
</style>
""", unsafe_allow_html=True)

with st.sidebar:
    st.markdown("### Traceboard")
    st.caption("Research agent evidence workspace")
    provider_name = st.selectbox("Provider", ["openrouter", "openai", "anthropic", "gemini"], index=0)
    version = st.selectbox("Artifact version", ["v3", "v2", "v1", "v0"], index=0)
    model = st.text_input("Model override (optional)", value="") or None
    max_rounds = st.slider("Max tool rounds", 1, 6, 4)
    st.divider()
    scenario = st.selectbox("Demo scenario", list(SCENARIOS))
    st.caption(SCENARIOS[scenario])
    if st.button("Run selected scenario", use_container_width=True):
        init_state(version)
        run_request(SCENARIOS[scenario], version, provider_name, model, max_rounds)
        st.rerun()
    if st.button("Clear session", use_container_width=True):
        for key in list(st.session_state.keys()):
            del st.session_state[key]
        st.rerun()

init_state(version)
context = artifact_context(version)
st.markdown('<div class="hero"><div class="eyebrow">Evidence-driven research agent</div><h1>See every decision behind the answer.</h1><p>Run one scenario through different artifact versions. Inspect the request, final response, every tool argument, round/status, result/error, and the transcript saved for review.</p></div>', unsafe_allow_html=True)

cols = st.columns(4)
stats = [("Version", context["artifact_version"]), ("Transcript", st.session_state.transcript_id), ("Run count", str(st.session_state.run_count)), ("Tools", "21 declared")]
for col, (name, value) in zip(cols, stats):
    with col:
        st.markdown(f'<div class="metric"><small>{html.escape(name)}</small><b>{html.escape(value)}</b></div>', unsafe_allow_html=True)

if "last_result" not in st.session_state:
    st.info("Chọn một scenario ở sidebar hoặc nhập request bên dưới để tạo live evidence.")
else:
    result = st.session_state.last_result
    st.markdown('<div class="panel">', unsafe_allow_html=True)
    st.markdown(f'<div class="eyebrow">Latest run · {html.escape(st.session_state.get("last_request", ""))}</div>', unsafe_allow_html=True)
    st.markdown(f'<div class="request"><label>Request</label><p>{html.escape(st.session_state.get("last_request", ""))}</p></div>', unsafe_allow_html=True)
    st.markdown(f'<div class="request"><label>Final response · status {html.escape(str(result.get("status", "unknown")))}</label><p>{html.escape(result.get("assistant_text", ""))}</p></div>', unsafe_allow_html=True)
    if result.get("error"):
        st.error(result["error"])
    st.markdown("#### Tool trace")
    for round_record in result.get("rounds", []):
        st.markdown(f"**Round {round_record.get('round')}** · {'tool call' if round_record.get('tool_calls') else 'final answer'}")
        for index, event in enumerate(round_record.get("tool_results", []), 1):
            render_event(int(round_record.get("round", 0)), event, index)
    path = st.session_state.get("last_transcript_path", "not saved")
    st.markdown(f'<div class="meta">transcript: {html.escape(path)}<br>artifact_version: {html.escape(context["artifact_version"])} · prompt_hash: {html.escape(context["prompt_hash"][:12])} · tools_hash: {html.escape(context["tools_hash"][:12])}</div>', unsafe_allow_html=True)
    st.markdown('</div>', unsafe_allow_html=True)

user_text = st.chat_input("Ask a research question…")
if user_text:
    run_request(user_text, version, provider_name, model, max_rounds)
    st.rerun()
