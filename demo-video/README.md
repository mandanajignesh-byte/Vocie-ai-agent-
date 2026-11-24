# Chat360 – Agentic AI for Insurance (event demo video)

HD rebuild of the insurance demo reel. Everything on screen is HTML/SVG rendered
frame-by-frame at 3840×2160, so text and phone mockups stay sharp on a TV.

## Layout

| Path | What it is |
| --- | --- |
| `build/script.py` | Narration script: captions and the spoken text for each scene |
| `build/vo.py` | Synthesises the voiceover, masters it, writes `out/vo.wav` + `out/timeline.json` |
| `build/scenes.js` | Scene markup. `data-at="c3+0.5"` = reveal 0.5 s after caption 3 of that scene is spoken |
| `build/main.js` | Builds one GSAP timeline from `timeline.json`; `window.seek(t)` renders any instant |
| `build/render.js` | Frame-accurate 4K render of a frame range (Playwright → ffmpeg) |
| `build/qa.js` | Checks every caption is centred and never overlaps content or the logo |
| `sr/avatar_sr.py` | Upscales the kiosk avatar clip taken from the original low-res video |
| `sr/natural.py` | Blends the upscaled avatar back toward the source footage + grain so it doesn't look AI-restored |

## Rebuild

Needs Node, Python 3, ffmpeg, Playwright with Chromium, and
`pip install edge-tts numpy faster-whisper opencv-python-headless torch spandrel`.

```bash
cd build && npm install
python3 vo.py            # voiceover + timings (VO_VOICE / VO_RATE env vars override the voice)
python3 avatar_map.py    # lip-sync map for the kiosk avatar (needs ../src/orig.mp4)
node mkassets.js         # icons, QR codes and timings -> assets/data.js
node qa.js               # layout checks
./finish.sh v2           # 4K render in 4 parallel segments, mux voiceover, 1080p copy
```

The avatar frames come from `sr/avatar_sr.py 179.0 201.6 frames` run against the
original video (`src/orig.mp4`) with the Real-ESRGAN `realesr-general-x4v3` and
`GFPGANv1.4` weights in `sr/weights/`, followed by `sr/natural.py frames_nat 0.28 0.5`. Swap in a native HD avatar clip if one is available.

To change wording, edit `script.py` (caption text and spoken text are separate, e.g.
`₹45,000` is spoken as "forty-five thousand rupees"), then rerun from `vo.py`.
Scene timings follow the voiceover automatically.
