# Source Data Samples

Most complete records from each source database. Use these to understand field coverage, data quality, and integration points.

---

## CDLI Catalog (CSV)

**Most complete record**: id=111372, 39 of 64 fields populated.
Old Babylonian legal tablet from Nippur (inheritance contract).

```
acquisition_history:   Nippur, Babylonian Expedition
ark_number:            21198/zz001txkfp
atf_source:            Goddeeris, Anne; Firth, Richard
atf_up:                20171004 firth
author:                Chiera, Edward
cdli_comments:         Goddeeris: cf. tablets TMH 019a & 019b and envelope frag. TMH 10, 019c
collection:            University of Pennsylvania Museum of Archaeology and Anthropology, Philadelphia, Pennsylvania, USA
condition_description: u. part
date_entered:          4/25/2005
date_of_origin:        Samsu-iluna.05.04.00
date_updated:          2018-10-21
dates_referenced:      Samsu-iluna.05.04.00
db_source:             20050425 fitzgerald_upenn
designation:           PBS 08/2, 154
genre:                 Legal
height:                ?
id:                    111372
id_text:               262170
join_information:      P262170 lead, single entry
language:              Akkadian
material:              clay
museum_no:             CBS 07134
object_preservation:   fragment
object_type:           tablet & envelope
period:                Old Babylonian (ca. 1900-1600 BC)
photo_up:              600ppi 20160630
primary_publication:   PBS 08/2, 154
provenience:           Nippur (mod. Nuffar)
publication_date:      1922
publication_history:   Goddeeris, TMH 10, 019d
seal_id:               Sx
seal_information:      bur-gul seal
subgenre:              inheritance
subgenre_remarks:      Contract; Description of a house; Seal impressions; (Obv)6x(Rev)3 lines
thickness:             ?
translation_source:    no translation
width:                 ?
object_remarks:        envelope
```

**File**: `data/sources/CDLI/metadata/cdli_cat.csv` (353,283 rows, 64 columns)

---

## CDLI ATF (Transliteration + Translation)

**P431083** — Eannatum inscription (Sumerian royal inscription, Early Dynastic IIIb).
One of the most complete ATF records: line-by-line transliteration with parallel English translation and composite (Q-number) alignment.

```
&P431083 = RIME 1.09.03.08
#atf: lang sux
@object composite text
@surface a
1. {d}nin-gir2-su
#tr.en: For Ningirsu,
>>Q001062 001
2. e2-an-na-tum2
#tr.en: Eannatum,
>>Q001062 002
3. ensi2
#tr.en: the ruler
>>Q001062 003
4. lagasz{ki}-ke4
#tr.en: of Lagaš,
>>Q001062 004
5. mu pa3-da
#tr.en: nominated
>>Q001062 005
6. {d}en-lil2-ke4
#tr.en: by Enlil,
>>Q001062 006
7. a2 szum2-ma
#tr.en: given strength
>>Q001062 007
8. {d}nin-gir2-su2-ke4
#tr.en: by Ningirsu,
>>Q001062 008
9. sza3 pa3-da
#tr.en: chosen by the heart
>>Q001062 009
10. {d}nansze-ke4
#tr.en: of Nanše,
>>Q001062 010
11. ga zi gu7-a
#tr.en: fed rich milk
>>Q001062 011
12. {d}nin-hur-sag-ke4
#tr.en: by Ninḫursaga,
>>Q001062 012
13. mu du10 sa4-a
#tr.en: called a good name
>>Q001062 013
14. {d}inanna-ke4
#tr.en: by Inanna,
>>Q001062 014
15. dumu a-kur-gal
#tr.en: son of Akurgal,
>>Q001062 015
16. ensi2
#tr.en: the ruler
>>Q001062 016
17. lagasz{ki}-ke4
#tr.en: of Lagaš,
>>Q001062 017
18. {d}nin-gir2-su-ra
#tr.en: for Ningirsu
>>Q001062 018
19. gir2-su{ki}
#tr.en: Girsu
>>Q001062 019
```

**Key ATF conventions**: `{d}` = divine determinative, `{ki}` = place determinative, `#tr.en:` = English translation, `>>Q` = composite alignment, `@surface` = physical surface marker.

**File**: `data/sources/CDLI/metadata/cdliatf_unblocked.atf` (135,200 texts, 3.5M lines)

---

## CDLI API (JSON)

**P000001** — Richly structured record with nested inscription, publications, collections, materials, languages, genres, and external resources.

```json
{
  "id": 1,
  "designation": "CDLI Lexical 000002, ex. 065",
  "excavation_no": "W 06435,a",
  "findspot_comments": "auf Hügeloberfläche in der Nähe des Südbaues",
  "findspot_square": "M XVIII,?",
  "museum_no": "VAT 01533",
  "thickness": "18.0",
  "height": "31.0",
  "width": "61.0",
  "composites": [
    {
      "composite_no": "Q000002",
      "composite": {
        "designation": "CDLI Lexical 000002 (Archaic Lu2 A) composite"
      }
    }
  ],
  "inscription": {
    "atf": "&P000001 = CDLI Lexical 000002, ex. 065\n#atf: lang qpc\n@tablet\n@obverse\n@column 1\n$ beginning broken\n1'. 1(N01) , [...]\n>>Q000002 014\n..."
  },
  "publications": [
    {
      "exact_reference": "pl. 11, W 6435,a",
      "publication_type": "history",
      "publication": {
        "designation": "ATU 3",
        "bibtexkey": "Englund1993ATU3",
        "year": "1993",
        "publisher": "Gebr. Mann",
        "title": "Die lexikalischen Listen der archaischen Texte aus Uruk"
      }
    }
  ],
  "materials": [
    { "material": { "material": "clay" } }
  ],
  "languages": [
    { "language": { "language": "undetermined", "inline_code": "qpc" } }
  ],
  "genres": [
    { "comments": "Archaic Lu2 A (witness)", "genre": { "genre": "Lexical" } }
  ],
  "external_resources": [
    {
      "external_resource_key": "P000001",
      "external_resource": {
        "external_resource": "Digital Corpus of Cuneiform Lexical Texts",
        "base_url": "http://oracc.org/dcclt/",
        "abbrev": "DCCLT"
      }
    }
  ],
  "collections": [
    {
      "collection": {
        "collection": "Vorderasiatisches Museum, Berlin, Germany",
        "country_iso": "DEU",
        "location_longitude_wgs1984": 13.3967,
        "location_latitude_wgs1984": 52.5211
      }
    }
  ],
  "artifact_type": { "artifact_type": "tablet" },
  "period": { "period": "Uruk III (ca. 3200-3000 BC)" },
  "provenience": { "provenience": "Uruk (mod. Warka)" }
}
```

**Unique vs CSV**: publications (structured), collections (with museum geolocation), external_resources (cross-database links), materials/languages/genres as structured arrays.

**File**: `data/sources/CDLI/catalogue/batch-00000.json` (100 records, sample only)

---

## ORACC Corpus — ETCSRI (Sumerian Royal Inscriptions)

**Richest lemmatization in the dataset**: 9/10 annotation fields. Sumerian text with full morphological analysis.

### Simple token: ud[sun]N

```json
{
  "node": "l",
  "id": "Q000377.l022cf",
  "ref": "Q000377.1.1",
  "inst": "ud[sun]",
  "sig": "@etcsri%sux:ud=ud[sun//sun]N'N$ud/ud#N1=ud##N1=STEM",
  "f": {
    "lang": "sux",
    "form": "ud",
    "delim": "",
    "gdl": [
      {
        "v": "an",
        "oid": "o0000565",
        "gdl_sign": "UD",
        "utf8": "𒌓",
        "id": "Q000377.1.1.0"
      }
    ],
    "cf": "ud",
    "gw": "sun",
    "sense": "sun",
    "norm": "ud",
    "pos": "N",
    "epos": "N",
    "base": "ud",
    "morph": "N1=ud",
    "morph2": "N1=STEM"
  }
}
```

### Multi-sign verb with morphology: tar-re-da = tar[cut]V/t

```json
{
  "node": "l",
  "id": "Q000377.l022d3",
  "ref": "Q000377.1.5",
  "inst": "tar[cut]\\l1",
  "sig": "@etcsri%sux:tar-re-da\\l1=tar[cut//cut]V/t'V/t$tar.ed.'a/tar#NV2=tar.NV3=ed.N5='a##NV2=STEM.NV3=PF.N5=L1",
  "f": {
    "lang": "sux",
    "form": "tar-re-da",
    "gdl": [
      {
        "v": "tar",
        "oid": "o0000548",
        "gdl_sign": "TAR",
        "utf8": "𒋻",
        "id": "Q000377.1.5.0",
        "delim": "-"
      },
      {
        "v": "re",
        "oid": "o0000514",
        "gdl_sign": "RI",
        "utf8": "𒊑",
        "id": "Q000377.1.5.1",
        "break": "missing",
        "delim": "-"
      },
      {
        "v": "da",
        "oid": "o0000132",
        "gdl_sign": "DA",
        "utf8": "𒁕",
        "id": "Q000377.1.5.2"
      }
    ],
    "cf": "tar",
    "gw": "cut",
    "sense": "cut",
    "norm": "tar.ed.'a",
    "pos": "V/t",
    "epos": "V/t",
    "base": "tar",
    "morph": "NV2=tar.NV3=ed.N5='a",
    "morph2": "NV2=STEM.NV3=PF.N5=L1"
  }
}
```

**Signature format**: `@project%lang:form=cf[gw//sense]POS'ePOS$norm/base#morph##morph2`

**Morphology slots** (Sumerian): NV2=STEM (verb stem), NV3=PF (perfective suffix), N5=L1 (locative 1 case marker). The `morph` field gives the actual forms; `morph2` gives the abstract slot labels.

**File**: `data/sources/ORACC/etcsri/json/etcsri/corpusjson/Q000377.json` (4,740 lemmas, 1,456 texts total)

---

## ORACC Corpus — RINAP (Akkadian Royal Inscriptions)

**Akkadian logographic writing**: Shows how Sumerian signs (E₂.GAL) are used as logograms for Akkadian words (ēkallu).

```json
{
  "node": "l",
  "frag": "E₂.GAL",
  "id": "Q003460.l017ce",
  "ref": "Q003460.2.1",
  "inst": "ēkal[palace]N",
  "sig": "@rinap/rinap1%akk:E₂.GAL=ēkallu[palace//palace]N'N$ēkal",
  "f": {
    "lang": "akk",
    "form": "E₂.GAL",
    "delim": "",
    "gdl": [
      {
        "gg": "logo",
        "gdl_type": "logo",
        "group": [
          {
            "s": "E₂",
            "oid": "o0000180",
            "gdl_sign": "E₂",
            "utf8": "𒂍",
            "role": "logo",
            "logolang": "sux",
            "delim": "."
          },
          {
            "s": "GAL",
            "oid": "o0000194",
            "gdl_sign": "GAL",
            "utf8": "𒃲",
            "role": "logo",
            "logolang": "sux"
          }
        ]
      }
    ],
    "cf": "ēkallu",
    "gw": "palace",
    "sense": "palace",
    "norm": "ēkal",
    "pos": "N",
    "epos": "N"
  }
}
```

**Key difference from Sumerian**: `gdl_type: "logo"` marks logographic usage, `logolang: "sux"` shows Sumerian signs reading Akkadian words. No `morph`/`base` fields — RINAP doesn't include morphological analysis (only ETCSRI does among current data).

**File**: `data/sources/ORACC/rinap/json/rinap/rinap1/corpusjson/Q003460.json` (1,378 lemmas, 48 texts)

---

## ORACC Corpus — DCCLT (Lexical Lists)

**Partial lemmatization**: Lexical list texts have GDL sign data but often lack cf/gw/pos (unlemmatized).

```json
{
  "node": "l",
  "frag": "an",
  "id": "P282465.l2ea14",
  "ref": "P282465.4.1",
  "inst": "%sux:an=",
  "f": {
    "lang": "sux",
    "form": "an",
    "gdl": [
      {
        "v": "an",
        "oid": "o0000099",
        "gdl_sign": "AN",
        "utf8": "𒀭",
        "key": "o0000099..an",
        "id": "P282465.4.1.0"
      }
    ]
  }
}
```

Note: `inst: "%sux:an="` — the empty string after `=` means no lemmatization. Compare to ETCSRI where `inst: "ud[sun]"` includes the lemma.

**CDL tree structure** (container hierarchy):

```
d surface  →  { "node": "d", "subtype": "obverse", "type": "surface", "label": "o" }
d column   →  { "node": "d", "subtype": "column 1o", "type": "column", "n": "1" }
c sentence →  { "node": "c", "type": "sentence", "label": "o i 1" }
d line     →  { "node": "d", "type": "line-start", "n": "1", "label": "o i 1" }
d cell     →  { "node": "d", "type": "cell-start" }
l lemma    →  { "node": "l", "f": { ... } }
d cell-end →  { "node": "d", "type": "cell-end" }
```

Node types: `c` = container (text, discourse, sentence), `d` = delimiter (surface, column, line, cell), `l` = lemma (token).

**File**: `data/sources/ORACC/dcclt/json/dcclt/corpusjson/` (4,980 texts)

---

## ORACC Catalogue (RINAP)

**Most complete catalogue entry**: Q006557, Sargon II 076 — 36 fields. Neo-Assyrian royal inscription on prismatic cylinder.

```json
{
  "project": "rinap",
  "cdli_id": "P238097; X876431; P251597; X876432; X876433",
  "collection": "British Museum, London; Iraq Museum, Baghdad; Schøyen Collection, Oslo",
  "designation": "Sargon II 076",
  "dynastic_seat": "Assyria",
  "exemplars": "BM — (K 01660); IM — (ND 03411); MS 2368; Moussaieff —; IM 08567 (35)",
  "genre": "Royal Inscription",
  "id_composite": "Q006557",
  "language": "Akkadian",
  "material": "clay",
  "object_type": "prismatic cylinder",
  "period": "Neo-Assyrian",
  "provenience": "Nimrud (Kalhu)",
  "pleiades_id": "894019",
  "pleiades_coord": "[43.3275,36.099167]",
  "ruler": "Sargon II",
  "script": "Neo-Assyrian",
  "script_type": "Cuneiform",
  "supergenre": "LIT",
  "trans": "en",
  "ancient_date": "12 - [...] - [(...)]",
  "century": "8th century",
  "exemplar_number": "5",
  "findspots": "Nineveh; Nimrud; Tell Baradan",
  "has_date": "yes, but date partially preserved",
  "regnal_dates": "721-705",
  "subproject": "rinap2"
}
```

**Fields unique to ORACC Catalogue** (not in CDLI CSV): `pleiades_id`, `pleiades_coord`, `ruler`, `dynastic_seat`, `supergenre`, `script`, `exemplar_number`, `regnal_dates`, `ancient_date`.

**File**: `data/sources/ORACC/rinap/json/rinap/catalogue.json`

---

## ORACC Glossary (dcclt/sux)

**Richest entry**: gub[stand]V/i — 176 attestations, 30+ attested forms, compound verbs.

```json
{
  "headword": "gub[stand]V/i",
  "id": "o0028628",
  "icount": "176",
  "ipct": "100",
  "cf": "gub",
  "gw": "stand",
  "pos": "V/i",
  "see-compounds": [
    { "xcpd": "ŋiri gub[step]V/t" },
    { "xcpd": "kaša guba[function]N" },
    { "xcpd": "ud guba[duration of a warranty]N" }
  ],
  "forms": [
    { "n": "al-gub", "icount": "2" },
    { "n": "ba-an-ne-en-gub-be₂-en", "icount": "1" },
    { "n": "ba-e-da-gub-be₂-en-ze₂-en", "icount": "1" },
    { "n": "gub", "icount": "34", "ipct": "19" },
    { "n": "gub-ba", "icount": "66", "ipct": "38" },
    { "n": "gub-ba-am₃", "icount": "3" },
    { "n": "gub-bu", "icount": "1" },
    { "n": "im-mi-in-gub", "icount": "1" },
    { "n": "mu-na-gub", "icount": "1" },
    { "n": "mu-un-gub", "icount": "2" }
  ]
}
```

**Key fields**: `cf` (citation form), `gw` (guide word / English gloss), `pos` (part of speech), `icount` (attestation count), `ipct` (percentage), `forms[]` (all attested spellings with counts), `see-compounds` (compound verbs using this root).

**File**: `data/sources/ORACC/dcclt/json/dcclt/gloss-sux.json` (5,271 entries, 61 MB)

---

## ORACC GeoJSON (SAAO)

**SAA 01 175** — Neo-Assyrian letter with coordinates, archive location, and ancient author/recipient metadata.

```json
{
  "type": "Feature",
  "properties": {
    "designation": "SAA 01 175",
    "ancient_author": "Adda-hati",
    "ancient_recipient": "the king",
    "archive": "006 - Northwest Palace, Room ZT 4",
    "cdli_excavation_no": "ND 02381",
    "cdli_id": "P224395",
    "cdli_museum_no": "IM 064018",
    "ch_name": "Letters from Western Provinces",
    "collection": "National Museum of Iraq, Baghdad, Iraq",
    "genre": "Royal Inscription",
    "language": "Akkadian",
    "period": "Neo-Assyrian",
    "provenience": "Nimrud (Kalhu)",
    "pleiades_id": "894019"
  },
  "geometry": {
    "type": "Point",
    "coordinates": [43.3275, 36.099167]
  }
}
```

**Fields unique to GeoJSON**: `geometry.coordinates` (lon, lat), `ancient_author`, `ancient_recipient`, `archive` (findspot within site), `ch_name`/`ch_no` (chapter in SAA publication).

**File**: `data/sources/ORACC/saao/json/saao/cat.geojson` (5,054 features)

---

## OGSL Sign List

**ŠID** — Sign with 79 reading values (most in the sign list), GDL definition, Unicode mapping, and variant form.

```json
{
  "values": [
    "sandaₓ", "ag₃", "aŋ₃", "ak₃", "aka₃", "alal₂", "bisag₂",
    "dilib", "gir₁₃", "kid₄", "kiri₈", "lag", "lak", "laq",
    "nesag₂", "pa₈", "pisag₂", "sagga", "saŋ₅", "sanga", "sangu",
    "sid₂", "silag", "silaŋ", "šanga", "šed", "šid", "šit",
    "šita₅", "šitim₂", "šub₆", "šudum", "ubisag", "umbisag",
    "uttu₂", "zadra", "zadri", "zandar"
  ],
  "gdl": [
    { "s": "ŠID" }
  ],
  "uphase": "1",
  "uname": "CUNEIFORM SIGN SHID",
  "utf8": "𒋃",
  "hex": "x122C3",
  "LAK636": {
    "values": [ "silaₓ" ],
    "var": "~a",
    "varid": "o0002837.a",
    "ref": "o0000405",
    "gdl": [ { "s": "LAK636" } ],
    "utf8": "𒔌",
    "hex": "x1250C"
  }
}
```

**Key fields**: `values[]` (all possible readings — 79 for this sign), `gdl[]` (structural definition), `utf8`/`hex`/`uname` (Unicode mapping), `uphase` (Unicode phase). Variant `LAK636` is an archaic form with its own readings and Unicode codepoint.

**File**: `data/sources/ORACC/ogsl/json/ogsl/ogsl-sl.json` (3,367 signs, ~15,000 values)

---

## CompVis Annotations

### Bounding box annotations

```csv
segm_idx,tablet_CDLI,view_desc,collection,mzl_label,train_label,bbox,relative_bbox
2061,P334894,Obv,saa05,839,11,"[805, 1979, 871, 2055]","[165, 60, 231, 136]"
2061,P334894,Obv,saa05,110,4,"[860, 1988, 981, 2049]","[220, 69, 341, 130]"
```

- `tablet_CDLI`: P-number (join key to CDLI artifacts)
- `view_desc`: surface (Obv/Rev/Lo.E./Up.E./Le.E./Ri.E.)
- `mzl_label`: Borger MZL integer (**needs concordance to OGSL**)
- `train_label`: ML class integer
- `bbox`: absolute pixel coordinates [x1, y1, x2, y2]
- `relative_bbox`: coordinates relative to segment crop

### Transliteration with reading order and damage status

```csv
segm_idx,tablet_CDLI,view_desc,rec_idx,line_idx,pos_idx,train_label,mzl_label,status
2,VAT11100Rs,Rev,0,0,0,11,839,2
2,VAT11100Rs,Rev,1,0,1,4,110,2
2,VAT11100Rs,Rev,7,2,1,5,248,1
```

- `line_idx` + `pos_idx`: reading order within text
- `status`: 0=background, 1=intact, 2=broken/uncertain

**Files**: `data/sources/compvis-annotations/annotations/` (8,109 bbox annotations, 81 tablets, all Neo-Assyrian SAA corpus)

---

## eBL Sign Mappings

**ebl.txt** — Concordance: eBL sign names to ABZ numbers and Unicode characters.

```
UnclearSign NoABZ0 None
A           ABZ579 𒀀
AB          ABZ128 𒀊
AB@g        ABZ195 𒀕
AB₂         ABZ420 𒀖
AB₂@t       NoABZ7 None
AD          ABZ145 𒀜
AK          ABZ97  𒀝
AL          ABZ298 𒀠
ALAN        ABZ358 𒀩
AMAR        ABZ437 𒀫
AN          ABZ13  𒀭
ANŠE        ABZ208 𒀲
APIN        ABZ56  𒀳
```

Format: `eBL_name  ABZ_number  unicode_char` (space separated).
`NoABZ` prefix = no ABZ number exists. `None` = no Unicode mapped.
This is the **only partial concordance** between ABZ numbering and Unicode — critical for future sign concordance table.

**File**: `data/sources/ebl-annotations/cuneiform_ocr_data/sign_mappings/ebl.txt` (2,496 lines, 173 sign classes)

---

## ePSD2 Reference

### Unicode Cuneiform Signs

```json
{
  "totalSigns": 1234,
  "ranges": [
    { "name": "Sumero-Akkadian Cuneiform", "start": "U+12000", "end": "U+123FF" },
    { "name": "Cuneiform Numbers and Punctuation", "start": "U+12400", "end": "U+1247F" },
    { "name": "Early Dynastic Cuneiform", "start": "U+12480", "end": "U+1254F" }
  ],
  "signs": [
    { "codePoint": "U+12000", "decimal": 73728, "character": "𒀀", "name": "CUNEIFORM SIGN A" },
    { "codePoint": "U+12001", "decimal": 73729, "character": "𒀁", "name": "CUNEIFORM SIGN A TIMES A" },
    { "codePoint": "U+12002", "decimal": 73730, "character": "𒀂", "name": "CUNEIFORM SIGN A TIMES BAD" }
  ]
}
```

**File**: `data/sources/ePSD2/unicode/cuneiform-signs.json` (1,234 signs across 3 Unicode ranges)

### CAD Index (Chicago Assyrian Dictionary)

```json
{
  "title": "The Assyrian Dictionary of the Oriental Institute of the University of Chicago",
  "abbreviation": "CAD",
  "volumes": [
    { "letter": "A", "part": 1, "abbrev": "A",
      "isacUrl": "https://isac.uchicago.edu/research/publications/chicago-assyrian-dictionary",
      "archiveUrl": "https://archive.org/details/Assyrian_cad" }
  ]
}
```

23 volumes (A through Z, some split). PDFs freely available at archive.org.

**File**: `data/sources/ePSD2/cad/cad-index.json`

---

## Corpus File Inventory

| Project | Path | Texts | Largest file | Lemmatization depth |
|---------|------|-------|--------------|---------------------|
| dcclt | `ORACC/dcclt/json/dcclt/corpusjson/` | 4,980 | P507554 (11 MB) | Partial: GDL only, no cf/gw/pos |
| etcsri | `ORACC/etcsri/json/etcsri/corpusjson/` | 1,456 | Q000377 (11 MB) | Full: cf/gw/pos/morph/base/norm |
| blms | `ORACC/blms/json/blms/corpusjson/` | 229 | P414363 (4 MB) | Full: cf/gw/pos/norm |
| hbtin | `ORACC/hbtin/json/hbtin/corpusjson/` | 487 | P342492 (3 MB) | Full: cf/gw/pos/norm |
| dccmt | `ORACC/dccmt/json/dccmt/corpusjson/` | 252 | P274707 (5 MB) | Full: cf/gw/pos/norm |
| rinap | `ORACC/rinap/json/rinap/rinap1/corpusjson/` | 48 | Q003460 (1 MB) | Full: cf/gw/pos/norm |

Note: saao, ribo, riao have catalogue + glossary data but no corpusjson files in the current extract.
