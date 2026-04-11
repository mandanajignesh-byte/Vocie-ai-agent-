"""
Speech-to-Text module using Groq's Whisper API.

Hardware Note: We use Groq's hosted Whisper (whisper-large-v3) via API instead of
running Whisper locally because Groq's inference is 10–20x faster than local CPU
execution and provides the same accuracy as the full large-v3 model. On typical
laptop hardware, local whisper-large-v3 transcription of a 30s clip takes ~45s;
via Groq it completes in under 2s. An OpenAI fallback is also provided.
"""

from __future__ import annotations

import io
import time
import numpy as np
from typing import Optional


# ── Microphone recording ───────────────────────────────────────────────────────

def record_audio(duration: int = 5, sample_rate: int = 16_000) -> bytes:
    """Record audio from the default microphone and return raw WAV bytes."""
    try:
        import sounddevice as sd
        import scipy.io.wavfile as wav_io

        recording = sd.rec(
            int(duration * sample_rate),
            samplerate=sample_rate,
            channels=1,
            dtype=np.int16,
        )
        sd.wait()

        buf = io.BytesIO()
        wav_io.write(buf, sample_rate, recording)
        return buf.getvalue()
    except ImportError:
        raise RuntimeError(
            "sounddevice / scipy not installed. Run: pip install sounddevice scipy"
        )


# ── Transcription ─────────────────────────────────────────────────────────────

def transcribe(audio_bytes: bytes, filename: str = "audio.wav") -> dict:
    """
    Transcribe audio bytes → text.

    Returns a dict with keys:
      text        – transcribed string (empty on failure)
      language    – detected language code
      duration_s  – audio duration in seconds (if available)
      latency_ms  – wall-clock ms taken for the API call
      model       – model name used
      success     – bool
      error       – error message (only on failure)
    """
    from config import GROQ_API_KEY, OPENAI_API_KEY, STT_MODEL

    if not audio_bytes:
        return _error_result("No audio data provided.")

    # ── Try Groq first ────────────────────────────────────────────────────────
    if GROQ_API_KEY:
        return _transcribe_groq(audio_bytes, filename, GROQ_API_KEY, STT_MODEL)

    # ── Fallback: OpenAI Whisper ──────────────────────────────────────────────
    if OPENAI_API_KEY:
        return _transcribe_openai(audio_bytes, filename, OPENAI_API_KEY)

    return _error_result(
        "No API key found. Set GROQ_API_KEY (or OPENAI_API_KEY) in your .env file."
    )


def _transcribe_groq(
    audio_bytes: bytes, filename: str, api_key: str, model: str
) -> dict:
    try:
        from groq import Groq

        client = Groq(api_key=api_key)
        t0 = time.perf_counter()

        resp = client.audio.transcriptions.create(
            file=(filename, audio_bytes),
            model=model,
            response_format="verbose_json",
            temperature=0.0,
        )
        latency = int((time.perf_counter() - t0) * 1000)

        return {
            "text": resp.text.strip(),
            "language": getattr(resp, "language", "en"),
            "duration_s": getattr(resp, "duration", None),
            "latency_ms": latency,
            "model": model,
            "provider": "Groq",
            "success": True,
        }
    except Exception as exc:
        return _error_result(f"Groq STT error: {exc}")


def _transcribe_openai(audio_bytes: bytes, filename: str, api_key: str) -> dict:
    try:
        from openai import OpenAI

        client = OpenAI(api_key=api_key)
        t0 = time.perf_counter()

        resp = client.audio.transcriptions.create(
            file=(filename, io.BytesIO(audio_bytes)),
            model="whisper-1",
            response_format="verbose_json",
        )
        latency = int((time.perf_counter() - t0) * 1000)

        return {
            "text": resp.text.strip(),
            "language": getattr(resp, "language", "en"),
            "duration_s": getattr(resp, "duration", None),
            "latency_ms": latency,
            "model": "whisper-1",
            "provider": "OpenAI",
            "success": True,
        }
    except Exception as exc:
        return _error_result(f"OpenAI STT error: {exc}")


def _error_result(msg: str) -> dict:
    return {
        "text": "",
        "language": None,
        "duration_s": None,
        "latency_ms": None,
        "model": None,
        "provider": None,
        "success": False,
        "error": msg,
    }
