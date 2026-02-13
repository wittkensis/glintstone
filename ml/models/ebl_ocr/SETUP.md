# eBL OCR -- DETR Sign Detection

Cuneiform sign detection using Deformable DETR with a ResNet-50 backbone. Trained for 1,000 epochs on eBL annotations covering 173 cuneiform sign classes. Achieves mAP@50 = 43.1%.

## Checkpoint

The trained model checkpoint is `detr-173-classes-10-2025.tar.gz`. This file is not included in git (too large). To obtain it:

1. Extract from the eBL OCR training pipeline output
2. Place the `.tar.gz` in this directory
3. Extract: `tar -xzf detr-173-classes-10-2025.tar.gz`

The extracted directory should contain the model weights and configuration used by `ml/service/inference.py`.

## Status in Glintstone

The model is trained and integrated into `ml/service/app.py` (FastAPI). However, it currently runs in **mock mode** on macOS ARM64 due to an mmcv compatibility issue. The inference pipeline works correctly -- only the native library loading fails on Apple Silicon.

Production deployment options:
- Docker container (x86_64)
- Modal serverless (cloud GPU)
- Google Colab (for batch processing)

## Architecture

- Model: Deformable DETR
- Backbone: ResNet-50
- Classes: 173 cuneiform signs (see `ml/service/sign_mapping.json`)
- Input: tablet photograph or line art
- Output: bounding boxes with sign labels and confidence scores
