# Glintstone Data Fixtures

This directory contains all data fixtures used by the Glintstone demo application.

## Files

### tablets.json
Contains 10 cuneiform tablet entries representing a mix of periods and genres:

**Schema:**
```json
{
  "id": "tablet-001",                          // Unique identifier
  "cdli_id": "P005377",                        // CDLI catalog reference
  "museum_number": "VAT 5018",                 // Museum accession number
  "period": "Ur III",                          // Historical period
  "genre": "Administrative",                   // Document type
  "images": {
    "obverse": "/images/tablets/...",          // Front side image
    "reverse": "/images/tablets/..."           // Back side image
  },
  "transcription_status": "untranscribed"      // Progress status: untranscribed | in_progress | verified
}
```

**Periods Included:**
- Ur III (Third Dynasty of Ur, ~2112-2004 BCE)
- Old Babylonian (~1900-1600 BCE)
- Akkadian Empire (~2334-2154 BCE)
- Neo-Assyrian (~911-609 BCE)
- Neo-Babylonian (~626-539 BCE)

**Genres Included:**
- Administrative (economic records, inventory)
- Legal Documents (contracts, agreements)
- Literary Works (epics, myths, wisdom literature)
- Correspondence (personal and official letters)
- Royal Inscriptions (commemorative texts)
- Votive Inscriptions (religious dedications)
- Temple Economy (temple administration records)

### tasks.json
Contains 50 sign-matching tasks for the demo. Each task presents a cuneiform sign image and asks users to select the correct name/transliteration from four options.

**Schema:**
```json
{
  "id": "task-001",                            // Unique task identifier
  "type": "sign_match",                        // Task type
  "tabletId": "tablet-001",                    // Associated tablet reference
  "signImage": "/images/signs/sign-001.png",   // Image of the sign to identify
  "options": [                                 // Four answer options
    {
      "id": "opt-001-a",                       // Option identifier
      "label": "KUR",                          // Sign name/transliteration
      "image": "/images/signs/sign-034.png"    // Visual representation
    },
    // ... 3 more options
  ],
  "correctAnswer": "opt-001-c"                 // ID of correct option
}
```

**Task Distribution:**
- 50 tasks total
- Tasks reference all 10 tablets (distributed evenly)
- Each task has 4 multiple-choice options
- Mix of similar-looking signs to test recognition skills

### experts.json
Contains 12 expert profiles representing leading Assyriology and Cuneiform scholars. Includes:
- Academic experts from major universities
- Museum curators
- Specializations across different periods and text types
- Credibility scores and publication counts

### institutions.json
Contains 13 institutional partners including:
- Leading universities with Near Eastern departments
- Major museums with cuneiform collections
- Research platforms (CDLI, ORACC)
- International representation across 5 continents

## Image Assets

### Tablet Images
Location: `/public/images/tablets/`

Files: `tablet-001-obverse.jpg` through `tablet-010-obverse.jpg` (plus corresponding reverse sides)

**Specifications:**
- Format: JPEG
- Dimensions: 800x600 pixels (minimum)
- Content: Placeholder images styled as cuneiform tablets with geometric wedge patterns
- Note: These are demonstration images. For production, source from Wikimedia Commons, CDLI, or museum collections.

### Sign Images
Location: `/public/images/signs/`

Files: `sign-001.png` through `sign-050.png`

**Specifications:**
- Format: PNG with transparency
- Dimensions: 200x200 pixels
- Content: Geometric representations of cuneiform wedge patterns
- Note: These are abstract placeholders. Real cuneiform signs should be sourced from academic resources.

## Data Usage

### Loading Data
```typescript
// In your application
import tablets from '@/public/data/tablets.json'
import tasks from '@/public/data/tasks.json'
import experts from '@/public/data/experts.json'
import institutions from '@/public/data/institutions.json'
```

### Type Definitions
Refer to `/src/types/index.ts` for TypeScript interfaces:
- `Tablet` - Cuneiform tablet metadata
- `Task` - Sign-matching task definition
- `Expert` - Researcher profile
- `Institution` - Partner organization

## Notes

- All data is fictional but structured to reflect real-world cuneiform scholarship
- CDLI IDs and museum numbers follow authentic conventions
- The fixture data is sufficient for demo/development purposes
- For production use, integrate with actual CDLI API or cuneiform database
- Image assets should be replaced with authentic sources before public deployment

## Sources & References

- CDLI (Cuneiform Digital Library Initiative): https://cdli.ucla.edu/
- ORACC (Open Richly Annotated Cuneiform Corpus): http://oracc.museum.upenn.edu/
- Wikimedia Commons Cuneiform Collection: Commons.wikimedia.org
- Academic institutions mentioned in institutions.json are real partnering organizations
