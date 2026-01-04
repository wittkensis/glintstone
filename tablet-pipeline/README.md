# Glintstone Tablet Management Scripts

Comprehensive toolkit for downloading, organizing, and managing cuneiform tablet images and metadata from the CDLI (Cuneiform Digital Library Initiative).

## Overview

This suite of scripts provides a robust, production-ready workflow for:
- Downloading tablet images from CDLI with validation and retry logic
- Managing rich metadata for each tablet
- Organizing tablets by period, genre, collection, or language
- Generating indexes and reports

## Directory Structure

```
scripts/
├── download-tablets.js        # Download and validate tablet images
├── update-metadata.js         # Interactive metadata editor
├── organize-tablets.js        # Organize tablets into categorized directories
├── tablet-list.txt           # List of P-numbers to download
├── metadata-template.csv     # Template for bulk metadata updates
├── tablet-metadata-schema.json # JSON Schema for metadata validation
└── README.md                 # This file

data/
└── tablets/                  # Metadata JSON files (one per tablet)
    ├── P005377.json
    ├── P010012.json
    └── organization-index.json

public/images/tablets/
├── authentic/                # Original downloaded images
│   ├── P005377.jpg
│   └── P010012.jpg
└── organized/                # Categorized copies/symlinks
    ├── by-period/
    │   ├── ur-iii-ca-2100-2000-bc/
    │   └── old-babylonian-ca-1900-1600-bc/
    ├── by-genre/
    │   ├── administrative/
    │   └── literary/
    ├── by-collection/
    └── by-language/
```

## Quick Start

### 1. Download Tablets

Download tablets from a list of P-numbers:

```bash
# Download individual tablets
node scripts/download-tablets.js P005377 P010012 P001251

# Download from a file
node scripts/download-tablets.js --file scripts/tablet-list.txt
```

The script will:
- Download each image from `https://cdli.earth/dl/photo/P{NUMBER}.jpg`
- Validate that the download contains actual image data (not error pages)
- Retry failed downloads up to 3 times
- Save images to `public/images/tablets/authentic/`
- Create initial metadata JSON files in `data/tablets/`
- Generate a detailed download report

**Output:**
```
Processing P005377...
  Downloading P005377 from https://cdli.earth/dl/photo/P005377.jpg...
    ✓ Valid image received (487.7 KB)
    ✓ Saved to /path/to/public/images/tablets/authentic/P005377.jpg
    ✓ Metadata saved to /path/to/data/tablets/P005377.json

=== Summary ===
Total: 9
Successful: 5
Failed: 4

Failed downloads:
  - P002878: Downloaded file is not a valid image (likely an error page)
  - P254202: Downloaded file is not a valid image (likely an error page)
```

### 2. Update Metadata

Edit tablet metadata interactively or via CSV bulk import:

```bash
# Interactive mode - select from list
node scripts/update-metadata.js

# Edit specific tablet
node scripts/update-metadata.js P005377

# Bulk update from CSV
node scripts/update-metadata.js --csv metadata-template.csv
```

The interactive editor lets you set:
- Historical period (Ur III, Old Babylonian, Neo-Assyrian, etc.)
- Genre (Administrative, Literary, Legal, etc.)
- Language (Sumerian, Akkadian, etc.)
- Collection/museum information
- Physical details (material, dimensions)
- Description and notes
- Custom tags

**Example metadata file** (`data/tablets/P005377.json`):
```json
{
  "id": "P005377",
  "cdliUrl": "https://cdli.earth/P005377",
  "downloadedAt": "2026-01-03T12:00:00Z",
  "updatedAt": "2026-01-03T14:30:00Z",
  "fileSize": 499390,
  "period": "Ur III (ca. 2100-2000 BC)",
  "genre": "Administrative",
  "language": "Sumerian",
  "collection": "Ur Excavations",
  "museum": "British Museum",
  "accessionNumber": "BM 106445",
  "provenience": "Ur",
  "material": "clay",
  "dimensions": "5.2 x 3.8 x 1.9 cm",
  "description": "Administrative tablet recording grain disbursements",
  "tags": ["grain", "economic", "ur-nammu"],
  "notes": "Well-preserved example",
  "translations": [],
  "transcriptions": []
}
```

### 3. Organize Tablets

Create categorized directory structures:

```bash
# Organize by a single criterion
node scripts/organize-tablets.js period
node scripts/organize-tablets.js genre
node scripts/organize-tablets.js collection
node scripts/organize-tablets.js language

# Organize using all methods
node scripts/organize-tablets.js all

# Use symlinks instead of copying (saves disk space)
node scripts/organize-tablets.js all --symlink

# Generate JSON index only
node scripts/organize-tablets.js index
```

This creates organized directories like:
```
public/images/tablets/organized/
├── by-period/
│   ├── ur-iii-ca-2100-2000-bc/
│   │   ├── P005377.jpg
│   │   └── P212322.jpg
│   └── old-babylonian-ca-1900-1600-bc/
│       └── P003512.jpg
├── by-genre/
│   ├── administrative/
│   └── literary/
└── by-collection/
    └── british-museum/
```

## CDLI API Documentation

### Image URLs

CDLI serves tablet images from:
```
https://cdli.earth/dl/photo/{P-NUMBER}.jpg
```

**Examples:**
- `https://cdli.earth/dl/photo/P005377.jpg`
- `https://cdli.earth/dl/photo/P010012.jpg`

**Important Notes:**
- Always follow redirects (301/302 responses)
- Check file size and magic numbers to validate images
- Files under 1KB are likely error pages (404s served as 200 status)
- Some tablets may not have images available

### Tablet Web Pages

Each tablet has a detail page at:
```
https://cdli.earth/{P-NUMBER}
```

This page contains metadata, transcriptions, and bibliographic information (not currently scraped by these scripts).

### Common Error Responses

**404 Not Found:**
```html
<html>
<head><title>404 Not Found</title></head>
<body>
<center><h1>404 Not Found</h1></center>
<hr><center>nginx/1.29.3</center>
</body>
</html>
```

The download script automatically detects these HTML responses and marks them as failed.

## Metadata Schema

Full schema available in `tablet-metadata-schema.json`.

### Core Fields

- **id** (required): CDLI P-number (e.g., "P005377")
- **cdliUrl** (required): Full URL to CDLI page
- **downloadedAt**: ISO 8601 timestamp
- **updatedAt**: Last modification timestamp
- **fileSize**: Image file size in bytes

### Categorization Fields

- **period**: Historical period (e.g., "Ur III (ca. 2100-2000 BC)")
- **genre**: Document type (Administrative, Literary, Legal, etc.)
- **language**: Primary language (Sumerian, Akkadian, etc.)
- **tags**: Array of custom tags

### Physical Information

- **collection**: Collection name
- **museum**: Institution housing the tablet
- **accessionNumber**: Museum catalogue number
- **provenience**: Archaeological findspot
- **excavationNumber**: Field number
- **material**: Usually "clay"
- **dimensions**: Physical size (e.g., "5.2 x 3.8 x 1.9 cm")

### Content Fields

- **description**: Brief summary of content
- **translations**: Array of translations in various languages
- **transcriptions**: Array of cuneiform transcriptions (ATF, Unicode, etc.)
- **notes**: Additional observations

### Advanced Fields

- **imageQuality**: "excellent" | "good" | "fair" | "poor"
- **preservationState**: "complete" | "nearly-complete" | "fragmentary" | "heavily-damaged"
- **relatedTablets**: Array of related P-numbers
- **bibliography**: Array of publication references

## Standard Periods

Use these standardized period names for consistency:

- Uruk IV-III (ca. 3400-3000 BC)
- Early Dynastic I-II (ca. 2900-2700 BC)
- Early Dynastic IIIa (ca. 2600-2500 BC)
- Early Dynastic IIIb (ca. 2500-2340 BC)
- Old Akkadian (ca. 2340-2200 BC)
- Lagash II (ca. 2200-2100 BC)
- **Ur III (ca. 2100-2000 BC)** ← Most common in CDLI
- **Old Babylonian (ca. 1900-1600 BC)** ← Very common
- Middle Babylonian (ca. 1400-1100 BC)
- **Neo-Assyrian (ca. 911-612 BC)** ← Common
- **Neo-Babylonian (ca. 626-539 BC)** ← Common
- Achaemenid (547-331 BC)
- Hellenistic (323-63 BC)

## Standard Genres

- **Administrative**: Record-keeping, receipts, inventories
- **Legal**: Contracts, court documents, property transfers
- **Letter**: Correspondence
- **Literary**: Myths, epics, hymns, prayers
- **Lexical**: Word lists, dictionaries, sign lists
- **Mathematical**: Calculations, problem texts
- **Astronomical**: Star catalogs, ephemerides
- **Medical**: Prescriptions, diagnoses
- **Omen**: Divination texts
- **Ritual**: Religious ceremonies
- **Royal/Monumental**: Inscriptions, building records
- **School**: Student exercises, practice tablets

## Bulk Metadata Update via CSV

Create a CSV file with headers:
```csv
pNumber,period,genre,language,collection,museum,accession,provenience,material,dimensions,description,tags
P005377,Ur III (ca. 2100-2000 BC),Administrative,Sumerian,Ur Excavations,British Museum,BM 106445,Ur,clay,5.2 x 3.8 x 1.9 cm,Grain disbursement record,grain;economic;disbursement
P010012,Old Babylonian (ca. 1900-1600 BC),Literary,Akkadian,,,,,clay,,Gilgamesh epic fragment,literary;epic;gilgamesh
```

Then run:
```bash
node scripts/update-metadata.js --csv your-metadata.csv
```

**Notes:**
- Use semicolons (;) to separate multiple tags
- Empty fields will not overwrite existing metadata
- First row must be the header row

## Troubleshooting

### Download Failures

**Problem:** "Downloaded file is not a valid image"
- **Cause:** CDLI doesn't have an image for this P-number
- **Solution:** The tablet may not have been photographed. Check CDLI website manually.

**Problem:** "Request timeout"
- **Cause:** Network issues or slow CDLI server
- **Solution:** Script will automatically retry up to 3 times. If it still fails, try again later.

### Existing Files

If you re-run downloads, the script will:
1. Check if the file already exists
2. Validate that it's a real image
3. Skip download if valid
4. Re-download if invalid (was an error page)

### Metadata Files

All metadata is stored as JSON in `data/tablets/`. These files are:
- Human-readable
- Version-control friendly
- Easily editable by hand if needed
- Validated against the JSON schema

## Integration with Glintstone App

The organized directory structure and metadata files are designed to integrate seamlessly with the Glintstone React application:

```javascript
// Example: Loading tablet metadata in React
import tabletMetadata from '@/data/tablets/P005377.json';

function TabletDisplay() {
  return (
    <div>
      <img src="/images/tablets/authentic/P005377.jpg" />
      <h2>{tabletMetadata.description}</h2>
      <p>Period: {tabletMetadata.period}</p>
      <p>Genre: {tabletMetadata.genre}</p>
    </div>
  );
}
```

## Best Practices

1. **Always download before organizing**: Run `download-tablets.js` first to ensure you have images and base metadata.

2. **Use bulk CSV updates for efficiency**: When adding many tablets, populate metadata via CSV rather than interactive mode.

3. **Use symlinks for organization**: When organizing, use `--symlink` to avoid duplicating large image files.

4. **Keep tablet-list.txt updated**: Maintain a canonical list of P-numbers your project uses.

5. **Commit metadata to git**: The JSON files are designed to be version-controlled alongside your code.

6. **Validate metadata**: Check that metadata conforms to the schema before using in production.

## Future Enhancements

Potential improvements for future iterations:

- [ ] Web scraper to extract metadata from CDLI web pages
- [ ] Integration with CDLI's search API (if/when available)
- [ ] Automatic image optimization (resize, compress for web)
- [ ] Generate thumbnail images
- [ ] OCR integration for transcription extraction
- [ ] Multi-language support for metadata
- [ ] Export to other formats (CSV, Excel, SQL)
- [ ] Validation against JSON schema on save
- [ ] CLI with progress bars and better UX

## Support

For issues or questions:
1. Check CDLI status at https://cdli.earth/
2. Review script output for specific error messages
3. Manually verify P-numbers exist on CDLI website
4. Check that Node.js version is 14+ (scripts use modern JS features)

## License

Part of the Glintstone project. All cuneiform images are from CDLI and subject to their usage terms.
