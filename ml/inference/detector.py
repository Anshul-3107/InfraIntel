"""
InfraIntel damage detector.

Runs two YOLOv8 models on an image and returns merged, structured detections:
  - pothole model  -> potholes (trusted source for this class)
  - crack model    -> longitudinal / transverse / alligator cracks
                      (its own pothole predictions are discarded)

Usage from the terminal:
    python detector.py --image "path\\to\\photo.jpg"
    python detector.py --image "path\\to\\photo.jpg" --save_annotated out.jpg

Usage from other code (e.g. a Django app later):
    from detector import DamageDetector
    detector = DamageDetector()
    result = detector.detect("photo.jpg")
"""

import argparse
import json
from pathlib import Path

from ultralytics import YOLO

MODELS_DIR = Path(r"D:\InfraIntel\ml\models\production")
POTHOLE_WEIGHTS = MODELS_DIR / "pothole_v1.pt"
CRACK_WEIGHTS = MODELS_DIR / "crack_v1.pt"

CONF_THRESHOLD = 0.25
IMG_SIZE = 672  # matches training resolution

# Class names as defined in the crack model's data.yaml, in index order
CRACK_CLASS_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",  # ignored; pothole model is used for this class instead
}


class DamageDetector:
    def __init__(self, conf_threshold: float = CONF_THRESHOLD, device=0):
        self.conf_threshold = conf_threshold
        self.device = device
        self.pothole_model = YOLO(str(POTHOLE_WEIGHTS))
        self.crack_model = YOLO(str(CRACK_WEIGHTS))

    def _run(self, model, image_path: str):
        return model.predict(
            source=image_path,
            conf=self.conf_threshold,
            imgsz=IMG_SIZE,
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
        crack_result = self._run(self.crack_model, image_path)
        for box in crack_result.boxes:
            class_id = int(box.cls[0])
            if class_id == 3:
                continue
            name = CRACK_CLASS_NAMES.get(class_id, f"class_{class_id}")
            detections.append(self._to_dict(box, name, "crack_model"))

        detections.sort(key=lambda d: d["confidence"], reverse=True)

        height, width = pothole_result.orig_shape
        return {
            "image": Path(image_path).name,
            "image_size": {"width": int(width), "height": int(height)},
            "conf_threshold": self.conf_threshold,
            "num_detections": len(detections),
            "counts": self._count_by_type(detections),
            "detections": detections,
        }

    @staticmethod
    def _to_dict(box, damage_type: str, source_model: str) -> dict:
        x1, y1, x2, y2 = [round(float(v), 1) for v in box.xyxy[0].tolist()]
        return {
            "damage_type": damage_type,
            "confidence": round(float(box.conf[0]), 3),
            "bounding_box": [x1, y1, x2, y2],  # pixel coords: xmin, ymin, xmax, ymax
            "source_model": source_model,
        }

    @staticmethod
    def _count_by_type(detections: list) -> dict:
        counts = {}
        for d in detections:
            counts[d["damage_type"]] = counts.get(d["damage_type"], 0) + 1
        return counts

    def save_annotated(self, image_path: str, out_path: str):
        """Draw all merged detections on the image and save it."""
        import cv2

        result = self.detect(image_path)
        img = cv2.imread(str(image_path))
        colors = {
            "pothole": (0, 0, 255),
            "longitudinal_crack": (0, 255, 255),
            "transverse_crack": (255, 0, 255),
            "alligator_crack": (0, 165, 255),
        }
        for d in result["detections"]:
            x1, y1, x2, y2 = map(int, d["bounding_box"])
            color = colors.get(d["damage_type"], (255, 255, 255))
            cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
            label = f'{d["damage_type"]} {d["confidence"]:.2f}'
            cv2.putText(img, label, (x1, max(y1 - 6, 12)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1, cv2.LINE_AA)
        cv2.imwrite(str(out_path), img)
        return result


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--image", required=True)
    parser.add_argument("--save_annotated", default=None, help="Optional path to save an annotated copy")
    parser.add_argument("--conf", type=float, default=CONF_THRESHOLD)
    args = parser.parse_args()

    detector = DamageDetector(conf_threshold=args.conf)
    if args.save_annotated:
        result = detector.save_annotated(args.image, args.save_annotated)
        print(f"Annotated image saved to {args.save_annotated}")
    else:
        result = detector.detect(args.image)

    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()