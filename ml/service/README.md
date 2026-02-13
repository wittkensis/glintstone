# ML Service for Cuneiform Sign Detection

Local FastAPI service for running EBL_OCR (Deformable DETR) model on tablet images.

## Current Status

**⚠️ Mock Data Mode**

The service is fully functional but returns mock detection data due to mmcv compatibility issues with macOS ARM64 (Apple Silicon). The API structure, database integration, and UI can all be developed and tested with mock data.

For real inference, see [Production Inference](#production-inference) below.

## Setup

```bash
cd ml-service

# Requires Python 3.11 (3.13 has compatibility issues)
/opt/homebrew/bin/python3.11 -m venv venv
source venv/bin/activate

# Install dependencies
pip install torch torchvision pillow numpy fastapi uvicorn python-multipart mmengine
```

## Running the Server

```bash
source venv/bin/activate
python app.py
```

The server will start at `http://localhost:8000`.

API documentation available at: http://localhost:8000/docs

## API Endpoints

### Health Check
```bash
curl http://localhost:8000/health
```

### Get Sign Classes
```bash
curl http://localhost:8000/classes
```

### Detect Signs (Upload)
```bash
curl -X POST "http://localhost:8000/detect-signs" \
  -F "file=@/path/to/tablet.jpg"
```

### Detect Signs (Local Path)
```bash
curl -X POST "http://localhost:8000/detect-signs-by-path?image_path=/path/to/tablet.jpg"
```

## PHP Integration

The Glintstone PHP app proxies to this service:

```
# Detect signs for a tablet
GET /api/ml/detect-signs.php?p=P123456

# Save results to database
POST /api/ml/save-results.php
{
  "p_number": "P123456",
  "detections": [...],
  "source": "ebl_ocr",
  "image_width": 1024,
  "image_height": 768
}
```

## Configuration

- **Model checkpoint:** `/models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth`
- **Sign mapping:** `sign_mapping.json` (173 sign classes)
- **Default confidence threshold:** 0.3

## Files

```
ml-service/
├── app.py              # FastAPI server
├── inference.py        # DETR model wrapper (currently mock)
├── sign_mapping.json   # 173 classes → sign name + unicode
├── requirements.txt    # Python dependencies
└── README.md
```

## Production Inference

To enable real inference (not mock data), choose one of these approaches:

### Option 1: Docker (Recommended)
Create a Docker container with the proper mmcv/mmdet environment:
```bash
docker build -t cuneiform-ocr .
docker run -p 8000:8000 -v /path/to/models:/models cuneiform-ocr
```

### Option 2: Modal Serverless
Deploy to Modal with CUDA for GPU inference:
```python
# See modal_app.py (to be created)
```

### Option 3: Google Colab
Use Google Colab for inference and call it via API.

## Known Issues

1. **mmcv on ARM64**: The mmcv package requires compiled CUDA extensions that don't build on macOS ARM64. This is a known upstream issue.

2. **Python 3.13**: Too new for mmengine/mmcv. Use Python 3.11.

3. **First request latency**: Model loading takes 10-30 seconds on first request.

## Model Info

- **Architecture**: Deformable DETR
- **Backbone**: ResNet-50
- **Classes**: 173 cuneiform signs
- **Training**: 1000 epochs on eBL annotations
- **mAP@50**: 43.1%
