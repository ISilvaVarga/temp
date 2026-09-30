#!/usr/bin/env python3
"""
run_depth_anything.py

Runs Depth-Anything-V2 (metric_depth, vits + hypersim checkpoint) on the
RGB image you captured with capture_pair.py, and saves the AI's guessed
depth map. Also times the inference, which doubles as your "is this fast
enough to run per-frame" benchmark (Step 2 of your plan).

BEFORE RUNNING:
- Edit CHECKPOINT_PATH below to point at your actual .pth file.
- Edit DEPTH_ANYTHING_REPO_PATH if you cloned the repo somewhere other
  than alongside this script.

HOW TO USE:
    python3 run_depth_anything.py
Output:
    predicted_depth.npy   (same shape as captured_depth.npy, in meters)
"""

import sys
import time
import numpy as np
import cv2
import torch

# --- EDIT THESE TWO PATHS FOR YOUR MACHINE ---
DEPTH_ANYTHING_REPO_PATH = "/mnt/c/Users/ilena/Depth-Anything-V2"
CHECKPOINT_PATH = "/mnt/c/Users/ilena/Depth-Anything-V2/metric_depth/checkpoints/depth_anything_v2_metric_hypersim_vits.pth"
# ----------------------------------------------

sys.path.append(f"{DEPTH_ANYTHING_REPO_PATH}/metric_depth")
sys.path.append(DEPTH_ANYTHING_REPO_PATH)

from depth_anything_v2.dpt import DepthAnythingV2  # noqa: E402

MODEL_CONFIGS = {
    "vits": {"encoder": "vits", "features": 64, "out_channels": [48, 96, 192, 384]},
}


def load_model():
    device = "cuda" if torch.cuda.is_available() else "cpu"
    print(f"Loading model on device: {device}")

    cfg = MODEL_CONFIGS["vits"]
    model = DepthAnythingV2(**{**cfg, "max_depth": 20})  # 20m = hypersim indoor
    model.load_state_dict(torch.load(CHECKPOINT_PATH, map_location="cpu"))
    model = model.to(device).eval()
    return model, device


def main():
    rgb = cv2.imread("captured_rgb.png")
    if rgb is None:
        raise FileNotFoundError(
            "captured_rgb.png not found — run capture_pair.py first."
        )

    model, device = load_model()

    # Time a few runs: first one includes warmup/model-loading overhead,
    # so time a second pass too for a fairer per-frame estimate.
    t0 = time.time()
    depth_pred = model.infer_image(rgb)  # returns metric depth in meters
    t1 = time.time()
    depth_pred_2 = model.infer_image(rgb)
    t2 = time.time()

    print(f"First inference call:  {t1 - t0:.3f} sec")
    print(f"Second inference call: {t2 - t1:.3f} sec  <- closer to steady-state speed")
    print(
        f"That's roughly {1 / (t2 - t1):.2f} frames/sec on this machine "
        f"({device})."
    )

    np.save("predicted_depth.npy", depth_pred_2.astype(np.float32))
    print(
        f"Saved predicted_depth.npy "
        f"(min={depth_pred_2.min():.3f}m, max={depth_pred_2.max():.3f}m)"
    )


if __name__ == "__main__":
    main()