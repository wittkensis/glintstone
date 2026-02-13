"""
Real DETR inference for cuneiform sign detection using MMDetection.
This module runs actual inference (not mock data) on Modal's GPU infrastructure.
"""

import json
import torch
import numpy as np
from pathlib import Path
from PIL import Image
from typing import Optional, List, Dict
import warnings

# Suppress mmdet warnings
warnings.filterwarnings('ignore')


class CuneiformDetector:
    """Cuneiform sign detector using Deformable DETR checkpoint."""

    def __init__(
        self,
        checkpoint_path: str,
        sign_mapping_path: str,
        device: str = 'cuda',
        confidence_threshold: float = 0.3
    ):
        """
        Initialize the detector.

        Args:
            checkpoint_path: Path to the .pth checkpoint file
            sign_mapping_path: Path to sign_mapping.json
            device: 'cuda', 'cpu', or 'mps'
            confidence_threshold: Minimum confidence for detections
        """
        self.checkpoint_path = Path(checkpoint_path)
        self.sign_mapping_path = Path(sign_mapping_path)
        self.confidence_threshold = confidence_threshold

        # Extract model name from checkpoint path
        self.model_name = self.checkpoint_path.parent.name
        checkpoint_file = self.checkpoint_path.stem
        self.epoch = checkpoint_file.split('_')[-1] if '_' in checkpoint_file else 'unknown'

        # Device setup
        self.device = device
        print(f"Using device: {self.device}")

        # Load sign mapping
        with open(self.sign_mapping_path, 'r', encoding='utf-8') as f:
            self.sign_mapping = json.load(f)

        self.class_names = [s['name'] for s in self.sign_mapping]
        self.num_classes = len(self.class_names)
        print(f"Loaded {self.num_classes} class names")

        # Model state
        self.model = None
        self.model_loaded = False
        self.checkpoint_meta = None

    def load_model(self):
        """Load the DETR model from checkpoint."""
        if self.model_loaded:
            return

        print(f"Loading checkpoint from: {self.checkpoint_path}")

        try:
            # Import MMDetection modules
            from mmdet.apis import init_detector
            from mmengine.config import Config

            # Load checkpoint to inspect structure
            checkpoint = torch.load(
                self.checkpoint_path,
                map_location='cpu',
                weights_only=False
            )

            self.checkpoint_meta = checkpoint.get('meta', {})
            dataset_meta = self.checkpoint_meta.get('dataset_meta', {})

            # Get config from checkpoint metadata
            if 'cfg' in self.checkpoint_meta:
                # Config embedded in checkpoint
                cfg = Config(self.checkpoint_meta['cfg'])
            else:
                # Build config manually for DETR model
                cfg = self._build_detr_config()

            # Override number of classes to match our dataset
            if hasattr(cfg.model, 'bbox_head'):
                cfg.model.bbox_head.num_classes = self.num_classes
            elif hasattr(cfg.model, 'roi_head'):
                cfg.model.roi_head.bbox_head.num_classes = self.num_classes

            # Initialize model
            self.model = init_detector(
                cfg,
                str(self.checkpoint_path),
                device=self.device
            )

            self.model_loaded = True
            print(f"Model loaded successfully on {self.device}")
            print(f"Checkpoint epoch: {self.checkpoint_meta.get('epoch', 'unknown')}")

        except Exception as e:
            print(f"Error loading model: {e}")
            raise

    def _build_detr_config(self):
        """
        Build a minimal DETR config for inference.
        This is used if the config isn't embedded in the checkpoint.
        """
        from mmengine.config import Config

        cfg_dict = dict(
            model=dict(
                type='DETR',
                num_queries=300,
                backbone=dict(
                    type='ResNet',
                    depth=50,
                    num_stages=4,
                    out_indices=(3,),
                    frozen_stages=1,
                    norm_cfg=dict(type='BN', requires_grad=False),
                    norm_eval=True,
                    style='pytorch'
                ),
                bbox_head=dict(
                    type='DETRHead',
                    num_classes=self.num_classes,
                    in_channels=2048,
                    transformer=dict(
                        type='Transformer',
                        encoder=dict(
                            type='DetrTransformerEncoder',
                            num_layers=6,
                            transformerlayers=dict(
                                type='BaseTransformerLayer',
                                attn_cfgs=dict(
                                    type='MultiheadAttention',
                                    embed_dims=256,
                                    num_heads=8,
                                    dropout=0.1),
                                ffn_cfgs=dict(
                                    type='FFN',
                                    embed_dims=256,
                                    feedforward_channels=2048,
                                    num_fcs=2,
                                    ffn_drop=0.1,
                                    act_cfg=dict(type='ReLU', inplace=True)),
                                operation_order=('self_attn', 'norm', 'ffn', 'norm'))),
                        decoder=dict(
                            type='DetrTransformerDecoder',
                            num_layers=6,
                            transformerlayers=dict(
                                type='DetrTransformerDecoderLayer',
                                attn_cfgs=[
                                    dict(
                                        type='MultiheadAttention',
                                        embed_dims=256,
                                        num_heads=8,
                                        dropout=0.1),
                                    dict(
                                        type='MultiheadAttention',
                                        embed_dims=256,
                                        num_heads=8,
                                        dropout=0.1)
                                ],
                                ffn_cfgs=dict(
                                    type='FFN',
                                    embed_dims=256,
                                    feedforward_channels=2048,
                                    num_fcs=2,
                                    ffn_drop=0.1,
                                    act_cfg=dict(type='ReLU', inplace=True)),
                                operation_order=('self_attn', 'norm', 'cross_attn', 'norm',
                                                'ffn', 'norm')),
                            return_intermediate=True)),
                    positional_encoding=dict(
                        type='SinePositionalEncoding',
                        num_feats=128,
                        normalize=True)),
                train_cfg=dict(
                    assigner=dict(
                        type='HungarianAssigner',
                        match_costs=[
                            dict(type='ClassificationCost', weight=1.),
                            dict(type='BBoxL1Cost', weight=5.0),
                            dict(type='IoUCost', iou_mode='giou', weight=2.0)
                        ])),
                test_cfg=dict(max_per_img=100))
        )

        return Config(cfg_dict)

    def detect(self, image_path: str) -> List[Dict]:
        """
        Run detection on an image.

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
        img = Image.open(image_path).convert('RGB')
        img_width, img_height = img.size
        img_array = np.array(img)

        print(f"Processing image: {image_path}")
        print(f"Image size: {img_width}x{img_height}")

        try:
            # Run inference using MMDetection API
            from mmdet.apis import inference_detector

            result = inference_detector(self.model, img_array)

            # Parse predictions
            detections = []

            # MMDet v3.x returns DetDataSample
            if hasattr(result, 'pred_instances'):
                pred_instances = result.pred_instances

                bboxes = pred_instances.bboxes.cpu().numpy()  # [N, 4] (x1, y1, x2, y2)
                scores = pred_instances.scores.cpu().numpy()  # [N]
                labels = pred_instances.labels.cpu().numpy()  # [N]

                for bbox, score, label in zip(bboxes, scores, labels):
                    if score >= self.confidence_threshold:
                        x1, y1, x2, y2 = bbox

                        # Get sign info
                        class_id = int(label)
                        sign_info = self.sign_mapping[class_id] if class_id < len(self.sign_mapping) else None
                        class_name = sign_info['name'] if sign_info else f'class_{class_id}'

                        detection = {
                            'class_id': class_id,
                            'class_name': class_name,
                            'confidence': float(score),
                            'bbox': [float(x1), float(y1), float(x2), float(y2)],
                            'bbox_normalized': [
                                x1 / img_width,
                                y1 / img_height,
                                x2 / img_width,
                                y2 / img_height
                            ],
                            'unicode': sign_info['unicode'] if sign_info else None
                        }
                        detections.append(detection)

            else:
                # Fallback for older MMDet versions
                # result is a tuple of (bboxes, labels) for each class
                for class_id, class_result in enumerate(result):
                    for detection in class_result:
                        if len(detection) == 5:  # [x1, y1, x2, y2, score]
                            x1, y1, x2, y2, score = detection

                            if score >= self.confidence_threshold:
                                sign_info = self.sign_mapping[class_id] if class_id < len(self.sign_mapping) else None
                                class_name = sign_info['name'] if sign_info else f'class_{class_id}'

                                det_dict = {
                                    'class_id': class_id,
                                    'class_name': class_name,
                                    'confidence': float(score),
                                    'bbox': [float(x1), float(y1), float(x2), float(y2)],
                                    'bbox_normalized': [
                                        x1 / img_width,
                                        y1 / img_height,
                                        x2 / img_width,
                                        y2 / img_height
                                    ],
                                    'unicode': sign_info['unicode'] if sign_info else None
                                }
                                detections.append(det_dict)

            # Sort by confidence
            detections.sort(key=lambda x: x['confidence'], reverse=True)

            print(f"Found {len(detections)} detections above threshold {self.confidence_threshold}")

            return detections

        except Exception as e:
            print(f"Error during inference: {e}")
            raise

    def get_metadata(self):
        """Return model metadata for API responses."""
        return {
            'model_name': self.model_name,
            'epoch': self.epoch,
            'num_classes': self.num_classes,
            'device': self.device,
            'checkpoint_path': str(self.checkpoint_path)
        }
