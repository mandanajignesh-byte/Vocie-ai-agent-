"""Synthesise the narration, assemble it with pacing gaps, master it, and emit
timeline.json (scene + caption timings) that drives the animation."""
import asyncio, hashlib, json, os, subprocess, sys
import numpy as np
import certifi
if os.path.exists("/root/.ccr/ca-bundle.crt"):  # cloud-session proxy CA
    certifi.where = lambda: "/root/.ccr/ca-bundle.crt"
import edge_tts
from script import SCENES

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.join(HERE, "..", "out"); CACHE = os.path.join(HERE, "..", "vo_cache")
os.makedirs(OUT, exist_ok=True); os.makedirs(CACHE, exist_ok=True)
PROXY = os.environ.get("HTTPS_PROXY") or os.environ.get("https_proxy")
SR = 48000

VOICES = {
    "narrator": dict(voice=os.environ.get("VO_VOICE", "hi-IN-SwaraNeural"), rate=os.environ.get("VO_RATE", "+8%"), pitch="+0Hz"),
    "avatar":   dict(voice="en-IN-NeerjaExpressiveNeural", rate="+14%", pitch="-4Hz"),
}
START_PAD = 0.85     # logo animates in before the first word
SENT_GAP = 0.36      # pause between sentences inside a scene
SCENE_GAP = 1.25     # pause across a scene change
END_HOLD = 3.6       # end card hold after last word
SENT_GAP_OVERRIDE = {"words": 0.34}                       # tighter beat between the four words
GAP_OVERRIDE = {"intro": 0.9, "words": 1.0, "cta": 1.3}   # pause after these scenes


async def synth(text, voice, rate, pitch):
    key = hashlib.sha1(f"{voice}|{rate}|{pitch}|{text}".encode()).hexdigest()[:16]
    mp3, meta = os.path.join(CACHE, key + ".mp3"), os.path.join(CACHE, key + ".json")
    if not (os.path.exists(mp3) and os.path.exists(meta)):
        for attempt in range(4):
            try:
                c = edge_tts.Communicate(text, voice, rate=rate, pitch=pitch, boundary="WordBoundary", proxy=PROXY)
                words, audio = [], b""
                async for ch in c.stream():
                    if ch["type"] == "audio":
                        audio += ch["data"]
                    elif ch["type"] == "WordBoundary":
                        words.append(dict(t=ch["offset"] / 1e7, d=ch["duration"] / 1e7, text=ch["text"]))
                if not audio:
                    raise RuntimeError("no audio")
                open(mp3, "wb").write(audio); json.dump(words, open(meta, "w"))
                break
            except Exception as e:  # network hiccup: back off and retry
                print("retry", attempt, e, file=sys.stderr); await asyncio.sleep(2 * (attempt + 1))
        else:
            raise SystemExit("TTS failed for: " + text)
    pcm = subprocess.run(["ffmpeg", "-v", "error", "-i", mp3, "-ac", "1", "-ar", str(SR), "-f", "f32le", "-"],
                         capture_output=True, check=True).stdout
    return np.frombuffer(pcm, np.float32).copy(), json.load(open(meta))


def trim(a):
    """Trim leading/trailing silence, return audio and the lead offset removed."""
    win = int(SR * 0.01)
    n = len(a) // win
    rms = np.sqrt((a[:n * win].reshape(n, win) ** 2).mean(axis=1) + 1e-12)
    loud = np.where(rms > 10 ** (-42 / 20))[0]
    s = max(0, loud[0] * win - int(0.03 * SR)); e = min(len(a), (loud[-1] + 1) * win + int(0.09 * SR))
    out = a[s:e].copy()
    f = int(0.008 * SR)
    out[:f] *= np.linspace(0, 1, f); out[-f:] *= np.linspace(1, 0, f)
    return out, s / SR


def chunk_starts(chunks, words):
    """Time (within utterance) at which each caption chunk's first word is spoken."""
    spoken = " ".join(c[1] for c in chunks).lower()
    bounds, pos = [], 0
    for c in chunks:
        bounds.append(pos); pos += len(c[1]) + 1
    cur, starts = 0, [None] * len(chunks)
    for w in words:
        tok = w["text"].lower().strip()
        i = spoken.find(tok, cur)
        if i < 0 or i - cur > 40:
            continue
        ci = max(k for k, b in enumerate(bounds) if b <= i)
        if starts[ci] is None:
            starts[ci] = w["t"]
        cur = i + len(tok)
    starts[0] = words[0]["t"] if words else 0.0
    for k in range(1, len(starts)):
        if starts[k] is None:
            raise SystemExit(f"could not align chunk: {chunks[k][1]}")
    return starts


async def main():
    track, t = [], START_PAD
    timeline = {"fps": 30, "scenes": []}
    segs = [np.zeros(int(START_PAD * SR), np.float32)]
    for si, (sid, sentences) in enumerate(SCENES):
        scene = {"id": sid, "caps": [], "sentences": []}
        for ki, sent in enumerate(sentences):
            role = "narrator"
            if isinstance(sent, dict):
                role, sent = sent["voice"], sent["chunks"]
            v = VOICES[role]
            audio, words = await synth(" ".join(c[1] for c in sent), v["voice"], v["rate"], v["pitch"])
            audio, lead = trim(audio)
            if role == "avatar":
                audio = audio * 0.92
            starts = [max(0.0, s - lead) for s in chunk_starts(sent, words)]
            dur = len(audio) / SR
            for ci, (html, _) in enumerate(sent):
                cs = t + starts[ci]
                ce = t + (starts[ci + 1] if ci + 1 < len(sent) else dur)
                if html == "+":                      # continuation: previous caption stays up
                    scene["caps"][-1]["end"] = round(ce, 3)
                    continue
                scene["caps"].append({"html": html, "start": round(cs, 3), "end": round(ce, 3), "role": role})
            scene["sentences"].append({"start": round(t, 3), "end": round(t + dur, 3), "role": role,
                                       "words": [{"t": round(t + w["t"] - lead, 3), "d": round(w["d"], 3), "w": w["text"]} for w in words]})
            segs.append(audio); t += dur
            last_in_scene = ki == len(sentences) - 1
            last = last_in_scene and si == len(SCENES) - 1
            gap = END_HOLD if last else (GAP_OVERRIDE.get(sid, SCENE_GAP) if last_in_scene else SENT_GAP_OVERRIDE.get(sid, SENT_GAP))
            segs.append(np.zeros(int(gap * SR), np.float32)); t += gap
        timeline["scenes"].append(scene)
    # scene windows: each scene begins a beat before its first word
    for i, sc in enumerate(timeline["scenes"]):
        sc["start"] = 0.0 if i == 0 else round(sc["caps"][0]["start"] - 0.62, 3)
    for i, sc in enumerate(timeline["scenes"]):
        sc["end"] = timeline["scenes"][i + 1]["start"] if i + 1 < len(timeline["scenes"]) else round(t, 3)
    full = np.concatenate(segs)
    timeline["duration"] = round(len(full) / SR, 3)
    raw = os.path.join(OUT, "vo_raw.wav")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-f", "f32le", "-ar", str(SR), "-ac", "1", "-i", "-", raw],
                   input=full.tobytes(), check=True)
    # broadcast-style polish: clean lows, a little warmth + presence, gentle compression, loudness normalise
    chain = ("highpass=f=70,equalizer=f=170:t=q:w=0.9:g=1.6,equalizer=f=3200:t=q:w=1.1:g=1.4,"
             "equalizer=f=9500:t=q:w=1.4:g=1.2,acompressor=threshold=-21dB:ratio=2.4:attack=6:release=140:makeup=1.5,"
             "loudnorm=I=-16:TP=-1.5:LRA=8,alimiter=limit=0.84,aresample=48000")
    subprocess.run(["ffmpeg", "-v", "error", "-y", "-i", raw, "-af", chain, "-ac", "2", "-c:a", "pcm_s16le",
                    os.path.join(OUT, "vo.wav")], check=True)
    json.dump(timeline, open(os.path.join(OUT, "timeline.json"), "w"), ensure_ascii=False, indent=1)
    print("duration %.1fs" % timeline["duration"])
    for sc in timeline["scenes"]:
        print("%-10s %6.1f -> %6.1f  (%d caps)" % (sc["id"], sc["start"], sc["end"], len(sc["caps"])))

asyncio.run(main())
