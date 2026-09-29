# InfraIntel

**AI-powered infrastructure inspection and predictive maintenance platform.**

InfraIntel is a computer-vision-based infrastructure inspection platform designed to help government and public-works teams identify road damage, record inspection locations, assess infrastructure condition, and eventually prioritize maintenance using data-driven risk scoring.

Inspectors can upload road images with location information. InfraIntel's computer vision pipeline detects and classifies road damage using dedicated YOLOv8 models, while the Django REST backend stores and exposes inspection results through an API.

---

## Project Status

**Early development — ML detection core and initial backend vertical slice are implemented.**

### Implemented

* YOLOv8 road-damage detection models
* BharatPothole-based pothole detector
* RDD2022-based crack detector
* Transverse-crack data supplementation
* YOLO inference pipeline
* Dedicated pothole and crack model inference
* Confidence thresholding
* NMS configuration
* Cross-class containment filtering
* Structured detection JSON output
* Annotated image generation
* Django backend
* Django REST API
* Road-image upload endpoint
* Inspection database model
* Inspection result persistence
* Latitude/longitude storage
* Inspection retrieval API
* Media/image serving

### In Development

* Damage severity scoring
* Road/asset health scoring
* Maintenance priority calculation
* Flutter mobile application
* Authentication and user roles
* GIS/map visualization
* Government/admin dashboard
* Inspection history and analytics
* PostgreSQL/PostGIS integration
* Production deployment

### Planned

* Asynchronous inference with Celery/Redis where required
* Historical inspection comparison
* Predictive maintenance
* Infrastructure risk monitoring
* Geographic prioritization of damaged assets

---

# Architecture

```text
                         ┌──────────────────────┐
                         │     Flutter App      │
                         │   Inspector Client   │
                         └──────────┬───────────┘
                                    │
                                    │ REST API
                                    ▼
                         ┌──────────────────────┐
                         │    Django + DRF      │
                         │    Backend API       │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │   DamageDetector     │
                         │   Inference Layer    │
                         └──────────┬───────────┘
                                    │
                         ┌──────────┴───────────┐
                         │                      │
                         ▼                      ▼
                ┌────────────────┐     ┌────────────────┐
                │ Pothole YOLOv8 │     │  Crack YOLOv8  │
                │    Detector    │     │    Detector    │
                └────────────────┘     └────────────────┘
                         │                      │
                         └──────────┬───────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Detection Results    │
                         │ type / confidence /  │
                         │ bounding box / model │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ Inspection Database  │
                         └──────────┬───────────┘
                                    │
                       ┌────────────┴────────────┐
                       ▼                         ▼
              Severity Scoring            Health Scoring
                (planned)                    (planned)
                       │                         │
                       └────────────┬────────────┘
                                    ▼
                         ┌──────────────────────┐
                         │ Maintenance Priority│
                         │       (planned)      │
                         └──────────┬───────────┘
                                    │
                                    ▼
                         ┌──────────────────────┐
                         │ GIS / Government     │
                         │ Dashboard (planned)  │
                         └──────────────────────┘
```

---

# Current Backend

InfraIntel currently has a working Django REST API that connects the trained computer-vision models directly to the backend.

## Inspection API

### Analyze an image

```http
POST /api/inspect/
```

The endpoint accepts a multipart image upload along with geographic coordinates.

Example:

```bash
curl.exe -X POST http://127.0.0.1:8000/api/inspect/ `
  -F "image=@ml\datasets\rdd2022_india_split\val\images\India_008597.jpg" `
  -F "latitude=23.2599" `
  -F "longitude=77.4126"
```

The API:

1. Receives the road image.
2. Stores the uploaded image.
3. Sends the image to the existing `DamageDetector`.
4. Runs the dedicated pothole model.
5. Runs the crack model.
6. Applies inference/post-processing logic.
7. Stores the inspection result.
8. Returns structured JSON.

### Retrieve an inspection

```http
GET /api/inspections/<id>/
```

Example:

```bash
curl.exe http://127.0.0.1:8000/api/inspections/1/
```

Example response:

```json
{
  "id": 1,
  "image": "http://127.0.0.1:8000/media/inspections/2026/09/India_008597.jpg",
  "latitude": 23.2599,
  "longitude": 77.4126,
  "image_width": 720,
  "image_height": 720,
  "num_detections": 7,
  "detections": [
    {
      "damage_type": "alligator_crack",
      "confidence": 0.663,
      "bounding_box": [
        201.0,
        233.5,
        720.0,
        720.0
      ],
      "source_model": "crack_model"
    },
    {
      "damage_type": "pothole",
      "confidence": 0.538,
      "bounding_box": [
        123.4,
        308.9,
        175.1,
        345.4
      ],
      "source_model": "pothole_model"
    }
  ],
  "created_at": "2026-09-29T13:11:42.696512Z"
}
```

The current backend therefore provides a working vertical slice:

```text
Road Image
    ↓
Django REST API
    ↓
DamageDetector
    ↓
YOLOv8 Models
    ↓
Post-processing
    ↓
Inspection Record
    ↓
JSON Response
```

---

# Machine Learning Pipeline

InfraIntel currently uses two specialized YOLOv8s detectors.

## 1. Pothole Detector

**Dataset:** BharatPothole

| Metric   |  Result |
| -------- | ------: |
| Class    | Pothole |
| mAP50    |   0.624 |
| mAP50-95 |   0.333 |

The standalone pothole detector is used for pothole detection because it performs better on potholes than the pothole class of the crack detector.

---

## 2. Crack Detector

**Dataset:** RDD2022 India subset

| Metric   |                                                         Result |
| -------- | -------------------------------------------------------------: |
| Classes  | Longitudinal crack, transverse crack, alligator crack, pothole |
| mAP50    |                                                          0.398 |
| mAP50-95 |                                                          0.170 |

### Per-class validation results

| Class              | mAP50 |
| ------------------ | ----: |
| Longitudinal crack | 0.329 |
| Transverse crack   | 0.198 |
| Alligator crack    | 0.639 |
| Pothole            | 0.425 |

---

# Inference Design

InfraIntel intentionally uses separate models for different damage types.

```text
                    Input Image
                         │
              ┌──────────┴──────────┐
              │                     │
              ▼                     ▼
       Pothole Model           Crack Model
              │                     │
              │                     ├── Longitudinal crack
              │                     ├── Transverse crack
              │                     └── Alligator crack
              │
              └── Pothole
```

Pothole detections from the crack model are not used as the primary pothole result because the dedicated BharatPothole model performs better for that class.

The inference layer also supports:

* Configurable confidence threshold
* Configurable NMS IoU
* Cross-class containment filtering
* Structured detection output
* Annotated image generation
* CPU/GPU inference configuration

---

# Example Detection

A test image from the India validation set produced:

```text
7 detections

3 × Alligator crack
2 × Pothole
2 × Longitudinal crack
```

Example detection:

```json
{
  "damage_type": "alligator_crack",
  "confidence": 0.663,
  "bounding_box": [
    201.0,
    233.5,
    720.0,
    720.0
  ],
  "source_model": "crack_model"
}
```

---

# Severity and Risk Scoring

The next major backend component is a deterministic infrastructure-risk engine.

The initial scoring system will not treat YOLO confidence as damage severity.

Instead, severity will be derived from measurable factors such as:

* Damage type
* Number of detected defects
* Bounding-box area
* Damage coverage relative to image area
* Detection confidence
* Historical inspection results
* Asset condition
* Geographic context
* Recurrence of damage

The planned pipeline is:

```text
YOLO Detection
      ↓
Damage Characteristics
      ↓
Severity Score
      ↓
Asset Health Score
      ↓
Risk / Maintenance Priority
```

The initial implementation will use an explainable rule-based scoring system before considering a separate machine-learning risk model.

---

# Known ML Limitations

### Transverse cracks

Transverse crack detection is currently the weakest class.

The India validation split contains only **12 transverse-crack instances**, making the validation metric noisy.

To reduce class imbalance during training, additional RDD-compatible transverse-crack images were added:

* 300 images from Czech Republic
* 600 images from Japan

These supplementary images were used specifically for transverse-crack training.

### Pothole detection

The crack detector contains a pothole class, but the dedicated BharatPothole detector performs better for potholes.

Therefore, the inference pipeline uses:

```text
BharatPothole model → Potholes
RDD2022 crack model → Cracks
```

### Other infrastructure damage

The current ML system does not detect every type of infrastructure deterioration.

Damage types such as:

* Corrosion
* Concrete spalling
* Structural deterioration
* Road-marking defects

are currently outside the supported detection scope because suitable India-specific labelled datasets were not available for the initial implementation.

---

# Datasets

The datasets are **not included in this repository**.

## BharatPothole

Used for the dedicated pothole detector.

Dataset:

https://www.kaggle.com/datasets/surbhisaswatimohanty/bharatpothole

## RDD2022

Used for crack detection.

Dataset:

https://figshare.com/articles/dataset/RDD2022_-_The_multi-national_Road_Damage_Dataset_released_through_CRDDC_2022/21431547

The India subset was used for the main training/validation pipeline.

Czech and Japanese RDD2022 data were used only to supplement transverse-crack training.

### RDD2022 class mapping

| RDD Code | InfraIntel Class   |
| -------- | ------------------ |
| D00      | Longitudinal crack |
| D10      | Transverse crack   |
| D20      | Alligator crack    |
| D40      | Pothole            |

The following classes are excluded from the current training pipeline:

* D43
* D44
* D50

---

# ML Training Pipeline

Training and dataset-preparation scripts are located in:

```text
ml/scripts/
```

## 1. Convert annotations

```text
convert_voc_to_yolo.py
```

Converts RDD2022 Pascal VOC XML annotations into YOLO-format labels.

## 2. Train/validation split

```text
split_train_val.py
```

Creates an 80/20 training-validation split of labelled India images.

## 3. Transverse-crack supplementation

```text
merge_transverse_crack.py
```

Adds a capped number of Czech and Japanese transverse-crack images to improve class balance.

## 4. Visualize annotations

```text
visualize_labels.py
```

Draws bounding boxes over sample images for annotation verification.

## 5. Train pothole model

```text
train_pothole_model.py
```

Trains the dedicated BharatPothole YOLOv8s detector.

## 6. Train crack model

```text
train_crack_model.py
```

Trains the RDD2022 crack detector.

---

# ML Inference

The reusable inference implementation is located under:

```text
ml/inference/
```

The main inference class is:

```text
DamageDetector
```

Example CLI usage:

```bash
python -m ml.inference.detector --image "ml\datasets\rdd2022_india_split\val\images\India_008597.jpg"
```

The inference layer returns structured JSON containing:

* Image information
* Image dimensions
* Detection count
* Damage type
* Confidence
* Bounding box
* Source model

---

# Project Structure

The project is organized into separate ML and backend components.

```text
InfraIntel/
│
├── backend/
│   ├── manage.py
│   │
│   ├── inspections/
│   │   ├── migrations/
│   │   ├── ...
│   │   └── ...
│   │
│   └── ...
│
├── ml/
│   ├── inference/
│   │   └── detector.py
│   │
│   ├── scripts/
│   │   ├── convert_voc_to_yolo.py
│   │   ├── split_train_val.py
│   │   ├── merge_transverse_crack.py
│   │   ├── visualize_labels.py
│   │   ├── train_pothole_model.py
│   │   └── train_crack_model.py
│   │
│   ├── datasets/
│   │   └── ...
│   │
│   └── ...
│
├── .gitignore
├── README.md
└── ...
```

Datasets and large model files are excluded from the repository where appropriate.

---

# Technology Stack

## Machine Learning

* Python
* PyTorch
* Ultralytics YOLOv8
* OpenCV
* NumPy

## Backend

* Django
* Django REST Framework
* SQLite during development
* PostgreSQL planned
* PostGIS planned

## Mobile

* Flutter
* Dart

## Planned Infrastructure

* Celery
* Redis
* PostgreSQL
* PostGIS

## GIS / Visualization

* Flutter maps
* PostGIS spatial queries
* Government/admin dashboard

---

# Development Environment

Current ML training environment:

```text
Python 3.11
PyTorch 2.6
CUDA 12.4
Ultralytics YOLOv8
```

Training was designed around an:

```text
RTX 3050 Laptop GPU
4 GB VRAM
```

Example training configuration:

```text
Model: YOLOv8s
Image size: 672
Batch size: 16
Epochs: 50–100
```

Training scripts currently contain Windows-local paths under:

```text
D:\InfraIntel
```

These paths should be changed when reproducing the training pipeline on another machine.

---

# Running the Backend

From the project root:

```bash
cd D:\InfraIntel
```

Activate the virtual environment:

```powershell
.\venv\Scripts\Activate.ps1
```

Run migrations:

```bash
python backend\manage.py migrate
```

Start the Django development server:

```bash
python backend\manage.py runserver
```

The development API will be available at:

```text
http://127.0.0.1:8000/
```

---

# Current Development Roadmap

## Phase 1 — ML Detection

* [x] Dataset preparation
* [x] Annotation conversion
* [x] Train/validation split
* [x] Label visualization
* [x] Class imbalance handling
* [x] Pothole model training
* [x] Crack model training
* [x] Model evaluation
* [x] Reusable inference class
* [x] Multi-model inference
* [x] Detection post-processing
* [x] CLI inference

## Phase 2 — Backend

* [x] Django project
* [x] Inspections app
* [x] Inspection model
* [x] Database migrations
* [x] Image upload
* [x] ML inference integration
* [x] Inspection persistence
* [x] Inspection retrieval API
* [ ] Inspection list/filter API
* [ ] Authentication
* [ ] User roles
* [ ] API validation and error handling

## Phase 3 — Infrastructure Risk Engine

* [ ] Damage severity calculation
* [ ] Damage coverage calculation
* [ ] Asset health score
* [ ] Risk score
* [ ] Maintenance priority
* [ ] Explainable scoring breakdown
* [ ] Historical inspection comparison

## Phase 4 — Flutter Application

* [ ] Authentication screens
* [ ] Inspector dashboard
* [ ] Camera/image upload
* [ ] Location capture
* [ ] Inspection submission
* [ ] Detection visualization
* [ ] Severity display
* [ ] Inspection history
* [ ] Asset details

## Phase 5 — GIS & Government Dashboard

* [ ] PostgreSQL
* [ ] PostGIS
* [ ] Infrastructure asset mapping
* [ ] Damage heatmaps
* [ ] Inspection map
* [ ] Priority-based filtering
* [ ] District/area analytics
* [ ] Government/admin dashboard

## Phase 6 — Production

* [ ] Production database
* [ ] Model-serving optimization
* [ ] Asynchronous inference where required
* [ ] Authentication hardening
* [ ] API security
* [ ] Dockerization
* [ ] Cloud deployment
* [ ] Monitoring
* [ ] Logging

---

# Design Goals

InfraIntel is being developed around several principles:

### 1. Explainability

Maintenance decisions should be based on understandable factors rather than an opaque prediction.

### 2. India-focused infrastructure

The initial computer-vision models prioritize road-damage data relevant to Indian road conditions.

### 3. Location-aware inspection

Each inspection can be associated with geographic coordinates, allowing future spatial analysis and infrastructure mapping.

### 4. Modular ML architecture

The ML inference layer is separated from Django so models can be reused by the API, CLI tools, and future applications.

### 5. Progressive complexity

The system starts with synchronous inference and deterministic scoring. Components such as Celery, Redis, PostGIS, and predictive maintenance models will be introduced when the platform actually requires them.

---

# Long-Term Vision

The long-term goal of InfraIntel is to provide a unified infrastructure-monitoring workflow:

```text
                 Inspector
                     │
                     ▼
              Capture Image
                     │
                     ▼
             AI Damage Detection
                     │
                     ▼
             Damage Classification
                     │
                     ▼
              Severity Analysis
                     │
                     ▼
               Asset Health
                     │
                     ▼
             Risk / Priority Score
                     │
                     ▼
            GIS Infrastructure Map
                     │
                     ▼
           Maintenance Planning
                     │
                     ▼
             Historical Tracking
```

This architecture is intended to evolve from individual road-image inspection into a broader infrastructure monitoring platform capable of tracking assets, identifying deterioration, and supporting maintenance planning over time.

---

# License

This project is currently under development.

Dataset licenses and terms of use remain subject to the original dataset providers.
