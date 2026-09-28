"""
Convert RDD2022 India Pascal VOC XML annotations to YOLO .txt format.

Usage (run from ml/scripts/ or anywhere, just pass the split root):
    python convert_voc_to_yolo.py --split_dir "D:\\InfraIntel\\ml\\datasets\\rdd2022_india\\India\\India\\train"

This expects, inside split_dir:
    annotations/xmls/*.xml
    images/*.jpg

It creates:
    labels/*.txt   (one per image, same basename, YOLO format)

Class mapping (RDD2022 standard damage codes):
    D00 -> 0  (longitudinal crack)
    D10 -> 1  (transverse crack)
    D20 -> 2  (alligator crack)
    D40 -> 3  (pothole)

Any other/unexpected class name is skipped with a warning printed, not silently dropped.
Images with zero <object> tags get an empty .txt file (correct YOLO convention for
negative/background samples), not a missing file.
"""

import argparse
import xml.etree.ElementTree as ET
from pathlib import Path

CLASS_MAP = {
    "D00": 0,  # longitudinal crack
    "D10": 1,  # transverse crack
    "D20": 2,  # alligator crack
    "D40": 3,  # pothole
}

CLASS_NAMES = ["longitudinal_crack", "transverse_crack", "alligator_crack", "pothole"]


def convert_one(xml_path: Path, labels_dir: Path):
    tree = ET.parse(xml_path)
    root = tree.getroot()

    size = root.find("size")
    img_w = float(size.find("width").text)
    img_h = float(size.find("height").text)

    lines = []
    skipped_classes = set()

    for obj in root.findall("object"):
        name = obj.find("name").text.strip()
        if name not in CLASS_MAP:
            skipped_classes.add(name)
            continue

        class_id = CLASS_MAP[name]
        bnd = obj.find("bndbox")
        xmin = float(bnd.find("xmin").text)
        ymin = float(bnd.find("ymin").text)
        xmax = float(bnd.find("xmax").text)
        ymax = float(bnd.find("ymax").text)

        # Clamp to image bounds defensively (some datasets have off-by-a-few errors)
        xmin = max(0, min(xmin, img_w))
        xmax = max(0, min(xmax, img_w))
        ymin = max(0, min(ymin, img_h))
        ymax = max(0, min(ymax, img_h))

        box_w = xmax - xmin
        box_h = ymax - ymin
        if box_w <= 0 or box_h <= 0:
            continue  # degenerate box, skip

        x_center = (xmin + xmax) / 2.0 / img_w
        y_center = (ymin + ymax) / 2.0 / img_h
        norm_w = box_w / img_w
        norm_h = box_h / img_h

        lines.append(f"{class_id} {x_center:.6f} {y_center:.6f} {norm_w:.6f} {norm_h:.6f}")

    out_path = labels_dir / (xml_path.stem + ".txt")
    out_path.write_text("\n".join(lines), encoding="utf-8")

    return len(lines), skipped_classes


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--split_dir", required=True, help="Path to train/ or test/ folder")
    args = parser.parse_args()

    split_dir = Path(args.split_dir)
    xml_dir = split_dir / "annotations" / "xmls"
    labels_dir = split_dir / "labels"
    labels_dir.mkdir(exist_ok=True)

    if not xml_dir.exists():
        print(f"ERROR: {xml_dir} does not exist. Check --split_dir.")
        return

    xml_files = sorted(xml_dir.glob("*.xml"))
    print(f"Found {len(xml_files)} XML files in {xml_dir}")

    total_boxes = 0
    total_negatives = 0
    all_skipped = set()

    for i, xml_path in enumerate(xml_files, 1):
        n_boxes, skipped = convert_one(xml_path, labels_dir)
        total_boxes += n_boxes
        if n_boxes == 0:
            total_negatives += 1
        all_skipped |= skipped

        if i % 1000 == 0:
            print(f"  ...processed {i}/{len(xml_files)}")

    print(f"\nDone. Wrote {len(xml_files)} label files to {labels_dir}")
    print(f"Total bounding boxes: {total_boxes}")
    print(f"Negative (no-damage) images: {total_negatives}")
    if all_skipped:
        print(f"WARNING: skipped unrecognized class names: {sorted(all_skipped)}")
    print(f"\nClass mapping used: {CLASS_MAP}")
    print(f"Class names (for data.yaml): {CLASS_NAMES}")


if __name__ == "__main__":
    main()
