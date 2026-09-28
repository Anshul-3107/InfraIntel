# InfraIntel

AI-powered infrastructure inspection and predictive maintenance platform.
Inspectors photograph damage, computer vision models detect and classify it,
and (planned) a risk engine scores asset health and prioritises maintenance.

> **Status:** early development. The ML detection core is trained; the
> backend (Django), mobile app (Flutter) and scoring engine are not built yet.

## Planned architecture

Flutter app -> Django REST API -> Celery/Redis -> ML inference (YOLOv8)
-> severity + health scoring -> PostgreSQL/PostGIS -> GIS dashboard

## What exists today

Two YOLOv8s detectors trained on Indian road-damage data:

| Model | Classes | mAP50 | mAP50-95 |
|---|---|---|---|
| Pothole detector (BharatPothole) | pothole | 0.624 | 0.333 |
| Crack detector (RDD2022) | longitudinal crack, transverse crack, alligator crack, pothole | 0.398 | 0.170 |

Per-class results for the crack detector (validation set):

| Class | mAP50 |
|---|---|
| Longitudinal crack | 0.329 |
| Transverse crack | 0.198 |
| Alligator crack | 0.639 |
| Pothole | 0.425 |

### Known limitations

- Transverse crack is the weakest class. The India validation split contains
  only 12 transverse-crack instances, so its metric is noisy. Training data was
  supplemented with 300 Czech and 600 Japanese transverse-crack images
  (same RDD annotation standard) to address class imbalance.
- The standalone pothole model outperforms the crack model on potholes, so the
  intended pipeline uses the pothole model for potholes.
- Corrosion, spalling and other damage types from the original plan are not
  covered; no India-specific labelled datasets were found.

## Datasets (not included in this repo)

- **BharatPothole**: https://www.kaggle.com/datasets/surbhisaswatimohanty/bharatpothole
- **RDD2022**: https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547
  (India subset used for training; Czech and Japan used only for transverse-crack supplementation)

RDD2022 damage codes mapped: D00 longitudinal crack, D10 transverse crack,
D20 alligator crack, D40 pothole. Road-marking codes (D43, D44) and D50 are excluded.

## Reproducing the training pipeline

All scripts are in `ml/scripts/`. Paths are currently hard-coded to a local
Windows layout under `D:\InfraIntel`; edit the constants at the top of each script.

1. `convert_voc_to_yolo.py`: convert RDD2022 Pascal VOC XML to YOLO labels
2. `split_train_val.py`: 80/20 train/val split of the labelled India images
3. `merge_transverse_crack.py`: add capped transverse-crack images from Czech/Japan
4. `visualize_labels.py`: draw boxes on samples to sanity-check labels
5. `train_pothole_model.py` / `train_crack_model.py`: train YOLOv8s
   (`imgsz=672`, `batch=16`, 50-100 epochs, RTX 3050 4GB)

## Environment

Python 3.11, PyTorch 2.6 (CUDA 12.4), Ultralytics YOLOv8.