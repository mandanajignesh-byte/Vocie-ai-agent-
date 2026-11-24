"""Tone down the AI-restored look of the avatar frames: blend the restored frame back
toward a plain upscale of the source footage and add fine photographic grain.
usage: natural.py <outdir> [face_keep] [body_keep] [frame indices...]"""
import os, subprocess, sys
import cv2, numpy as np
HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "orig.mp4")
X, Y, W, H, FPS, T0, T1 = 435, 46, 218, 332, 30, 179.0, 201.6
EYES = ((91.5, 148.0), (134.0, 148.0))

def source_frames():
    n = int(round((T1 - T0) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{T0:.4f}", "-i", SRC, "-frames:v", str(n),
                          "-vf", f"crop={W}:{H}:{X}:{Y},hqdn3d=2:2:5:5", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"], stdout=subprocess.PIPE)
    for i in range(n):
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3: break
        yield i, np.frombuffer(b, np.uint8).reshape(H, W, 3)

def main():
    out = sys.argv[1]; face_keep = float(sys.argv[2]) if len(sys.argv) > 2 else 0.4
    body_keep = float(sys.argv[3]) if len(sys.argv) > 3 else 0.6
    only = set(map(int, sys.argv[4:])); os.makedirs(out, exist_ok=True)
    S = 4; (lx, ly), (rx, ry) = EYES; s = 126.0 / (rx - lx); side = 512.0 / s
    sd = int(round(side * S)); x0 = int(round(((lx + rx) / 2 - 256 / s) * S)); y0 = int(round(((ly + ry) / 2 - 240 / s) * S))
    m = np.zeros((sd, sd), np.float32)
    cv2.ellipse(m, (sd // 2, int(sd * 0.50)), (int(sd * 0.36), int(sd * 0.44)), 0, 0, 360, 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), sd * 0.06)
    keep = np.full((H * S, W * S), body_keep, np.float32)          # how much of the AI-restored frame to keep
    ys, xs = slice(max(0, y0), min(H * S, y0 + sd)), slice(max(0, x0), min(W * S, x0 + sd))
    mm = m[ys.start - y0:ys.stop - y0, xs.start - x0:xs.stop - x0]
    keep[ys, xs] = keep[ys, xs] * (1 - mm) + face_keep * mm
    keep = keep[:, :, None]
    for i, f in source_frames():
        if only and i not in only: continue
        ai = cv2.imread(os.path.join(HERE, "frames", f"a_{i:04d}.jpg")).astype(np.float32)
        base = cv2.resize(f, (W * S, H * S), interpolation=cv2.INTER_CUBIC).astype(np.float32)
        base = base + 0.6 * (base - cv2.GaussianBlur(base, (0, 0), 3.0))      # gentle unsharp on the plain upscale
        res = ai * keep + base * (1 - keep)
        rng = np.random.default_rng(1000 + i)                                  # fine luma grain, new every frame
        g = cv2.GaussianBlur(rng.normal(0, 1, (H * S, W * S)).astype(np.float32), (0, 0), 0.9) * 5.0
        res = np.clip(res + g[:, :, None], 0, 255).astype(np.uint8)
        cv2.imwrite(os.path.join(out, f"a_{i:04d}.jpg"), res, [cv2.IMWRITE_JPEG_QUALITY, 95])
main()
