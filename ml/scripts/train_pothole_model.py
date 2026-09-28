# """
# Train a YOLOv8 pothole detector on the BharatPothole dataset.

# Usage:
#     python train_pothole_model.py

# Adjust the constants below if your paths differ. Designed for a 4GB VRAM
# GPU (RTX 3050 Laptop) -- batch size and image size are kept conservative
# to avoid out-of-memory errors. If you hit a CUDA OOM error, lower BATCH
# further (try 8, then 4) before lowering IMG_SIZE.
# """

# from ultralytics import YOLO

# DATA_YAML = r"D:\InfraIntel\ml\datasets\bharatpothole\BharatPotHole\BharatPotHole\data.yaml"
# #MODEL_ARCH = "yolov8n.pt"   # nano -- smallest, fastest, best fit for 4GB VRAM
# MODEL_ARCH = "yolov8s.pt" # s -- small better and heavier than nano yolo model
# EPOCHS = 50
# IMG_SIZE = 672
# BATCH = 16                  # lower to 8 or 4 if you get a CUDA out-of-memory error
# PROJECT_DIR = r"D:\InfraIntel\ml\models"
# RUN_NAME = "pothole_v1"


# def main():
#     model = YOLO(MODEL_ARCH)  # downloads pretrained weights on first run

#     results = model.train(
#         data=DATA_YAML,
#         epochs=EPOCHS,
#         imgsz=IMG_SIZE,
#         batch=BATCH,
#         project=PROJECT_DIR,
#         name=RUN_NAME,
#         device=0,        # use GPU 0 (your RTX 3050); use 'cpu' if this errors
#         patience=15,      # stop early if val performance plateaus for 15 epochs
#         workers=4,        # CPU threads for data loading, alongside the GPU
#     )

#     print("\nTraining complete.")
#     print(f"Best weights saved to: {PROJECT_DIR}\\{RUN_NAME}\\weights\\best.pt")
#     print(f"Results/plots saved to: {PROJECT_DIR}\\{RUN_NAME}\\")


# if __name__ == "__main__":
#     main() 







# """
# Continue training the pothole detector for more epochs, starting from
# the best weights already trained (pothole_v1), rather than starting over
# from scratch. mAP50 was still climbing at epoch 50, so more training
# may still help before concluding the model has plateaued.
# """

# from ultralytics import YOLO

# # Resume from your existing best weights, not the generic pretrained yolov8s.pt
# PREVIOUS_BEST = r"D:\InfraIntel\ml\models\pothole_v1\weights\best.pt"

# DATA_YAML = r"D:\InfraIntel\ml\datasets\bharatpothole\BharatPotHole\BharatPotHole\data.yaml"
# EPOCHS = 80
# IMG_SIZE = 672
# BATCH = 16
# PROJECT_DIR = r"D:\InfraIntel\ml\models"
# RUN_NAME = "pothole_v2_80ep"   # NEW name -- keeps v1 results intact for comparison


# def main():
#     model = YOLO(PREVIOUS_BEST)  # load your already-trained weights, not a fresh pretrained model

#     results = model.train(
#         data=DATA_YAML,
#         epochs=EPOCHS,
#         imgsz=IMG_SIZE,
#         batch=BATCH,
#         project=PROJECT_DIR,
#         name=RUN_NAME,
#         device=0,
#         patience=20,      # a bit more patience since we're testing if it keeps improving
#         workers=4,
#     )

#     print("\nTraining complete.")
#     print(f"Best weights saved to: {PROJECT_DIR}\\{RUN_NAME}\\weights\\best.pt")
#     print(f"Results/plots saved to: {PROJECT_DIR}\\{RUN_NAME}\\")


# if __name__ == "__main__":
#     main()








"""
Fresh training run for the pothole detector, starting from the pretrained
yolov8s.pt weights (not continuing from pothole_v1). Using a higher epoch
budget and increased patience, since pothole_v1's mAP50 was still climbing
at epoch 50 without clearly plateauing.
"""

import sys
from pathlib import Path
from ultralytics import YOLO

# Ensure project root is in sys.path if run directly
PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from ml import config

DATA_YAML = str(config.DATASETS_DIR / "bharatpothole" / "BharatPotHole" / "BharatPotHole" / "data.yaml")
MODEL_ARCH = "yolov8s.pt"
EPOCHS = 100
IMG_SIZE = config.IMG_SIZE
BATCH = 16
PROJECT_DIR = str(config.ML_DIR / "models")
RUN_NAME = "pothole_v3_100ep"


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