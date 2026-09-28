"""
Compare detection counts across de-duplication settings on random validation images.

Run from the project root:
    python -m ml.scripts.benchmark_dedup --num_images 20
"""

import argparse
import random
from collections import Counter

from ml import config
from ml.inference.detector import DamageDetector

VAL_IMAGES = config.DATASETS_DIR / "rdd2022_india_split" / "val" / "images"

SETTINGS = [
    ("baseline (iou 0.70, no filter)", 0.70, False),
    ("lower iou (0.50, no filter)", 0.50, False),
    ("containment only (0.70, filter)", 0.70, True),
    ("combined (0.50, filter)", 0.50, True),
]


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--num_images", type=int, default=20)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    images = sorted(VAL_IMAGES.glob("*.jpg"))
    random.seed(args.seed)
    sample = random.sample(images, min(args.num_images, len(images)))
    print(f"Benchmarking on {len(sample)} validation images\n")

    for label, iou, use_filter in SETTINGS:
        detector = DamageDetector(nms_iou=iou, filter_contained_cracks=use_filter)
        totals = Counter()
        for img in sample:
            totals.update(detector.detect(str(img))["counts"])
        print(f"{label}")
        print(f"  total detections: {sum(totals.values())}")
        for name, n in sorted(totals.items()):
            print(f"    {name}: {n}")
        print()


if __name__ == "__main__":
    main()