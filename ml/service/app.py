"""
FastAPI server for cuneiform sign detection.
Runs locally on port 8000.
"""

import os
import tempfile
import time
from pathlib import Path
from typing import Optional

from fastapi import FastAPI, UploadFile, File, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from inference import get_detector

# Initialize FastAPI app
app = FastAPI(
    title="Cuneiform Sign Detection API",
    description="DETR-based cuneiform sign detection for tablet images",
    version="1.0.0",
)

# Add CORS middleware for local development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for local dev
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Response models
class DetectionResult(BaseModel):
    class_id: int
    class_name: str
    confidence: float
    bbox: list[float]  # [x_min, y_min, x_max, y_max] pixels
    bbox_normalized: list[float]  # [x_min, y_min, x_max, y_max] 0-1
    unicode: Optional[str]
    mock: Optional[bool] = None  # Flag indicating mock data


class DetectionResponse(BaseModel):
    success: bool
    inference_time_ms: float
    image_width: int
    image_height: int
    num_detections: int
    detections: list[DetectionResult]
    model_name: Optional[str] = None
    model_epoch: Optional[str] = None
    model_device: Optional[str] = None


class HealthResponse(BaseModel):
    status: str
    model_loaded: bool
    device: str


# Global state
_model_loaded = False


@app.on_event("startup")
async def startup_event():
    """Pre-load the model on startup for faster first inference."""
    global _model_loaded
    print("Starting up... Model will be loaded on first request.")
    # Don't load model on startup to allow fast server start
    # Model will be loaded lazily on first detection request


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Health check endpoint."""
    detector = get_detector()
    return HealthResponse(
        status="healthy", model_loaded=detector.model_loaded, device=detector.device
    )


@app.get("/classes")
async def get_classes():
    """Return the list of sign classes the model can detect."""
    detector = get_detector()
    return {"num_classes": len(detector.sign_mapping), "classes": detector.sign_mapping}


@app.post("/detect-signs", response_model=DetectionResponse)
async def detect_signs(
    file: UploadFile = File(...),
    confidence_threshold: float = Query(
        0.3, ge=0.0, le=1.0, description="Minimum confidence threshold"
    ),
):
    """
    Detect cuneiform signs in an uploaded image.

    - **file**: Image file (JPEG, PNG)
    - **confidence_threshold**: Minimum confidence for detections (0-1)

    Returns detected signs with bounding boxes and confidence scores.
    """
    global _model_loaded

    # Validate file type
    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(
            status_code=400,
            detail=f"Invalid file type: {file.content_type}. Expected image/*",
        )

    # Save uploaded file to temp location
    suffix = Path(file.filename or "image.jpg").suffix or ".jpg"
    with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
        content = await file.read()
        tmp.write(content)
        tmp_path = tmp.name

    try:
        # Get detector (lazy load model on first call)
        detector = get_detector(confidence_threshold=confidence_threshold)

        if not _model_loaded:
            print("Loading model for first time...")
            detector.load_model()
            _model_loaded = True
            print("Model loaded!")

        # Update threshold if different
        detector.confidence_threshold = confidence_threshold

        # Run detection
        start_time = time.time()
        detections = detector.detect(tmp_path)
        inference_time = (time.time() - start_time) * 1000  # ms

        # Get image dimensions
        from PIL import Image

        with Image.open(tmp_path) as img:
            img_width, img_height = img.size

        # Get model metadata
        metadata = detector.get_metadata()

        return DetectionResponse(
            success=True,
            inference_time_ms=round(inference_time, 2),
            image_width=img_width,
            image_height=img_height,
            num_detections=len(detections),
            detections=[DetectionResult(**d) for d in detections],
            model_name=metadata["model_name"],
            model_epoch=metadata["epoch"],
            model_device=metadata["device"],
        )

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")

    finally:
        # Clean up temp file
        os.unlink(tmp_path)


@app.post("/detect-signs-by-path")
async def detect_signs_by_path(
    image_path: str = Query(..., description="Path to image file on disk"),
    confidence_threshold: float = Query(0.3, ge=0.0, le=1.0),
):
    """
    Detect signs in an image at a local file path.
    Useful for processing database images without re-uploading.
    """
    global _model_loaded

    if not os.path.exists(image_path):
        raise HTTPException(status_code=404, detail=f"Image not found: {image_path}")

    try:
        detector = get_detector(confidence_threshold=confidence_threshold)

        if not _model_loaded:
            print("Loading model for first time...")
            detector.load_model()
            _model_loaded = True
            print("Model loaded!")

        detector.confidence_threshold = confidence_threshold

        start_time = time.time()
        detections = detector.detect(image_path)
        inference_time = (time.time() - start_time) * 1000

        from PIL import Image

        with Image.open(image_path) as img:
            img_width, img_height = img.size

        # Get model metadata
        metadata = detector.get_metadata()

        return {
            "success": True,
            "inference_time_ms": round(inference_time, 2),
            "image_width": img_width,
            "image_height": img_height,
            "num_detections": len(detections),
            "detections": detections,
            "model_name": metadata["model_name"],
            "model_epoch": metadata["epoch"],
            "model_device": metadata["device"],
        }

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Detection failed: {str(e)}")


if __name__ == "__main__":
    import uvicorn

    print("Starting Cuneiform Sign Detection Server...")
    print("API docs available at: http://localhost:8000/docs")

    uvicorn.run(
        "app:app",
        host="0.0.0.0",
        port=8000,
        reload=False,  # Disable reload to keep model in memory
        workers=1,  # Single worker to share model
    )
