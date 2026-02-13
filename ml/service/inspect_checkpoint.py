#!/usr/bin/env python3
"""
Inspect the DETR checkpoint to understand its structure.
Run this to discover:
- Model architecture keys
- Number of classes
- State dict structure
"""

import torch
from pathlib import Path


def inspect_checkpoint(checkpoint_path: str):
    """Load and inspect a PyTorch checkpoint."""
    print(f"Loading checkpoint: {checkpoint_path}")

    # Load checkpoint
    checkpoint = torch.load(checkpoint_path, map_location='cpu', weights_only=False)

    print(f"\nCheckpoint type: {type(checkpoint)}")

    if isinstance(checkpoint, dict):
        print(f"Top-level keys: {list(checkpoint.keys())}")

        # Check for state_dict
        if 'state_dict' in checkpoint:
            state_dict = checkpoint['state_dict']
            print(f"\nstate_dict has {len(state_dict)} keys")

            # Find classifier head to determine number of classes
            for key in state_dict.keys():
                if 'class' in key.lower() or 'cls' in key.lower() or 'head' in key.lower():
                    tensor = state_dict[key]
                    print(f"  {key}: {tensor.shape}")

            # Print first 20 keys to understand structure
            print("\nFirst 20 keys in state_dict:")
            for i, key in enumerate(list(state_dict.keys())[:20]):
                print(f"  {key}: {state_dict[key].shape}")

        # Check for meta info
        if 'meta' in checkpoint:
            meta = checkpoint['meta']
            print(f"\nMeta info: {meta}")

        # Check for config
        if 'cfg' in checkpoint or 'config' in checkpoint:
            cfg_key = 'cfg' if 'cfg' in checkpoint else 'config'
            print(f"\nConfig found under '{cfg_key}'")
            cfg = checkpoint[cfg_key]
            if hasattr(cfg, 'model'):
                print(f"Model config: {cfg.model}")
    else:
        # Direct state dict
        print(f"Direct state dict with {len(checkpoint)} keys")
        print("\nFirst 20 keys:")
        for i, key in enumerate(list(checkpoint.keys())[:20]):
            print(f"  {key}: {checkpoint[key].shape}")


if __name__ == "__main__":
    checkpoint_path = Path(__file__).parent.parent / "models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth"

    if not checkpoint_path.exists():
        print(f"Checkpoint not found at: {checkpoint_path}")
        print("Trying alternative path...")
        checkpoint_path = Path("/Volumes/Portable Storage/CUNEIFORM/models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth")

    if checkpoint_path.exists():
        inspect_checkpoint(str(checkpoint_path))
    else:
        print(f"Checkpoint not found: {checkpoint_path}")
