"""
Split RDD2022 India's labeled images (currently all under train/) into
a proper train/val split for YOLO training.

Usage:
    python split_train_val.py --source_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india\\India\\India\\train" ^
                               --output_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india_split" ^
                               --val_ratio 0.2

This expects, inside source_dir:
    images/*.jpg
    labels/*.txt   (created by convert_voc_to_yolo.py)

It creates, inside output_dir:
    train/images/, train/labels/
    val/images/,   val/labels/

Files are copied, not moved -- your original data is untouched.
A fixed random seed (42) makes the split reproducible if you rerun it.
"""

import argparse
import random
import shutil
from pathlib import Path


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--source_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--val_ratio", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    source_dir = Path(args.source_dir)
    images_dir = source_dir / "images"
    labels_dir = source_dir / "labels"
    output_dir = Path(args.output_dir)

    if not images_dir.exists() or not labels_dir.exists():
        print(f"ERROR: expected {images_dir} and {labels_dir} to both exist.")
        return

    image_files = sorted(images_dir.glob("*.jpg"))
    print(f"Found {len(image_files)} images in {images_dir}")

    # Only keep images that actually have a matching label file
    paired = []
    missing_labels = 0
    for img_path in image_files:
        label_path = labels_dir / (img_path.stem + ".txt")
        if label_path.exists():
            paired.append((img_path, label_path))
        else:
            missing_labels += 1

    if missing_labels:
        print(f"WARNING: {missing_labels} images had no matching label file and were skipped.")

    random.seed(args.seed)
    random.shuffle(paired)

    val_count = int(len(paired) * args.val_ratio)
    val_set = paired[:val_count]
    train_set = paired[val_count:]

    print(f"Splitting into {len(train_set)} train / {len(val_set)} val (seed={args.seed})")

    for split_name, split_data in [("train", train_set), ("val", val_set)]:
        split_images_dir = output_dir / split_name / "images"
        split_labels_dir = output_dir / split_name / "labels"
        split_images_dir.mkdir(parents=True, exist_ok=True)
        split_labels_dir.mkdir(parents=True, exist_ok=True)

        for img_path, label_path in split_data:
            shutil.copy2(img_path, split_images_dir / img_path.name)
            shutil.copy2(label_path, split_labels_dir / label_path.name)

    print(f"\nDone. Output written to {output_dir}")
    print(f"  train: {len(train_set)} images -> {output_dir / 'train'}")
    print(f"  val:   {len(val_set)} images -> {output_dir / 'val'}")


if __name__ == "__main__":
    main()
