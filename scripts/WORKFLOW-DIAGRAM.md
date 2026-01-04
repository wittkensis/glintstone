# Tablet Management Workflow - Visual Guide

Complete visual reference for the Glintstone tablet management workflow.

## 1. System Overview

```
┌─────────────────────────────────────────────────────────────────┐
│                         CDLI Database                            │
│                    (cdli.earth API/servers)                      │
└───────────────────────────┬─────────────────────────────────────┘
                            │
                            │ HTTPS Download
                            │
                            ▼
        ┌──────────────────────────────────────────────┐
        │      download-tablets.js                     │
        │  • Fetches images from CDLI                  │
        │  • Validates file signatures                 │
        │  • Retries failed downloads                  │
        │  • Creates initial metadata                  │
        └───────────────────┬──────────────────────────┘
                            │
                ┌───────────┴───────────┐
                │                       │
                ▼                       ▼
    ┌──────────────────┐    ┌──────────────────┐
    │  Image Files     │    │  Metadata JSON   │
    │  (authentic/)    │    │  (data/tablets/) │
    │  P005377.jpg     │    │  P005377.json    │
    └────────┬─────────┘    └────────┬─────────┘
             │                       │
             │                       │
             ▼                       │
    ┌──────────────────┐            │
    │ validate-images  │            │
    │      .js         │            │
    │  • Check validity│            │
    │  • Identify errors│           │
    └──────────────────┘            │
                                    │
                                    ▼
                        ┌──────────────────────┐
                        │  update-metadata.js  │
                        │  • Interactive edit  │
                        │  • Bulk CSV import   │
                        │  • Enrichment        │
                        └──────────┬───────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │  organize-tablets.js │
                        │  • By period         │
                        │  • By genre          │
                        │  • By collection     │
                        │  • By language       │
                        └──────────┬───────────┘
                                   │
                ┌──────────────────┴──────────────────┐
                │                                     │
                ▼                                     ▼
    ┌──────────────────────┐              ┌──────────────────┐
    │  Organized Structure │              │ Index JSON       │
    │  (by-period/, etc)   │              │ (searchable)     │
    └──────────────────────┘              └──────────────────┘
                │                                     │
                └──────────────────┬──────────────────┘
                                   │
                                   ▼
                        ┌──────────────────────┐
                        │   React Application  │
                        │  • Browse tablets    │
                        │  • Display images    │
                        │  • Show metadata     │
                        └──────────────────────┘
```

## 2. Data Structure

```
Project Root
│
├── scripts/                              # Management tools
│   ├── download-tablets.js              # Download & validate
│   ├── update-metadata.js               # Metadata editor
│   ├── organize-tablets.js              # Categorization
│   ├── validate-images.js               # Quality check
│   ├── setup.sh                         # Initial setup
│   ├── tablet-list.txt                  # P-number list
│   ├── metadata-template.csv            # Bulk import template
│   └── *.md                             # Documentation
│
├── data/
│   └── tablets/                         # Metadata storage
│       ├── P005377.json                 # Rich metadata
│       ├── P010012.json
│       ├── P001251.json
│       ├── organization-index.json      # Summary index
│       └── download-report-*.json       # Operation logs
│
└── public/
    └── images/
        └── tablets/
            ├── authentic/               # Original downloads
            │   ├── P005377.jpg         # (488 KB)
            │   ├── P010012.jpg         # (37 MB)
            │   └── P001251.jpg         # (307 KB)
            │
            └── organized/               # Categorized views
                ├── by-period/
                │   ├── ur-iii-ca-2100-2000-bc/
                │   │   ├── P005377.jpg  # → symlink
                │   │   └── P212322.jpg  # → symlink
                │   └── old-babylonian-ca-1900-1600-bc/
                │       └── P003512.jpg  # → symlink
                │
                ├── by-genre/
                │   ├── administrative/
                │   │   ├── P005377.jpg  # → symlink
                │   │   └── P212322.jpg
                │   └── literary/
                │       └── P003512.jpg
                │
                ├── by-collection/
                │   └── british-museum/
                │       └── P005377.jpg  # → symlink
                │
                └── by-language/
                    ├── sumerian/
                    │   └── P005377.jpg  # → symlink
                    └── akkadian/
                        └── P003512.jpg
```

## 3. Metadata Flow

```
Empty Metadata Template
         │
         │ download-tablets.js creates
         │
         ▼
┌─────────────────────────┐
│ Basic Metadata          │
│ • id: P005377           │
│ • cdliUrl: https://...  │
│ • downloadedAt: (date)  │
│ • fileSize: 499390      │
│ • period: null          │
│ • genre: null           │
│ • language: null        │
│ • ... (all other nulls) │
└─────────────────────────┘
         │
         │ User runs: update-metadata.js
         │
         ▼
┌─────────────────────────┐
│ Enriched Metadata       │
│ • id: P005377           │
│ • cdliUrl: https://...  │
│ • downloadedAt: (date)  │
│ • updatedAt: (date)     │
│ • fileSize: 499390      │
│ • period: "Ur III..."   │
│ • genre: "Administrative"│
│ • language: "Sumerian"  │
│ • collection: "Ur..."   │
│ • museum: "British..."  │
│ • description: "..."    │
│ • tags: ["grain", ...]  │
│ • translations: [...]   │
│ • ... (fully populated) │
└─────────────────────────┘
         │
         │ organize-tablets.js uses
         │
         ▼
   Categorized in:
   • by-period/ur-iii-ca-2100-2000-bc/
   • by-genre/administrative/
   • by-language/sumerian/
   • by-collection/ur-excavations/
```

## 4. Download Validation Process

```
Start Download
      │
      ▼
┌──────────────────┐
│ Fetch from CDLI  │
│ P005377.jpg      │
└────────┬─────────┘
         │
         ▼
┌──────────────────┐
│ Check HTTP Status│
│ 200? 301? 404?   │
└────────┬─────────┘
         │
         ├─── 301/302 ──▶ Follow Redirect ──┐
         │                                   │
         ├─── 404 ──────▶ Mark Failed ──────┤
         │                                   │
         └─── 200 ──────▶ Continue          │
                          │                 │
                          ▼                 │
                 ┌──────────────────┐       │
                 │ Check File Size  │       │
                 │ > 1KB?           │       │
                 └────────┬─────────┘       │
                          │                 │
                    NO ───┤                 │
                          │                 │
                    YES   ▼                 │
                 ┌──────────────────┐       │
                 │ Check Magic #s   │       │
                 │ 0xFF 0xD8 0xFF?  │       │
                 │ (JPG signature)  │       │
                 └────────┬─────────┘       │
                          │                 │
                    NO ───┤                 │
                          │                 │
                    YES   ▼                 │
                 ┌──────────────────┐       │
                 │ Scan for HTML    │       │
                 │ "<html>" present?│       │
                 └────────┬─────────┘       │
                          │                 │
                    YES ──┤                 │
                          │                 │
                    NO    ▼                 │
                 ┌──────────────────┐       │
                 │ ✓ VALID IMAGE    │       │
                 │ Save to disk     │       │
                 └──────────────────┘       │
                                            │
                 ┌──────────────────┐       │
                 │ ✗ INVALID        │ ◀─────┘
                 │ Retry (max 3x)   │
                 └──────────────────┘
                          │
                    Retry ┘
```

## 5. Organization Process

```
Input: Tablet Images + Metadata
         │
         ▼
┌──────────────────────────┐
│ Read metadata files      │
│ from data/tablets/*.json │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ For each tablet:         │
│ Extract categorizations  │
│ • period                 │
│ • genre                  │
│ • collection             │
│ • language               │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Create directory paths   │
│ Sanitize names           │
│ "Ur III (ca...)" →       │
│ "ur-iii-ca-2100-2000-bc" │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Create symlinks          │
│ authentic/P005377.jpg →  │
│ by-period/ur-iii-.../... │
└────────┬─────────────────┘
         │
         ▼
┌──────────────────────────┐
│ Generate index JSON      │
│ {                        │
│   byPeriod: {...},       │
│   byGenre: {...},        │
│   ...                    │
│ }                        │
└──────────────────────────┘
```

## 6. Typical User Workflows

### Workflow A: First-Time Setup

```
User                    System
  │
  ├──▶ bash setup.sh
  │                      ├─ Create directories
  │                      ├─ Make scripts executable
  │                      └─ Check dependencies
  │
  ├──▶ Edit tablet-list.txt
  │    (add P-numbers)
  │
  ├──▶ node download-tablets.js --file tablet-list.txt
  │                      ├─ Download images
  │                      ├─ Validate each
  │                      ├─ Create metadata
  │                      └─ Generate report
  │
  ├──▶ node validate-images.js
  │                      └─ Show validation results
  │
  ├──▶ Edit metadata-template.csv
  │    (add details)
  │
  ├──▶ node update-metadata.js --csv metadata-template.csv
  │                      └─ Import metadata
  │
  └──▶ node organize-tablets.js all --symlink
                         └─ Create categorized views
```

### Workflow B: Adding Single Tablet

```
User                    System
  │
  ├──▶ node download-tablets.js P123456
  │                      ├─ Download image
  │                      └─ Create metadata
  │
  ├──▶ node update-metadata.js P123456
  │                      └─ Interactive editing
  │
  └──▶ node organize-tablets.js all --symlink
                         └─ Update organization
```

### Workflow C: Maintenance

```
User                    System
  │
  ├──▶ node validate-images.js
  │                      └─ Show invalid images
  │
  ├──▶ node download-tablets.js P002878 P254202
  │                      └─ Re-download failed tablets
  │
  └──▶ node organize-tablets.js index
                         └─ Regenerate index
```

## 7. Integration with React App

```
React Component
      │
      ├─ Import metadata JSON
      │  import tablet from '@/data/tablets/P005377.json'
      │
      ├─ Load image
      │  <img src="/images/tablets/authentic/P005377.jpg" />
      │
      ├─ Display metadata
      │  <h2>{tablet.description}</h2>
      │  <p>Period: {tablet.period}</p>
      │  <p>Genre: {tablet.genre}</p>
      │
      └─ Browse organized view
         const urIII = '/images/tablets/organized/by-period/ur-iii...'
         // List all tablets in this category
```

## 8. Error Recovery

```
Download Failure
      │
      ├─ Network timeout
      │  └─▶ Automatic retry (up to 3x)
      │      └─ Success ──▶ Continue
      │      └─ Failure ──▶ Log and continue
      │
      ├─ Invalid image (HTML error page)
      │  └─▶ Mark as failed
      │      └─ Report in summary
      │      └─ User can retry manually
      │
      └─ CDLI server down
         └─▶ All downloads fail
             └─ Try again later
             └─ No data corrupted
```

## Command Cheat Sheet

```bash
# Setup
bash scripts/setup.sh

# Download
node scripts/download-tablets.js P005377 P010012
node scripts/download-tablets.js --file tablet-list.txt

# Validate
node scripts/validate-images.js

# Metadata
node scripts/update-metadata.js
node scripts/update-metadata.js P005377
node scripts/update-metadata.js --csv metadata.csv

# Organize
node scripts/organize-tablets.js period
node scripts/organize-tablets.js all
node scripts/organize-tablets.js all --symlink
node scripts/organize-tablets.js index
```

## File Permissions

```
Before setup.sh:
-rw-r--r--  download-tablets.js
-rw-r--r--  update-metadata.js
-rw-r--r--  organize-tablets.js
-rw-r--r--  validate-images.js

After setup.sh:
-rwxr-xr-x  download-tablets.js     (executable)
-rwxr-xr-x  update-metadata.js      (executable)
-rwxr-xr-x  organize-tablets.js     (executable)
-rwxr-xr-x  validate-images.js      (executable)
```

## Directory Creation Timeline

```
1. Initial State
   project/
   └── (empty or minimal structure)

2. After setup.sh
   project/
   ├── data/
   │   └── tablets/
   ├── public/
   │   └── images/
   │       └── tablets/
   │           ├── authentic/
   │           └── organized/
   └── scripts/
       └── (all script files)

3. After download
   data/tablets/
   ├── P005377.json
   └── ...
   public/images/tablets/authentic/
   ├── P005377.jpg
   └── ...

4. After organize
   public/images/tablets/organized/
   ├── by-period/
   ├── by-genre/
   ├── by-collection/
   └── by-language/
```

---

This visual guide provides a complete overview of the tablet management workflow. For detailed instructions, see the other documentation files in the scripts/ directory.
