# Voice AI Agent

A production-grade, voice-controlled AI agent built on **LangGraph**, **Groq**, **ChromaDB RAG**, and **Streamlit**.

Speak or type — the agent transcribes your audio, classifies intent, executes the right tool, and shows every step of the pipeline live in the UI.

---

## Features

### Core Capabilities

| Voice Command / Message | What the Agent Does |
|---|---|
| *"Create a Python file with a retry function"* | Generates code → shows preview → waits for confirmation → saves to `output/` |
| *"Create a folder called utils"* | Creates folder in `output/` after confirmation |
| *"Summarize: [paste text]"* | Returns a bullet-point summary |
| *"Summarize this and save it to notes.txt"* | Summarizes AND saves — compound command |
| *"What's the price of the Pro plan?"* | RAG retrieval → accurate answer from local knowledge base |
| *"I want to sign up for the Pro plan"* | Detects buying intent → collects name → email → platform across turns → fires lead capture |
| *"Hi, how are you?"* | General chat with full session memory |

### Bonus Features (All Implemented)

| Bonus | How |
|---|---|
| **Compound Commands** | Single message triggers multiple tools sequentially |
| **Human-in-the-Loop** | Confirmation dialog before any file is written to disk |
| **Graceful Degradation** | Bad audio, unknown intent, API errors all handled with clean UI feedback |
| **Memory** | LangGraph `MemorySaver` + Streamlit session state persists full context across 6+ turns |
| **Model Benchmarking** | Dedicated `/Benchmark` page with live latency metrics for STT and LLM |

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                       Streamlit UI (app.py)                     │
│  ┌─────────────────────┐   ┌────────────────────────────────┐   │
│  │   Audio Input        │   │   Pipeline Results             │   │
│  │   • Browser mic      │   │   • Transcription              │   │
│  │   • File upload      │   │   • Intent badge + confidence  │   │
│  │   • Direct text      │   │   • Action taken               │   │
│  └──────────┬───────────┘   │   • Output (markdown)          │   │
│             │               └────────────────────────────────┘   │
└─────────────┼───────────────────────────────────────────────────┘
              │ audio bytes
      ┌───────▼────────┐
      │  STT Module    │  Groq whisper-large-v3 (~1-2s per 30s clip)
      │  stt/          │  Fallback: OpenAI Whisper API
      └───────┬────────┘
              │ transcription text
      ┌───────▼──────────────────────────────────────────────────┐
      │               LangGraph Agent  (agent/graph.py)          │
      │                                                          │
      │  START → classify_intent → [conditional router]         │
      │              ├─ handle_file_ops   (create / write code)  │
      │              ├─ handle_rag        (product inquiry)      │
      │              ├─ handle_lead       (multi-turn capture)   │
      │              ├─ handle_summarize  (text summarization)   │
      │              ├─ handle_compound   (multi-action)         │
      │              └─ handle_general_chat                      │
      │                                                          │
      │  State persists via MemorySaver thread checkpoints       │
      └──────────────────┬───────────────────────────────────────┘
                         │
         ┌───────────────┴──────────────────┐
         │                                  │
 ┌───────▼───────┐                ┌────────▼──────────┐
 │  Tools Layer  │                │   RAG Pipeline    │
 │ agent/tools   │                │   rag/retriever   │
 │ • create_file │                │   • ChromaDB      │
 │ • write_code  │                │   • MiniLM-L6-v2  │
 │ • summarize   │                │   • Local JSON KB │
 │ • lead_capture│                └───────────────────┘
 └───────┬───────┘
         │  (safety-constrained)
 ┌───────▼───────┐
 │   output/     │  All file I/O restricted here
 └───────────────┘
```

### Why LangGraph?

LangGraph was chosen over plain LangChain or AutoGen for three specific reasons:

1. **Stateful multi-turn flows** — The lead collection funnel requires 3–4 sequential turns where the agent remembers exactly which fields (name, email, platform) have been collected. LangGraph's `MemorySaver` checkpointer persists `AgentState` across invocations keyed by a `thread_id`, making this trivial without any manual state tracking.

2. **Explicit conditional routing** — Each intent maps to a distinct handler node via `add_conditional_edges`. The full graph topology is readable at a glance and easy to extend.

3. **Human-in-the-loop** — The `confirmation_required` flag pattern (a lightweight version of LangGraph's `interrupt`) lets the UI pause before destructive operations without blocking the server.

### State Management

`AgentState` (TypedDict) carries all cross-turn context:

- `messages` — full conversation history (`operator.add` reducer for automatic merging)
- `lead_stage` / `lead_data` — 4-step lead funnel progression
- `files_created` — list of files created this session
- `confirmed` — human-in-the-loop flag set by the UI layer
- `intent`, `sub_intents` — current and compound intent classifications
- `retrieved_context` — last RAG result for auditability

All fields are re-injected from Streamlit `session_state` on each graph call, giving seamless multi-turn memory across 6+ turns.

### STT: Why Groq API instead of a local Whisper model?

> **Hardware Note (as required):** Running `whisper-large-v3` locally on a typical laptop CPU takes approximately 45 seconds to transcribe a 30-second audio clip — longer than the clip itself. On a GPU-equipped machine it is viable, but not reliable across all reviewer environments.
>
> Groq runs the identical `whisper-large-v3` model on custom LPU hardware and returns the same transcription in **1–2 seconds**. The assignment explicitly permits API-based STT when local inference is impractical, provided it is documented here. An OpenAI Whisper API fallback is also included in `stt/transcriber.py` if Groq is unavailable.
>
> For local execution, replacing `_transcribe_groq()` with a `transformers` pipeline call requires only a 5-line change in `stt/transcriber.py`.

---

## Setup

### 1. Clone and install

```bash
git clone <your-repo-url>
cd voice-ai-agent
pip install -r requirements.txt
```

### 2. Configure environment

```bash
cp .env.example .env
# Open .env and add your GROQ_API_KEY
# Free key available at: https://console.groq.com
```

### 3. Run

```bash
streamlit run app.py
```

Open `http://localhost:8501` — use Chrome or Edge for microphone access.

The **Benchmark** page is available at `http://localhost:8501/Benchmark`.

---

## Usage Examples

### Local Agent (File & Code Operations)

```
"Create an empty file called config.json"
→ confirmation dialog → output/config.json created

"Write a Python class for a rate limiter"
→ code generated → preview shown → confirm → output/rate_limiter.py saved

"Summarize: Large language models are neural networks trained..."
→ bullet-point summary returned

"Summarize this and save it to notes.txt: [text]"
→ compound: summarizes + saves output/notes.txt in one step
```

### Conversational Sales Agent (RAG + Lead Capture)

```
"What's the difference between Basic and Pro?"
→ RAG retrieves pricing docs → accurate comparison returned

"Does the Basic plan support 4K?"
→ RAG answers: No, Basic is 720p; 4K is Pro only

"I want to try the Pro plan for my Instagram channel"
→ HIGH INTENT detected → "What's your name?"
→ "Alex" → "What's your email?"
→ "alex@example.com" → "Which platform?"
→ "Instagram" → mock_lead_capture("Alex", "alex@example.com", "Instagram") fires
→ Lead ID returned, saved to output/leads.json
```

---

## WhatsApp Deployment via Webhooks

To deploy this agent on WhatsApp:

**1. Set up WhatsApp Business API**
Create a Meta Developer app at [developers.facebook.com](https://developers.facebook.com), generate a permanent access token, and get your phone number ID.

**2. Wrap the agent in a FastAPI webhook**

```python
from fastapi import FastAPI, Request
import httpx

app = FastAPI()

@app.post("/webhook")
async def receive_message(request: Request):
    body = await request.json()
    entry = body["entry"][0]["changes"][0]["value"]

    # Text message
    if "messages" in entry:
        msg = entry["messages"][0]
        sender = msg["from"]
        msg_type = msg["type"]

        if msg_type == "text":
            user_text = msg["text"]["body"]
        elif msg_type == "audio":
            # Download audio → transcribe
            media_url = get_media_url(msg["audio"]["id"])
            audio_bytes = download_media(media_url)
            user_text = transcribe(audio_bytes)["text"]

        # Run LangGraph agent (sender phone = thread_id = per-user memory)
        result = run_agent(user_text, thread_id=sender)
        send_whatsapp_message(sender, result["output"])

    return {"status": "ok"}

@app.get("/webhook")
def verify_webhook(hub_mode: str, hub_verify_token: str, hub_challenge: str):
    if hub_verify_token == "YOUR_VERIFY_TOKEN":
        return int(hub_challenge)
    return 403
```

**3. Key points**
- Use the **sender's phone number as `thread_id`** — every user gets their own isolated LangGraph memory, including their own lead collection progress
- Use `ngrok` or Railway for local testing before deploying to a server
- Subscribe to `messages` events in the Meta Webhook dashboard
- Voice messages are delivered as audio URLs — download, pass to `stt/transcriber.py`, then run agent normally

---

## Project Structure

```
.
├── app.py                    # Main Streamlit UI (Agent + History + Knowledge Base)
├── pages/
│   └── Benchmark.py          # Model benchmarking page (STT + LLM latency)
├── config.py                 # Central config (keys, models, paths)
├── agent/
│   ├── state.py              # AgentState TypedDict definition
│   ├── graph.py              # LangGraph nodes, edges, MemorySaver
│   └── tools.py              # create_file, write_code, summarize, mock_lead_capture
├── rag/
│   └── retriever.py          # ChromaDB + sentence-transformers RAG pipeline
├── stt/
│   └── transcriber.py        # Groq Whisper STT (+ OpenAI fallback)
├── knowledge_base/
│   └── autostream.json       # Product knowledge: pricing, features, policies
├── output/                   # Safety-constrained: all file I/O goes here
├── requirements.txt
└── .env.example
```

---

## Model Benchmarking

See the live **Benchmark** page in the app (`/Benchmark`) for real-time metrics.

Summary of observed performance on a standard laptop (no GPU):

| Task | Model | Avg Latency |
|---|---|---|
| STT — 10s clip | Groq whisper-large-v3 | ~800 ms |
| STT — 30s clip | Groq whisper-large-v3 | ~1,800 ms |
| STT — local whisper-base | CPU | ~12,000 ms |
| Intent classification | llama-3.3-70b (Groq) | ~600 ms |
| RAG retrieval (ChromaDB) | all-MiniLM-L6-v2 | ~40 ms |
| Full pipeline | End-to-end | ~2,500 ms |

Groq's LPU inference provides **15–20x speedup** over local CPU Whisper without any accuracy trade-off, which is why it was selected as the primary STT provider.
