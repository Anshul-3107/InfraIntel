import threading

import torch

from ml.inference.detector import DamageDetector

_detector = None
_lock = threading.Lock()


def run_detection(image_path) -> dict:
    global _detector
    with _lock:
        if _detector is None:
            device = 0 if torch.cuda.is_available() else "cpu"
            _detector = DamageDetector(device=device)
        return _detector.detect(str(image_path))