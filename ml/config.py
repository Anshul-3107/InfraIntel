"""
Shared configuration for InfraIntel ML code.

Paths are derived from this file's location, so the project runs from any
directory or machine. Override with environment variables when needed:
    INFRAINTEL_MODELS_DIR   folder containing pothole_v1.pt and crack_v1.pt
    INFRAINTEL_DATASETS_DIR folder containing the datasets
"""

import os
from pathlib import Path

ML_DIR = Path(__file__).resolve().parent
PROJECT_ROOT = ML_DIR.parent

MODELS_DIR = Path(os.getenv("INFRAINTEL_MODELS_DIR", ML_DIR / "models" / "production"))
DATASETS_DIR = Path(os.getenv("INFRAINTEL_DATASETS_DIR", ML_DIR / "datasets"))

POTHOLE_WEIGHTS = MODELS_DIR / "pothole_v1.pt"
CRACK_WEIGHTS = MODELS_DIR / "crack_v1.pt"

# Inference defaults
CONF_THRESHOLD = 0.25
IMG_SIZE = 672            # matches training resolution
NMS_IOU = 0.50            # Ultralytics default is 0.70; lower merges more overlaps
CONTAINMENT_THRESHOLD = 0.70

# Crack model class order, as defined in rdd2022_india_split/data.yaml
CRACK_CLASS_NAMES = {
    0: "longitudinal_crack",
    1: "transverse_crack",
    2: "alligator_crack",
    3: "pothole",  # ignored at inference; the pothole model is used instead
}
POTHOLE_CLASS_ID_IN_CRACK_MODEL = 3

# BGR colours for annotated output
DAMAGE_COLORS = {
    "pothole": (0, 0, 255),
    "longitudinal_crack": (0, 255, 255),
    "transverse_crack": (255, 0, 255),
    "alligator_crack": (0, 165, 255),
}