"""LangGraph state definition for the unified Voice AI Agent."""

from __future__ import annotations

from typing import Annotated, Any, Dict, List, Optional
import operator
from langchain_core.messages import BaseMessage
from typing_extensions import TypedDict


class AgentState(TypedDict, total=False):
    # ── Input ─────────────────────────────────────────────────────────────────
    input_text: str                        # text fed into the graph (post-STT or direct)

    # ── Classification ────────────────────────────────────────────────────────
    intent: str                            # primary intent
    sub_intents: List[str]                 # compound command sub-intents
    intent_confidence: float

    # ── Pipeline metadata (shown in UI) ───────────────────────────────────────
    processing_steps: List[str]
    action_taken: str
    output: str

    # ── File operations ───────────────────────────────────────────────────────
    files_created: List[str]
    pending_file_data: Dict[str, Any]      # staged file before confirmation

    # ── Human-in-the-loop ────────────────────────────────────────────────────
    confirmation_required: bool
    confirmation_message: str
    confirmed: bool                        # set to True by UI before re-run

    # ── RAG ──────────────────────────────────────────────────────────────────
    retrieved_context: str

    # ── Lead capture (AutoStream sales bot) ──────────────────────────────────
    lead_stage: str          # none | ask_name | ask_email | ask_platform | complete
    lead_data: Dict[str, str]

    # ── Conversation memory ───────────────────────────────────────────────────
    # Annotated with operator.add so LangGraph merges lists across checkpoints
    messages: Annotated[List[BaseMessage], operator.add]

    # ── Error handling ────────────────────────────────────────────────────────
    error: str


# Default / empty state factory
def empty_state() -> AgentState:
    return AgentState(
        input_text="",
        intent="",
        sub_intents=[],
        intent_confidence=0.0,
        processing_steps=[],
        action_taken="",
        output="",
        files_created=[],
        pending_file_data={},
        confirmation_required=False,
        confirmation_message="",
        confirmed=False,
        retrieved_context="",
        lead_stage="none",
        lead_data={},
        messages=[],
        error="",
    )
