"""
InfraIntel damage detector.

Runs two YOLOv8 models on an image and returns merged, structured detections:
  - pothole model  -> potholes (trusted source for this class)
  - crack model    -> longitudinal / transverse / alligator cracks
                      (its own pothole predictions are discarded)

Optional de-duplication:
  - nms_iou: lower value merges more overlapping boxes within a class
  - filter_contained_cracks: drops a lower-confidence crack box that lies mostly
    inside a higher-confidence crack box of a different class

Usage from the terminal (from the project root):
    python -m ml.inference.detector --image "path/to/photo.jpg"
    python -m ml.inference.detector --image photo.jpg --save_annotated out.jpg

Usage from other code:
    from ml.inference.detector import DamageDetector
    result = DamageDetector().detect("photo.jpg")
"""

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

from ml import config


def _box_area(b):
    return max(0.0, b[2] - b[0]) * max(0.0, b[3] - b[1])


def _intersection_area(a, b):
    x1, y1 = max(a[0], b[0]), max(a[1], b[1])
    x2, y2 = min(a[2], b[2]), min(a[3], b[3])
    return max(0.0, x2 - x1) * max(0.0, y2 - y1)


class DamageDetector:
    def __init__(
        self,
        conf_threshold: float = config.CONF_THRESHOLD,
        nms_iou: float = config.NMS_IOU,
        filter_contained_cracks: bool = True,
        containment_threshold: float = config.CONTAINMENT_THRESHOLD,
        device=0,
    ):
        self.conf_threshold = conf_threshold
        self.nms_iou = nms_iou
        self.filter_contained_cracks = filter_contained_cracks
        self.containment_threshold = containment_threshold
        self.device = device
        self.pothole_model = YOLO(str(config.POTHOLE_WEIGHTS))
        self.crack_model = YOLO(str(config.CRACK_WEIGHTS))

    def _run(self, model, image_path: str):
        return model.predict(
            source=image_path,
            conf=self.conf_threshold,
            iou=self.nms_iou,
            imgsz=config.IMG_SIZE,
            device=self.device,
            verbose=False,
        )[0]

    def detect(self, image_path: str) -> dict:
        image_path = str(image_path)
        detections = []

        # 1) Potholes from the specialist model
        pothole_result = self._run(self.pothole_model, image_path)
        for box in pothole_result.boxes:
            detections.append(self._to_dict(box, "pothole", "pothole_model"))

        # 2) Cracks from the crack model, skipping its pothole class
        crack_dets = []
        crack_result = self._run(self.crack_model, image_path)
        for box in crack_result.boxes:
            class_id = int(box.cls[0])
            if class_id == config.POTHOLE_CLASS_ID_IN_CRACK_MODEL:
                continue
            name = config.CRACK_CLASS_NAMES.get(class_id, f"class_{class_id}")
            crack_dets.append(self._to_dict(box, name, "crack_model"))

        if self.filter_contained_cracks:
            crack_dets = self._drop_contained_cross_class(crack_dets)

        detections.extend(crack_dets)
        detections.sort(key=lambda d: d["confidence"], reverse=True)

        height, width = pothole_result.orig_shape
        return {
            "image": Path(image_path).name,
            "image_size": {"width": int(width), "height": int(height)},
            "conf_threshold": self.conf_threshold,
            "nms_iou": self.nms_iou,
            "num_detections": len(detections),
            "counts": self._count_by_type(detections),
            "detections": detections,
        }

    def _drop_contained_cross_class(self, dets: list) -> list:
        """Drop a box mostly inside a higher-confidence box of a different class."""
        ordered = sorted(dets, key=lambda d: d["confidence"], reverse=True)
        kept = []
        for cand in ordered:
            area = _box_area(cand["bounding_box"])
            contained = False
            for keeper in kept:
                if keeper["damage_type"] == cand["damage_type"]:
                    continue
                if area > 0 and (
                    _intersection_area(cand["bounding_box"], keeper["bounding_box"]) / area
                    >= self.containment_threshold
                ):
                    contained = True
                    break
            if not contained:
                kept.append(cand)
        return kept

    @staticmethod
    def _to_dict(box, damage_type: str, source_model: str) -> dict:
        x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        return {
            "damage_type": damage_type,
            "confidence": round(float(box.conf[0]), 3),
            "bounding_box": [x1, y1, x2, y2],  # pixels: xmin, ymin, xmax, ymax
            "source_model": source_model,
        }

    @staticmethod
    def _count_by_type(detections: list) -> dict:
        counts = {}
        for d in detections:
            counts[d["damage_type"]] = counts.get(d["damage_type"], 0) + 1
        return counts

    def save_annotated(self, image_path: str, out_path: str) -> dict:
        """Draw all merged detections on the image and save it."""
        import cv2

        result = self.detect(image_path)
        img = cv2.imread(str(image_path))
        for d in result["detections"]:
            x1, y1, x2, y2 = map(int, d["bounding_box"])
            color = config.DAMAGE_COLORS.get(d["damage_type"], (255, 255, 255))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f'{d["damage_type"]} {d["confidence"]:.2f}'
            cv2.putText(img, label, (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        cv2.imwrite(str(out_path), img)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--save_annotated", default=None)
    parser.add_argument("--conf", type=float, default=config.CONF_THRESHOLD)
    parser.add_argument("--nms_iou", type=float, default=config.NMS_IOU)
    parser.add_argument("--no_containment_filter", action="store_true")
    args = parser.parse_args()

    detector = DamageDetector(
        conf_threshold=args.conf,
        nms_iou=args.nms_iou,
        filter_contained_cracks=not args.no_containment_filter,
    )
    if args.save_annotated:
        result = detector.save_annotated(args.image, args.save_annotated)
        print(f"Annotated image saved to {args.save_annotated}")
    else:
        result = detector.detect(args.image)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()