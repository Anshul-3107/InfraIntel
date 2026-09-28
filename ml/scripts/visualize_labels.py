"""
Visual sanity check: draws YOLO-format bounding boxes on top of a handful of
sample images, so you can eyeball whether the Pascal VOC -> YOLO conversion
actually produced correct boxes before training on it.

Usage:
    python visualize_labels.py --images_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india_split\\train\\images" ^
                                --labels_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india_split\\train\\labels" ^
                                --output_dir "D:\\InfraIntel\\ml\\scripts\\label_check" ^
                                --num_samples 12

It only picks images that actually HAVE at least one box (skips empty/negative
labels for this check, since there's nothing to visually verify on those).
Saves annotated copies to output_dir so you can open and look at them in
VS Code or any image viewer.
"""

import argparse
import random
from pathlib import Path

import cv2

CLASS_NAMES = ["longitudinal_crack", "transverse_crack", "alligator_crack", "pothole"]
CLASS_COLORS = [
    (0, 255, 255),   # yellow - longitudinal crack
    (255, 0, 255),   # magenta - transverse crack
    (0, 165, 255),   # orange - alligator crack
    (0, 0, 255),     # red - pothole
]


def draw_boxes(image_path: Path, label_path: Path, out_path: Path):
    img = cv2.imread(str(image_path))
    if img is None:
        print(f"  Could not read image: {image_path}")
        return False

    h, w = img.shape[:2]
    lines = label_path.read_text(encoding="utf-8").strip().splitlines()

    for line in lines:
        parts = line.split()
        if len(parts) != 5:
            continue
        class_id = int(parts[0])
        x_center, y_center, box_w, box_h = map(float, parts[1:])

        # Convert normalized YOLO format back to pixel corners
        xmin = int((x_center - box_w / 2) * w)
        xmax = int((x_center + box_w / 2) * w)
        ymin = int((y_center - box_h / 2) * h)
        ymax = int((y_center + box_h / 2) * h)

        color = CLASS_COLORS[class_id % len(CLASS_COLORS)]
        label_text = CLASS_NAMES[class_id] if class_id < len(CLASS_NAMES) else f"class_{class_id}"

        cv2.rectangle(img, (xmin, ymin), (xmax, ymax), color, 2)
        cv2.putText(img, label_text, (xmin, max(ymin - 5, 10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)

    cv2.imwrite(str(out_path), img)
    return True


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--images_dir", required=True)
    parser.add_argument("--labels_dir", required=True)
    parser.add_argument("--output_dir", required=True)
    parser.add_argument("--num_samples", type=int, default=12)
    parser.add_argument("--seed", type=int, default=42)
    args = parser.parse_args()

    images_dir = Path(args.images_dir)
    labels_dir = Path(args.labels_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Only consider images whose label file is non-empty (has real boxes)
    candidates = []
    for label_path in labels_dir.glob("*.txt"):
        if label_path.stat().st_size > 0:
            img_path = images_dir / (label_path.stem + ".jpg")
            if img_path.exists():
                candidates.append((img_path, label_path))

    print(f"Found {len(candidates)} labeled images with at least one box.")

    random.seed(args.seed)
    random.shuffle(candidates)
    sample = candidates[: args.num_samples]

    written = 0
    for img_path, label_path in sample:
        out_path = output_dir / f"check_{img_path.name}"
        if draw_boxes(img_path, label_path, out_path):
            written += 1

    print(f"\nWrote {written} annotated sample images to {output_dir}")
    print("Open these and visually confirm the boxes actually line up with the damage.")


if __name__ == "__main__":
    main()
