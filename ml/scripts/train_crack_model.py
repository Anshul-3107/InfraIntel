"""
Train a YOLOv8 crack+pothole detector on the RDD2022 India subset.
4 classes: longitudinal_crack, transverse_crack, alligator_crack, pothole.

Fresh training run (not resumed/fine-tuned from anything), following the
same approach that worked well for the pothole model: full epoch budget
from the start, generous patience, distinct run name.
"""

import sys
from pathlib import Path
from ultralytics import YOLO

# Ensure project root is in sys.path if run directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml import config

DATA_YAML = str(config.DATASETS_DIR / "rdd2022_india_split" / "data.yaml")
MODEL_ARCH = "yolov8s.pt"
EPOCHS = 100
IMG_SIZE = config.IMG_SIZE
BATCH = 16
PROJECT_DIR = str(config.ML_DIR / "models")
RUN_NAME = "crack_v3_japan_czech"


def main():
    model = YOLO(MODEL_ARCH)

    results = model.train(
        data=DATA_YAML,
        epochs=EPOCHS,
        imgsz=IMG_SIZE,
        batch=BATCH,
        project=PROJECT_DIR,
        name=RUN_NAME,
        device=0,
        patience=25,
        workers=4,
    )

    print("\nTraining complete.")
    print(f"Best weights saved to: {PROJECT_DIR}\\{RUN_NAME}\\weights\\best.pt")


if __name__ == "__main__":
    main()