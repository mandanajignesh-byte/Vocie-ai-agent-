"""Upscale the kiosk avatar clip from the original video: 4x super-resolution on the
whole frame plus GFPGAN face restoration blended over the face.
usage: avatar_sr.py <t0> <t1> <outdir> [threads] [part k/n]"""
import os, subprocess, sys
import cv2, numpy as np, torch
from spandrel import ModelLoader

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(HERE, "..", "src", "orig.mp4")
X, Y, W, H = 435, 46, 218, 332         # avatar screen inside the kiosk bezel (source pixels)
FPS = 30

def load(name):
    m = ModelLoader().load_from_file(os.path.join(HERE, "weights", name)); m.eval(); return m

def run(model, bgr):
    t = torch.from_numpy(bgr[:, :, ::-1].copy()).permute(2, 0, 1).float().div(255).unsqueeze(0)
    with torch.no_grad():
        o = model(t)
    o = o.squeeze(0).clamp(0, 1).permute(1, 2, 0).numpy()[:, :, ::-1]
    return (o * 255 + 0.5).astype(np.uint8)

def frames(t0, t1):
    n = int(round((t1 - t0) * FPS))
    p = subprocess.Popen(["ffmpeg", "-v", "error", "-ss", f"{t0:.4f}", "-i", SRC, "-frames:v", str(n),
                          "-vf", f"crop={W}:{H}:{X}:{Y},hqdn3d=1.5:1.5:4:4", "-f", "rawvideo", "-pix_fmt", "bgr24", "-"],
                         stdout=subprocess.PIPE)
    for i in range(n):
        b = p.stdout.read(W * H * 3)
        if len(b) < W * H * 3:
            break
        yield i, np.frombuffer(b, np.uint8).reshape(H, W, 3)

# FFHQ-style framing GFPGAN expects: eye midpoint at (256,240) of 512, inter-eye distance ~126px
EYES = ((91.5, 148.0), (134.0, 148.0))   # measured in the source crop
def face_box():
    (lx, ly), (rx, ry) = EYES
    s = 126.0 / (rx - lx)                # source px -> 512 face px
    side = 512.0 / s
    cx, cy = (lx + rx) / 2, (ly + ry) / 2
    return cx - 256 / s, cy - 240 / s, side

def main():
    t0, t1, out = float(sys.argv[1]), float(sys.argv[2]), sys.argv[3]
    torch.set_num_threads(int(sys.argv[4]) if len(sys.argv) > 4 else 4)
    k, n = (map(int, sys.argv[5].split("/")) if len(sys.argv) > 5 else (0, 1))
    os.makedirs(out, exist_ok=True)
    sr, gfp = load("realesr-general-x4v3.pth"), load("GFPGANv1.4.pth")
    fx, fy, side = face_box()
    S = 4
    x0, y0, sd = int(round(fx * S)), int(round(fy * S)), int(round(side * S))
    # soft elliptical mask so the restored face melts into the upscaled frame
    m = np.zeros((sd, sd), np.float32)
    cv2.ellipse(m, (sd // 2, int(sd * 0.50)), (int(sd * 0.36), int(sd * 0.44)), 0, 0, 360, 1.0, -1)
    m = cv2.GaussianBlur(m, (0, 0), sd * 0.06)[:, :, None]
    for i, f in frames(t0, t1):
        if i % n != k:
            continue
        dst = os.path.join(out, f"a_{i:04d}.jpg")
        if os.path.exists(dst):
            continue
        up = run(sr, f)                                              # 872 x 1328
        pad = cv2.copyMakeBorder(up, sd, sd, sd, sd, cv2.BORDER_REFLECT)
        crop = pad[y0 + sd:y0 + 2 * sd, x0 + sd:x0 + 2 * sd]
        face = run(gfp, cv2.resize(crop, (512, 512), interpolation=cv2.INTER_AREA))
        face = cv2.resize(face, (sd, sd), interpolation=cv2.INTER_LANCZOS4)
        # keep GFPGAN's detail (luma) but the source's own colours, so eye/skin tone don't drift
        fl, cl = cv2.cvtColor(face, cv2.COLOR_BGR2LAB).astype(np.float32), cv2.cvtColor(crop, cv2.COLOR_BGR2LAB).astype(np.float32)
        fl[:, :, 1:] = 0.25 * fl[:, :, 1:] + 0.75 * cv2.GaussianBlur(cl[:, :, 1:], (0, 0), 2.0)
        face = cv2.cvtColor(np.clip(fl, 0, 255).astype(np.uint8), cv2.COLOR_LAB2BGR)
        blend = (face * m + crop * (1 - m)).astype(np.uint8)
        pad[y0 + sd:y0 + 2 * sd, x0 + sd:x0 + 2 * sd] = blend
        res = pad[sd:-sd, sd:-sd]
        cv2.imwrite(dst, res, [cv2.IMWRITE_JPEG_QUALITY, 96])
    print("done", k, n)

main()
