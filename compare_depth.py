#!/usr/bin/env python3
"""
compare_depth.py

The actual validation check. Loads Gazebo's ground-truth depth and
Depth-Anything-V2's predicted depth for the same frame, and checks
whether they differ by a roughly CONSTANT ratio (good news — just
apply a scale multiplier) or an INCONSISTENT ratio (bad news — the
model is unreliable at certain distances, as the reference paper warns).

HOW TO USE:
    python3 compare_depth.py
Requires captured_depth.npy and predicted_depth.npy in this folder.
"""

import numpy as np

GT_PATH = "captured_depth.npy"
PRED_PATH = "predicted_depth.npy"


def main():
    gt = np.load(GT_PATH)
    pred = np.load(PRED_PATH)

    if gt.shape != pred.shape:
        print(
            f"Shape mismatch: ground truth is {gt.shape}, "
            f"prediction is {pred.shape}. Resize one to match before "
            f"comparing (they must line up pixel-for-pixel)."
        )
        return

    # Ignore invalid pixels: 0, negative, NaN, or inf depth values
    valid = np.isfinite(gt) & np.isfinite(pred) & (gt > 0.05) & (pred > 0.05)
    print(f"Valid comparable pixels: {valid.sum()} / {gt.size}")

    ratio = gt[valid] / pred[valid]

    mean_ratio = np.mean(ratio)
    median_ratio = np.median(ratio)
    std_ratio = np.std(ratio)
    coeff_of_variation = std_ratio / mean_ratio  # normalized spread

    print("\n--- Ground truth / predicted depth ratio ---")
    print(f"Mean ratio:   {mean_ratio:.4f}")
    print(f"Median ratio: {median_ratio:.4f}")
    print(f"Std dev:      {std_ratio:.4f}")
    print(f"Coefficient of variation (std/mean): {coeff_of_variation:.4f}")

    print("\n--- Verdict ---")
    if coeff_of_variation < 0.15:
        print(
            "LOOKS GOOD: the ratio is fairly consistent across the image.\n"
            f"Try re-running your pseudo_depth_node.py with "
            f"--scale-correction {median_ratio:.4f}\n"
            "and see if the resulting point cloud looks sane."
        )
    elif coeff_of_variation < 0.35:
        print(
            "MIXED: there's a usable average scale, but real spread too.\n"
            f"A starting scale-correction of {median_ratio:.4f} is worth\n"
            "trying, but expect some noisy/wrong points, especially at\n"
            "longer range — check the per-distance breakdown below."
        )
    else:
        print(
            "INCONSISTENT: the ratio swings too much to fix with one\n"
            "number. This matches the 'high uncertainty at far distances'\n"
            "problem the Tiwari et al. paper flags. Worth checking the\n"
            "per-distance breakdown below before concluding this path\n"
            "needs more work than expected."
        )

    # Break down by distance band, since near/far accuracy often differs
    print("\n--- Ratio by distance band (ground truth distance) ---")
    bands = [(0.05, 1.0), (1.0, 2.5), (2.5, 5.0), (5.0, 10.0), (10.0, 20.0)]
    gt_valid = gt[valid]
    for lo, hi in bands:
        band_mask = (gt_valid >= lo) & (gt_valid < hi)
        if band_mask.sum() < 20:
            continue
        band_ratio = ratio[band_mask]
        print(
            f"  {lo:>4.1f}m - {hi:>4.1f}m  "
            f"(n={band_mask.sum():>6}):  "
            f"mean ratio = {np.mean(band_ratio):.3f}, "
            f"std = {np.std(band_ratio):.3f}"
        )


if __name__ == "__main__":
    main()