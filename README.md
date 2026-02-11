# GLINTSTONE - Cuneiform Research Database

> Explore 389,715+ cuneiform tablets with ML-powered sign detection

## Quick Start

### First Time Setup (15 minutes)
```bash
./setup-server.sh
```

### Daily Use (One Command)
```bash
./start-glintstone.sh
```

This starts:
- ✅ Valet web server
- ✅ ML detection service
- ✅ Opens browser to http://glintstone.test

**To stop:**
```bash
./stop-glintstone.sh
# Or press Ctrl+C in the terminal running start-glintstone.sh
```

---

## What's Inside

- **389,715 artifacts** from CDLI
- **SQLite database** (297MB)
- **ML sign detection** (DETR model)
- **Remote image support** (automatic CDLI download)
- **Dictionary browser** with linguistic metadata
- **ATF viewer** with parallel text display

---

## Access Points

```
Main Site:       http://glintstone.test
Tablet Browser:  http://glintstone.test/tablets/detail.php?p=P388097
Dictionary:      http://glintstone.test/dictionary/
Collections:     http://glintstone.test/collections/
ML Detection:    http://glintstone.test/api/ml/detect-signs.php?p=P388097
```

---

## Scripts

| Script | Purpose |
|--------|---------|
| `setup-server.sh` | One-time setup (installs Valet) |
| `start-glintstone.sh` | Start everything |
| `stop-glintstone.sh` | Stop services |
| `downgrade-php.sh` | Fix PHP version issues |
| `test-detection.php` | Test ML without browser |

---

## Features Added Today

### 1. Remote Image Support ✨
- Automatically downloads images from CDLI
- Streaming download (no memory issues)
- Works with tablets that don't have local images
- File: `app/public_html/api/ml/detect-signs.php`

### 2. ML Detection Progress 📊
- Real-time elapsed time
- Status messages (Initializing → Loading model → Running)
- Model metadata display (name, epoch, device, inference time)
- File: `app/public_html/assets/js/ml-panel.js`

### 3. Enhanced Error Messages 💬
- Clear explanations when ML service isn't running
- Helpful hints for common issues
- Validates image downloads
- File: `app/public_html/assets/js/ml-panel.js`

### 4. Proper Web Server 🚀
- Replaced crashing PHP dev server with Valet
- Handles large SQLite databases
- Production-quality setup
- File: `setup-server.sh`

---

## Architecture

```
Browser
  ↓
Valet (Nginx + PHP-FPM)
  ↓
┌─────────────────────────┐
│  GLINTSTONE Backend     │
│  - SQLite (297MB)       │
│  - PHP APIs             │
│  - JavaScript UI        │
└─────────────────────────┘
  ↓                    ↓
CDLI Images      ML Service
(Remote)         (localhost:8000)
```

---

## Troubleshooting

### Services won't start
```bash
# Check status
valet status
php -v

# Restart everything
valet restart
./stop-glintstone.sh
./start-glintstone.sh
```

### ML detection not working
```bash
# Check if service is running
lsof -i :8000

# View logs
tail -f ml-service.log

# Restart just ML service
./stop-glintstone.sh
./start-glintstone.sh
```

### Site not loading
```bash
# Check if linked
valet links

# Re-link if needed
cd app/public_html
valet link glintstone
```

---

## Development

### Database
- **Location:** `database/glintstone.db`
- **Size:** 297MB
- **Records:** 389,715 artifacts
- **Engine:** SQLite 3
- **Why SQLite?** Perfect for read-heavy, single-user research databases

### ML Service
- **Model:** DETR (DEtection TRansformer)
- **Classes:** 173 cuneiform signs
- **Framework:** FastAPI + PyTorch
- **Inference:** CPU (MPS support for Apple Silicon)

### Frontend
- **Style:** Custom CSS with CSS Grid/Flexbox
- **JavaScript:** Vanilla JS (no framework)
- **Components:** Modular, reusable components

---

## File Structure

```
CUNEIFORM/
├── app/public_html/          # Web application
│   ├── api/                  # API endpoints
│   │   └── ml/               # ML detection API
│   ├── assets/               # CSS, JS, images
│   ├── collections/          # Collection browser
│   ├── dictionary/           # Dictionary browser
│   ├── includes/             # PHP utilities
│   └── tablets/              # Tablet detail pages
├── database/                 # SQLite database
│   ├── glintstone.db         # Main database
│   └── images/               # Cached tablet images
├── ml-service/               # FastAPI ML service
│   ├── app.py                # Main server
│   ├── inference.py          # Detection logic
│   └── sign_mapping.json     # Sign classifications
└── models/                   # ML model checkpoints
    └── ebl_ocr/              # DETR model
```

---

## Next Steps

- [ ] Add sign search functionality
- [ ] Implement annotation saving
- [ ] Add user preferences
- [ ] Export detection results
- [ ] Batch processing

---

## Credits

- **CDLI:** Cuneiform Digital Library Initiative (data source)
- **eBL:** electronic Babylonian Library (annotations)
- **CompVis ML:** Sign detection dataset

---

## Support

For issues or questions:
1. Check `SERVER-SETUP.md` for detailed setup info
2. View logs: `tail -f ml-service.log`
3. Check Valet status: `valet status`

**Database works perfectly. Server is solid. ML detection is operational. Happy researching! 🏺✨**
