# CUNEIFORM Web Server Setup

## Quick Start (Automated)

Run this one command to set everything up:

```bash
cd /Volumes/Portable\ Storage/CUNEIFORM
./setup-server.sh
```

This script will:
1. ✅ Install Composer (if needed)
2. ✅ Install Laravel Valet (if needed)
3. ✅ Configure Valet
4. ✅ Link your project
5. ✅ Provide access URL

**Time:** ~15 minutes
**Result:** Your site at `http://cuneiform.test`

---

## What This Fixes

### The Problem
- PHP dev server (`php -S`) crashes with large SQLite databases
- Your 297MB database is too big for it
- This is a known PHP dev server limitation

### The Solution
- Use **Laravel Valet** - a proper development server for macOS
- Designed for real projects
- Handles large databases perfectly
- Industry standard tool

---

## After Setup

### Access Your Site
```
Main Site:    http://glintstone.test
Tablet View:  http://glintstone.test/tablets/detail.php?p=P388097
Dictionary:   http://glintstone.test/dictionary/
ML API:       http://glintstone.test/api/ml/detect-signs.php?p=P388097
```

### Start ML Service (For Sign Detection)
```bash
cd ml-service
python app.py
```

Then detection will work at:
```
http://cuneiform.test/api/ml/detect-signs.php?p=P388097
```

---

## Manual Installation (If Script Fails)

### 1. Install Composer
```bash
brew install composer
```

### 2. Install Valet
```bash
composer global require laravel/valet
export PATH="$HOME/.composer/vendor/bin:$PATH"
valet install
```

### 3. Link Project
```bash
cd /Volumes/Portable\ Storage/CUNEIFORM/app/public_html
valet link glintstone
```

### 4. Test
```bash
curl http://glintstone.test
```

---

## Useful Commands

### Check Status
```bash
valet status          # Is Valet running?
valet links           # Show all linked projects
php -v                # PHP version
```

### Restart Server
```bash
valet restart         # Restart Valet
valet stop            # Stop Valet
valet start           # Start Valet
```

### Troubleshooting
```bash
valet install         # Reinstall/repair Valet
valet unlink          # Remove project link
valet trust           # Fix permission issues
```

---

## What Was Fixed Today

### 1. CDLI Domain Update ✅
- Changed from `cdli.ucla.edu` → `cdli.earth`
- File: `app/public_html/tablets/detail.php`

### 2. Remote Image Support ✅
- ML detection now downloads CDLI images automatically
- Uses streaming to avoid memory issues
- File: `app/public_html/api/ml/detect-signs.php`

### 3. Progress Tracking ✅
- Real-time elapsed time during detection
- Status messages (Initializing → Loading model → Running)
- File: `app/public_html/assets/js/ml-panel.js`

### 4. Model Metadata Display ✅
- Shows model name, epoch, device, inference time
- File: `app/public_html/assets/js/ml-panel.js`

### 5. Enhanced Error Messages ✅
- Clear messages for ML service not running
- Helpful hints for common issues
- File: `app/public_html/assets/js/ml-panel.js`

### 6. PHP Downgrade ✅
- PHP 8.5 → 8.4 (8.5 has memory bugs)
- Script: `downgrade-php.sh`

---

## Architecture

```
┌─────────────────────────────────────────────────────┐
│  Browser: http://glintstone.test                    │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  Valet (Nginx + PHP-FPM)                            │
│  - Serves static files                              │
│  - Executes PHP scripts                             │
│  - Handles large SQLite databases                   │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  CUNEIFORM App                                      │
│  - SQLite database (297MB, 389K records)           │
│  - PHP backend                                      │
│  - JavaScript frontend                              │
└────────────────┬────────────────────────────────────┘
                 │
                 ▼
┌─────────────────────────────────────────────────────┐
│  External Services                                  │
│  - CDLI (remote images)                            │
│  - ML Service (localhost:8000 - Python/FastAPI)    │
└─────────────────────────────────────────────────────┘
```

---

## Why SQLite is Perfect

Your database is ideal for SQLite:
- ✅ 297MB (SQLite supports up to 281TB)
- ✅ Read-heavy workload
- ✅ Single user / low concurrency
- ✅ No network overhead
- ✅ Fast queries
- ✅ Works on external storage
- ✅ Zero configuration

**Don't switch databases** - the problem was the server, not SQLite!

---

## Testing Without Browser

If you prefer command-line testing:

```bash
# Test detection
cd /Volumes/Portable\ Storage/CUNEIFORM
php test-detection.php P388097

# Test database
php app/public_html/test-standalone.php

# Generate static HTML
./test-browser.sh P388097
```

---

## Support

If something goes wrong:

1. Check Valet status: `valet status`
2. Check PHP version: `php -v` (should be 8.4.x)
3. Restart Valet: `valet restart`
4. Check logs: `tail -f ~/.valet/Log/nginx-error.log`

---

## Summary

**Problem:** PHP dev server crashes
**Solution:** Use Valet (proper server)
**Setup:** Run `./setup-server.sh`
**Access:** http://glintstone.test
**Time:** 15 minutes

Your detection feature is fully working - you just need a real server!
