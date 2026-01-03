# Assyriology Digital Ecosystem Research Report

**Prepared for:** Glintstone Project Team
**Date:** January 2, 2026
**Author:** Assyriology Ecosystem Advisor
**Version:** 1.0

---

## Executive Summary

The digital Assyriology ecosystem presents a significant opportunity for AI-assisted acceleration of cuneiform transcription and translation. With an estimated 500,000 to 2,000,000 excavated tablets and only 5-6% digitally cataloged (approximately 175,000), the field faces a massive backlog that current methodologies cannot address at scale.

This report maps the existing landscape of platforms, institutions, workflows, and standards to inform Glintstone's strategic positioning. Our analysis reveals fragmented tooling, limited API accessibility, and substantial gaps in the transcription-to-translation pipeline---precisely the conditions where an AI-accelerated platform can create transformative value.

**Key Findings:**
- Three major platforms (CDLI, ORACC, BDTNS) dominate the ecosystem but serve different purposes with limited interoperability
- ATF (ASCII Transliteration Format) is the de facto standard, making it a critical integration point
- Expert capacity is the primary bottleneck; crowdsourcing models remain underutilized
- No existing platform leverages modern AI/ML for assisted transcription or translation
- Strong collaborative culture exists but is constrained by manual, fragmented workflows

---

## 1. Major Digital Platforms and Databases

### 1.1 CDLI (Cuneiform Digital Library Initiative)

**URL:** https://cdli.earth/
**Primary Function:** The largest digital repository of cuneiform artifacts globally
**Institutional Home:** UCLA (previously joint with Max Planck Institute)

#### Scope and Coverage
- **Catalog Size:** 350,000+ artifact entries (as of latest data)
- **Image Holdings:** High-resolution photographs for approximately 120,000+ objects
- **Temporal Coverage:** 3400 BCE to 100 CE (entire cuneiform tradition)
- **Language Coverage:** Sumerian, Akkadian, Elamite, Hittite, Hurrian, Urartian, and others

#### Data Formats and Structure
- **Catalog Records:** Structured metadata including museum numbers, provenience, period, genre, and physical dimensions
- **Transliterations:** ATF format (see Section 3.2)
- **Images:** High-resolution TIFF masters with JPEG derivatives
- **Search Interface:** Web-based search with filtering by period, genre, provenience, and museum

#### Technical Integration Capabilities
- **API Status:** Limited public API; bulk data accessible through periodic data dumps
- **Export Formats:** ATF files, CSV metadata exports
- **Linked Data:** Partial implementation of linked open data principles
- **GitHub Presence:** CDLI maintains repositories for data and tools at github.com/cdli-gh

#### Gaps and Limitations
- Search functionality can be cumbersome for complex queries
- Image-to-text alignment not systematically maintained
- No built-in collaborative annotation features
- Limited real-time contribution workflow for external scholars
- Translation coverage is sparse; primarily stores transliterations

#### Strategic Relevance for Glintstone
CDLI is the essential data backbone for any cuneiform project. Glintstone should prioritize:
1. Importing CDLI catalog metadata as the primary artifact registry
2. Linking Glintstone work products back to CDLI identifiers (P-numbers)
3. Positioning as a complementary "acceleration layer" rather than a competitor

---

### 1.2 ORACC (Open Richly Annotated Cuneiform Corpus)

**URL:** https://oracc.museum.upenn.edu/
**Primary Function:** Platform for creating richly annotated cuneiform text editions
**Institutional Home:** University of Pennsylvania Museum

#### Scope and Coverage
- **Project Structure:** Federated model with 40+ individual corpus projects
- **Total Texts:** 20,000+ published text editions across projects
- **Key Projects:**
  - RINAP (Royal Inscriptions of the Neo-Assyrian Period)
  - ETCSL (Electronic Text Corpus of Sumerian Literature)
  - SAAo (State Archives of Assyria Online)
  - Dcclt (Digital Corpus of Cuneiform Lexical Texts)
  - GKAB (Geography of Knowledge in Assyria and Babylonia)

#### Data Formats and Structure
- **ATF (ASCII Transliteration Format):** The canonical encoding standard (detailed in Section 3.2)
- **Lemmatization:** Full morphological analysis with glossary linkage
- **Translation:** Interlinear translations aligned to source text
- **Metadata:** TEI-influenced structured annotations

#### Technical Integration Capabilities
- **API Status:** JSON API available for programmatic access to corpora
- **Build System:** Open-source toolchain for corpus creation
- **Export Formats:** ATF source files, JSON, XML
- **Documentation:** Comprehensive technical documentation for ATF format
- **GitHub Presence:** Active repositories at github.com/oracc

#### Gaps and Limitations
- Steep learning curve for new contributors
- Each project operates semi-independently, creating inconsistencies
- No AI-assisted features for transcription or translation
- Focused on expert-level curation; not designed for crowdsourcing
- Publication workflow can be slow due to quality requirements

#### Strategic Relevance for Glintstone
ORACC represents the gold standard for scholarly annotation. Glintstone should:
1. Adopt ATF format as native data format for maximum interoperability
2. Consider ORACC projects as potential "export destinations" for expert-validated work
3. Leverage ORACC's lemmatization resources for translation assistance
4. Engage ORACC project leads as potential academic partners

---

### 1.3 BDTNS (Database of Neo-Sumerian Texts)

**URL:** https://bdtns.cesga.es/
**Primary Function:** Specialized database for Ur III administrative texts
**Institutional Home:** University of Oxford / CESGA (Spain)
**Project Lead:** Manuel Molina (CSIC, Madrid)

#### Scope and Coverage
- **Focus Period:** Ur III Dynasty (2112-2004 BCE)
- **Catalog Size:** 100,000+ administrative text records
- **Text Types:** Economic tablets, receipts, labor records, livestock accounts
- **Coverage:** Near-comprehensive for published Ur III texts

#### Data Formats and Structure
- **Transliterations:** ATF-compatible format
- **Metadata:** Detailed administrative classification (transaction type, commodities, personal names)
- **Prosopography:** Extensive personal name database with cross-references
- **Seals:** Seal impression catalog linked to texts

#### Technical Integration Capabilities
- **API Status:** No public API; web-based search only
- **Export:** Limited; manual copy of individual records
- **Search:** Sophisticated Boolean search with sign-level queries
- **Updates:** Regularly updated with new publications

#### Gaps and Limitations
- Narrow temporal focus (Ur III only)
- No programmatic access for bulk operations
- Interface designed for expert users
- Limited image integration

#### Strategic Relevance for Glintstone
BDTNS offers high-quality specialized data for a well-defined corpus:
1. Excellent training data source for Ur III administrative text patterns
2. Personal name database valuable for entity recognition
3. Lower integration priority than CDLI/ORACC due to narrow scope
4. Potential partnership opportunity for demonstrating AI value on formulaic texts

---

### 1.4 Additional Platforms and Resources

#### ePSD2 (Electronic Pennsylvania Sumerian Dictionary)
- **URL:** https://oracc.museum.upenn.edu/epsd2/
- **Function:** Comprehensive Sumerian lexicon with attestations
- **Value:** Essential reference for translation; programmatically accessible

#### ARCHIBAB (Archives Babyloniennes)
- **URL:** https://www.archibab.fr/
- **Function:** Old Babylonian text corpus and prosopography
- **Value:** Specialized for OB period; French-language interface

#### SEAL (Sources of Early Akkadian Literature)
- **URL:** https://seal.huji.ac.il/
- **Function:** Old Akkadian and Old Babylonian literary texts
- **Value:** High-quality translations and commentary

#### CCP (Cuneiform Commentaries Project)
- **URL:** https://ccp.yale.edu/
- **Function:** First-millennium scholarly commentaries
- **Value:** Demonstrates importance of intertextual connections

#### CAMS (Corpus of Ancient Mesopotamian Scholarship)
- **URL:** Via ORACC
- **Function:** Scholarly and scientific texts (medicine, astrology, divination)
- **Value:** Specialized domain knowledge

---

## 2. Key Institutions and Research Groups

### 2.1 Major Research Universities

#### North America

**Yale University - Yale Babylonian Collection**
- One of the largest cuneiform collections in the Americas (~45,000 tablets)
- Key researchers: Eckart Frahm, Benjamin Foster, Agnete Lassen
- Specializations: Assyrian royal inscriptions, Akkadian literature, Babylonian scholarship
- Active in: RINAP, CCP, digital imaging projects

**University of Pennsylvania Museum**
- Hosts ORACC infrastructure
- Large tablet collection from Nippur excavations
- Key researchers: Steve Tinney (ORACC director), Grant Frame
- Specializations: Sumerian literature, Neo-Assyrian inscriptions

**UCLA**
- Current home of CDLI
- Key researchers: Robert Englund (CDLI founder, emeritus)
- Specializations: Archaic texts, digital curation methodology

**University of Chicago - Oriental Institute**
- Historic center of Assyriology in North America
- Chicago Assyrian Dictionary (CAD) - foundational reference work
- Key researchers: Christopher Woods, Hervieu-Leger
- Specializations: Sumerian grammar, archaic texts

**Harvard University**
- Semitic Museum collection
- Key researchers: Gojko Barjamovic, Piotr Steinkeller
- Specializations: Old Assyrian trade, Ur III administration

#### Europe

**University of Oxford**
- Major collection at Ashmolean Museum
- Key researchers: Eleanor Robson, Jacob Dahl
- Specializations: Mathematical texts, Ur III studies, digital humanities
- Active in: BDTNS, Nahrein Network

**SOAS University of London**
- Strong Assyriology program
- Key researchers: Andrew George (Gilgamesh expert)
- Specializations: Babylonian literature, first-millennium texts

**LMU Munich**
- Major German center for Assyriology
- Key researchers: Karen Radner, Enrique Jimenez
- Specializations: Neo-Assyrian empire, Babylonian scholarly texts
- Active in: RINAP, numerous ORACC projects

**Leiden University**
- Active digital humanities engagement
- Key researchers: Caroline Waerzeggers
- Specializations: Neo-Babylonian archives, prosopography

**Sapienza University of Rome / CNR**
- Key researchers: Alfonso Catagnoti
- Specializations: Ebla texts, third-millennium Syria

### 2.2 Museums with Major Holdings

| Institution | Location | Approximate Holdings | Notable Strengths |
|-------------|----------|---------------------|-------------------|
| British Museum | London | 130,000+ | Nineveh library, Babylonian chronicles |
| Vorderasiatisches Museum | Berlin | 35,000+ | Babylon excavations, Assur tablets |
| Iraq Museum | Baghdad | 100,000+ | Ur, Nippur, and Iraqi site excavations |
| Louvre | Paris | 25,000+ | Susa, Tello, Mari excavations |
| Penn Museum | Philadelphia | 30,000+ | Nippur excavations |
| Yale Babylonian Collection | New Haven | 45,000+ | Diverse purchase collections |
| Istanbul Archaeological Museums | Istanbul | 75,000+ | Ottoman-era excavation shares |

### 2.3 Collaborative Networks

#### International Association for Assyriology (IAA)
- Primary professional organization
- Hosts Rencontre Assyriologique Internationale (RAI) annual conference
- Key venue for announcements and collaboration building

#### Nahrein Network
- UK-funded network for Iraqi and Middle Eastern heritage
- Focus on capacity building and knowledge exchange
- Led by Eleanor Robson (Oxford)

#### MOCCI (Munich Open-access Cuneiform Corpus Initiative)
- LMU Munich-based digitization and publication efforts
- Emphasizes open access and data sharing

#### CUNE-IIIF Initiative
- Emerging effort to apply IIIF standards to cuneiform imaging
- Would enable standardized image sharing across institutions

### 2.4 Key Individual Researchers to Engage

| Name | Institution | Specialization | Relevance to Glintstone |
|------|-------------|----------------|------------------------|
| Steve Tinney | Penn Museum | ORACC director, Sumerian | Critical for ORACC integration |
| Eckart Frahm | Yale | Neo-Assyrian inscriptions | High-profile scholar, potential advisor |
| Eleanor Robson | Oxford | Digital humanities, education | Crowdsourcing expertise |
| Jacob Dahl | Oxford | Ur III, proto-cuneiform | CDLI contributor, digital methods |
| Enrique Jimenez | LMU Munich | Babylonian scholarship | Digital edition methodology |
| Manuel Molina | CSIC Madrid | BDTNS director | Neo-Sumerian administrative texts |
| Karen Radner | LMU Munich | Neo-Assyrian period | Large-scale corpus projects |
| Niek Veldhuis | UC Berkeley | Sumerian lexicography | Computational approaches |

---

## 3. Current Workflows and Data Standards

### 3.1 Typical Transcription/Translation Workflow

The traditional workflow for processing a cuneiform tablet follows these stages:

```
1. ARTIFACT ACCESS
   Physical tablet OR photograph/scan
           |
           v
2. CATALOGING
   Assign identifiers, record metadata
   (museum number, provenience, period, dimensions)
           |
           v
3. COLLATION
   Expert examines signs, often with multiple light angles
   Physical access strongly preferred
           |
           v
4. TRANSLITERATION
   Convert signs to normalized Latin-script representation
   Encoded in ATF format
           |
           v
5. NORMALIZATION
   Resolve sign ambiguities, apply conventional readings
           |
           v
6. LEMMATIZATION
   Parse words, link to dictionary entries
   Identify morphological structure
           |
           v
7. TRANSLATION
   Produce target-language rendering
   Interlinear or running prose
           |
           v
8. COMMENTARY
   Scholarly notes, parallels, interpretive discussion
           |
           v
9. PUBLICATION
   Journal article, book, or digital edition
```

**Key Observations:**
- Steps 3-7 require specialized expertise (estimated 200-500 active scholars globally)
- Physical access to tablets remains important for disputed readings
- Typical time from collation to publication: 6 months to several years
- Backlogs are enormous; many tablets photographed but never transcribed

### 3.2 ATF (ASCII Transliteration Format)

ATF is the de facto standard for encoding cuneiform transliterations. Understanding ATF is essential for Glintstone integration.

#### Basic Structure

```
&P123456 = Museum Number, Tablet Name
#atf: lang akk
@tablet
@obverse
1. a-na {d}utu be-li2-ia
2. um-ma {m}a-bi-e-szar2-rum
3. ar-du-ka-a-ma
@reverse
1. u2-ul i-ba-asz-szi
2. a-na be-li2-ia
3. asz-pu-ur
```

#### Key Conventions

| Element | Meaning | Example |
|---------|---------|---------|
| `&P######` | CDLI text identifier | `&P123456` |
| `@tablet` | Object type | `@tablet`, `@envelope` |
| `@obverse/@reverse` | Surface designation | Tablet sides |
| `{d}` | Determinative (divine) | `{d}utu` = god Shamash |
| `{m}` | Determinative (male name) | `{m}szu-i3-li2-szu` |
| Line numbers | Physical line on tablet | `1.`, `2.`, etc. |
| `#` | Comment lines | `# broken` |
| `[...]` | Missing/damaged signs | `[a-na]` |
| `x` | Unreadable sign | `x-bi-um` |
| `!` | Collation correction | `a!-na` |
| `?` | Uncertain reading | `a?-na` |
| `#` (after sign) | Damaged sign | `a#-na` |

#### Lemmatization Layer

```
1. a-na {d}utu be-li2-ia
#lem: ana[to]PRP; +Šamaš[1]DN$; bēlu[lord]N$bēlīya
```

#### Value for Glintstone
- ATF provides structured representation of uncertainty (crucial for confidence levels)
- Lemmatization links enable dictionary lookup and translation assistance
- Wide adoption means Glintstone outputs can integrate with existing tools
- Format is human-readable but machine-parseable

### 3.3 Confidence Level Conventions

Current approaches to encoding uncertainty are inconsistent but include:

#### Sign-Level Uncertainty (in ATF)
- `x` = completely unreadable
- `[sign]` = restored (broken but inferable from context)
- `sign?` = reading uncertain
- `sign!` = reading collated/corrected from previous publication
- `sign#` = sign partially damaged

#### Word/Phrase Level
- Often handled in commentary rather than encoding
- Some projects use custom notation
- No standardized confidence scoring (0-100% type system)

#### Translation Level
- Typically conveyed through:
  - Parenthetical phrases: "(lit. 'house of binding')"
  - Footnotes and commentary
  - Alternative translations presented
- No machine-readable confidence encoding

**Gap for Glintstone:** No existing platform provides systematic, machine-readable confidence scoring at the translation level. This is an opportunity for innovation.

### 3.4 Image Standards

- **Resolution:** Minimum 300 DPI for publication; 600+ DPI for analysis
- **Format:** TIFF for archival; JPEG/PNG for web
- **Lighting:** Multiple angles (raking light) essential for sign reading
- **RTI (Reflectance Transformation Imaging):** Emerging standard for interactive lighting
- **3D Scanning:** Increasingly common but not yet standardized

---

## 4. Ecosystem Pain Points and Opportunities

### 4.1 Critical Pain Points

#### 1. Expert Capacity Bottleneck
- **Problem:** Only 200-500 scholars can read cuneiform at expert level globally
- **Impact:** 94-95% of tablets remain untranscribed after a century of work
- **Current Mitigation:** None effective at scale

#### 2. Fragmented Data Ecosystem
- **Problem:** CDLI, ORACC, BDTNS, and institutional databases operate independently
- **Impact:** No single source of truth; scholars must search multiple platforms
- **Current Mitigation:** Manual cross-referencing; some linking via P-numbers

#### 3. Limited Crowdsourcing Infrastructure
- **Problem:** No effective platform for non-experts to contribute
- **Impact:** Untapped volunteer enthusiasm; no pathway for learners
- **Current Mitigation:** Limited Zooniverse-style projects (e.g., Micropasts)

#### 4. No AI/ML Acceleration
- **Problem:** All transcription and translation done manually
- **Impact:** Unsustainable given backlog size
- **Current Mitigation:** None

#### 5. Poor Image-Text Alignment
- **Problem:** Images and transliterations often stored separately
- **Impact:** Difficult to verify readings; training data hard to assemble
- **Current Mitigation:** Ad hoc solutions in individual projects

#### 6. Publication Bottleneck
- **Problem:** Traditional journal publication is slow and siloed
- **Impact:** Knowledge trapped behind paywalls; duplicated effort
- **Current Mitigation:** Growing open-access movement but slow adoption

#### 7. Inconsistent Metadata Quality
- **Problem:** Provenience, dating, and classification vary in quality and granularity
- **Impact:** Difficult to contextualize tablets; training data is noisy
- **Current Mitigation:** Manual curation in specific projects

### 4.2 Strategic Opportunities for Glintstone

| Opportunity | Description | Difficulty | Impact |
|-------------|-------------|------------|--------|
| **AI-Assisted Transcription** | Computer vision to suggest sign readings | High | Transformative |
| **AI-Assisted Translation** | LLM-powered translation with confidence scoring | High | Transformative |
| **Crowdsourced Verification** | Zooniverse-style tasks for non-experts | Medium | High |
| **Unified Search Interface** | Aggregate data from CDLI, ORACC, BDTNS | Medium | High |
| **Expert Workflow Acceleration** | AI suggestions + streamlined review interface | Medium | High |
| **Confidence Scoring System** | Machine-readable uncertainty at all levels | Medium | Medium |
| **Image-Text Alignment Tool** | Interactive linking of images to transliteration | Medium | Medium |
| **Social Collaboration Layer** | Connect scholars across institutions | Low | Medium |
| **Learning Pathway** | Gamified education for hobbyists | Low | Medium |
| **Open Corpus Building** | Platform for collaborative edition building | High | High |

---

## 5. Recommendations for Glintstone Integration

### 5.1 Platform Integration Priority Matrix

| Platform | Priority | Rationale | Integration Approach |
|----------|----------|-----------|---------------------|
| **CDLI** | Critical | Largest catalog; P-number identifiers are universal | Bulk metadata import; image linking; P-number as foreign key |
| **ORACC** | Critical | ATF standard; richest annotations; API available | ATF format adoption; JSON API consumption; lemmatization data |
| **ePSD2** | High | Essential for translation; well-structured | API integration for dictionary lookup |
| **BDTNS** | Medium | Specialized but high-quality Ur III data | Web scraping or partnership for bulk access |
| **Zooniverse** | Medium | Model for crowdsourcing UX | Study workflow patterns; potentially build Glintstone project on platform |

### 5.2 Data Format Strategy

**Recommendation:** Adopt ATF as the native internal format with extensions

**Rationale:**
- Maximum compatibility with existing ecosystem
- Human-readable and machine-parseable
- Well-documented standard

**Proposed Extensions for Glintstone:**
```
# Confidence extension
#glint: confidence sign=0.87 word=0.72 translation=0.65

# AI provenance
#glint: source ai-model=cuneiform-vision-v1 timestamp=2026-01-02T14:30:00Z

# Crowdsource verification
#glint: verified user=anon_contributor_42 agreement=0.92
```

### 5.3 Identifier Strategy

- Use CDLI P-numbers as primary external identifier
- Generate internal Glintstone IDs for workflow management
- Maintain mapping table for cross-reference
- Support linking to ORACC project/text identifiers (Q-numbers)

### 5.4 Positioning Strategy

**Position Glintstone as:** An acceleration layer that enhances, not replaces, the existing ecosystem

**Key Messages:**
1. "We help you work faster, not differently" - familiar workflows, AI assistance
2. "Your work flows back to the community" - export to CDLI/ORACC
3. "Everyone can contribute" - crowdsourcing expands the field
4. "Experts remain in control" - validation and approval workflows

**What Glintstone is NOT:**
- Not a replacement for CDLI (catalog) or ORACC (scholarly editions)
- Not a competitor to existing scholarly publication venues
- Not an attempt to "solve" cuneiform with AI alone

### 5.5 Academic Engagement Strategy

**Phase 1: Advisory Network (Pre-launch)**
- Engage 3-5 key scholars as advisors
- Target: Mix of senior figures (legitimacy) and digital-savvy researchers (adoption)
- Suggested initial outreach: Steve Tinney (ORACC), Eleanor Robson (Oxford), Eckart Frahm (Yale)

**Phase 2: Pilot Partnership (Release 2)**
- Partner with 1-2 institutions for controlled pilot
- Target: Medium-sized project with backlog (e.g., unpublished museum collection)
- Success metric: Demonstrated acceleration with maintained quality

**Phase 3: Community Building (Release 3+)**
- Present at Rencontre Assyriologique Internationale
- Publish methodology paper in digital humanities venue
- Build contributor community through hobbyist track

### 5.6 Technical Architecture Recommendations

```
+--------------------------------------------------+
|                  GLINTSTONE PLATFORM              |
+--------------------------------------------------+
|  User Interfaces                                  |
|  +------------+  +-------------+  +------------+ |
|  | Hobbyist   |  | Learner     |  | Expert     | |
|  | (Zooniverse|  | (Guided     |  | (Full      | |
|  |  style)    |  |  learning)  |  |  workflow) | |
|  +------------+  +-------------+  +------------+ |
+--------------------------------------------------+
|  AI Services Layer                               |
|  +-------------+  +--------------+  +----------+ |
|  | Sign        |  | Translation  |  | Context  | |
|  | Recognition |  | Assistance   |  | Engine   | |
|  +-------------+  +--------------+  +----------+ |
+--------------------------------------------------+
|  Data Layer                                      |
|  +-------------+  +--------------+  +----------+ |
|  | Artifact    |  | Contribution |  | User     | |
|  | Registry    |  | Workflow     |  | Profiles | |
|  | (ATF store) |  | (confidence) |  | (social) | |
|  +-------------+  +--------------+  +----------+ |
+--------------------------------------------------+
|  External Integrations                           |
|  +------+  +-------+  +-------+  +------------+ |
|  | CDLI |  | ORACC |  | ePSD2 |  | Future     | |
|  | sync |  | API   |  | lookup|  | platforms  | |
|  +------+  +-------+  +-------+  +------------+ |
+--------------------------------------------------+
```

### 5.7 Risk Mitigation

| Risk | Likelihood | Impact | Mitigation |
|------|------------|--------|------------|
| Academic skepticism of AI | High | High | Expert oversight, transparent confidence scoring, conservative claims |
| Data quality issues | Medium | High | Validation workflows, crowdsource verification, expert review gates |
| Platform fragmentation | Medium | Medium | Prioritize interoperability, export capabilities, open data |
| Limited API access | Medium | Medium | Pursue partnerships; fallback to authorized scraping |
| Scope creep | Medium | Medium | Phased releases; POC-first approach |

---

## 6. Appendices

### Appendix A: Glossary of Terms

| Term | Definition |
|------|------------|
| ATF | ASCII Transliteration Format - standard encoding for cuneiform texts |
| Collation | Physical examination of tablet to verify sign readings |
| Determinative | Semantic classifier sign (not pronounced) |
| Lemmatization | Linking words to dictionary entries with morphological analysis |
| P-number | CDLI unique identifier (e.g., P123456) |
| Provenience | Archaeological find location |
| Transliteration | Representation of cuneiform signs in Latin script |
| Ur III | Third Dynasty of Ur (2112-2004 BCE) |

### Appendix B: Key URLs

| Resource | URL |
|----------|-----|
| CDLI | https://cdli.earth/ |
| ORACC | https://oracc.museum.upenn.edu/ |
| BDTNS | https://bdtns.cesga.es/ |
| ePSD2 | https://oracc.museum.upenn.edu/epsd2/ |
| CDLI GitHub | https://github.com/cdli-gh |
| ORACC GitHub | https://github.com/oracc |
| ATF Documentation | http://oracc.museum.upenn.edu/doc/help/editinginatf/ |

### Appendix C: Sample ATF Document

```
&P123456 = YBC 4644
#atf: lang akk
#project: cams/gkab
#atf: use unicode
@tablet
@obverse
1. a-na {d}utu be-li2-ia
#lem: ana[to]PRP; +Šamaš[1]DN$; bēlu[lord]N$bēlīya
#tr.en: To Shamash, my lord,
2. qi2-bi-ma
#lem: qabû[say]V$qibīma
#tr.en: speak!
3. um-ma {m}szu-i3-li2-szu
#lem: umma[saying]PRP; +Šū-ilišu[1]PN$
#tr.en: Thus says Shu-ilishu:
@reverse
1. u2-ul i-ba-asz-szi
#lem: ul[not]MOD; bašû[exist]V$ibaššī
#tr.en: There is not
2. a-na be-li2-ia
#lem: ana[to]PRP; bēlu[lord]N$bēlīya
#tr.en: for my lord
3. sza2 asz-pu-ru
#lem: ša[that]REL; šapāru[send]V$ašpuru
#tr.en: what I wrote.
```

---

## 7. Document Control

| Version | Date | Author | Changes |
|---------|------|--------|---------|
| 1.0 | 2026-01-02 | Assyriology Ecosystem Advisor | Initial release |

---

*This document should be updated as the ecosystem evolves and as Glintstone development progresses. Recommend quarterly review of platform capabilities and annual comprehensive update.*
