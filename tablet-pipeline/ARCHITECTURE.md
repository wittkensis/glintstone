# Tablet Management System - Architecture

Technical architecture and design decisions for the Glintstone tablet management system.

## Design Philosophy

### Goals

1. **Reliability**: Downloads must be verified; error pages must not be saved as valid images
2. **Repeatability**: Scripts can be run multiple times safely (idempotent operations)
3. **Transparency**: Clear logging and reporting of all operations
4. **Flexibility**: Support multiple organization schemes and metadata structures
5. **Version Control Friendly**: All metadata stored as human-readable JSON
6. **Progressive Enhancement**: Start with basic metadata, enrich over time

### Non-Goals

- Real-time web scraping of CDLI pages (CDLI structure may change)
- Automated transcription or translation (requires domain expertise)
- Database storage (prefer flat files for simplicity and git-friendliness)
- GUI/web interface (command-line first, integrates with existing dev workflow)

## System Architecture

### Component Overview

```
┌─────────────────────────────────────────────────────────────┐
│                    Glintstone Project                        │
├─────────────────────────────────────────────────────────────┤
│                                                               │
│  ┌────────────────┐      ┌──────────────────┐               │
│  │   CDLI API     │─────▶│ download-tablets │               │
│  │ (cdli.earth)   │      │      .js         │               │
│  └────────────────┘      └──────────────────┘               │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │  Image Files    │                │
│                          │ (authentic/)    │                │
│                          └─────────────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ validate-images │                │
│                          │      .js        │                │
│                          └─────────────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ Metadata JSON   │◀────┐          │
│                          │ (data/tablets/) │     │          │
│                          └─────────────────┘     │          │
│                                   │              │          │
│                                   │      ┌───────────────┐  │
│                                   │      │ update-       │  │
│                                   │      │ metadata.js   │  │
│                                   │      └───────────────┘  │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ organize-       │                │
│                          │ tablets.js      │                │
│                          └─────────────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ Organized Views │                │
│                          │ (by-period/etc) │                │
│                          └─────────────────┘                │
│                                   │                          │
│                                   ▼                          │
│                          ┌─────────────────┐                │
│                          │ React App       │                │
│                          │ (consumes data) │                │
│                          └─────────────────┘                │
│                                                               │
└─────────────────────────────────────────────────────────────┘
```

### Data Flow

1. **Acquisition**: `download-tablets.js` fetches images from CDLI
2. **Validation**: Image data is validated using file signatures (magic numbers)
3. **Storage**: Images saved to `public/images/tablets/authentic/`
4. **Metadata Creation**: JSON file created in `data/tablets/`
5. **Enrichment**: User adds metadata via `update-metadata.js`
6. **Organization**: `organize-tablets.js` creates categorized views
7. **Consumption**: React app imports metadata and displays images

## Key Design Decisions

### 1. Image Validation Strategy

**Problem**: CDLI returns HTTP 200 with HTML error pages instead of HTTP 404 for missing images.

**Solution**: Multi-level validation
- Check file size (minimum 1KB threshold)
- Verify image file signatures (magic numbers)
  - JPG: `0xFF 0xD8 0xFF`
  - PNG: `0x89 0x50 0x4E 0x47`
- Scan for HTML tags in first 200 bytes
- Automatic retry up to 3 times

**Rationale**: Prevents storing 153-byte HTML files as ".jpg" images, which would break the application.

### 2. Metadata Storage Format

**Decision**: Individual JSON files per tablet, not a single database

**Advantages**:
- Git-friendly: Each tablet's history tracked separately
- Merge-friendly: Multiple team members can edit different tablets
- Easy to edit: Standard JSON, can use any editor
- No database setup required
- Easy to backup/restore individual tablets
- Schema evolution is straightforward

**Trade-offs**:
- Slower than database for complex queries (acceptable for < 10,000 tablets)
- Need to aggregate for full-collection views (solved by organization index)

### 3. Directory Organization Philosophy

**Decision**: Support multiple concurrent organization schemes via symlinks

**Why**:
- Same tablet might be valuable from multiple perspectives
  - Historical period (when was it written?)
  - Genre (what type of document?)
  - Collection (where is it housed?)
  - Language (what language is it in?)
- Researchers think in different categories
- Symlinks avoid disk space duplication
- Easy to regenerate if organization scheme changes

**Structure**:
```
organized/
├── by-period/      # Chronological view
├── by-genre/       # Document type view
├── by-collection/  # Museum/institutional view
└── by-language/    # Linguistic view
```

### 4. Retry Logic

**Strategy**: Exponential backoff with maximum attempts

```javascript
const CONFIG = {
  maxRetries: 3,
  retryDelay: 2000, // 2 seconds base
  requestTimeout: 30000 // 30 second timeout
};
```

**Rationale**:
- CDLI can be slow or temporarily unavailable
- Network issues are transient
- 3 retries catches most transient failures
- 2-second delay prevents hammering the server
- 30-second timeout prevents indefinite hangs

### 5. Metadata Schema Design

**Core Principles**:
- **Extensible**: Easy to add new fields without breaking existing data
- **Optional**: Most fields nullable to allow progressive enrichment
- **Structured**: Arrays for multi-value fields (translations, transcriptions)
- **Standardized**: Controlled vocabularies for period/genre/language
- **Documented**: Full JSON Schema with examples

**Key Sections**:
```json
{
  "identification": ["id", "cdliUrl", "accessionNumber"],
  "categorization": ["period", "genre", "language"],
  "physical": ["material", "dimensions", "provenience"],
  "content": ["description", "translations", "transcriptions"],
  "metadata": ["downloadedAt", "updatedAt", "tags", "notes"]
}
```

### 6. Error Handling Philosophy

**Approach**: Fail gracefully, report clearly, continue processing

- Individual tablet failures don't stop batch operations
- All errors logged with context
- Summary report generated at end
- Failed operations can be retried individually

**Example**: If downloading 100 tablets and 10 fail:
- Continue processing remaining 90
- Report all 10 failures with reasons
- Save successful 90 immediately
- Provide command to retry just the 10 failures

### 7. File Naming Conventions

**Images**: `{P-NUMBER}.jpg`
- Example: `P005377.jpg`
- Always uppercase P
- Always .jpg extension (even if downloaded as .png, should be converted)

**Metadata**: `{P-NUMBER}.json`
- Example: `P005377.json`
- Matches image filename exactly (minus extension)

**Reports**: `{type}-report-{timestamp}.json`
- Example: `download-report-1735891234567.json`
- Timestamped to avoid overwrites

**Rationale**: Consistent, predictable, easy to script against

### 8. Technology Choices

**Node.js (not Python/Bash)**:
- ✓ Native JSON handling
- ✓ Async I/O excellent for network operations
- ✓ Same language as React frontend
- ✓ Cross-platform (works on macOS/Linux/Windows)
- ✓ Rich ecosystem for HTTP, file I/O

**No External Dependencies**:
- Uses only Node.js built-in modules
- No `npm install` required
- Easier to maintain
- No security vulnerabilities from dependencies

**Trade-off**: More verbose code vs. using libraries like `axios`, `cheerio`, etc.

## Scalability Considerations

### Current Scale (< 100 tablets)

Current design is optimal:
- JSON files load instantly
- Directory traversal is fast
- Git handles this easily

### Medium Scale (100-1,000 tablets)

Current design still works well:
- Consider adding an in-memory cache for organization index
- May want thumbnail generation
- Batch operations should process in parallel

### Large Scale (10,000+ tablets)

Would need architectural changes:
- Move to SQLite or PostgreSQL for metadata
- Generate static index files for fast lookups
- Add pagination to organization views
- Consider CDN for image serving
- May need image optimization pipeline

**Decision**: Start simple. YAGNI (You Aren't Gonna Need It) applies.

## Security Considerations

### Input Validation

- P-numbers validated with regex: `/^P\d+$/`
- File paths validated to prevent directory traversal
- No shell command injection (no `exec()` of user input)
- URLs hardcoded or validated

### Downloaded Content

- All downloads validated before saving
- Magic number verification prevents code injection via fake images
- Error pages detected and rejected

### File System Access

- All operations use absolute paths
- Recursive directory creation with `mkdir -p`
- Atomic writes where possible

## Future Enhancements

### Near-term (Next Release)

- [ ] Add progress bars for better UX (`cli-progress`)
- [ ] Generate thumbnail images (160x160px)
- [ ] Add image compression/optimization
- [ ] Web interface for metadata editing

### Medium-term

- [ ] Scrape metadata from CDLI web pages
- [ ] Integration with CDLI API (if one becomes available)
- [ ] Export to CSV/Excel for analysis
- [ ] Import from existing cuneiform catalogs

### Long-term

- [ ] Collaborative editing with conflict resolution
- [ ] Machine learning for image classification
- [ ] OCR for cuneiform transcription
- [ ] 3D model support for tablets

## Testing Strategy

### Current State

Scripts are manually tested with:
- Valid P-numbers (P005377, P010012)
- Invalid P-numbers (404 responses)
- Malformed P-numbers
- Network failures (timeout tests)

### Recommended Additions

```javascript
// Unit tests with Jest or Mocha
describe('isValidImage', () => {
  test('detects valid JPG', () => {
    const jpgBuffer = Buffer.from([0xFF, 0xD8, 0xFF, ...]);
    expect(isValidImage(jpgBuffer)).toBe(true);
  });

  test('rejects HTML error page', () => {
    const htmlBuffer = Buffer.from('<html>404</html>');
    expect(isValidImage(htmlBuffer)).toBe(false);
  });
});
```

### Integration Testing

- Test full download → validate → organize pipeline
- Test with actual CDLI endpoints
- Test with various network conditions

## Performance Benchmarks

### Expected Performance

| Operation | Tablets | Time | Rate |
|-----------|---------|------|------|
| Download | 10 | ~30s | 3/sec |
| Validate | 100 | <1s | 100+/sec |
| Organize (copy) | 100 | ~5s | 20/sec |
| Organize (symlink) | 100 | <1s | 100+/sec |
| Metadata update (CSV) | 100 | <2s | 50+/sec |

### Bottlenecks

1. **Network I/O**: Downloading is slowest operation
   - Mitigation: Parallel downloads (future enhancement)
2. **Disk I/O**: Large images take time to write
   - Mitigation: Use symlinks instead of copies

## Monitoring and Observability

### Logging Strategy

- Console output with clear status indicators (✓, ✗, !)
- Progress updates for long operations
- Summary reports with statistics
- Timestamped report files for audit trail

### Error Tracking

All errors include:
- P-number affected
- Operation being performed
- Error message and type
- Timestamp
- Context (retry attempt, etc.)

### Metrics to Track

- Download success rate
- Average download time
- Total storage used
- Metadata completeness percentage
- Organization efficiency (symlinks vs copies)

## Conclusion

This architecture prioritizes:
1. **Correctness**: Validate everything
2. **Simplicity**: No unnecessary complexity
3. **Maintainability**: Clear code, good documentation
4. **Flexibility**: Easy to extend and modify
5. **Developer Experience**: Fast, intuitive, well-reported

The system is designed to grow with the project while remaining simple enough for a single developer to understand and maintain.
