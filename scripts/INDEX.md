# Scripts Directory Index

Complete reference for all tablet management scripts and documentation.

## Scripts (Executable)

| Script | Purpose | Usage Example |
|--------|---------|---------------|
| `download-tablets.js` | Download and validate tablet images from CDLI | `node download-tablets.js P005377 P010012` |
| `update-metadata.js` | Interactive/batch metadata editor | `node update-metadata.js P005377` |
| `organize-tablets.js` | Create categorized directory structures | `node organize-tablets.js all --symlink` |
| `validate-images.js` | Validate existing images, identify errors | `node validate-images.js` |
| `setup.sh` | Initial setup (one-time) | `bash setup.sh` |

## Documentation

| File | Description |
|------|-------------|
| `README.md` | Complete user guide and reference |
| `QUICKSTART.md` | 5-minute getting started guide |
| `ARCHITECTURE.md` | Technical design decisions and rationale |
| `INDEX.md` | This file - directory overview |

## Configuration Files

| File | Purpose |
|------|---------|
| `tablet-list.txt` | Curated list of P-numbers to download |
| `metadata-template.csv` | Template for bulk metadata import |
| `tablet-metadata-schema.json` | JSON Schema for metadata validation |

## Quick Navigation

### I want to...

**Download tablets**
→ Read: [QUICKSTART.md](QUICKSTART.md#step-2-download-missinginvalid-tablets)
→ Run: `node download-tablets.js --file tablet-list.txt`

**Check which images are valid**
→ Run: `node validate-images.js`

**Add metadata to tablets**
→ Read: [QUICKSTART.md](QUICKSTART.md#step-3-add-metadata)
→ Run: `node update-metadata.js`

**Organize tablets by category**
→ Read: [README.md](README.md#3-organize-tablets)
→ Run: `node organize-tablets.js all --symlink`

**Understand the system architecture**
→ Read: [ARCHITECTURE.md](ARCHITECTURE.md)

**Learn about CDLI's API**
→ Read: [README.md](README.md#cdli-api-documentation)

**Troubleshoot issues**
→ Read: [README.md](README.md#troubleshooting)

## File Tree

```
scripts/
├── Core Scripts
│   ├── download-tablets.js        (590 lines - Download & validate)
│   ├── update-metadata.js         (360 lines - Metadata editor)
│   ├── organize-tablets.js        (280 lines - Categorization)
│   └── validate-images.js         (120 lines - Image validation)
│
├── Setup
│   └── setup.sh                   (60 lines - Initial setup)
│
├── Documentation
│   ├── README.md                  (Comprehensive guide)
│   ├── QUICKSTART.md              (5-minute tutorial)
│   ├── ARCHITECTURE.md            (Design decisions)
│   └── INDEX.md                   (This file)
│
└── Configuration
    ├── tablet-list.txt            (P-numbers to download)
    ├── metadata-template.csv      (Bulk import template)
    └── tablet-metadata-schema.json (JSON Schema)
```

## Output Directories

Scripts create and use these directories:

```
public/images/tablets/
├── authentic/                    # Original downloaded images
│   ├── P005377.jpg
│   └── ...
└── organized/                    # Categorized views (symlinks)
    ├── by-period/
    ├── by-genre/
    ├── by-collection/
    └── by-language/

data/tablets/
├── P005377.json                  # Metadata for each tablet
├── P010012.json
├── organization-index.json       # Summary of all tablets
└── download-report-*.json        # Download operation logs
```

## Common Workflows

### First-time Setup

```bash
# 1. Setup
bash scripts/setup.sh

# 2. Download tablets
node scripts/download-tablets.js --file scripts/tablet-list.txt

# 3. Add metadata
node scripts/update-metadata.js --csv scripts/metadata-template.csv

# 4. Organize
node scripts/organize-tablets.js all --symlink
```

### Adding New Tablets

```bash
# 1. Add to list
echo "P123456" >> scripts/tablet-list.txt

# 2. Download
node scripts/download-tablets.js P123456

# 3. Edit metadata interactively
node scripts/update-metadata.js P123456

# 4. Re-organize
node scripts/organize-tablets.js all --symlink
```

### Maintenance

```bash
# Check image validity
node scripts/validate-images.js

# Re-download failed images
node scripts/download-tablets.js P002878 P254202

# Regenerate organization
node scripts/organize-tablets.js all --symlink

# Update organization index
node scripts/organize-tablets.js index
```

## Script Dependencies

```
download-tablets.js
├── Uses: Node.js built-in modules (https, fs, path)
└── Creates: Image files, metadata JSON files

update-metadata.js
├── Uses: Node.js built-in modules (fs, readline)
├── Reads: Existing metadata JSON files
└── Updates: Metadata JSON files

organize-tablets.js
├── Uses: Node.js built-in modules (fs, path)
├── Reads: Image files, metadata JSON files
└── Creates: Organized directory structure, symlinks

validate-images.js
├── Uses: Node.js built-in modules (fs, path)
├── Reads: Image files
└── Output: Console report (no file modifications)

setup.sh
├── Uses: bash, chmod, mkdir
└── Creates: Directory structure, sets permissions
```

## Version History

| Version | Date | Changes |
|---------|------|---------|
| 1.0.0 | 2026-01-03 | Initial release with full suite |

## Support

- Questions about usage → See [README.md](README.md) or [QUICKSTART.md](QUICKSTART.md)
- Questions about design → See [ARCHITECTURE.md](ARCHITECTURE.md)
- Issues with scripts → Check console output and error messages
- CDLI connectivity → Visit https://cdli.earth/ to check service status

## Contributing

When modifying these scripts:
1. Follow existing code style
2. Update relevant documentation
3. Test with both valid and invalid P-numbers
4. Update this INDEX.md if adding new files
5. Commit with clear messages (see CLAUDE.md)

## License

Part of the Glintstone project. CDLI images subject to CDLI terms of use.
