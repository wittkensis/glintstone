# Institutional Logos

This directory contains logos for universities, museums, and research platforms featured in the Glintstone Release 1 demo.

## Status: PLACEHOLDERS NEEDED

The following institutional logo files need to be sourced and placed in this directory:

### Required Files

#### Universities

1. `yale.png` - Yale University
   - Official site: https://nelc.yale.edu/
   - Colors: Yale Blue (#00356b)
   - Style: Shield/crest or wordmark

2. `chicago.png` - University of Chicago
   - Official site: https://oi.uchicago.edu/
   - Colors: Maroon (#800000)
   - Style: Phoenix crest or Oriental Institute logo

3. `penn.png` - University of Pennsylvania
   - Official site: https://www.sas.upenn.edu/nelc/
   - Colors: Penn Red (#990000), Penn Blue (#01256e)
   - Style: Shield with dolphins

4. `oxford.png` - University of Oxford
   - Official site: https://www.orinst.ox.ac.uk/
   - Colors: Oxford Blue (#002147)
   - Style: University crest or text wordmark

5. `harvard.png` - Harvard University
   - Official site: https://nelc.fas.harvard.edu/
   - Colors: Crimson (#a51c30)
   - Style: Shield/Veritas crest

6. `heidelberg.png` - Heidelberg University
   - Official site: https://www.uni-heidelberg.de/
   - Colors: Red/Gold
   - Style: University seal or wordmark

7. `berlin-fu.png` - Freie Universität Berlin
   - Official site: https://www.fu-berlin.de/
   - Colors: Green/White
   - Style: University wordmark

8. `leiden.png` - Leiden University
   - Official site: https://www.universiteitleiden.nl/
   - Colors: Blue/White
   - Style: University seal or wordmark

9. `lmu-munich.png` - Ludwig Maximilian University of Munich
   - Official site: https://www.lmu.de/
   - Colors: Blue/Gold
   - Style: University crest or wordmark

#### Museums

10. `british-museum.png` - British Museum
    - Official site: https://www.britishmuseum.org/
    - Style: Classical building facade icon or wordmark
    - Note: Iconic, highly recognizable

11. `louvre.png` - Louvre Museum
    - Official site: https://www.louvre.fr/
    - Style: Pyramid icon or Louvre wordmark
    - Note: Iconic, highly recognizable

12. `penn-museum.png` - Penn Museum
    - Official site: https://www.penn.museum/
    - Colors: Penn colors
    - Style: Museum wordmark

13. `vorderasiatisches.png` - Vorderasiatisches Museum (Pergamon Museum)
    - Official site: https://www.smb.museum/
    - Style: Staatliche Museen zu Berlin wordmark
    - Note: Part of Berlin State Museums

#### Research Platforms

14. `cdli.png` - Cuneiform Digital Library Initiative
    - Official site: https://cdli.ucla.edu/
    - Style: CDLI logo (if available) or text-based
    - Note: May need to create simplified version

15. `oracc.png` - ORACC (Open Richly Annotated Cuneiform Corpus)
    - Official site: http://oracc.museum.upenn.edu/
    - Style: ORACC logo or text-based
    - Note: May need to create simplified version

## Image Specifications

- **Format:** PNG (with transparency) or SVG
- **Dimensions:** 200x200px (square) or proportional
- **File size:** Small as possible while maintaining clarity
- **Background:** Transparent
- **Quality:** Vector-based preferred, or high-res raster

## Sourcing Instructions

See `/public/ASSET-SOURCING.md` for detailed sourcing strategy.

### Primary Sourcing Methods

1. **Official Press/Media Kits**
   - Search: "[Institution name] media kit" or "[Institution name] brand guidelines"
   - Most universities provide downloadable logos for press use
   - Check usage guidelines (usually allows factual representation)

2. **Wikimedia Commons**
   - URL: https://commons.wikimedia.org/
   - Search: "[Institution name] logo"
   - Verify license allows commercial/demo use

3. **Simplified Text-Based Versions (Fallback)**
   - Create clean, professional text-based logo
   - Use institutional colors
   - Simple sans-serif typography
   - Transparent background

### Quick Temporary Solution

For development, create SVG text-based placeholders:
```svg
<svg width="200" height="200" xmlns="http://www.w3.org/2000/svg">
  <rect width="200" height="200" fill="transparent"/>
  <text x="50%" y="50%" text-anchor="middle" fill="#00356b" font-size="20" font-family="Arial">
    YALE
  </text>
</svg>
```

## Legal Considerations

- **Trademark Notice:** Institutional logos are typically trademarked
- **Demo Use:** Generally acceptable for non-commercial POC demonstrations
- **No Implied Endorsement:** Do not suggest partnership without permission
- **Required Disclaimer:** Include demo notice on marketing page

## Attribution

Document specific sources and licenses in `/public/ASSET-SOURCING.md` as logos are added.

## Demo Disclaimer

The following disclaimer should appear on the marketing page:

```
Institutional logos are used for illustrative purposes only and do not imply
endorsement, affiliation, or partnership. This is a proof-of-concept demonstration
using fictional expert profiles and dummy data.
```
