import argparse, math, os
import numpy as np
from PIL import Image, ImageOps
import torch
import imageio

from transformers import AutoImageProcessor, AutoModelForDepthEstimation

# ---- Stereo warp (horizontal DIBR-lite) ----
def warp_horizontal(img_np, depth01, disparity_px, sway_px=0.0):
    h, w, _ = img_np.shape
    x = np.arange(w, dtype=np.float32)
    y = np.arange(h, dtype=np.float32)
    xv, yv = np.meshgrid(x, y)               # xv,yv float grids
    yi = yv.astype(np.int32)                 # row indices

    # Left eye
    shiftL = (depth01 - 0.5) * disparity_px + sway_px
    src_xL = np.clip(xv - shiftL, 0, w - 1)
    x0 = np.floor(src_xL).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    t = src_xL - x0
    left = ((1 - t)[..., None] * img_np[yi, x0] + t[..., None] * img_np[yi, x1]).astype(np.uint8)

    # Right eye
    shiftR = (depth01 - 0.5) * (-disparity_px) + sway_px
    src_xR = np.clip(xv - shiftR, 0, w - 1)
    x0 = np.floor(src_xR).astype(np.int32)
    x1 = np.clip(x0 + 1, 0, w - 1)
    t = src_xR - x0
    right = ((1 - t)[..., None] * img_np[yi, x0] + t[..., None] * img_np[yi, x1]).astype(np.uint8)

    return left, right

def normalize01(a):
    a = a.astype(np.float32)
    a -= a.min()
    m = a.max()
    return a / (m + 1e-6)

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="Path to input image (jpg/png)")
    ap.add_argument("--outdir", default="out", help="Output directory")
    ap.add_argument("--model", default="depth-anything/Depth-Anything-V2-Large",
                    help="HF model id (e.g., depth-anything/Depth-Anything-V2-Large or -Small)")
    ap.add_argument("--size", type=int, default=2048, help="Output square size (TB: size x size)")
    ap.add_argument("--seconds", type=float, default=4.0, help="MP4 duration")
    ap.add_argument("--fps", type=int, default=24, help="MP4 framerate")
    ap.add_argument("--max_disp", type=float, default=16.0, help="Max disparity in px (stereo strength)")
    ap.add_argument("--invert_depth", action="store_true",
                    help="Invert depth if near/far looks reversed")
    args = ap.parse_args()

    os.makedirs(args.outdir, exist_ok=True)

    # --- Load input & portrait-fit (nice framing for faces/subjects) ---
    img = Image.open(args.input).convert("RGB")
    # Try a portrait crop (4:5) to keep the subject centered; adjust if you prefer native aspect.
    img_portrait = ImageOps.fit(img, (1280, 1600), Image.Resampling.LANCZOS)

    # --- Depth-Anything V2 (HF Transformers) ---
    device = "cuda" if torch.cuda.is_available() else "cpu"
    processor = AutoImageProcessor.from_pretrained(args.model)
    model = AutoModelForDepthEstimation.from_pretrained(args.model).to(device).eval()

    inputs = processor(images=img_portrait, return_tensors="pt").to(device)
    with torch.no_grad():
        outputs = model(**inputs)
        pred = outputs.predicted_depth  # (1,H,W) relative depth

    # Resize back to image size
    pred_resized = torch.nn.functional.interpolate(
        pred.unsqueeze(1), size=img_portrait.size[::-1], mode="bicubic", align_corners=False
    ).squeeze(1).squeeze(0).cpu().numpy()

    depth01 = normalize01(pred_resized)
    if args.invert_depth:
        depth01 = 1.0 - depth01

    # Save depth preview
    depth_png = os.path.join(args.outdir, "depth_preview.png")
    Image.fromarray((depth01 * 255).astype(np.uint8)).save(depth_png)

    # --- Stereo generation ---
    base_np = np.array(img_portrait)
    # Precompute three pairs and crossfade for a gentle parallax "breath"
    settings = [(args.max_disp * 0.65, -2.0), (args.max_disp * 0.9, 0.0), (args.max_disp * 1.1, +2.0)]
    pairs = []
    for disp, sway in settings:
        L, R = warp_horizontal(base_np, depth01, disp, sway)
        pairs.append((Image.fromarray(L), Image.fromarray(R)))

    # --- Pack TB still (square canvas) ---
    size = args.size
    eye_w, eye_h = size, size // 2
    def pack_tb(Limg, Rimg):
        canvas = Image.new("RGB", (size, size), (0, 0, 0))
        canvas.paste(Limg.resize((eye_w, eye_h), Image.Resampling.LANCZOS), (0, 0))
        canvas.paste(Rimg.resize((eye_w, eye_h), Image.Resampling.LANCZOS), (0, eye_h))
        return canvas

    still_path = os.path.join(args.outdir, "output_180_TB.jpg")
    pack_tb(*pairs[1]).save(still_path, quality=95)

    # --- Short MP4 (TB), filename tags for auto-detect in players ---
    mp4_path = os.path.join(args.outdir, "output_180_TB.mp4")
    fps = args.fps
    frames = int(args.seconds * fps)
    sequence = [(0,1), (1,2), (2,1), (1,0)]
    seg = max(1, frames // len(sequence))

    writer = imageio.get_writer(mp4_path, fps=fps, codec="libx264", quality=8)
    count = 0
    for a, b in sequence:
        La, Ra = pairs[a]
        Lb, Rb = pairs[b]
        for i in range(seg):
            t = i / max(1, seg - 1)
            alpha = 0.5 * (1 - math.cos(math.pi * t))  # smooth ease
            L = Image.blend(La, Lb, alpha)
            R = Image.blend(Ra, Rb, alpha)
            frame = pack_tb(L, R)
            writer.append_data(np.array(frame))
            count += 1
    # pad if short
    while count < frames:
        writer.append_data(np.array(pack_tb(*pairs[1])))
        count += 1
    writer.close()

    print("Wrote:")
    print(" ", still_path)
    print(" ", mp4_path)
    print(" ", depth_png)

if __name__ == "__main__":
    main()
