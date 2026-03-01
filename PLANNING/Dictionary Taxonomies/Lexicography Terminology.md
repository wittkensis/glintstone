**Cuneiform Lexicography**

*Terminology, Concepts & Taxonomy for a Multi-Language Gloss Dictionary*

Covering Sumerian · Akkadian · Hittite · Elamite

**1. Core Terminology**

The following terms form the conceptual foundation for working with
cuneiform lexical data. Each term operates at a different level of
abstraction --- from physical tablet through linguistic reconstruction
to philosophical referent.

+--------------+-----------------------------------+------------------+
| **Term**     | **Definition**                    | **In             |
|              |                                   | Assyriology**    |
+==============+===================================+==================+
| **Sign**     | A specific cuneiform impression   | *Identified by   |
|              | on a tablet --- the physical mark | Borger number    |
| *p           | made by a stylus. Signs are the   | (e.g. DUMU =     |
| hilological* | raw unit of identification. A     | Borger 296). The |
|              | single sign can be read multiple  | entry point to   |
|              | ways depending on language and    | all analysis.*   |
|              | context.                          |                  |
+--------------+-----------------------------------+------------------+
| **Reading**  | The phonological realization of a | *Lives at the    |
|              | sign --- what you say when you    | transliteration  |
| *            | read it aloud. Logographic signs  | layer. Recorded  |
| philological | in Sumerian are read in lowercase | sign-by-sign     |
| /            | (dumu). The same sign used as a   | before           |
| tran         | Sumerogram in Akkadian is read in | normalization.*  |
| sliteration* | uppercase (DUMU), signaling a     |                  |
|              | cross-language borrowing.         |                  |
+--------------+-----------------------------------+------------------+
| **Lemma**    | The dictionary citation form ---  | *Used by CAD,    |
|              | the normalized headword a scholar | ePSD, ORACC. The |
| *            | writes in a lexicon entry. mārum, | primary          |
| philological | šak, dumu are lemmata. The lemma  | organizational   |
| /            | is a scholarly construct that     | unit of          |
| tr           | represents a word as a stable     | Assyriological   |
| anscription* | lexical unit, abstracting away    | dictionaries.*   |
|              | from individual attestations.     |                  |
+--------------+-----------------------------------+------------------+
| **Gloss**    | A short target-language (usually  | *Used throughout |
|              | English) translation label        | CAD and AHw.     |
| *le          | offered as a navigational         | Best understood  |
| xicographic* | approximation. \'King\', \'son\', | as a door into   |
|              | \'house\' are glosses. A gloss is | the entry, not   |
|              | honest about being provisional    | the entry        |
|              | --- it claims to orient the       | itself.*         |
|              | reader, not to fully capture      |                  |
|              | meaning. The term originates from |                  |
|              | the medieval practice of writing  |                  |
|              | explanatory words above or beside |                  |
|              | difficult text.                   |                  |
+--------------+-----------------------------------+------------------+
| **Sense**    | The conceptual content of a word  | *Not standard    |
|              | as it existed in a speaker\'s     | Assyriological   |
| *p           | mind --- the full internal        | terminology.     |
| hilosophical | meaning-package including         | Useful for       |
| / semantic*  | connotations, cultural weight,    | distinguishing   |
|              | and associative network. Sense is | what we know     |
|              | only partially recoverable for    | from what we\'ve |
|              | dead languages. It is what a      | lost. The Lemma  |
|              | native Babylonian speaker carried | box in a diagram |
|              | in their head, not what a scholar | approximates     |
|              | reconstructs.                     | sense without    |
|              |                                   | fully capturing  |
|              |                                   | it.*             |
+--------------+-----------------------------------+------------------+
| *            | The actual thing in the world a   | *Closer to what  |
| *Reference** | word points at in a specific use. | ORACC calls      |
|              | \'Gilgamesh\' has a reference (a  | \'the instance\' |
| *p           | legendary king of Uruk). šarrum   | --- the word as  |
| hilosophical | in a specific inscription has a   | used in a        |
| / semantic*  | reference (a particular ruler).   | specific text,   |
|              | Reference is contextual and       | pointing at a    |
|              | usage-specific, not a property of | specific         |
|              | the dictionary entry itself.      | real-world       |
|              |                                   | entity or        |
|              |                                   | concept.*        |
+--------------+-----------------------------------+------------------+
| **Meaning**  | The everyday term that loosely    | *The most        |
|              | covers all of the above ---       | commonly used    |
| *general /   | sense, reference, gloss, and      | term in          |
| umbrella*    | contextual interpretation         | Assyriology.     |
|              | together. Most useful in informal | Fine for general |
|              | discussion. Breaks down under     | discourse;       |
|              | pressure because it conflates     | imprecise for    |
|              | distinct layers that matter for   | data modeling.*  |
|              | database design.                  |                  |
+--------------+-----------------------------------+------------------+
| **Semantic   | The full spread of meanings a     | *Used in         |
| Range**      | single sign or lemma can carry    | Assyriological   |
|              | across attested uses. DINGIR/AN   | literature.      |
| *linguistic* | has a semantic range that         | Closely related  |
|              | includes \'sky\', \'heaven\',     | to the           |
|              | \'god\', \'the deity AN\', and a  | philological     |
|              | silent determinative function.    | concept of       |
|              | Semantic range is what a          | polysemy.*       |
|              | dictionary entry maps.            |                  |
+--------------+-----------------------------------+------------------+
| **Zero       | The absence of a \'to be\' verb   | *Relevant for    |
| Copula**     | in nominal sentences. Akkadian,   | parsing nominal  |
|              | Hittite, and Elamite all form     | clauses on       |
| *            | grammatically complete sentences  | tablets --- an   |
| grammatical* | like \'house big\' without any    | apparent         |
|              | equivalent of the English \'is\'. | \'missing verb\' |
|              | The copula is conceptually        | is often not     |
|              | present but has no written form.  | missing at all.* |
+--------------+-----------------------------------+------------------+
| **           | The interpretive step between a   | *Visualized as   |
| Phonological | sign\'s reading and its lemma --- | the dashed arrow |
| Inference**  | reconstructing what a word        | in the           |
|              | actually sounded like from the    | tablet→si        |
| *p           | writing system\'s imperfect       | gn→reading→lemma |
| hilological* | phonological representation. The  | diagram. Most    |
|              | longer and more uncertain this    | tenuous for      |
|              | inference, the more the lemma is  | Hittite          |
|              | a scholarly hypothesis.           | Sumerograms.*    |
+--------------+-----------------------------------+------------------+

**2. The Critical Three-Way Distinction**

The most important conceptual distinction for dictionary design is the
difference between **gloss**, **sense**, and **reference**. They are
easy to conflate but serve different functions.

**Gloss vs. Sense**

A gloss is what a lexicographer **writes**. A sense is what a speaker
**knew**. For living languages the gap is small enough to ignore. For
dead languages reconstructed from clay tablets, the gap is where all the
interpretive uncertainty lives. When the CAD writes šarrum = \'king\',
that gloss captures perhaps sixty percent of the sense --- the
referential category, but not the divine connotations, the relationship
to the gods, the distinction from rubûm or bēlum that a native speaker
felt immediately.

**Gloss vs. Reference**

A gloss lives in the **dictionary entry**. A reference lives in a
**specific text**. \'King\' is a gloss for šarrum. But in the prologue
to the Code of Hammurabi, šarrum refers to Hammurabi specifically ---
that is the reference. The same lemma with the same gloss can have
thousands of different references across the corpus. This is a database
layer distinction: gloss belongs to the lexical record; reference
belongs to the attestation record.

**Sense vs. Reference**

Frege\'s classic example: \'the morning star\' and \'the evening star\'
share a **reference** (Venus) but have different **senses** (different
conceptual pathways to the same object). In cuneiform terms: DUMU in
Sumerian, Akkadian, Hittite, and Elamite contexts all share a reference
(\'son\') but carry genuinely different senses --- different conceptual
packages embedded in different linguistic and cultural systems. The
Hittite case is the most extreme: the reference is recoverable but the
sense remains debated, meaning scholars can agree on what the sign
points at without being able to reconstruct the native speaker\'s
concept.

**3. Proposed Taxonomy for a Multi-Language Gloss Dictionary**

The following taxonomy organizes a massive cross-language cuneiform
gloss collection into distinct layers. Each layer corresponds to a
specific type of information and should be modeled as a distinct record
type or field group in a database --- not collapsed into a single entry.

**Layer 0: Sign**

The physical and graphical unit. Language-independent. Every lexical
chain begins here.

  -------------------------------------------------------------------------
  **Layer**   **Field**     **Description**             **Example**
  ----------- ------------- --------------------------- -------------------
  **Sign**    Sign form     Unicode codepoint(s) and    *𒌉 U+12049*
                            cuneiform character

  **Sign**    Borger number Standard sign list          *Borger 296*
                            identifier

  **Sign**    Sign name     Conventional Assyriological *DUMU*
                            label

  **Sign**    Sign type     Logograph, syllabogram,     *Logograph (also
                            determinative, or hybrid    syllabogram in some
                                                        uses)*

  **Sign**    Period        Chronological range of      *Ur III through
              attested      attestation                 Neo-Babylonian*
  -------------------------------------------------------------------------

**Layer 1: Reading**

The phonological realization --- language-specific and
context-dependent. A single sign can have multiple readings.

  -------------------------------------------------------------------------------
  **Layer**     **Field**         **Description**             **Example**
  ------------- ----------------- --------------------------- -------------------
  **Reading**   Transliteration   Sign-by-sign phonological   *ma-ru-um*
                                  representation

  **Reading**   Language          Which language this reading *Akkadian*
                                  belongs to

  **Reading**   Case convention   Lowercase = native          *DUMU (Akkadian
                                  Sumerian; UPPERCASE =       use)*
                                  Sumerogram in another
                                  language

  **Reading**   Phonetic          Syllabic additions that     *DUMU-šu → māršu*
                complements       clarify the reading of a
                                  logogram

  **Reading**   Inference         How directly the reading    *High (syllabic) /
                confidence        maps to the lemma           Low (Sumerogram in
                                                              Hittite)*
  -------------------------------------------------------------------------------

**Layer 2: Lemma**

The normalized dictionary headword. The primary organizational unit.
Language-specific.

  -------------------------------------------------------------------------
  **Layer**   **Field**     **Description**             **Example**
  ----------- ------------- --------------------------- -------------------
  **Lemma**   Citation form Normalized headword in      *mārum*
                            scholarly transcription

  **Lemma**   Language      Sumerian, Akkadian,         *Akkadian*
                            Hittite, or Elamite

  **Lemma**   Dialect /     Old Babylonian,             *Old Babylonian*
              period        Neo-Assyrian, Middle
                            Elamite, etc.

  **Lemma**   Part of       Noun, verb, adjective,      *Noun, masculine*
              speech        particle, etc.

  **Lemma**   Stem /        For verbs: G, D, Š, N stems *G-stem (basic)*
              derivation    and variants

  **Lemma**   Certainty     Is this lemma established,  *\[debated\] for
              flag          debated, or reconstructed?  Hittite DUMU*
  -------------------------------------------------------------------------

**Layer 3: Gloss**

The target-language translation label. Navigational and provisional. Can
be one-to-many: a single lemma may require multiple glosses to cover its
semantic range.

  -------------------------------------------------------------------------
  **Layer**   **Field**     **Description**             **Example**
  ----------- ------------- --------------------------- -------------------
  **Gloss**   Primary gloss The main English            *\"king\"*
                            translation handle

  **Gloss**   Secondary     Additional glosses covering *\"ruler\",
              glosses       extended semantic range     \"lord\" (for
                                                        specific
                                                        registers)*

  **Gloss**   Register      Administrative, legal,      *Royal inscription
                            literary, religious, royal  use*

  **Gloss**   Period        Gloss may differ by period  *\"chieftain\" in
              qualifier                                 early periods*

  **Gloss**   Source        Which dictionary or corpus  *CAD Š/2 p.78*
                            the gloss comes from

  **Gloss**   Gloss type    Common noun, proper noun,   *Common noun*
                            divine name, technical term
  -------------------------------------------------------------------------

**Layer 4: Attestation**

The specific textual instance --- where the lemma actually appears, what
reference it carries in that context, and what the surrounding sentence
structure tells us about its use.

  -------------------------------------------------------------------------------
  **Layer**         **Field**     **Description**             **Example**
  ----------------- ------------- --------------------------- -------------------
  **Attestation**   Text ID       CDLI/ORACC identifier for   *P123456*
                                  the source tablet

  **Attestation**   Line          Tablet, column, line        *obv. ii 14*
                    reference

  **Attestation**   Context gloss What this specific instance *Hammurabi
                                  refers to in this text      (specific ruler)*

  **Attestation**   Writing form  How it actually appears on  *LUGAL-ri (mixed)*
                                  the tablet (syllabic,
                                  logographic, mixed)

  **Attestation**   Sentence type Verbal, nominal,            *Nominal sentence,
                                  imperative, subordinate     zero copula*

  **Attestation**   Notes         Any disambiguation,         *Phonetic
                                  uncertainty, or editorial   complement confirms
                                  comment                     case*
  -------------------------------------------------------------------------------

**4. Key Design Principles**

**Glosses belong to lexical entries; references belong to attestations**

Do not store \'Gilgamesh\' and \'king\' in the same field type. A proper
noun like Gilgamesh is a reference, not a gloss. It belongs at Layer 4
(attestation), not Layer 3 (gloss). Common nouns like \'king\' are
glosses that live at Layer 3 and apply across all attestations of that
lemma.

**One lemma, many glosses --- model this as a one-to-many relationship**

The semantic range of a Sumerian or Akkadian word routinely spans what
English requires multiple words to express. dumu means son, child,
member of a class, and professional dependent depending on register.
Each distinct sense cluster deserves its own gloss record linked to the
lemma, with period and register qualifiers, not a single concatenated
string like \'son/child/member\'.

**Flag inference confidence explicitly**

The path from sign to lemma is not equally reliable across languages.
Akkadian syllabic spellings carry high confidence. Hittite Sumerograms
without phonetic complements carry low confidence. The \[debated\] flag
at the lemma layer is not just a note --- it is a data quality signal
that affects how downstream glosses should be weighted and displayed.

**Treat the gloss as a door, not a definition**

The gloss column is navigation infrastructure. A user searching for
\'king\' needs to find šarrum, LUGAL, sunki-\*, and ḫaššuš. The full
account of what any of those words meant to their native speakers lives
in the definition, usage examples, and attestation notes --- not in the
gloss string itself. Design the interface accordingly: gloss for
finding, attestation for understanding.

**Preserve the sign as language-neutral anchor**

The same physical sign --- 𒌉, 𒈗 --- appears across all four languages
with different lemmata and different glosses. The sign record is the one
genuinely language-neutral layer and should be modeled as such, with
language-specific reading and lemma records hanging off it rather than
duplicating the sign data per language.

*Sumerian · Akkadian · Hittite · Elamite*
