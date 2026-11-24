"""Word-level time map: new avatar line -> the avatar's lip movements in the source clip."""
import numpy as np, subprocess, json, re, os
SRCW = "../out/avatar_src_words.json"
if not os.path.exists(SRCW):
    from faster_whisper import WhisperModel
    T0 = 183.0
    pcm = subprocess.run(["ffmpeg","-v","error","-ss",str(T0),"-t","10.5","-i","../src/orig.mp4","-vn","-ac","1","-ar","16000","-f","f32le","-"],capture_output=True).stdout
    m = WhisperModel("small.en", device="cpu", compute_type="int8")
    segs, _ = m.transcribe(np.frombuffer(pcm, np.float32), word_timestamps=True, vad_filter=False)
    json.dump([(w.word.strip(), float(T0 + w.start), float(T0 + w.end)) for s in segs for w in s.words], open(SRCW, "w"))
src = json.load(open(SRCW))
tl = json.load(open("../out/timeline.json"))
k = [s for s in tl["scenes"] if s["id"] == "kiosk"][0]
av = [s for s in k["sentences"] if s["role"] == "avatar"][0]
norm = lambda w: re.sub(r"[^a-z]", "", w.lower())
i0 = next(i for i, w in enumerate(src) if norm(w[0]).startswith("congrat"))
srcw, anchors, j = src[i0:], [], 0
for w in av["words"]:
    n = norm(w["w"])
    for jj in range(j, min(j + 4, len(srcw))):
        if norm(srcw[jj][0]) == n or (n and norm(srcw[jj][0]).startswith(n[:4])):
            anchors.append([w["t"], round(srcw[jj][1], 3)]); j = jj + 1; break
anchors.append([av["end"], round(srcw[-1][2] + 0.15, 3)])
mono = [anchors[0]]
for a in anchors[1:]:
    if a[0] > mono[-1][0] + 0.05 and a[1] > mono[-1][1] + 0.03:
        mono.append(a)
json.dump({"anchors": mono, "src0": 179.0, "src1": 201.6, "fps": 30, "scene": [k["start"], k["end"]]}, open("../out/avatar_map.json", "w"))
print("kiosk scene", k["start"], k["end"], "| avatar speech", av["start"], av["end"], "|", len(mono), "anchors | src speech", mono[0][1], mono[-1][1])
