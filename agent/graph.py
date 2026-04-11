"""
LangGraph-based unified agent.

Handles all agent intents in a single unified graph:
  Local operations  – create_file, write_code, summarize_text, general_chat
  Sales bot         – product_inquiry, high_intent_lead, lead collection (multi-turn)
  Bonus             – compound_command, graceful degradation, human-in-the-loop

Graph topology:
  START → classify_intent → [conditional router]
              ├─ handle_file_ops     (create_file / write_code)
              ├─ handle_rag          (product_inquiry)
              ├─ handle_lead         (high_intent_lead + multi-turn collection)
              ├─ handle_summarize    (summarize_text)
              ├─ handle_compound     (compound_command)
              └─ handle_general_chat (fallback)
          each handler → END
"""

from __future__ import annotations

import json
import re
import time
from typing import Literal

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage
from langgraph.graph import END, StateGraph
from langgraph.checkpoint.memory import MemorySaver

from agent.state import AgentState
from agent.tools import (
    create_file,
    create_folder,
    extract_email,
    extract_filename,
    mock_lead_capture,
    summarize_text,
    write_code_to_file,
)


# ── Intent constants ──────────────────────────────────────────────────────────
INTENTS = [
    "create_file",
    "write_code",
    "summarize_text",
    "product_inquiry",
    "high_intent_lead",
    "general_chat",
    "compound_command",
]


# ── Graph factory ─────────────────────────────────────────────────────────────

def build_graph(llm, rag):
    """
    Build and compile the LangGraph agent.

    Args:
        llm  – ChatGroq (or any LangChain ChatModel) instance
        rag  – AutoStreamRAG instance
    """

    # ── Node helpers ──────────────────────────────────────────────────────────

    def _call_llm_json(prompt: str) -> dict:
        """Call LLM and parse JSON from the response."""
        resp = llm.invoke([HumanMessage(content=prompt)])
        try:
            match = re.search(r"\{.*\}", resp.content, re.DOTALL)
            return json.loads(match.group()) if match else {}
        except Exception:
            return {}

    def _steps(state: AgentState) -> list:
        return list(state.get("processing_steps") or [])

    # ── Node: classify_intent ─────────────────────────────────────────────────

    def classify_intent(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        lead_stage = state.get("lead_stage", "none")

        # If we're mid lead-collection, skip re-classification
        if lead_stage in ("ask_name", "ask_email", "ask_platform"):
            return {
                **state,
                "intent": "high_intent_lead",
                "processing_steps": _steps(state) + ["Continuing lead collection…"],
            }

        # Build recent-history context
        recent = (state.get("messages") or [])[-6:]
        history = "\n".join(f"{m.type.upper()}: {m.content}" for m in recent)

        prompt = f"""You are an intent classifier for a dual-purpose AI agent.

Classify the user's message into EXACTLY ONE intent from this list:
{json.dumps(INTENTS, indent=2)}

Definitions:
- create_file       : user wants to create an empty file or folder
- write_code        : user wants AI to generate code and save it to a file
- summarize_text    : user wants to summarize some text
- product_inquiry   : question about AutoStream product, pricing, features, or policies
- high_intent_lead  : user shows buying intent for AutoStream (wants to sign up / try / buy)
- general_chat      : greetings, off-topic, small talk, or anything else
- compound_command  : the message contains TWO OR MORE distinct actions

Recent conversation:
{history or "(none)"}

User message: "{user_input}"

Respond ONLY with valid JSON:
{{
  "intent": "<one of the intents above>",
  "confidence": <0.0–1.0>,
  "sub_intents": ["<intent1>", "<intent2>"],
  "reasoning": "<one sentence>"
}}"""

        result = _call_llm_json(prompt)

        intent = result.get("intent", "general_chat")
        if intent not in INTENTS:
            intent = "general_chat"

        new_messages = list(state.get("messages") or []) + [HumanMessage(content=user_input)]

        return {
            **state,
            "intent": intent,
            "sub_intents": result.get("sub_intents", []),
            "intent_confidence": result.get("intent_confidence", 0.9),
            "messages": new_messages,
            "processing_steps": _steps(state) + [f"Intent → {intent}"],
            "error": "",
        }

    # ── Node: handle_file_ops ─────────────────────────────────────────────────

    def handle_file_ops(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        intent = state.get("intent", "")

        # ── If already confirmed, execute the staged operation ─────────────
        if state.get("confirmed") and state.get("pending_file_data"):
            pending = state["pending_file_data"]
            filename = pending.get("filename", "output.txt")
            content = pending.get("code", "")
            result = create_file(filename, content)

            files = list(state.get("files_created") or []) + [result["filepath"]]
            lang = pending.get("language", "")
            code_block = f"```{lang}\n{content}\n```" if content else ""
            ai_msg = AIMessage(
                content=f"Done! I've created `{filename}` in the output folder."
            )

            return {
                **state,
                "action_taken": f"Created file: output/{filename}",
                "output": (
                    f"✅ **File created:** `output/{filename}`\n\n"
                    + (f"{code_block}" if code_block else "")
                ),
                "files_created": files,
                "messages": list(state.get("messages") or []) + [ai_msg],
                "confirmation_required": False,
                "confirmed": False,
                "pending_file_data": {},
                "processing_steps": _steps(state) + ["File written to output/"],
            }

        # ── Stage the operation and request confirmation ───────────────────
        if intent == "write_code":
            prompt = f"""Generate code for this request and respond ONLY with valid JSON.

Request: "{user_input}"

JSON schema:
{{
  "filename": "<filename with extension>",
  "language": "<language name for syntax highlighting>",
  "code": "<complete, runnable code>",
  "description": "<one-line description>"
}}"""
            result = _call_llm_json(prompt)
            if not result.get("filename"):
                result["filename"] = extract_filename(user_input, "generated_code.py")
            if not result.get("code"):
                result["code"] = f"# Code generated from: {user_input}\n"

        else:  # create_file
            # Extract filename / folder name from request
            filename = extract_filename(user_input, "new_file.txt")
            result = {"filename": filename, "code": "", "language": "", "description": "Empty file"}

        lang = result.get("language", "")
        code_preview = result.get("code", "")[:800]
        confirmation_msg = (
            f"Ready to create **`output/{result['filename']}`**\n\n"
            + (f"```{lang}\n{code_preview}\n```" if code_preview else "")
        )

        return {
            **state,
            "confirmation_required": True,
            "confirmation_message": confirmation_msg,
            "pending_file_data": result,
            "action_taken": f"Awaiting confirmation: create {result['filename']}",
            "output": confirmation_msg,
            "processing_steps": _steps(state) + ["Awaiting user confirmation"],
        }

    # ── Node: handle_rag ──────────────────────────────────────────────────────

    def handle_rag(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        context = rag.get_context(user_input, n=3)

        recent = (state.get("messages") or [])[-6:]
        history = "\n".join(f"{m.type.upper()}: {m.content}" for m in recent)

        prompt = f"""You are a knowledgeable and friendly sales assistant for **AutoStream** — an AI-powered automated video editing SaaS platform.

Answer the user's question ACCURATELY using the knowledge base below. Do not invent information.
If relevant, gently invite the user to try AutoStream when they seem interested.

KNOWLEDGE BASE:
{context}

CONVERSATION HISTORY:
{history or "(first message)"}

USER: {user_input}

Respond in a warm, professional tone. Use markdown formatting where helpful."""

        resp = llm.invoke([HumanMessage(content=prompt)])

        ai_msg = AIMessage(content=resp.content)

        return {
            **state,
            "retrieved_context": context,
            "action_taken": "RAG retrieval from AutoStream knowledge base",
            "output": resp.content,
            "messages": list(state.get("messages") or []) + [ai_msg],
            "processing_steps": _steps(state) + ["Knowledge base retrieved", "Response generated"],
        }

    # ── Node: handle_lead ─────────────────────────────────────────────────────

    def handle_lead(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        lead_stage = state.get("lead_stage", "none")
        lead_data = dict(state.get("lead_data") or {})
        msgs = list(state.get("messages") or [])

        # ── Start qualification ────────────────────────────────────────────
        if lead_stage in ("none", "complete"):
            response = (
                "That's awesome — I'd love to get you started with **AutoStream Pro**! 🚀\n\n"
                "I just need a few quick details.\n\n"
                "First, what's your **name**?"
            )
            return {
                **state,
                "lead_stage": "ask_name",
                "lead_data": {},
                "action_taken": "Lead qualification started",
                "output": response,
                "messages": msgs + [AIMessage(content=response)],
                "processing_steps": _steps(state) + ["High-intent detected", "Lead qualification started"],
            }

        elif lead_stage == "ask_name":
            name = user_input.strip().title()
            lead_data["name"] = name
            response = (
                f"Great to meet you, **{name}**! 👋\n\n"
                "What's your **email address**? I'll use it to set up your account."
            )
            return {
                **state,
                "lead_stage": "ask_email",
                "lead_data": lead_data,
                "action_taken": f"Collected name: {name}",
                "output": response,
                "messages": msgs + [AIMessage(content=response)],
                "processing_steps": _steps(state) + [f"Name collected: {name}"],
            }

        elif lead_stage == "ask_email":
            email = extract_email(user_input)
            lead_data["email"] = email
            response = (
                f"Perfect! And which platform do you primarily create content for?\n\n"
                "*(e.g. YouTube, Instagram, TikTok, LinkedIn…)*"
            )
            return {
                **state,
                "lead_stage": "ask_platform",
                "lead_data": lead_data,
                "action_taken": f"Collected email: {email}",
                "output": response,
                "messages": msgs + [AIMessage(content=response)],
                "processing_steps": _steps(state) + [f"Email collected: {email}"],
            }

        elif lead_stage == "ask_platform":
            platform = user_input.strip()
            lead_data["platform"] = platform

            # ── Call the required mock API ─────────────────────────────────
            result = mock_lead_capture(
                lead_data["name"], lead_data["email"], platform
            )

            response = (
                f"🎉 **You're all set, {lead_data['name']}!**\n\n"
                f"Here's a summary of your registration:\n"
                f"- **Name:** {lead_data['name']}\n"
                f"- **Email:** {lead_data['email']}\n"
                f"- **Platform:** {platform}\n"
                f"- **Plan:** AutoStream Pro\n"
                f"- **Lead ID:** `{result['lead_id']}`\n\n"
                f"Our team will reach out to **{lead_data['email']}** shortly. "
                f"You can also start your **free 3-day trial** immediately at autostream.io/trial 🎬"
            )

            return {
                **state,
                "lead_stage": "complete",
                "lead_data": lead_data,
                "action_taken": (
                    f"Lead captured via mock API — {lead_data['name']} "
                    f"({lead_data['email']}, {platform})"
                ),
                "output": response,
                "messages": msgs + [AIMessage(content=response)],
                "processing_steps": _steps(state) + [
                    f"Platform collected: {platform}",
                    f"mock_lead_capture() called → {result['lead_id']}",
                ],
            }

        # Fallback (shouldn't reach here)
        return {**state, "error": "Unknown lead stage", "output": "Something went wrong in lead capture."}

    # ── Node: handle_summarize ────────────────────────────────────────────────

    def handle_summarize(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        msgs = list(state.get("messages") or [])

        # Extract text to summarize using LLM
        extract_resp = llm.invoke(
            [
                SystemMessage(
                    content=(
                        "Extract ONLY the text the user wants summarized. "
                        "If no text was provided, respond with exactly: NEEDS_INPUT"
                    )
                ),
                HumanMessage(content=user_input),
            ]
        )
        extracted = extract_resp.content.strip()

        if extracted == "NEEDS_INPUT":
            response = (
                "Please provide the text you'd like me to summarize.\n\n"
                "Example: *\"Summarize: [paste your text here]\"*"
            )
            return {
                **state,
                "action_taken": "Waiting for text input",
                "output": response,
                "messages": msgs + [AIMessage(content=response)],
            }

        summary = summarize_text(extracted, llm)

        # Check if user also asked to save to a file
        save_check = llm.invoke(
            [HumanMessage(content=f"Did this request ask to save to a file? '{user_input}' Answer YES or NO only.")]
        )
        save = "YES" in save_check.content.upper()

        files_created = list(state.get("files_created") or [])
        extra = ""

        if save:
            fname = extract_filename(user_input, "summary.txt")
            result = create_file(fname, summary)
            files_created.append(result["filepath"])
            extra = f"\n\n✅ Saved to `output/{fname}`"

        response = summary + extra

        return {
            **state,
            "action_taken": "Text summarized" + (" and saved" if save else ""),
            "output": response,
            "files_created": files_created,
            "messages": msgs + [AIMessage(content=response)],
            "processing_steps": _steps(state) + ["Text summarized"],
        }

    # ── Node: handle_compound ─────────────────────────────────────────────────

    def handle_compound(state: AgentState) -> AgentState:
        """
        Handle compound commands like 'Summarize X and save to Y.txt'.

        Root-cause of the original bug: embedding large user text inside a JSON
        prompt then calling json.loads() fails silently whenever the text contains
        em-dashes, smart quotes, or newlines — giving tasks=[] and 0 executions.

        Fix: parse structure (what to do + filename) with a tiny JSON call that
        NEVER includes the raw text body, then operate on the original input
        directly for text-heavy steps.
        """
        user_input = state.get("input_text", "")
        msgs = list(state.get("messages") or [])

        output_parts: list[str] = []
        actions: list[str] = []
        files_created = list(state.get("files_created") or [])
        last_summary = ""

        # ── Step 1: Detect "summarize … and save to <file>" pattern directly ──
        # This covers the most common compound command without any JSON parsing
        # of the content body, so special characters can never break it.
        summarize_save_match = re.search(
            r'(?:summarize|summarise)(?:\s+this)?(?:\s+text)?'
            r'(?:\s+and\s+save\s+(?:it\s+)?to\s+([\w\-]+\.[\w]+))?'
            r'[\s:]+(.+)',
            user_input,
            re.I | re.DOTALL,
        )

        if summarize_save_match:
            # Extract filename from the "save to X.txt" part
            fname_inline = summarize_save_match.group(1)  # may be None
            body = summarize_save_match.group(2).strip()

            # Also try regex on the full string for "save to X.txt" anywhere
            save_match = re.search(
                r'save\s+(?:it\s+)?to\s+([\w\-]+\.[\w]+)', user_input, re.I
            )
            filename = (
                fname_inline
                or (save_match.group(1) if save_match else None)
                or extract_filename(user_input, "summary.txt")
            )

            # Strip "and save to filename.txt" from the text body if present
            clean_body = re.sub(
                r'\s+and\s+save\s+(?:it\s+)?to\s+[\w\-]+\.[\w]+', '', body, flags=re.I
            ).strip()

            # Summarize
            last_summary = summarize_text(clean_body, llm)
            output_parts.append(f"**Summary:**\n{last_summary}")
            actions.append("Summarized text")

            # Save
            r = create_file(filename, last_summary)
            files_created.append(r["filepath"])
            output_parts.append(f"✅ Saved to `output/{filename}`")
            actions.append(f"Saved {filename}")

        else:
            # ── Step 2: Generic compound — ask LLM only for structure, NOT content
            # We only ask for task types + filenames/descriptions (no text bodies).
            parse_prompt = (
                f'The user sent a compound command with multiple actions.\n'
                f'Message: "{user_input[:300]}"\n\n'
                f'List ONLY the action types and filenames/descriptions needed.\n'
                f'Do NOT include any content body in the JSON.\n'
                f'Respond with JSON:\n'
                f'{{"tasks": ['
                f'{{"type": "generate_code", "description": "...", "filename": "..."}}, '
                f'{{"type": "create_file", "filename": "...", "content": "short content only"}}'
                f']}}'
            )

            result = _call_llm_json(parse_prompt)
            tasks = result.get("tasks", [])

            for task in tasks:
                t = task.get("type", "")

                if t == "generate_code":
                    code_resp = _call_llm_json(
                        f'Generate code for: "{task.get("description", user_input[:200])}". '
                        f'Respond with JSON: {{"filename": "...", "language": "...", "code": "..."}}'
                    )
                    fname = code_resp.get("filename", extract_filename(user_input))
                    code = code_resp.get("code", "# generated\n")
                    r = create_file(fname, code)
                    files_created.append(r["filepath"])
                    lang = code_resp.get("language", "")
                    output_parts.append(
                        f"**Generated `output/{fname}`:**\n```{lang}\n{code[:600]}\n```"
                    )
                    actions.append(f"Generated code → {fname}")

                elif t == "create_file":
                    fname = task.get("filename", "new_file.txt")
                    content = task.get("content", "")
                    r = create_file(fname, content)
                    files_created.append(r["filepath"])
                    output_parts.append(f"✅ Created `output/{fname}`")
                    actions.append(f"Created {fname}")

            if not output_parts:
                output_parts = ["Could not parse compound command. Try: 'Summarize [text] and save to file.txt'"]

        combined = "\n\n---\n\n".join(output_parts)
        action_str = " → ".join(actions) if actions else "Compound command"
        total_tasks = len(actions)

        return {
            **state,
            "action_taken": action_str,
            "output": combined,
            "files_created": files_created,
            "messages": msgs + [AIMessage(content=combined)],
            "processing_steps": _steps(state) + [f"Executed {total_tasks} compound tasks"],
        }

    # ── Node: handle_general_chat ─────────────────────────────────────────────

    def handle_general_chat(state: AgentState) -> AgentState:
        user_input = state.get("input_text", "")
        msgs = list(state.get("messages") or [])

        system = SystemMessage(
            content=(
                "You are a versatile, helpful AI assistant. You can:\n"
                "• Help with local file and code operations\n"
                "• Answer questions about AutoStream (automated video editing SaaS)\n"
                "• Have natural conversations\n\n"
                "Be concise, friendly, and helpful."
            )
        )
        history = msgs[-8:]  # last 4 exchanges
        resp = llm.invoke([system] + history + [HumanMessage(content=user_input)])

        return {
            **state,
            "action_taken": "General chat",
            "output": resp.content,
            "messages": msgs + [AIMessage(content=resp.content)],
            "processing_steps": _steps(state) + ["Chat response generated"],
        }

    # ── Router ────────────────────────────────────────────────────────────────

    def route_intent(
        state: AgentState,
    ) -> Literal[
        "handle_file_ops",
        "handle_rag",
        "handle_lead",
        "handle_summarize",
        "handle_compound",
        "handle_general_chat",
    ]:
        lead_stage = state.get("lead_stage", "none")
        if lead_stage in ("ask_name", "ask_email", "ask_platform"):
            return "handle_lead"

        routing = {
            "create_file": "handle_file_ops",
            "write_code": "handle_file_ops",
            "summarize_text": "handle_summarize",
            "product_inquiry": "handle_rag",
            "high_intent_lead": "handle_lead",
            "compound_command": "handle_compound",
        }
        return routing.get(state.get("intent", ""), "handle_general_chat")

    # ── Assemble graph ────────────────────────────────────────────────────────

    workflow = StateGraph(AgentState)

    workflow.add_node("classify_intent", classify_intent)
    workflow.add_node("handle_file_ops", handle_file_ops)
    workflow.add_node("handle_rag", handle_rag)
    workflow.add_node("handle_lead", handle_lead)
    workflow.add_node("handle_summarize", handle_summarize)
    workflow.add_node("handle_compound", handle_compound)
    workflow.add_node("handle_general_chat", handle_general_chat)

    workflow.set_entry_point("classify_intent")

    workflow.add_conditional_edges(
        "classify_intent",
        route_intent,
        {
            "handle_file_ops": "handle_file_ops",
            "handle_rag": "handle_rag",
            "handle_lead": "handle_lead",
            "handle_summarize": "handle_summarize",
            "handle_compound": "handle_compound",
            "handle_general_chat": "handle_general_chat",
        },
    )

    for node in (
        "handle_file_ops",
        "handle_rag",
        "handle_lead",
        "handle_summarize",
        "handle_compound",
        "handle_general_chat",
    ):
        workflow.add_edge(node, END)

    return workflow.compile(checkpointer=MemorySaver())
