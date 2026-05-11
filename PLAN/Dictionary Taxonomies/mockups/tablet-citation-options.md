# Tablet Citation Display Options

Three approaches for presenting citation/metadata for a tablet. Using **P134010** (CM 26, 037) — an Ur III administrative tablet from Umma with 502 text lines, seal impression, physical dimensions, dated text, and full publication data.

---

## Available Citation Fields (P134010)

| Field | Value |
|-------|-------|
| CDLI P-number | P134010 |
| Designation | CM 26, 037 |
| Museum number | NBC 00419 |
| Material | clay |
| Object type | tablet |
| Dimensions | 38 x 38 x 15 mm |
| Seal | S000207 |
| Period | Ur III (ca. 2100-2000 BC) |
| Provenience | Umma (mod. Tell Jokha) |
| Genre | Administrative |
| Language | Sumerian |
| Primary publication | CM 26, 037 |
| Publication author | Sharlach, Tonia M. |
| Surfaces | obverse, reverse |
| Text lines | 502 |
| Collection | Nies Babylonian Collection, Yale |

---

## Option 1: Bibliographic Card (Library Catalog Style)

Treats the tablet as a published artifact. Citation-first layout modeled on library catalog entries and CDLI's own record format. Groups data into labeled blocks.

```
+-------------------------------------------------------------+
|  CM 26, 037                                    P134010       |
|  ===========                                                 |
|                                                              |
|  IDENTIFICATION                                              |
|  Museum no.     NBC 00419                                    |
|  Collection     Nies Babylonian Collection, Yale             |
|  Seal           S000207                                      |
|                                                              |
|  PHYSICAL DESCRIPTION                                        |
|  Object         tablet . clay                                |
|  Dimensions     38 x 38 x 15 mm (W x H x T)                |
|  Surfaces       obverse . reverse                            |
|  Preservation   --                                           |
|                                                              |
|  TEXT                                                        |
|  Language        Sumerian                                    |
|  Lines           502                                         |
|  Genre           Administrative                              |
|  ATF source      cdlistaff                                   |
|  Translation     --                                          |
|                                                              |
|  PROVENANCE                                                  |
|  Provenience     Umma (mod. Tell Jokha)                      |
|  Period          Ur III (ca. 2100-2000 BC)                   |
|  Date            (regnal date if available)                   |
|                                                              |
|  BIBLIOGRAPHY                                                |
|  Primary pub.    CM 26, 037                                  |
|  Author          Sharlach, Tonia M.                          |
|  ORACC           epsd2                                       |
|  CDLI            https://cdli.ucla.edu/P134010               |
|                                                              |
|  +-----------------------------------------------------+    |
|  |  Cite as:                                            |    |
|  |  Sharlach, T.M. CM 26, 037. NBC 00419.              |    |
|  |  Nies Babylonian Collection, Yale.                   |    |
|  |  CDLI P134010.                                       |    |
|  +-----------------------------------------------------+    |
+-------------------------------------------------------------+
```

**Pros:** Familiar to scholars, complete, machine-parsable sections, easy to scan for a specific field. Copyable citation block.
**Cons:** Verbose, lots of vertical space, many fields empty for sparse tablets. Static feel.

---

## Option 2: Compact Header + Metadata Chips (Dashboard Style)

Citation compressed into a dense header above the ATF viewer. Key facts as inline chips/badges. Secondary fields in a collapsible "More details" drawer.

```
+-------------------------------------------------------------+
|                                                              |
|  CM 26, 037                                                  |
|  NBC 00419 . Nies Babylonian Collection, Yale                |
|                                                              |
|  [Ur III] [Umma] [Admin] [Sumerian]                         |
|                                                              |
|  502 lines . obv + rev . 38x38x15 mm . Seal S000207         |
|                                                              |
|  Pub: Sharlach, T.M.  .  CDLI P134010  .  ORACC: epsd2     |
|                                                              |
|  > More details                                              |
|                                                              |
+-------------------------------------------------------------+
|                                                              |
|  @obverse                                                    |
|  1'. [...]-nita2# szu                                        |
|  2'. [...] AN                                                |
|  ...                                                         |
+-------------------------------------------------------------+

Expanded "More details":
+-------------------------------------------------------------+
|  v More details                                              |
|                                                              |
|  Material        clay tablet                                 |
|  Date            (regnal date)                               |
|  ATF source      cdlistaff                                   |
|  Translation     not available                               |
|  Preservation    --                                          |
|                                                              |
|  [ Copy citation ]                                           |
+-------------------------------------------------------------+
```

**Pros:** Minimal vertical footprint, chips scannable at a glance, progressive disclosure. Best when citation supports reading rather than being the primary focus.
**Cons:** Important fields may hide behind "More details." Chips can feel reductive for nuanced metadata.

---

## Option 3: Structured Sidebar (Reference Pane)

Citation data lives in a persistent sidebar column alongside the ATF viewer. Always visible while scrolling through text.

```
+----------------------+--------------------------------------+
|  TABLET              |  @obverse                            |
|                      |  1'. [...]-nita2# szu                |
|  CM 26, 037          |  2'. [...] AN                        |
|  P134010             |  3'. [x] masz2-gal                   |
|                      |  4'. [x] masz2-nita2                 |
|  ----------------    |  5'. ur-{d}lamma                     |
|  Museum              |  6'. 1(u) 3(disz) ud5 ...            |
|  NBC 00419           |  7'. a-ra2 1(disz)-kam               |
|  Nies Babylonian     |  8'. ...                             |
|  Coll., Yale         |  9'. ...                             |
|                      |  10'. ...                            |
|  ----------------    |  ...                                 |
|  Physical            |                                      |
|  tablet . clay       |  @reverse                            |
|  38 x 38 x 15 mm    |  1. ...                              |
|  obv . rev           |  2. ...                              |
|  Seal S000207        |  3. ...                              |
|                      |                                      |
|  ----------------    |                                      |
|  Context             |                                      |
|  Ur III              |                                      |
|  Umma (Tell Jokha)   |                                      |
|  Administrative      |                                      |
|  Sumerian            |                                      |
|                      |                                      |
|  ----------------    |                                      |
|  Publication         |                                      |
|  CM 26, 037          |                                      |
|  Sharlach, T.M.      |                                      |
|                      |                                      |
|  ----------------    |                                      |
|  Links               |                                      |
|  CDLI  .  ORACC      |                                      |
|  epsd2               |                                      |
|                      |                                      |
|  ----------------    |                                      |
|  Copy citation       |                                      |
+----------------------+--------------------------------------+
```

**Pros:** Citation always visible during reading. Natural for comparison. Mirrors physical museum experience.
**Cons:** Costs horizontal space permanently. On narrow screens, must collapse. Sidebar can feel disconnected from text.

---

## Comparison

| | 1: Bibliographic Card | 2: Compact Header + Chips | 3: Structured Sidebar |
|---|---|---|---|
| Layout | Full-width block above text | Compressed header above text | Persistent column beside text |
| Vertical cost | High (15-25 lines) | Low (5-8 lines) | None (parallel) |
| Horizontal cost | None | None | ~220px sidebar |
| Always visible | No (scrolls away) | Partially (header stays) | Yes |
| Sparse tablets | Many empty rows | Chips just absent -- clean | Short sidebar -- clean |
| Rich tablets | Complete display | Overflow into drawer | Complete display |
| Mobile | Good | Best | Poor (needs collapse) |
| Scholar workflow | Reference lookup | Reading-focused | Side-by-side study |
| Copy citation | Block at bottom | Button in drawer | Button at bottom |

## Recommendation

**Option 2 (Compact Header + Chips) as default** for the ATF viewer, where the text is the focus. **Option 1 (Bibliographic Card)** for a dedicated tablet detail/catalog page. Option 3 is elegant for desktop but breaks on mobile and duplicates the Knowledge Bar's sidebar real estate.
