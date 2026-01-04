# Claude

## Workflow
- Commit and push origin to main after every key task.
- **ALWAYS check for unresolved feedback** before starting work (see Feedback Protocol below).

## Feedback Protocol
When starting a session or task:
1. Search for active feedback comments: `[@Claude ...]` or `[@agent-name ...]`
2. **IGNORE struck-through comments**: `~~[@Claude ...]~~` (already resolved)
3. After completing feedback, mark it resolved with strikethrough

See [.claude-feedback-protocol.md](.claude-feedback-protocol.md) for full details.

---

## General Process Guidelines

### File Organization
- **Keep app assets separate from process docs**: Source code in `src/`, public assets in `public/`, process/strategy docs in `docs/`
- **Prefer HTML over MD for UX deliverables**: HTML files are easier to scan visually and reduce context window clutter
- **Archive old iterations**: Move superseded versions to `archive/` with clear demo/phase labels
- **Remove redundant files**: If an MD file was converted to HTML, remove the MD version

### App vs. Spec Separation (Critical Principle)
- **App files change like clay**: Source code (`/src`), assets (`/public`), build output (`/dist`) evolve fluidly
- **Spec files capture iterations**: Strategy docs, PRDs, and agent instructions should be versioned to show evolution
- **Git commits provide history**: Reference commits when archiving to maintain historical integrity
- **Specs folder for process docs**: All agentic instructions, PRDs, and strategy documents live in `/specs`
- **Never mix concerns**: App code should not contain strategy docs; specs should not contain runtime code

### Output Quality Standards
- **Avoid tackiness**: No floating decorative unicode characters, no excessive hover effects on non-interactive elements
- **Be purposeful and elegant, not gaudy and chaotic**
- **Hover effects only on interactive elements** (buttons, links, cards that navigate)
- **Remove fake stats and advocacy**: Only show real data or describe work remaining honestly
- **Anonymize testimonials**: Use "Feedback from academic consultation" rather than fake expert names

### Trust-Building Principles (from YCombinator agentic advice)
- **Start with the real problem**: Lead with the 500,000 tablet backlog, not inflated claims
- **Honest framing builds credibility**: Academics especially will see through fake advocacy
- **Show the pipeline, not just the dream**: Source → Crowd → AI → Expert Review
- **Describe what remains to be done**: Let the mission speak for itself

### Agent Coordination
- **UX agents produce HTML**: All visual deliverables should be HTML files, not markdown
- **Check for tackiness**: UX designer should review for purposeful elegance
- **File/folder curation**: Consider context window efficiency when organizing

### Project Structure Standards
```
# === APP FILES (change like clay) ===
/src                     # Application source code (React/TypeScript)
/public                  # Static assets for dev (images, data, fonts)
/dist                    # Vite production build output (gitignored)

# === SPEC FILES (capture iterations) ===
/specs                   # All process/strategy documentation
  /discovery            # Research reports and findings
  /ux                   # UX specs and component designs (HTML)
  /prds                 # Product requirement documents
  /landing-options      # Alternative landing page approaches
/.claude
  /agents              # Agent definitions
  /plans               # Planning documents

# === TABLET PIPELINE ===
/tablet-pipeline        # CDLI download/validation/organization scripts

# === HISTORICAL ARCHIVE ===
/archive                # Previous demo iterations (reference only)
  /Demo 1               # First demo attempt
  /Demo 2               # Second demo iteration
  /capstone            # Course materials
```

### Tablet Image Sourcing
- Use CDLI (cdli.earth) as primary source
- Verify downloads contain actual image data (not error pages)
- Store metadata alongside images
- Attribute properly: "Images courtesy of CDLI and respective museums"

---

## Current Phase: Release 1 (POC Demo)

### Goals
- Make vision "believable, enticing, and a source for feedback"
- Demonstrate value for both academics and hobbyists
- Marketing page + Passerby flow functional
- Expert demo experience coming next

### Key Constraints
- Dummy data only - no live integrations
- No fake stats or testimonials
- Focus on honest problem framing

### Primary KPIs (for real adoption later)
- Academics: Number of newly transcribed artifacts
- Hobbyists: Number of contributions per hour
