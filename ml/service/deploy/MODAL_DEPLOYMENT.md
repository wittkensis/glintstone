# Modal Deployment Quick Reference

Fast reference guide for deploying and managing the Cuneiform Sign Detection service on Modal.

---

## Initial Setup (One-Time)

### 1. Install Modal CLI
```bash
pip install modal
```

### 2. Authenticate
```bash
modal token new
```
Opens browser to create token. Click "Create Token".

### 3. Create Volume
```bash
modal volume create cuneiform-models
```

### 4. Upload Model Checkpoint
```bash
cd "/Volumes/Portable Storage/CUNEIFORM"

modal volume put cuneiform-models \
  "models/ebl_ocr/detr-173-classes-10-2025/epoch_1000.pth" \
  /models/epoch_1000.pth
```

Verify upload:
```bash
modal volume ls cuneiform-models
```

---

## Deployment

### First Deployment
```bash
cd "/Volumes/Portable Storage/CUNEIFORM/ml-service"
modal deploy modal_app.py
```

**Expected:**
- Build time: 8-10 minutes (first time)
- Subsequent: 30 seconds
- Returns endpoint URL

### Update Deployment (After Code Changes)
```bash
modal deploy modal_app.py
```

**Zero downtime** - new version gradually replaces old.

---

## Environment Variable

After deployment, set the Modal endpoint in your environment:

```bash
# Get your endpoint URL from deployment output, then:
export MODAL_ENDPOINT="https://your-username--cuneiform-detection-detect-signs.modal.run"
```

**Persistent (add to ~/.zshrc or ~/.bashrc):**
```bash
echo 'export MODAL_ENDPOINT="https://your-username--cuneiform-detection-detect-signs.modal.run"' >> ~/.zshrc
source ~/.zshrc
```

**For PHP/Valet:**
Create `.env` file in project root:
```bash
echo "MODAL_ENDPOINT=https://your-username--cuneiform-detection-detect-signs.modal.run" > "/Volumes/Portable Storage/CUNEIFORM/.env"
```

---

## Testing

### Test Health Endpoint
```bash
curl https://your-username--cuneiform-detection-health.modal.run
```

**Expected response:**
```json
{
  "status": "healthy",
  "model_path": "/models/epoch_1000.pth",
  "model_exists": true,
  "gpu": "T4"
}
```

### Test Detection (Direct)
```bash
curl -X POST "https://your-username--cuneiform-detection-detect-signs.modal.run?image_path=https://cdli.earth/dl/photo/P388097.jpg&confidence_threshold=0.3"
```

### Test via Web UI
1. Open http://glintstone.test/tablets/detail.php?p=P388097
2. Click "Detect Signs" button
3. Should see real detections (not "MOCK DATA")

---

## Monitoring

### View Logs (Real-Time)
```bash
modal app logs cuneiform-detection --follow
```

### View Recent Logs
```bash
modal app logs cuneiform-detection --n 100
```

### Check Deployment Status
```bash
modal app list
```

### Usage Statistics
```bash
modal app stats cuneiform-detection
```

Or visit: https://modal.com/usage

---

## Management

### Stop Deployment
```bash
modal app stop cuneiform-detection
```

**Note:** Deployment will restart automatically on next request (serverless).

### Delete Deployment
```bash
modal app delete cuneiform-detection
```

### List All Deployments
```bash
modal app list
```

---

## Volume Management

### List Files in Volume
```bash
modal volume ls cuneiform-models
```

### Download File from Volume
```bash
modal volume get cuneiform-models /models/epoch_1000.pth ./downloaded_model.pth
```

### Upload New Checkpoint
```bash
modal volume put cuneiform-models \
  "new_checkpoint.pth" \
  /models/epoch_1000.pth
```

### Delete Volume
```bash
modal volume delete cuneiform-models
```

---

## Local Development

### Run Locally (Modal Environment)
```bash
modal serve modal_app.py
```

**Access at:** http://localhost:8000

**Endpoints:**
- Health: http://localhost:8000/health
- Detection: http://localhost:8000/detect-signs

### Test Function Locally
```bash
modal run modal_app.py
```

Runs the `main()` local entrypoint.

### Interactive Shell
```bash
modal shell cuneiform-detection
```

Opens Python shell inside Modal container.

---

## Configuration

### Change GPU Type
Edit `modal_app.py`:
```python
@app.function(
    gpu="A10G",  # Options: T4, A10G, A100, H100
    # ...
)
```

### Adjust Timeout
```python
@app.function(
    timeout=600,  # Seconds (max 10 minutes)
    # ...
)
```

### Keep Warm (Reduce Cold Starts)
```python
@app.function(
    container_idle_timeout=600,  # Keep warm for 10 min
    # ...
)
```

**Cost impact:** Charges for idle time (T4 = $0.56/hour)

---

## Endpoints Reference

After deployment, your endpoints will be:

### Health Check
```
GET https://your-username--cuneiform-detection-health.modal.run
```

### Sign Detection
```
POST https://your-username--cuneiform-detection-detect-signs.modal.run
?image_path={url_or_path}
&confidence_threshold={0.0-1.0}
```

### Class List
```
GET https://your-username--cuneiform-detection-classes.modal.run
```

---

## Costs

### Free Tier
- $30 credit/month
- ~3,200 inferences at 600ms each on T4
- Resets monthly

### Pricing (After Free Tier)
- **T4 GPU:** $0.56/hour = $0.00016/second
- **A10G GPU:** $1.10/hour = $0.0003/second
- **Storage:** $0.10/GB/month (volume)

### Estimated Monthly Costs

| Usage | Inferences/Month | GPU Time | Cost |
|-------|------------------|----------|------|
| Light | 100 | 1 min | $0.01 |
| Medium | 1,000 | 10 min | $0.09 |
| Heavy | 10,000 | 1.67 hrs | $0.94 |
| Very Heavy | 100,000 | 16.67 hrs | $9.34 |

**Storage:** ~$0.05-0.10/month for model checkpoint

---

## Common Commands

```bash
# Full deployment workflow
modal deploy modal_app.py

# Test locally
modal serve modal_app.py

# View logs
modal app logs cuneiform-detection --follow

# Check status
modal app list

# Stop deployment
modal app stop cuneiform-detection

# Check usage/costs
modal app stats cuneiform-detection

# Upload model
modal volume put cuneiform-models "local/path.pth" /models/epoch_1000.pth

# Interactive debugging
modal shell cuneiform-detection
```

---

## Troubleshooting

For detailed troubleshooting, see [MODAL_TROUBLESHOOTING.md](MODAL_TROUBLESHOOTING.md).

**Quick fixes:**

- **Model not found:** Re-upload checkpoint to volume
- **Cold starts slow:** Increase `container_idle_timeout`
- **CUDA OOM:** Upgrade to A10G GPU
- **Auth error:** Run `modal token new`
- **Build fails:** Check logs with `modal app logs`

---

## Links

- **Modal Dashboard:** https://modal.com/apps
- **Usage & Billing:** https://modal.com/usage
- **Documentation:** https://modal.com/docs
- **Status Page:** https://modal.statuspage.io/

---

## Support

- **Modal Discord:** https://discord.gg/modal
- **Modal Docs:** https://modal.com/docs
- **GitHub Issues:** https://github.com/modal-labs/modal-client/issues
