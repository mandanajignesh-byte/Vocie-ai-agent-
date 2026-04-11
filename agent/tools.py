"""
Tool implementations for the Voice AI Agent.

All file I/O is restricted to the output/ directory to satisfy the safety
constraint: all writes go to output/ to avoid accidental system overwrites.
"""

from __future__ import annotations

import json
import re
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from config import OUTPUT_DIR


# ── File Operations ───────────────────────────────────────────────────────────

def create_file(filename: str, content: str = "") -> Dict[str, Any]:
    """Create a file inside output/. Returns result dict."""
    # Safety: strip any path traversal
    safe_name = Path(filename).name
    filepath = OUTPUT_DIR / safe_name
    filepath.parent.mkdir(parents=True, exist_ok=True)
    filepath.write_text(content, encoding="utf-8")

    return {
        "success": True,
        "filepath": str(filepath),
        "filename": safe_name,
        "size_bytes": filepath.stat().st_size,
        "message": f"Created `output/{safe_name}`",
    }


def create_folder(folder_name: str) -> Dict[str, Any]:
    """Create a folder inside output/."""
    safe_name = Path(folder_name).name
    folder = OUTPUT_DIR / safe_name
    folder.mkdir(parents=True, exist_ok=True)
    return {
        "success": True,
        "path": str(folder),
        "message": f"Created folder `output/{safe_name}`",
    }


# ── Code Generation ───────────────────────────────────────────────────────────

def write_code_to_file(filename: str, code: str) -> Dict[str, Any]:
    """Alias for create_file — semantics make intent clearer in logs."""
    return create_file(filename, code)


# ── Text Summarization ────────────────────────────────────────────────────────

def summarize_text(text: str, llm) -> str:
    """Summarize text using the provided LLM instance."""
    from langchain_core.messages import HumanMessage, SystemMessage

    resp = llm.invoke(
        [
            SystemMessage(
                content=(
                    "You are a precise text summarizer. "
                    "Provide a clear summary using bullet points. "
                    "Be concise but comprehensive."
                )
            ),
            HumanMessage(content=f"Summarize the following text:\n\n{text}"),
        ]
    )
    return resp.content.strip()


# ── Lead Capture ──────────────────────────────────────────────────────────────

def mock_lead_capture(name: str, email: str, platform: str) -> Dict[str, Any]:
    """
    Mock CRM API call for lead capture.
    Also persists leads to output/leads.json for demo purposes.
    """
    # Required print per assignment spec
    print(f"Lead captured successfully: {name}, {email}, {platform}")

    leads_file = OUTPUT_DIR / "leads.json"
    leads: list = []
    if leads_file.exists():
        try:
            leads = json.loads(leads_file.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            leads = []

    lead_id = f"LEAD-{len(leads) + 1:04d}"
    lead = {
        "id": lead_id,
        "name": name,
        "email": email,
        "platform": platform,
        "product_interest": "AutoStream Pro",
        "captured_at": datetime.now().isoformat(),
    }
    leads.append(lead)
    leads_file.write_text(json.dumps(leads, indent=2), encoding="utf-8")

    return {
        "success": True,
        "lead_id": lead_id,
        "message": f"Lead captured successfully: {name}, {email}, {platform}",
    }


# ── Helpers ───────────────────────────────────────────────────────────────────

def extract_email(text: str) -> str:
    """Pull the first email address found in text."""
    match = re.search(r"\b[\w.%+\-]+@[\w.\-]+\.\w{2,}\b", text)
    return match.group() if match else text.strip()


def extract_filename(text: str, default: str = "output.txt") -> str:
    """Best-effort filename extraction from natural language."""
    match = re.search(r"\b([\w\-]+\.(?:py|txt|js|ts|html|css|md|json|yaml|sh))\b", text, re.I)
    return match.group(1) if match else default
