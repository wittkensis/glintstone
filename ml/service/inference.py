"""
DETR inference wrapper for cuneiform sign detection.

NOTE: Full inference requires mmcv compiled extensions which have
compatibility issues with macOS ARM64. This module provides:
1. A working API structure for the FastAPI server
2. Checkpoint loading and class mapping
3. Mock inference for development/testing

For production inference, consider:
- Using Docker with the mmdet environment
- Deploying to Modal/RunPod with CUDA
- Using a remote inference API
"""

import json
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Optional, List, Dict
import torchvision.transforms as T


class CuneiformDetector:
    """Cuneiform sign detector using Deformable DETR checkpoint."""

    def __init__(
        self,
        checkpoint_path: str,
        device: str = "auto",
        confidence_threshold: float = 0.3,
    ):
        """
        Initialize the detector.

        Args:
            checkpoint_path: Path to the .pth checkpoint file
            device: 'auto', 'mps', 'cuda', or 'cpu'
            confidence_threshold: Minimum confidence for detections
        """
        self.checkpoint_path = Path(checkpoint_path)
        self.confidence_threshold = confidence_threshold

        # Extract model name from checkpoint path
        # e.g., "/path/models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth"
        # -> model_name: "detr-173-classes-10-2025", epoch: 1000
        self.model_name = self.checkpoint_path.parent.name
        checkpoint_file = self.checkpoint_path.stem  # "epoch_1000"
        self.epoch = (
            checkpoint_file.split("_")[-1] if "_" in checkpoint_file else "unknown"
        )

        # Determine device
        if device == "auto":
            if torch.backends.mps.is_available():
                self.device = "mps"
            elif torch.cuda.is_available():
                self.device = "cuda:0"
            else:
                self.device = "cpu"
        else:
            self.device = device

        print(f"Using device: {self.device}")

        # Load sign mapping
        mapping_path = Path(__file__).parent / "sign_mapping.json"
        with open(mapping_path, "r", encoding="utf-8") as f:
            self.sign_mapping = json.load(f)

        self.class_names = [s["name"] for s in self.sign_mapping]
        self.num_classes = len(self.class_names)
        print(f"Loaded {self.num_classes} class names")

        # Preprocessing transforms (matches training config)
        self.transform = T.Compose(
            [T.ToTensor(), T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])]
        )

        # Model state
        self.model_loaded = False
        self.checkpoint_meta = None

    def load_model(self):
        """Load the model checkpoint metadata."""
        if self.model_loaded:
            return

        print(f"Loading checkpoint from: {self.checkpoint_path}")

        # Load checkpoint to extract metadata
        checkpoint = torch.load(
            self.checkpoint_path, map_location="cpu", weights_only=False
        )

        self.checkpoint_meta = checkpoint.get("meta", {})
        print(f"Checkpoint epoch: {self.checkpoint_meta.get('epoch', 'unknown')}")

        # Verify classes match
        dataset_meta = self.checkpoint_meta.get("dataset_meta", {})
        checkpoint_classes = dataset_meta.get("classes", [])
        if checkpoint_classes:
            print(f"Checkpoint has {len(checkpoint_classes)} classes")
            if len(checkpoint_classes) != self.num_classes:
                print(
                    f"WARNING: Class count mismatch! Expected {self.num_classes}, got {len(checkpoint_classes)}"
                )

        self.model_loaded = True
        print("Model metadata loaded successfully")
        print("\nNOTE: Full inference requires mmcv compiled extensions.")
        print("Currently returning mock data for API development.")

    def detect(self, image_path: str) -> List[Dict]:
        """
        Run detection on an image.

        Currently returns mock data due to mmcv compatibility issues.
        The API structure is correct and ready for when inference is working.

        Args:
            image_path: Path to the image file

        Returns:
            List of detection dicts with keys:
            - class_id: int
            - class_name: str
            - confidence: float
            - bbox: [x_min, y_min, x_max, y_max] in pixels
            - bbox_normalized: [x_min, y_min, x_max, y_max] normalized 0-1
            - unicode: str or None
        """
        if not self.model_loaded:
            self.load_model()

        # Load image to get dimensions
        img = Image.open(image_path).convert("RGB")
        img_width, img_height = img.size

        print(f"Processing image: {image_path}")
        print(f"Image size: {img_width}x{img_height}")

        # Generate mock detections for testing
        # These are sample cuneiform signs that would be detected
        mock_detections = self._generate_mock_detections(img_width, img_height)

        return mock_detections

    def _generate_mock_detections(self, img_width: int, img_height: int) -> List[Dict]:
        """Generate mock detections for API testing."""
        # Common cuneiform signs for testing
        mock_signs = [
            (6, "GAL", 0.92),  # "great"
            (33, "AN", 0.88),  # "heaven/god"
            (23, "DIŠ", 0.85),  # numeral 1
            (34, "NA", 0.82),  # various meanings
            (11, "A", 0.79),  # "water"
            (65, "LU₂", 0.76),  # "man"
            (22, "E₂", 0.73),  # "house"
            (24, "MU", 0.70),  # "year/name"
        ]

        detections = []
        np.random.seed(42)  # Consistent mock results

        # Generate random positions for mock detections
        for i, (class_id, name, conf) in enumerate(mock_signs):
            # Random position within image
            x1 = np.random.randint(50, img_width - 100)
            y1 = np.random.randint(50, img_height - 100)
            w = np.random.randint(30, 80)
            h = np.random.randint(30, 80)
            x2 = min(x1 + w, img_width - 10)
            y2 = min(y1 + h, img_height - 10)

            # Add some noise to confidence
            actual_conf = conf + np.random.uniform(-0.05, 0.05)
            actual_conf = max(0.3, min(0.99, actual_conf))

            if actual_conf >= self.confidence_threshold:
                sign_info = (
                    self.sign_mapping[class_id]
                    if class_id < len(self.sign_mapping)
                    else None
                )

                detection = {
                    "class_id": class_id,
                    "class_name": name,
                    "confidence": float(actual_conf),
                    "bbox": [float(x1), float(y1), float(x2), float(y2)],
                    "bbox_normalized": [
                        x1 / img_width,
                        y1 / img_height,
                        x2 / img_width,
                        y2 / img_height,
                    ],
                    "unicode": sign_info["unicode"] if sign_info else None,
                    "mock": True,  # Flag indicating this is mock data
                }
                detections.append(detection)

        # Sort by confidence
        detections.sort(key=lambda x: x["confidence"], reverse=True)

        return detections

    def get_metadata(self):
        """Return model metadata for API responses."""
        return {
            "model_name": self.model_name,
            "epoch": self.epoch,
            "num_classes": self.num_classes,
            "device": self.device,
            "checkpoint_path": str(self.checkpoint_path),
        }


# Singleton instance for reuse
_detector: Optional[CuneiformDetector] = None


def get_detector(
    checkpoint_path: Optional[str] = None,
    device: str = "auto",
    confidence_threshold: float = 0.3,
) -> CuneiformDetector:
    """Get or create detector singleton."""
    global _detector

    if _detector is None:
        if checkpoint_path is None:
            checkpoint_path = "/Volumes/Portable Storage/CUNEIFORM/models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth"

        _detector = CuneiformDetector(
            checkpoint_path=checkpoint_path,
            device=device,
            confidence_threshold=confidence_threshold,
        )

    return _detector


if __name__ == "__main__":
    import sys

    print("Cuneiform Sign Detection - Test Mode")
    print("=" * 50)

    detector = get_detector()
    detector.load_model()

    print("\nDetector ready!")
    print(f"Device: {detector.device}")
    print(f"Classes: {len(detector.class_names)}")

    if len(sys.argv) >= 2:
        image_path = sys.argv[1]
        detections = detector.detect(image_path)
        print(f"\nFound {len(detections)} signs (mock data):")
        for det in detections[:10]:
            unicode_char = det["unicode"] or "?"
            print(f"  {unicode_char} {det['class_name']}: {det['confidence']:.2%}")
    else:
        print("\nUsage: python inference.py <image_path>")
        print("No image provided, showing sample class data:")
        for i, cls in enumerate(detector.class_names[:10]):
            sign = detector.sign_mapping[i]
            unicode_char = sign["unicode"] or "N/A"
            print(f"  {i}: {cls} ({unicode_char})")
