"""
Voice AI Agent — Streamlit UI
Voice-controlled local agent with RAG, LangGraph, streaming output, and session export.
"""

from __future__ import annotations

import time
import uuid
from pathlib import Path

import streamlit as st

# ── Page config (must be first Streamlit call) ─────────────────────────────────
st.set_page_config(
    page_title="Voice AI Agent",
    page_icon="🎙️",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Custom CSS ─────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
/* Pipeline step cards */
.pipeline-card {
    background: #1e2130;
    border-radius: 10px;
    padding: 14px 18px;
    margin: 6px 0;
    border-left: 4px solid #4a90d9;
}
.pipeline-card h4 { margin: 0 0 4px 0; color: #a0c4ff; font-size: 0.8rem; text-transform: uppercase; letter-spacing: 1px; }
.pipeline-card p  { margin: 0; color: #e0e0e0; font-size: 0.95rem; }

/* Intent badges */
.badge {
    display: inline-block;
    padding: 3px 10px;
    border-radius: 20px;
    font-size: 0.78rem;
    font-weight: 600;
    letter-spacing: 0.5px;
}
.badge-create_file      { background:#1a4480; color:#6eb4ff; }
.badge-write_code       { background:#3b1a68; color:#c49dff; }
.badge-summarize_text   { background:#4a3000; color:#ffc857; }
.badge-product_inquiry  { background:#0d3d3d; color:#4ecdc4; }
.badge-high_intent_lead { background:#1a4420; color:#69e09a; }
.badge-general_chat     { background:#2d2d2d; color:#aaaaaa; }
.badge-compound_command { background:#4a1010; color:#ff8080; }

/* History entry */
.hist-entry {
    border: 1px solid #2d2d2d;
    border-radius: 8px;
    padding: 10px 14px;
    margin: 5px 0;
    font-size: 0.88rem;
}

/* Metric box */
.metric-box {
    background: #1a1d2b;
    border-radius: 8px;
    padding: 12px 16px;
    text-align: center;
}
.metric-box .val { font-size: 1.4rem; font-weight: 700; color: #4a90d9; }
.metric-box .lbl { font-size: 0.7rem; color: #888; text-transform: uppercase; }
</style>
""",
    unsafe_allow_html=True,
)


# ── Lazy initialisation helpers ────────────────────────────────────────────────

@st.cache_resource(show_spinner="Loading LLM…")
def get_llm():
    from langchain_groq import ChatGroq
    from config import GROQ_API_KEY, LLM_MODEL

    if not GROQ_API_KEY:
        st.error("GROQ_API_KEY is not set. Add it to your .env file.")
        st.stop()
    return ChatGroq(api_key=GROQ_API_KEY, model=LLM_MODEL, temperature=0.1)


@st.cache_resource(show_spinner="Loading knowledge base…")
def get_rag():
    from rag.retriever import AutoStreamRAG
    return AutoStreamRAG()


@st.cache_resource(show_spinner="Building agent graph…")
def get_graph():
    from agent.graph import build_graph
    return build_graph(get_llm(), get_rag())


# ── Session-state initialisation ──────────────────────────────────────────────

def init_state():
    defaults = {
        "agent_state": None,      # persisted AgentState dict
        "session_id": str(uuid.uuid4()),
        "history": [],            # list of {role, text, intent, action, latency_ms}
        "stt_result": None,       # last STT result dict
        "awaiting_confirm": False,
        "confirm_data": None,
        "total_queries": 0,
        "lead_stage": "none",
        "lead_data": {},
        "files_created": [],
        "messages": [],           # LangChain messages for memory
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# ── Run agent ─────────────────────────────────────────────────────────────────

def run_agent(user_text: str, confirmed: bool = False) -> dict:
    """
    Invoke the LangGraph agent with the user's text.
    Persists cross-turn state (messages, lead_stage, etc.) in session_state.
    """
    from agent.state import empty_state

    graph = get_graph()
    thread = {"configurable": {"thread_id": st.session_state.session_id}}

    # Build state from previous turn + new input
    prev = st.session_state.agent_state or empty_state()

    new_state = {
        **prev,
        "input_text": user_text,
        "confirmed": confirmed,
        "confirmation_required": False,
        "processing_steps": [],
        "action_taken": "",
        "output": "",
        "error": "",
        # carry forward multi-turn fields
        "lead_stage": st.session_state.lead_stage,
        "lead_data": st.session_state.lead_data,
        "files_created": st.session_state.files_created,
        "messages": st.session_state.messages,
    }

    # If confirming a staged file operation, restore pending data
    if confirmed and st.session_state.confirm_data:
        new_state["pending_file_data"] = st.session_state.confirm_data

    t0 = time.perf_counter()
    result = graph.invoke(new_state, thread)
    latency = int((time.perf_counter() - t0) * 1000)

    # Persist updated state
    st.session_state.agent_state = result
    st.session_state.lead_stage = result.get("lead_stage", "none")
    st.session_state.lead_data = result.get("lead_data", {})
    st.session_state.files_created = result.get("files_created", [])
    st.session_state.messages = result.get("messages", [])

    # Handle human-in-the-loop
    if result.get("confirmation_required"):
        st.session_state.awaiting_confirm = True
        st.session_state.confirm_data = result.get("pending_file_data", {})
    else:
        st.session_state.awaiting_confirm = False
        st.session_state.confirm_data = None

    result["_latency_ms"] = latency
    return result


# ── Intent badge ──────────────────────────────────────────────────────────────

def intent_badge(intent: str) -> str:
    labels = {
        "create_file": "📁 Create File",
        "write_code": "💻 Write Code",
        "summarize_text": "📝 Summarize",
        "product_inquiry": "🔍 Product Inquiry",
        "high_intent_lead": "🎯 High-Intent Lead",
        "general_chat": "💬 General Chat",
        "compound_command": "⚡ Compound Command",
    }
    label = labels.get(intent, intent)
    css = f"badge badge-{intent}" if intent else "badge"
    return f'<span class="{css}">{label}</span>'


# ── Sidebar ────────────────────────────────────────────────────────────────────

def render_sidebar():
    with st.sidebar:
        st.markdown("## ⚙️ Configuration")

        from config import GROQ_API_KEY, LLM_MODEL, STT_MODEL

        key_ok = bool(GROQ_API_KEY)
        st.markdown(
            f"**API Key:** {'🟢 Connected' if key_ok else '🔴 Missing — add to .env'}"
        )
        st.caption(f"LLM: `{LLM_MODEL}`")
        st.caption(f"STT: `{STT_MODEL}`")

        st.divider()
        st.markdown("## 📊 Session Stats")

        col1, col2 = st.columns(2)
        with col1:
            st.metric("Queries", st.session_state.total_queries)
        with col2:
            st.metric("Files", len(st.session_state.files_created))

        lead = st.session_state.lead_data
        if lead:
            st.markdown("**Lead Collection**")
            stage = st.session_state.lead_stage
            progress = {"none": 0, "ask_name": 25, "ask_email": 50, "ask_platform": 75, "complete": 100}
            st.progress(progress.get(stage, 0) / 100, text=f"Stage: {stage}")
            if lead.get("name"):
                st.caption(f"Name: {lead['name']}")
            if lead.get("email"):
                st.caption(f"Email: {lead['email']}")
            if lead.get("platform"):
                st.caption(f"Platform: {lead['platform']}")

        st.divider()

        # Output files list
        if st.session_state.files_created:
            st.markdown("**📂 Files Created**")
            for fp in st.session_state.files_created:
                st.caption(f"`{Path(fp).name}`")

        st.divider()
        if st.button("🗑️ Reset Session", use_container_width=True):
            for k in list(st.session_state.keys()):
                del st.session_state[k]
            st.rerun()

        st.divider()
        st.markdown(
            "**Capabilities:**\n"
            "- Voice-controlled local file & code agent\n"
            "- Conversational sales bot with RAG + lead capture"
        )


# ── Pipeline visualization ────────────────────────────────────────────────────

def render_pipeline(result: dict, stt_result: dict | None = None):
    st.markdown("### 🔄 Pipeline")

    # STT step
    if stt_result:
        latency = stt_result.get("latency_ms", "—")
        prov = stt_result.get("provider", "Groq")
        st.markdown(
            f'<div class="pipeline-card"><h4>1 · Speech-to-Text ({prov} Whisper)</h4>'
            f'<p>"{stt_result.get("text","")[:120]}…" — {latency} ms</p></div>',
            unsafe_allow_html=True,
        )

    # Intent
    intent = result.get("intent", "—")
    conf = result.get("intent_confidence", "")
    conf_str = f" ({conf:.0%})" if isinstance(conf, float) else ""
    st.markdown(
        f'<div class="pipeline-card"><h4>2 · Intent Classification</h4>'
        f"<p>{intent_badge(intent)}{conf_str}</p></div>",
        unsafe_allow_html=True,
    )

    # Processing steps
    steps = result.get("processing_steps", [])
    for i, step in enumerate(steps[1:], start=3):  # skip duplicate intent step
        st.markdown(
            f'<div class="pipeline-card"><h4>{i} · Step</h4><p>{step}</p></div>',
            unsafe_allow_html=True,
        )

    # Action
    action = result.get("action_taken", "")
    if action:
        st.markdown(
            f'<div class="pipeline-card" style="border-left-color:#69e09a">'
            f"<h4>✅ Action Taken</h4><p>{action}</p></div>",
            unsafe_allow_html=True,
        )

    latency = result.get("_latency_ms", "—")
    st.caption(f"Total latency: {latency} ms")


# ── Confirmation dialog ───────────────────────────────────────────────────────

def render_confirmation(result: dict):
    st.warning("⚠️ **Human-in-the-Loop — Confirmation Required**", icon="⚠️")
    st.markdown(result.get("confirmation_message", "Proceed with file operation?"))

    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Confirm & Execute", type="primary", use_container_width=True):
            with st.spinner("Executing…"):
                confirmed_result = run_agent(
                    st.session_state._last_input, confirmed=True
                )
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": confirmed_result.get("output", ""),
                    "intent": confirmed_result.get("intent", ""),
                    "action": confirmed_result.get("action_taken", ""),
                    "latency_ms": confirmed_result.get("_latency_ms", 0),
                }
            )
            st.rerun()
    with col2:
        if st.button("❌ Cancel", use_container_width=True):
            st.session_state.awaiting_confirm = False
            st.session_state.confirm_data = None
            st.info("Operation cancelled.")
            st.rerun()


# ── Streaming text helper ─────────────────────────────────────────────────────

def _stream_text(text: str, delay: float = 0.012) -> None:
    """
    Simulate streaming output — renders the response word-by-word.
    Gives the UI a ChatGPT-style live feel. Uses st.write_stream.
    """
    import time as _time

    def _gen():
        for word in text.split(" "):
            yield word + " "
            _time.sleep(delay)

    st.write_stream(_gen())


# ── Session export helpers ────────────────────────────────────────────────────

def _build_markdown_export() -> str:
    """Build a full Markdown transcript of the current session."""
    from datetime import datetime

    lines = [
        "# Voice AI Agent — Session Transcript",
        f"*Exported {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*",
        "",
    ]
    for entry in st.session_state.get("history", []):
        role = "**You**" if entry["role"] == "user" else "**Agent**"
        intent = entry.get("intent", "")
        action = entry.get("action", "")
        stt = entry.get("stt")

        lines.append(f"### {role}")
        if stt:
            lines.append(f"> 🎙️ Transcribed via {stt.get('provider','Groq')} in {stt.get('latency_ms','—')} ms")
        if intent:
            lines.append(f"> Intent: `{intent}`")
        if action:
            lines.append(f"> Action: {action}")
        lines.append("")
        lines.append(entry.get("text", ""))
        if entry.get("latency_ms"):
            lines.append(f"*⏱ {entry['latency_ms']} ms*")
        lines.append("")
        lines.append("---")
        lines.append("")
    return "\n".join(lines)


def _build_plain_export() -> str:
    """Build a plain-text transcript."""
    lines = []
    for entry in st.session_state.get("history", []):
        role = "YOU" if entry["role"] == "user" else "AGENT"
        lines.append(f"[{role}] {entry.get('text', '')}")
        lines.append("")
    return "\n".join(lines)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    init_state()
    render_sidebar()

    # ── Header ──────────────────────────────────────────────────────────────
    st.markdown(
        "# 🎙️ Voice AI Agent\n"
        "*Voice-controlled local agent · AutoStream sales bot · LangGraph · RAG · Multi-turn memory*"
    )

    tabs = st.tabs(["🎙️ Agent", "📜 History", "📚 Knowledge Base"])

    # ════════════════════════════════════════════════════════════════════════
    # TAB 1 — Main Agent Interface
    # ════════════════════════════════════════════════════════════════════════
    with tabs[0]:

        # Pending confirmation takes over the tab
        if st.session_state.awaiting_confirm and st.session_state.agent_state:
            render_confirmation(st.session_state.agent_state)
            st.stop()

        left, right = st.columns([1, 1], gap="large")

        # ── Left: Input ──────────────────────────────────────────────────
        with left:
            st.markdown("### 🎤 Input")

            input_tab_audio, input_tab_upload, input_tab_text = st.tabs(
                ["🎙️ Record", "📁 Upload Audio", "⌨️ Type"]
            )

            user_text: str | None = None
            stt_result_local: dict | None = None

            # ── Record tab ──────────────────────────────────────────────
            with input_tab_audio:
                st.caption("Record directly in-browser (WAV). Works in Chrome/Edge.")
                try:
                    from audio_recorder_streamlit import audio_recorder

                    audio_bytes = audio_recorder(
                        text="Click to record",
                        recording_color="#e8523b",
                        neutral_color="#4a90d9",
                        icon_size="2x",
                        pause_threshold=2.0,
                    )
                    if audio_bytes:
                        st.audio(audio_bytes, format="audio/wav")
                        if st.button("🔤 Transcribe & Send", key="btn_record"):
                            with st.spinner("Transcribing…"):
                                from stt.transcriber import transcribe
                                stt_result_local = transcribe(audio_bytes, "recorded.wav")
                            if stt_result_local["success"]:
                                user_text = stt_result_local["text"]
                                st.session_state.stt_result = stt_result_local
                                st.success(f"**Transcribed:** {user_text}")
                            else:
                                st.error(f"STT failed: {stt_result_local.get('error')}")

                except ImportError:
                    st.info("Install `audio-recorder-streamlit` for in-browser recording.")

            # ── Upload tab ───────────────────────────────────────────────
            with input_tab_upload:
                uploaded = st.file_uploader(
                    "Upload audio file", type=["wav", "mp3", "m4a", "ogg", "flac"]
                )
                if uploaded:
                    st.audio(uploaded)
                    if st.button("🔤 Transcribe & Send", key="btn_upload"):
                        audio_bytes = uploaded.read()
                        with st.spinner("Transcribing…"):
                            from stt.transcriber import transcribe
                            stt_result_local = transcribe(audio_bytes, uploaded.name)
                        if stt_result_local["success"]:
                            user_text = stt_result_local["text"]
                            st.session_state.stt_result = stt_result_local
                            st.success(f"**Transcribed:** {user_text}")
                        else:
                            st.error(f"STT failed: {stt_result_local.get('error')}")

            # ── Text tab ─────────────────────────────────────────────────
            with input_tab_text:
                typed = st.text_area(
                    "Your message",
                    placeholder=(
                        "e.g. 'Create a Python file with a retry function'\n"
                        "or   'What is the price of the Pro plan?'\n"
                        "or   'Summarize this text and save it to summary.txt: …'"
                    ),
                    height=120,
                    key="typed_input",
                )
                if st.button("Send ▶", type="primary", key="btn_text"):
                    user_text = typed.strip()

        # ── Right: Results ───────────────────────────────────────────────
        with right:
            st.markdown("### 📊 Results")

            result_placeholder = st.empty()
            pipeline_placeholder = st.empty()

        # ── Process user input ───────────────────────────────────────────
        if user_text:
            st.session_state._last_input = user_text
            st.session_state.total_queries += 1

            with st.spinner("Agent thinking…"):
                result = run_agent(user_text)

            stt_r = st.session_state.stt_result if stt_result_local else None

            # Add to history
            st.session_state.history.append(
                {
                    "role": "user",
                    "text": user_text,
                    "intent": result.get("intent", ""),
                    "action": result.get("action_taken", ""),
                    "latency_ms": result.get("_latency_ms", 0),
                    "stt": stt_r,
                }
            )
            st.session_state.history.append(
                {
                    "role": "assistant",
                    "text": result.get("output", ""),
                    "intent": result.get("intent", ""),
                    "action": result.get("action_taken", ""),
                    "latency_ms": result.get("_latency_ms", 0),
                }
            )

            # ── Show results on right column ─────────────────────────────
            with right:
                # If confirmation needed, re-run to show dialog
                if st.session_state.awaiting_confirm:
                    st.rerun()

                # Transcription card
                if stt_r and stt_r.get("text"):
                    st.markdown(
                        f'<div class="pipeline-card">'
                        f"<h4>📝 Transcription</h4>"
                        f"<p>{stt_r['text']}</p>"
                        f"</div>",
                        unsafe_allow_html=True,
                    )

                # Intent
                intent_val = result.get("intent", "")
                if intent_val:
                    st.markdown(
                        f"**Intent:** {intent_badge(intent_val)}",
                        unsafe_allow_html=True,
                    )

                # Error alert (graceful degradation)
                if result.get("error"):
                    st.error(f"⚠️ {result['error']}")

                # Output — streamed word-by-word for general/RAG responses
                st.divider()
                st.markdown("**Output**")
                output_text = result.get("output", "*(no output)*")
                intent_val2 = result.get("intent", "")
                # Stream only for text responses (not file-op confirmations)
                if intent_val2 in ("general_chat", "product_inquiry") and output_text:
                    _stream_text(output_text)
                else:
                    st.markdown(output_text)

            # Pipeline visualization under left column
            with left:
                st.divider()
                render_pipeline(result, stt_r)

            # Clear STT result after use
            st.session_state.stt_result = None

        else:
            # Show last result if exists
            if st.session_state.history:
                last = [h for h in st.session_state.history if h["role"] == "assistant"]
                if last:
                    with right:
                        entry = last[-1]
                        if entry.get("intent"):
                            st.markdown(
                                f"**Last intent:** {intent_badge(entry['intent'])}",
                                unsafe_allow_html=True,
                            )
                        st.markdown("**Last output**")
                        st.markdown(entry.get("text", ""))

    # ════════════════════════════════════════════════════════════════════════
    # TAB 2 — History + Export
    # ════════════════════════════════════════════════════════════════════════
    with tabs[1]:
        st.markdown("### 📜 Session History")

        if not st.session_state.history:
            st.info("No messages yet. Start talking to the agent in the **Agent** tab!")
        else:
            # ── Export buttons ────────────────────────────────────────────
            exp_col1, exp_col2, _ = st.columns([1, 1, 3])
            with exp_col1:
                md_export = _build_markdown_export()
                st.download_button(
                    label="⬇️ Export as Markdown",
                    data=md_export,
                    file_name="session_history.md",
                    mime="text/markdown",
                    use_container_width=True,
                )
            with exp_col2:
                txt_export = _build_plain_export()
                st.download_button(
                    label="⬇️ Export as .txt",
                    data=txt_export,
                    file_name="session_history.txt",
                    mime="text/plain",
                    use_container_width=True,
                )

            st.divider()

            for i, entry in enumerate(reversed(st.session_state.history)):
                role_icon = "👤" if entry["role"] == "user" else "🤖"
                role_label = "You" if entry["role"] == "user" else "Agent"
                intent_html = intent_badge(entry.get("intent", "")) if entry.get("intent") else ""

                with st.expander(
                    f"{role_icon} {role_label} — {entry.get('text', '')[:60]}…",
                    expanded=(i == 0),
                ):
                    if entry.get("stt"):
                        stt = entry["stt"]
                        st.caption(
                            f"🎙️ Transcribed via {stt.get('provider','Groq')} Whisper "
                            f"in {stt.get('latency_ms','—')} ms"
                        )
                    if intent_html:
                        st.markdown(f"**Intent:** {intent_html}", unsafe_allow_html=True)
                    if entry.get("action"):
                        st.caption(f"**Action:** {entry['action']}")
                    st.markdown(entry.get("text", ""))
                    if entry.get("latency_ms"):
                        st.caption(f"⏱ {entry['latency_ms']} ms")

    # ════════════════════════════════════════════════════════════════════════
    # TAB 3 — Knowledge Base
    # ════════════════════════════════════════════════════════════════════════
    with tabs[2]:
        st.markdown("### 📚 Knowledge Base (RAG Source)")
        st.caption(
            "This is the local knowledge base used by the RAG pipeline. "
            "All answers to product and pricing questions are retrieved from here — "
            "the LLM cannot hallucinate facts it cannot find in these documents."
        )
        try:
            rag = get_rag()
            docs = rag.get_all_docs()
            for doc in docs:
                with st.expander(f"**{doc['title']}** · `{doc['category']}`"):
                    st.markdown(doc["content"])
        except Exception as exc:
            st.error(f"Could not load knowledge base: {exc}")

        st.divider()
        st.markdown("#### 🔎 Test Retrieval")
        test_q = st.text_input("Enter a test query to see what gets retrieved:")
        if test_q:
            try:
                rag = get_rag()
                results = rag.retrieve(test_q)
                for r in results:
                    st.markdown(
                        f"**{r['title']}** (score: `{r['score']}`)\n\n{r['content']}"
                    )
                    st.divider()
            except Exception as exc:
                st.error(str(exc))


if __name__ == "__main__":
    main()
