# Public Assets - Glintstone Release 1

This directory contains all publicly-accessible assets for the Glintstone POC demo, including images, data manifests, and documentation.

## Directory Structure

```
public/
├── README.md                    # This file
├── ASSET-SOURCING.md           # Asset sourcing strategy and attribution guide
├── data/                        # JSON data manifests
│   ├── experts.json            # Fictional expert profiles (12 experts)
│   └── institutions.json       # Institutional partners (15 organizations)
└── images/                      # Visual assets
    ├── experts/                 # Expert headshots/avatars
    │   ├── README.md           # Expert avatar sourcing guide
    │   └── [lastname-firstname].jpg  # Individual expert photos (TO BE ADDED)
    └── institutions/            # Institutional logos
        ├── README.md           # Logo sourcing guide
        └── [institution-slug].png     # Individual logos (TO BE ADDED)
```

## Quick Reference

### Data Manifests

**experts.json** - 12 fictional Assyriologist experts
- Diverse backgrounds (gender, ethnicity, age)
- Affiliated with top universities and museums
- Realistic specializations and credentials
- Use for: Expert review features, trust indicators, attribution

**institutions.json** - 15 major organizations
- 9 Universities with Assyriology programs
- 4 Museums with cuneiform collections
- 2 Research platforms (CDLI, ORACC)
- Use for: Partnership badges, institutional credibility, logos

### Image Assets

**Expert Avatars** (Status: PLACEHOLDERS NEEDED)
- Location: `/images/experts/`
- Format: JPG, 400x400px, 50-80kb
- Style: Professional academic headshots
- Source: CC0/public domain or AI-generated
- See: `images/experts/README.md` for specific requirements

**Institutional Logos** (Status: PLACEHOLDERS NEEDED)
- Location: `/images/institutions/`
- Format: PNG (transparent) or SVG
- Size: 200x200px or proportional
- Source: Official press kits or simplified versions
- See: `images/institutions/README.md` for specific requirements

## Usage in Release 1

These assets support trust and credibility across all demo journeys:

### J1: Marketing Page
- Show featured expert avatars in "Expert Review" section
- Display institutional partner logos in footer/sidebar
- Build academic credibility for new visitors

### J2: Passerby Contribution Flow
- Display expert avatars in "Your work will be reviewed by..." messaging
- Show institutional badges for tablets (e.g., "From British Museum collection")
- Trust indicators throughout task flow

### J3: Early Learner Onboarding
- Expert testimonials with avatars
- Institution affiliations for curriculum designers
- Trust-building for learning content

### J4: Expert Review Preview
- Realistic expert profiles for demo review queue
- Institutional affiliations for credibility
- Professional avatars in review interface

### J5: CDLI Integration Demo
- CDLI and ORACC logos for integration visualization
- Museum logos for tablet provenance
- Research platform branding

## Implementation Notes

### Loading Data Manifests

```typescript
// Example: Load experts
import expertsData from '@/public/data/experts.json';

// Type-safe usage
interface Expert {
  id: string;
  firstName: string;
  lastName: string;
  title: string;
  affiliation: string;
  avatarUrl: string;
  specialization: string;
  credibilityScore: number;
}

const experts: Expert[] = expertsData;
```

### Displaying Images

```tsx
// Example: Expert avatar with fallback
<img
  src={expert.avatarUrl}
  alt={`${expert.firstName} ${expert.lastName}, ${expert.title}`}
  onError={(e) => {
    // Fallback to UI Avatars if image not found
    e.currentTarget.src = `https://ui-avatars.com/api/?name=${expert.firstName}+${expert.lastName}&size=400&background=1a1f3a&color=d4af37`;
  }}
/>
```

### Institutional Logos

```tsx
// Example: Partner logo grid
{institutions
  .filter(inst => inst.partnered)
  .map(inst => (
    <img
      key={inst.id}
      src={inst.logoUrl}
      alt={inst.name}
      className="institution-logo"
    />
  ))
}
```

## Asset Status

### Current Status: SETUP PHASE

✅ **Completed:**
- Directory structure created
- Data manifests (experts.json, institutions.json)
- Sourcing strategy documentation
- Implementation guides

⚠️ **Needs Attention:**
- [ ] Source/generate 12 expert avatar images
- [ ] Source/create 15 institutional logos
- [ ] Optimize all images for web
- [ ] Test image loading in demo components
- [ ] Update ASSET-SOURCING.md with actual sources
- [ ] Add demo disclaimer to marketing page

### Next Steps

1. **Source Expert Avatars:**
   - Use AI-generated faces (This Person Does Not Exist, Generated Photos)
   - Or search CC0 archives for professional headshots
   - Save as `[lastname-firstname].jpg` in `images/experts/`
   - See `images/experts/README.md` for specific demographic requirements

2. **Source Institutional Logos:**
   - Download from official university/museum press kits
   - Create simplified versions where licensing unclear
   - Save as `[institution-slug].png` in `images/institutions/`
   - See `images/institutions/README.md` for logo list

3. **Update Documentation:**
   - Document actual sources in ASSET-SOURCING.md
   - Add attribution if required
   - Note any licensing restrictions

4. **Integration Testing:**
   - Test image loading in all demo journeys
   - Verify responsive scaling
   - Check accessibility (alt text, contrast)
   - Ensure fallback handling works

## Legal and Ethical Notes

### Demo Disclaimer

**IMPORTANT:** All expert profiles are fictional and created for demonstration purposes only. No real academics are being represented or impersonated.

Recommended disclaimer for demo interface:
```
DEMO NOTICE: All expert profiles are fictional and created for demonstration
purposes. Institutional logos are used for illustrative purposes only and do
not imply endorsement or affiliation. This is a proof-of-concept demonstration.
```

### Licensing

- **Expert Avatars:** CC0/public domain or AI-generated (no copyright)
- **Institutional Logos:** Used for factual representation (demo purposes)
- **Data Manifests:** Original work, no restrictions

See `ASSET-SOURCING.md` for complete licensing details.

## Resources

- **Asset Sourcing Guide:** `/public/ASSET-SOURCING.md`
- **Expert Avatar Guide:** `/public/images/experts/README.md`
- **Institution Logo Guide:** `/public/images/institutions/README.md`
- **PRD Reference:** `/docs/phase2/prds/L2-foundation-dummy-data.md`

## Support

For questions about asset sourcing, licensing, or implementation:
- See ASSET-SOURCING.md for detailed guidance
- Check component README files for specific requirements
- Reference L2 PRD for data schema details

---

**Last Updated:** 2026-01-03
**Status:** Asset infrastructure ready, images needed
**Next Milestone:** Source and add all expert avatars and institutional logos
