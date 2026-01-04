# Quick Start Guide - Tablet Management

Get up and running with the Glintstone tablet management system in 5 minutes.

## Initial Setup

```bash
# 1. Run setup script (one-time)
cd scripts
bash setup.sh

# 2. Verify your Node.js installation
node --version  # Should be 14.0.0 or higher
```

## Basic Workflow

### Step 1: Validate Existing Images

Check which downloaded images are valid vs. error pages:

```bash
node scripts/validate-images.js
```

Output will show:
```
✓ P005377.jpg      487.7 KB - Valid
✓ P010012.jpg      37512.1 KB - Valid
✗ P002878.jpg      0.1 KB - HTML error page instead of image
✗ P254202.jpg      0.1 KB - HTML error page instead of image
```

### Step 2: Download Missing/Invalid Tablets

Re-download any failed tablets identified in Step 1:

```bash
# Re-download specific tablets
node scripts/download-tablets.js P002878 P254202 P346222 P448739

# Or download from your curated list
node scripts/download-tablets.js --file scripts/tablet-list.txt
```

Expected output:
```
Processing P002878...
  Downloading P002878 from https://cdli.earth/dl/photo/P002878.jpg...
    ✗ Failed: Downloaded file is not a valid image

=== Summary ===
Total: 4
Successful: 2
Failed: 2
```

### Step 3: Add Metadata

Option A - Interactive (best for a few tablets):
```bash
node scripts/update-metadata.js P005377
```

Option B - Bulk CSV import (best for many tablets):
```bash
# Edit metadata-template.csv with your data, then:
node scripts/update-metadata.js --csv scripts/metadata-template.csv
```

### Step 4: Organize Tablets

Create categorized directory structure:

```bash
# Organize by all criteria using symlinks (recommended)
node scripts/organize-tablets.js all --symlink
```

This creates:
```
public/images/tablets/organized/
├── by-period/ur-iii-ca-2100-2000-bc/
├── by-genre/administrative/
├── by-collection/british-museum/
└── by-language/sumerian/
```

## Common Tasks

### Add One New Tablet

```bash
# 1. Download
node scripts/download-tablets.js P123456

# 2. Add metadata
node scripts/update-metadata.js P123456

# 3. Re-organize
node scripts/organize-tablets.js all --symlink
```

### Batch Add Multiple Tablets

```bash
# 1. Add P-numbers to tablet-list.txt
echo "P123456" >> scripts/tablet-list.txt
echo "P789012" >> scripts/tablet-list.txt

# 2. Download all
node scripts/download-tablets.js --file scripts/tablet-list.txt

# 3. Add metadata via CSV
# Edit metadata-template.csv, then:
node scripts/update-metadata.js --csv scripts/metadata-template.csv

# 4. Re-organize
node scripts/organize-tablets.js all --symlink
```

### Check Current Status

```bash
# Validate all images
node scripts/validate-images.js

# View metadata for a tablet
cat data/tablets/P005377.json

# List all tablets with metadata
ls data/tablets/*.json
```

### Generate Reports

```bash
# Create organization index
node scripts/organize-tablets.js index

# View the index
cat data/tablets/organization-index.json
```

## Troubleshooting

### "Downloaded file is not a valid image"

This is normal. Many CDLI P-numbers don't have images available. The script correctly detects this.

**What to do:**
1. Visit `https://cdli.earth/P{NUMBER}` in your browser
2. Check if there's actually an image on the page
3. If not, remove that P-number from your list

### "No such file or directory"

Run the setup script first:
```bash
bash scripts/setup.sh
```

### Images aren't organizing

Make sure metadata is filled in. Check:
```bash
cat data/tablets/P005377.json
```

If `period`, `genre`, `collection`, or `language` are `null`, they'll go into the "unknown" category.

## Next Steps

- Read the full [README.md](README.md) for detailed documentation
- Review the [metadata schema](tablet-metadata-schema.json) to understand all available fields
- Check the [CLAUDE.md](../CLAUDE.md) feedback protocol before making changes

## File Locations Reference

| What | Where |
|------|-------|
| Downloaded images | `/public/images/tablets/authentic/` |
| Tablet metadata | `/data/tablets/P{NUMBER}.json` |
| Organized images | `/public/images/tablets/organized/` |
| Download reports | `/data/tablets/download-report-*.json` |
| Organization index | `/data/tablets/organization-index.json` |
| Scripts | `/scripts/` |
| This guide | `/scripts/QUICKSTART.md` |

## Quick Command Reference

```bash
# Download
node scripts/download-tablets.js P005377 P010012
node scripts/download-tablets.js --file scripts/tablet-list.txt

# Validate
node scripts/validate-images.js

# Metadata
node scripts/update-metadata.js                    # Interactive
node scripts/update-metadata.js P005377           # Specific tablet
node scripts/update-metadata.js --csv data.csv    # Bulk import

# Organize
node scripts/organize-tablets.js period           # By period only
node scripts/organize-tablets.js all              # All methods (copy files)
node scripts/organize-tablets.js all --symlink    # All methods (symlinks)
node scripts/organize-tablets.js index            # Generate index only

# Setup
bash scripts/setup.sh                             # Initial setup
```
