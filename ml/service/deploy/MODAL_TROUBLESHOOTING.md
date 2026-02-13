# Modal Deployment Troubleshooting Guide

Common issues and solutions for the Cuneiform Sign Detection Modal deployment.

---

## Installation & Setup Issues

### "modal: command not found"

**Problem:** Modal CLI is not installed or not in PATH

**Solution:**
```bash
pip install modal
# If using system Python, may need:
pip3 install modal
# Or with sudo:
sudo pip3 install modal
```

**Verify installation:**
```bash
modal --version
```

---

### "Authentication required"

**Problem:** Modal token not configured

**Solution:**
```bash
modal token new
```

This opens a browser window. Click "Create Token" to authenticate.

**Verify authentication:**
```bash
modal profile current
```

---

## Deployment Issues

### "mmcv-full compilation failed"

**Problem:** mmcv-full couldn't be compiled during image build

**Solution:** Modal should use pre-built wheels. If it fails:

1. Check modal_app.py uses the correct wheel URL:
   ```python
   extra_index_url="https://download.openmmlab.com/mmcv/dist/cu118/torch2.0/index.html"
   ```

2. Try alternative CUDA version:
   ```python
   # For CUDA 11.7:
   extra_index_url="https://download.openmmlab.com/mmcv/dist/cu117/torch2.0/index.html"
   ```

3. Check Modal logs:
   ```bash
   modal app logs cuneiform-detection
   ```

---

### "Model checkpoint not found: /models/epoch_1000.pth"

**Problem:** Checkpoint file not uploaded to Modal volume

**Solution:**
```bash
# List files in volume to verify
modal volume ls cuneiform-models

# If empty, upload the checkpoint
cd "/Volumes/Portable Storage/CUNEIFORM"
modal volume put cuneiform-models \
  "models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth" \
  /models/epoch_1000.pth

# Verify upload
modal volume ls cuneiform-models
```

---

### "sign_mapping.json not found"

**Problem:** Sign mapping file missing from container

**Solution:** The file should be automatically copied during image build. Check that:

1. File exists locally:
   ```bash
   ls -la ml-service/sign_mapping.json
   ```

2. modal_app.py includes:
   ```python
   .copy_local_file("sign_mapping.json", "/root/sign_mapping.json")
   ```

3. Redeploy:
   ```bash
   modal deploy ml-service/modal_app.py
   ```

---

## Runtime Issues

### "CUDA out of memory"

**Problem:** Model requires more GPU memory than available

**Solution:**

1. **Upgrade to larger GPU:**
   Edit modal_app.py:
   ```python
   gpu="A10G",  # 24GB VRAM instead of T4's 16GB
   ```

2. **Reduce batch size** (if processing multiple images):
   In modal_inference.py, ensure single-image inference

3. **Monitor GPU usage:**
   ```bash
   modal app logs cuneiform-detection --follow
   ```

---

### "Cold start too slow (>30 seconds)"

**Problem:** Modal container takes too long to start

**Solutions:**

1. **Keep container warm** (costs ~$0.56/hour while active):
   ```python
   # In modal_app.py function decorator:
   container_idle_timeout=600,  # Keep warm for 10 minutes
   ```

2. **Use smaller container** (if possible):
   - Reduce dependencies
   - Use smaller base image

3. **Accept cold starts:**
   - First request: 5-10 seconds
   - Subsequent requests: <1 second
   - Update UI to show "First request may take 10 seconds"

---

### "Detection returns empty results"

**Problem:** Model runs but finds no signs

**Possible causes:**

1. **Confidence threshold too high:**
   ```bash
   # Test with lower threshold
   curl "https://your-endpoint.modal.run/detect-signs?image_path=...&confidence_threshold=0.1"
   ```

2. **Image preprocessing issues:**
   - Check image loads correctly
   - Verify dimensions are reasonable
   - Ensure image is RGB (not grayscale)

3. **Model not actually loaded:**
   ```bash
   # Check health endpoint
   curl "https://your-endpoint.modal.run/health"
   # Should show: "model_exists": true
   ```

4. **Wrong model checkpoint:**
   - Verify checkpoint matches expected classes
   - Check model was trained on cuneiform signs

---

### "Request timeout after 180 seconds"

**Problem:** PHP times out waiting for Modal response

**Solutions:**

1. **Increase PHP timeout:**
   Edit `detect-signs.php`:
   ```php
   CURLOPT_TIMEOUT => 300,  // 5 minutes
   ```

2. **Check Modal logs** for actual error:
   ```bash
   modal app logs cuneiform-detection --follow
   ```

3. **Test endpoint directly:**
   ```bash
   time curl -X POST "https://your-endpoint.modal.run/detect-signs?image_path=..."
   ```

---

## Cost & Quota Issues

### "Free tier quota exceeded"

**Problem:** Used all $30 of free credit

**Solutions:**

1. **Check usage:**
   ```bash
   modal app stats cuneiform-detection
   ```

2. **Add payment method:**
   - Go to https://modal.com/settings/billing
   - Add credit card
   - Set spending limits

3. **Optimize usage:**
   - Cache results in your database
   - Don't re-detect same tablet multiple times
   - Use higher confidence threshold to reduce false positives

---

### "Unexpected high costs"

**Problem:** Bills higher than expected

**Debug:**

1. **Check active containers:**
   ```bash
   modal app list
   ```

2. **View detailed usage:**
   - Go to https://modal.com/usage
   - Filter by date range
   - Check GPU hours

3. **Common causes:**
   - Container kept warm 24/7 (check `container_idle_timeout`)
   - Multiple deployments running simultaneously
   - Development testing left running

**Solution:**
```bash
# Stop all deployments
modal app stop cuneiform-detection

# Redeploy with conservative settings
modal deploy ml-service/modal_app.py
```

---

## Network & Connectivity Issues

### "Failed to fetch: Network error"

**Problem:** Can't reach Modal endpoint from PHP

**Debug:**

1. **Test endpoint directly:**
   ```bash
   curl https://your-endpoint.modal.run/health
   ```

2. **Check firewall:**
   - Ensure outbound HTTPS (443) is allowed
   - Modal runs on standard HTTPS ports

3. **Verify endpoint URL:**
   ```bash
   # Should output endpoint URL
   modal app list
   ```

4. **Check environment variable:**
   ```bash
   # In your PHP environment
   echo $MODAL_ENDPOINT
   ```

---

## Debugging Commands

### View Real-Time Logs
```bash
modal app logs cuneiform-detection --follow
```

### Check Deployment Status
```bash
modal app list
```

### Test Health Endpoint
```bash
curl https://your-username--cuneiform-detection-health.modal.run
```

### Test Detection Endpoint
```bash
curl -X POST "https://your-username--cuneiform-detection-detect-signs.modal.run?image_path=https://cdli.earth/dl/photo/P388097.jpg&confidence_threshold=0.3"
```

### Check Volume Contents
```bash
modal volume ls cuneiform-models
```

### Interactive Shell (for debugging)
```bash
modal shell cuneiform-detection
```

---

## Performance Optimization

### Slow First Request

**Normal behavior:**
- Cold start: 5-10 seconds
- Model loading: 2-3 seconds
- Inference: 0.5-1 second

**To optimize:**
1. Keep container warm (costs $)
2. Cache model in memory after first load (already implemented)
3. Update UI to show "Loading..." message

### Slow Subsequent Requests

**If >2 seconds per request:**

1. **Check GPU utilization:**
   ```bash
   modal app logs cuneiform-detection | grep "GPU"
   ```

2. **Profile inference:**
   Add timing logs in modal_inference.py

3. **Possible issues:**
   - Image too large (resize before detection)
   - Too many detections (increase confidence threshold)
   - Network latency (check image download time)

---

## Getting Help

If issues persist:

1. **Check Modal status:** https://modal.statuspage.io/
2. **Modal docs:** https://modal.com/docs
3. **Modal Discord:** https://discord.gg/modal
4. **Review deployment logs:** `modal app logs cuneiform-detection`

For CUNEIFORM-specific issues, check:
- ml-service.log (local logs before Modal)
- Browser console (JavaScript errors)
- PHP error logs
