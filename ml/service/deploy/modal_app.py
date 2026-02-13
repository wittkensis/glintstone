"""
Modal deployment for Cuneiform Sign Detection
Deploys DETR model with MMDetection on Modal's GPU infrastructure
"""

import modal
import os
from pathlib import Path

# Create Modal app
app = modal.App("cuneiform-detection")

# Create persistent volume for model checkpoint
volume = modal.Volume.from_name("cuneiform-models", create_if_missing=True)

# Define GPU-enabled container image
# This installs all dependencies including mmcv-full with CUDA support
image = (
    modal.Image.debian_slim(python_version="3.10")
    .apt_install("git", "libgl1", "libglib2.0-0")
    .pip_install(
        "torch==2.0.1",
        "torchvision==0.15.2",
        "numpy==1.24.3",
        "pillow==10.0.0",
        "fastapi==0.100.0",
        "python-multipart==0.0.6",
    )
    # Install mmcv-full with CUDA support (prebuilt wheel for faster build)
    .pip_install(
        "mmcv-full==1.7.1",
        pre=True,
        extra_index_url="https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html",
    )
    .pip_install(
        "mmengine==0.10.3",
        "mmdet==3.3.0",
    )
    .copy_local_file("sign_mapping.json", "/root/sign_mapping.json")
    .copy_local_file("modal_inference.py", "/root/modal_inference.py")
)

# Model configuration
MODEL_PATH = "/models/epoch_1000.pth"
CONFIDENCE_THRESHOLD = 0.3


@app.function(
    image=image,
    gpu="T4",  # NVIDIA T4 GPU with 16GB VRAM - sufficient for DETR
    volumes={"/models": volume},
    timeout=300,  # 5 minute timeout
    container_idle_timeout=120,  # Keep warm for 2 minutes after request
)
@modal.web_endpoint(method="POST")
async def detect_signs(image_path: str = modal.web_parameter(), confidence_threshold: float = modal.web_parameter(default=0.3)):
    """
    Detect cuneiform signs in an image.

    Args:
        image_path: Path to image file (can be local or URL)
        confidence_threshold: Minimum confidence for detections (0-1)

    Returns:
        JSON with detections, model metadata, and inference time
    """
    import time
    import json
    import sys
    from PIL import Image
    import tempfile
    import urllib.request

    # Import detector
    sys.path.insert(0, "/root")
    from modal_inference import CuneiformDetector

    start_time = time.time()

    try:
        # Initialize detector (cached after first load)
        detector = CuneiformDetector(
            checkpoint_path=MODEL_PATH,
            sign_mapping_path="/root/sign_mapping.json",
            device="cuda",
            confidence_threshold=confidence_threshold
        )

        # Load model if not already loaded
        if not detector.model_loaded:
            detector.load_model()

        # Handle image input
        if image_path.startswith('http://') or image_path.startswith('https://'):
            # Download image from URL
            with tempfile.NamedTemporaryFile(delete=False, suffix='.jpg') as tmp:
                urllib.request.urlretrieve(image_path, tmp.name)
                local_image_path = tmp.name
        else:
            # Use local path
            local_image_path = image_path

        # Run detection
        detections = detector.detect(local_image_path)

        # Get image dimensions
        with Image.open(local_image_path) as img:
            img_width, img_height = img.size

        # Clean up temp file if downloaded
        if image_path.startswith('http'):
            os.unlink(local_image_path)

        # Calculate inference time
        inference_time_ms = (time.time() - start_time) * 1000

        # Get model metadata
        metadata = detector.get_metadata()

        return {
            "success": True,
            "inference_time_ms": round(inference_time_ms, 2),
            "image_width": img_width,
            "image_height": img_height,
            "num_detections": len(detections),
            "detections": detections,
            "model_name": metadata['model_name'],
            "model_epoch": metadata['epoch'],
            "model_device": metadata['device']
        }

    except FileNotFoundError as e:
        return {
            "success": False,
            "error": f"Image file not found: {image_path}",
            "detail": str(e)
        }
    except Exception as e:
        return {
            "success": False,
            "error": "Detection failed",
            "detail": str(e)
        }


@app.function(
    image=image,
    gpu="T4",
    volumes={"/models": volume},
    timeout=300,
)
@modal.web_endpoint(method="POST")
async def detect_signs_by_path(image_path: str = modal.web_parameter(), confidence_threshold: float = modal.web_parameter(default=0.3)):
    """
    Detect signs in an image at a local file path.
    Equivalent to the local API's /detect-signs-by-path endpoint.

    Note: This works with URLs but not with local file paths since Modal runs remotely.
    Use detect_signs() instead which handles both cases.
    """
    return await detect_signs(image_path=image_path, confidence_threshold=confidence_threshold)


@app.function(image=image, volumes={"/models": volume})
@modal.web_endpoint(method="GET")
def health():
    """Health check endpoint."""
    import sys
    sys.path.insert(0, "/root")
    from modal_inference import CuneiformDetector

    # Check if model file exists
    model_exists = os.path.exists(MODEL_PATH)

    return {
        "status": "healthy",
        "model_path": MODEL_PATH,
        "model_exists": model_exists,
        "gpu": "T4"
    }


@app.function(image=image)
@modal.web_endpoint(method="GET")
def classes():
    """Return the list of sign classes the model can detect."""
    import json
    import sys
    sys.path.insert(0, "/root")

    with open("/root/sign_mapping.json", 'r', encoding='utf-8') as f:
        sign_mapping = json.load(f)

    return {
        "num_classes": len(sign_mapping),
        "classes": sign_mapping
    }


# Local development entry point
@app.local_entrypoint()
def main():
    """
    Local testing entry point.
    Run with: modal run modal_app.py
    """
    print("Testing Modal deployment locally...")

    # Test health endpoint
    result = health.remote()
    print(f"Health check: {result}")

    print("\nTo deploy to Modal cloud:")
    print("  modal deploy modal_app.py")
    print("\nTo test locally:")
    print("  modal serve modal_app.py")
    print("  # Then access at http://localhost:8000")
