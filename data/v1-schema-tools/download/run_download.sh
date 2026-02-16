#!/bin/bash
cd "/Volumes/Portable Storage/CUNEIFORM"
python3 download_cuneiform_data.py --source cdli --limit 10000 --no-verify-ssl > download_images.log 2>&1
