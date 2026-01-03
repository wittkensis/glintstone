# Visual Assets Sourcing Guide for Glintstone Release 1

**Project:** Glintstone - Agentic Cuneiform
**Purpose:** Build trust and credibility through authentic visual assets
**Status:** In Progress
**Created:** 2026-01-03

---

## Overview

This document outlines the sourcing strategy, attribution requirements, and implementation guidelines for visual assets used in the Glintstone Release 1 POC demo. All assets are for demonstration purposes using dummy/fictional data, prioritizing authenticity and credibility over actual accuracy.

---

## Asset Categories

### 1. Expert Headshots/Avatars (12 fictional experts)

**Purpose:** Create believable expert profiles to build trust in the review process

**Requirements:**
- Professional academic style (university faculty page aesthetic)
- Diverse representation: gender, age, ethnicity, backgrounds
- Authentic, credible appearance
- High quality, web-optimized (200x200px minimum)

**Sourcing Strategy:**

#### Primary Sources (CC0/Public Domain)

1. **This Person Does Not Exist (AI-Generated)**
   - URL: https://thispersondoesnotexist.com/
   - License: Free to use (AI-generated, no copyright)
   - Pros: Realistic, diverse, unlimited variations
   - Cons: Requires manual curation for professional appearance
   - Usage: Generate multiple options, select most academic-looking

2. **Generated Photos**
   - URL: https://generated.photos/
   - License: Free tier available with attribution
   - Pros: High quality, diverse, can filter by attributes
   - Cons: Limited free downloads
   - Usage: Use for specific demographic requirements

3. **CC0 Photo Archives**
   - Rawpixel Public Domain: https://www.rawpixel.com/public-domain
   - CC0.photo: https://cc0.photo/
   - Free-images.com: https://free-images.com/
   - AltPhotos: https://altphotos.com/
   - Pros: Legally clear, no attribution required
   - Cons: Limited selection of professional headshots
   - Usage: Search for "portrait professional headshot" + demographic terms

#### Image Specifications

- Format: JPG (optimized for web)
- Dimensions: 400x400px (will scale to various sizes)
- File naming: `[lastname]-[firstname].jpg`
- Location: `/public/images/experts/`
- Compression: High quality, ~50-80kb per file

#### Fictional Expert Profiles Created

| ID | Name | Affiliation | Specialization | Avatar Status |
|----|------|-------------|----------------|---------------|
| expert-001 | Sarah Morrison | Yale University | Neo-Assyrian administrative texts | Placeholder |
| expert-002 | David Chen | University of Chicago | Sumerian literary texts | Placeholder |
| expert-003 | Amira Hassan | British Museum | Old Babylonian legal documents | Placeholder |
| expert-004 | Michael Fitzgerald | University of Oxford | Akkadian correspondence | Placeholder |
| expert-005 | Yuki Tanaka | University of Pennsylvania | Ur III administrative archives | Placeholder |
| expert-006 | Elena Volkov | Heidelberg University | Neo-Babylonian temple economy | Placeholder |
| expert-007 | James O'Brien | Harvard University | Sumerian mathematical texts | Placeholder |
| expert-008 | Fatima Al-Rashid | Freie Universität Berlin | Achaemenid administrative texts | Placeholder |
| expert-009 | Robert Lindström | Leiden University | Middle Babylonian royal inscriptions | Placeholder |
| expert-010 | Priya Sharma | Louvre Museum | Sumerian votive inscriptions | Placeholder |
| expert-011 | Thomas Weber | LMU Munich | Akkadian lexicography | Placeholder |
| expert-012 | Aisha Nkrumah | Johns Hopkins University | Old Babylonian personal letters | Placeholder |

---

### 2. Institutional Logos (15 organizations)

**Purpose:** Demonstrate academic credibility and institutional partnerships

**Requirements:**
- Official or simplified versions of real institutional logos
- Clear, recognizable branding
- Web-optimized (SVG preferred, PNG acceptable)
- Transparent backgrounds

**Sourcing Strategy:**

#### Primary Sources

1. **Official University/Museum Websites**
   - Most institutions provide logo downloads in media/press kits
   - Look for: "[Institution] media kit" or "[Institution] logo download"
   - License: Typically allowed for factual representation
   - Usage: Download official logos from press resources

2. **Wikimedia Commons**
   - URL: https://commons.wikimedia.org/
   - License: Various (check individual logos)
   - Search: "[Institution] logo"
   - Pros: Often has official logos with clear licensing
   - Usage: Verify license allows commercial/demo use

3. **Simplified/Generic Versions**
   - For institutions without clear licensing: create simplified text-based logos
   - Style: Clean sans-serif type, institutional color scheme
   - Tools: Figma, Canva, or SVG editors
   - Usage: When official logo licensing is unclear

#### Image Specifications

- Format: PNG (transparent background) or SVG
- Dimensions: 200x200px (square) or proportional
- File naming: `[institution-slug].png`
- Location: `/public/images/institutions/`
- Background: Transparent
- Compression: Lossless for clarity

#### Institutions Included

| ID | Institution | Type | Logo Status | Website |
|----|-------------|------|-------------|---------|
| inst-yale | Yale University | University | Placeholder | https://nelc.yale.edu/ |
| inst-chicago | University of Chicago | University | Placeholder | https://oi.uchicago.edu/ |
| inst-penn | University of Pennsylvania | University | Placeholder | https://www.sas.upenn.edu/nelc/ |
| inst-oxford | University of Oxford | University | Placeholder | https://www.orinst.ox.ac.uk/ |
| inst-harvard | Harvard University | University | Placeholder | https://nelc.fas.harvard.edu/ |
| inst-heidelberg | Heidelberg University | University | Placeholder | https://www.uni-heidelberg.de/ |
| inst-berlin-fu | Freie Universität Berlin | University | Placeholder | https://www.fu-berlin.de/ |
| inst-leiden | Leiden University | University | Placeholder | https://www.universiteitleiden.nl/ |
| inst-british-museum | British Museum | Museum | Placeholder | https://www.britishmuseum.org/ |
| inst-louvre | Louvre Museum | Museum | Placeholder | https://www.louvre.fr/ |
| inst-penn-museum | Penn Museum | Museum | Placeholder | https://www.penn.museum/ |
| inst-vorderasiatisches | Vorderasiatisches Museum | Museum | Placeholder | https://www.smb.museum/ |
| inst-cdli | CDLI | Research Platform | Placeholder | https://cdli.ucla.edu/ |
| inst-oracc | ORACC | Research Platform | Placeholder | http://oracc.museum.upenn.edu/ |
| inst-lmu-munich | LMU Munich | University | Placeholder | https://www.lmu.de/ |

---

## Attribution Requirements

### For CC0/Public Domain Images

**License:** Creative Commons Zero (CC0)
- **Attribution Required:** No
- **Commercial Use:** Allowed
- **Modifications:** Allowed
- **Best Practice:** Document source in this file for transparency

### For AI-Generated Images

**This Person Does Not Exist:**
- **License:** No copyright (AI-generated)
- **Attribution Required:** No
- **Usage Rights:** Unlimited
- **Ethical Note:** Clearly fictional, not representing real people

**Generated Photos:**
- **License:** Check specific tier (free tier may require attribution)
- **Attribution Required:** Varies by plan
- **Usage:** Include attribution if required by plan

### For Institutional Logos

**Official Logos (Press Kit Downloads):**
- **License:** Typically trademarked
- **Usage:** Generally permitted for factual representation
- **Restrictions:** Cannot imply endorsement without permission
- **Demo Use:** Acceptable for non-commercial POC demonstrations
- **Best Practice:** Include disclaimer that logos are used for demonstration purposes

**Simplified/Generic Versions:**
- **License:** Created in-house, no restrictions
- **Usage:** Unlimited
- **Note:** Clearly inspired by but not copying official logos

### Required Disclaimer

Add to demo interface:

```
DEMO NOTICE: All expert profiles are fictional and created for demonstration
purposes. Institutional logos are used for illustrative purposes only and do
not imply endorsement or affiliation. This is a proof-of-concept demonstration.
```

---

## Implementation Checklist

### Phase 1: Expert Avatars
- [ ] Generate/source 12 diverse professional headshots
- [ ] Optimize images (400x400px, JPG, ~50kb each)
- [ ] Rename files to match experts.json naming convention
- [ ] Save to `/public/images/experts/`
- [ ] Verify all images display correctly in demo
- [ ] Document actual sources in this file (update table above)

### Phase 2: Institutional Logos
- [ ] Download official logos from university/museum press kits
- [ ] Create simplified versions where licensing is unclear
- [ ] Optimize images (PNG with transparency or SVG)
- [ ] Rename files to match institutions.json slug convention
- [ ] Save to `/public/images/institutions/`
- [ ] Verify all logos display correctly in demo
- [ ] Document actual sources in this file (update table above)

### Phase 3: Integration
- [ ] Update experts.json with final avatar URLs
- [ ] Update institutions.json with final logo URLs
- [ ] Test image loading in all demo journeys (J1-J5)
- [ ] Add demo disclaimer to marketing page (J1)
- [ ] Verify responsive image scaling
- [ ] Test accessibility (alt text, contrast)

### Phase 4: Documentation
- [ ] Update this file with actual image sources
- [ ] Create attribution.txt if required
- [ ] Document any licensing restrictions
- [ ] Note any images that need replacement before production

---

## Placeholder Strategy

For initial development, use placeholder images:

**Expert Avatars:**
- Use https://ui-avatars.com/api/ for instant text-based avatars
- Format: `https://ui-avatars.com/api/?name=[First+Last]&size=400&background=1a1f3a&color=d4af37`
- Replace with real images before final demo

**Institutional Logos:**
- Use simple text-based placeholders initially
- Format: Institution name in institutional color on transparent background
- Replace with official/simplified logos before final demo

---

## Quality Standards

### Expert Avatars Must:
- Look professional and academic (not casual/social media style)
- Be well-lit with neutral backgrounds
- Show appropriate diversity (not all same demographic)
- Appear credible (age-appropriate for professor/curator roles)
- Be high enough quality to not look "stock photo fake"

### Institutional Logos Must:
- Be clearly recognizable (for known institutions)
- Maintain brand consistency with official materials
- Scale well at various sizes (100px to 400px)
- Work on both light and dark backgrounds
- Not appear stretched, pixelated, or low-quality

---

## Future Considerations (Post-Release 1)

### If Moving to Production:
1. **Expert Avatars:**
   - Replace with real contributor photos (with permission)
   - Implement user avatar upload system
   - Consider illustrated/stylized avatars for anonymity

2. **Institutional Logos:**
   - Obtain formal permission for logo usage
   - Sign partnership agreements with featured institutions
   - Remove logos of non-partner institutions

3. **Licensing:**
   - Audit all images for production use
   - Implement proper attribution system
   - Create comprehensive asset license documentation

---

## Resources and References

### CC0/Public Domain Image Sources
- [CC0.photo - Public Domain Photos](https://cc0.photo/)
- [Rawpixel Public Domain Collection](https://www.rawpixel.com/public-domain)
- [Free-images.com](https://free-images.com/)
- [AltPhotos CC0 Collection](https://altphotos.com/)
- [Unsplash CC0 Images](https://unsplash.com/s/photos/cc0)

### AI-Generated Portraits
- [This Person Does Not Exist](https://thispersondoesnotexist.com/)
- [Generated Photos](https://generated.photos/)

### Institutional Resources
- [CDLI - Cuneiform Digital Library Initiative](https://cdli.ucla.edu/)
- [ORACC - Open Richly Annotated Cuneiform Corpus](http://oracc.museum.upenn.edu/)
- University press kits (search: "[university name] media kit logo")

### Design Tools
- **Figma** - Logo simplification/creation
- **TinyPNG** - Image compression
- **SVGOMG** - SVG optimization
- **UI Avatars** - Temporary placeholder avatars

---

## Notes

- **Demo-First Approach:** This is a POC demo with dummy data. Perfect accuracy is not required; authenticity and credibility are the priorities.
- **Ethical Considerations:** All expert profiles are clearly fictional. No real academics are being impersonated.
- **Legal Compliance:** All assets use CC0/public domain sources or are clearly identified as placeholders for demonstration purposes.
- **Update Frequency:** This document should be updated whenever new assets are sourced or licensing information changes.

---

## Change Log

| Date | Author | Changes |
|------|--------|---------|
| 2026-01-03 | Claude | Initial asset sourcing strategy and documentation |

---

*This document serves as the single source of truth for visual asset sourcing and attribution for Glintstone Release 1.*
