"""
Train a YOLOv8 crack+pothole detector on the RDD2022 India subset.
4 classes: longitudinal_crack, transverse_crack, alligator_crack, pothole.

Fresh training run (not resumed/fine-tuned from anything), following the
same approach that worked well for the pothole model: full epoch budget
from the start, generous patience, distinct run name.
"""

from ultralytics import YOLO

DATA_YAML = r"D:\InfraIntel\ml\datasets\rdd2022_india_split\data.yaml"
MODEL_ARCH = "yolov8s.pt"
EPOCHS = 100
IMG_SIZE = 672
BATCH = 16
PROJECT_DIR = r"D:\InfraIntel\ml\models"
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