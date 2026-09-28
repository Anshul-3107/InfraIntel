"""
Filter a country's converted YOLO labels to keep ONLY images that contain
at least one transverse_crack (class id 1 / D10) box, then copy a capped,
randomly-sampled subset of those image+label pairs into the existing
India training set.

Same rationale as before: targeted fix for transverse_crack class
imbalance, without letting one supplementary country's imagery dominate
an otherwise India-focused dataset. The --max_images cap and random
sampling (fixed seed, reproducible) keep the contribution proportionate.

Usage:
    python merge_transverse_crack.py --source_dir "D:\\InfraIntel\\ml\\datasets\\RDD2022\\Japan_extracted\\Japan\\train" ^
                                      --target_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india_split\\train" ^
                                      --country_prefix Japan ^
                                      --max_images 600
"""

import argparse
import random
import shutil
from pathlib import Path

TRANSVERSE_CRACK_CLASS_ID = 1  # matches CLASS_MAP in convert_voc_to_yolo.py


def has_transverse_crack(label_path: Path) -> bool:
    if label_path.stat().st_size == 0:
        return False
    lines = label_path.read_text(encoding="utf-8").strip().splitlines()
    for line in lines:
        parts = line.split()
        if parts and int(parts[0]) == TRANSVERSE_CRACK_CLASS_ID:
            return True
    return False


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", required=True, help="Country's train/ folder (must have images/ and labels/)")
    parser.add_argument("--target_dir", required=True, help="Existing train/ folder to merge into (must have images/ and labels/)")
    parser.add_argument("--country_prefix", required=True, help="Prefix for copied filenames, e.g. Japan")
    parser.add_argument("--max_images", type=int, default=None, help="Cap on number of images to copy (random sample if exceeded)")
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    source_images = Path(args.source_dir) / "images"
    source_labels = Path(args.source_dir) / "labels"
    target_images = Path(args.target_dir) / "images"
    target_labels = Path(args.target_dir) / "labels"

    if not source_labels.exists():
        print(f"ERROR: {source_labels} does not exist. Run convert_voc_to_yolo.py on source_dir first.")
        return
    if not target_images.exists() or not target_labels.exists():
        print(f"ERROR: {target_images} or {target_labels} does not exist. Check --target_dir.")
        return

    matched = []
    for label_path in source_labels.glob("*.txt"):
        if has_transverse_crack(label_path):
            img_path = source_images / (label_path.stem + ".jpg")
            if img_path.exists():
                matched.append((img_path, label_path))
            else:
                print(f"WARNING: label {label_path.name} has no matching image, skipping")

    print(f"Found {len(matched)} images containing transverse_crack in {source_images}")

    if args.max_images is not None and len(matched) > args.max_images:
        random.seed(args.seed)
        random.shuffle(matched)
        matched = matched[: args.max_images]
        print(f"Capped to a random sample of {args.max_images} images (seed={args.seed})")

    copied = 0
    for img_path, label_path in matched:
        new_stem = f"{args.country_prefix}_{img_path.stem}"
        dest_img = target_images / (new_stem + ".jpg")
        dest_label = target_labels / (new_stem + ".txt")

        if dest_img.exists():
            print(f"WARNING: {dest_img.name} already exists in target, skipping (avoid overwrite)")
            continue

        shutil.copy2(img_path, dest_img)
        shutil.copy2(label_path, dest_label)
        copied += 1

    print(f"\nCopied {copied} transverse_crack image+label pairs into:")
    print(f"  {target_images}")
    print(f"  {target_labels}")


if __name__ == "__main__":
    main()
