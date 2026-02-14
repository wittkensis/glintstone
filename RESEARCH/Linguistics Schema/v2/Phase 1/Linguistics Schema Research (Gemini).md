# **Cross-Linguistic Philology and Graphemic Architectures: A Comprehensive Analysis of Sumerian, Akkadian, Hittite, and Elamite Cuneiform Systems**

The structural history of the cuneiform script represents the first and perhaps most complex instance of globalized intellectual technology. From its inception in the late fourth millennium BCE to its eventual displacement by alphabetic systems during the Roman era, cuneiform served as the primary vehicle for the divergent linguistic families of the ancient Near East.1 This report provides an exhaustive technical analysis of the philological and logographic differences between Sumerian, Akkadian (specifically the Assyrian and Babylonian dialects), Hittite, and Elamite. It is designed to inform the creation of a unified data schema for a translation pipeline and to provide a foundational perspective for the development of a "Sign-Topology Folding" model—an "AlphaFold" for cuneiform signs.

## **1\. Typological and Syntactic Frameworks**

Understanding cuneiform requires distinguishing between the script and the languages it encodes. The script is logo-syllabic, meaning it utilizes signs to represent both entire words (logograms) and phonetic units (syllabograms).3 The four target languages represent three distinct linguistic families and two isolates, necessitating radically different syntactic approaches to the same script.

### **1.1. Sumerian: The Agglutinative Isolate**

Sumerian, the script's progenitor, is an agglutinative isolate with no known genetic relatives.3 Its grammar is characterized by the attachment of morphemes to a stable root, forming complex chains.6

#### **1.1.1. Sentence Structure and Verbal Morphology**

The Sumerian sentence typically follows a Subject-Object-Verb (SOV) order, though the ergative-absolutive alignment defines its core syntactic relations.7 In this system, the subject of an intransitive verb and the direct object of a transitive verb are both in the "absolutive" case (often unmarked), while the subject of a transitive verb is in the "ergative" case (marked with the suffix *\-e*).8

The verbal chain is the most complex aspect of Sumerian. It consists of a root preceded by up to ten prefix slots and followed by several suffix slots. These slots encode information about person, number, aspect, mood, and dimensionality (directional and dimensional prefixes).5 For example, the ventive prefix indicates motion toward the speaker, a concept later borrowed and modified by Akkadian.5

#### **1.1.2. Nominal Class and Gender**

Sumerian distinguishes between "personal" (human and divine) and "impersonal" (animals and objects) noun classes rather than masculine/feminine genders.5 This distinction dictates the choice of plural markers: *\-ene* for the personal class and *\-hi-a* or *\-meš* (borrowed later) for the impersonal.1

### **1.2. Akkadian (Assyrian and Babylonian): The Inflecting Semitic**

Akkadian, the language of the Assyrians and Babylonians, is an inflecting Semitic language. Unlike Sumerian, it is based on tri-consonantal roots (e.g., ![][image1] "to cut/decide") that undergo internal vowel changes (ablaut) to express grammatical categories.5

#### **1.2.1. Syntactic Shift and Word Order**

While most Semitic languages follow a Verb-Subject-Object (VSO) order (comparable to Classical Arabic), Akkadian adopted the SOV order from Sumerian.7 This is a prime example of "language area" (Sprachbund) effects, where long-term contact leads to shared structural features despite differing genetic origins.5

#### **1.2.2. Case and Verbal Systems**

Akkadian uses a three-case system: nominative (*\-u*), genitive (*\-i*), and accusative (*\-a*). Its verbal system is based on "stems" (G, D, Š, and N) that modify the root’s basic meaning (e.g., intensive, causative, passive).7 The relationship between these stems and the Sumerian verbal chain was codified by ancient scholars in bilingual paradigms, where they mapped Akkadian inflections to Sumerian prefixes.9

### **1.3. Hittite: The Indo-European Heterography**

Hittite is the oldest recorded Indo-European language. Its adaptation of cuneiform is characterized by "heterography"—the use of Sumerian and Akkadian words as signs for Hittite concepts.12

#### **1.3.1. Clause Structure and Enclitic Chains**

Hittite sentences are defined by the "Wackernagel's Position," where a string of enclitic particles (pronouns, reflexive markers, and local particles) attaches to the first word of the clause.13 The introductory particle *nu* often serves as the anchor for these chains.13

#### **1.3.2. Animacy and Alignment**

Hittite distinguishes between "common" (animate) and "neuter" (inanimate) genders.13 It follows a nominative-accusative alignment, though its use of "local particles" (e.g., *\-kan*, *\-ašta*) to modify verbal meaning mirrors the dimensional prefixes of Sumerian, albeit through a different morphological mechanism.13

### **1.4. Elamite: The Agglutinative Nominal System**

Elamite is an agglutinative isolate spoken in what is now southwestern Iran. Its primary distinction is its pervasive nominal class system.15

#### **1.4.1. Locutive, Allocutive, and Delocutive**

Elamite categorizes nouns based on their relationship to the speech act:

* **Locutive (1st person):** The speaker (marked with *\-k*).  
* **Allocutive (2nd person):** The addressee (marked with *\-t*).  
* **Delocutive (3rd person):** The person or thing spoken of (marked with *\-r* for animate singular, *\-p* for animate plural, and *\-me* for inanimate).15

#### **1.4.2. Suffixaufnahme and Apposition**

Elamite utilizes *Suffixaufnahme* (suffix doubling), where a genitive modifier or an adjective takes the class marker of its head noun.8 For instance, in the phrase *sunki-k GN-k* ("I, the king of GN"), the locutive marker *\-k* is applied to both the noun "king" and the city name because the speaker is the subject.15

### **Table 1: Fundamental Typological Comparison**

| Feature | Sumerian | Akkadian | Hittite | Elamite |
| :---- | :---- | :---- | :---- | :---- |
| **Language Family** | Isolate 3 | Semitic 5 | Indo-European 1 | Isolate 18 |
| **Morphology** | Agglutinative 6 | Inflecting 7 | Inflecting 13 | Agglutinative 17 |
| **Alignment** | Ergative-Absolutive 8 | Nominative-Accusative 7 | Nominative-Accusative 13 | Nominative-Accusative\* 8 |
| **Word Order** | SOV 7 | SOV 7 | SOV (Final Verb) 13 | SOV 17 |
| **Gender/Class** | Personal/Impersonal 8 | Masculine/Feminine 1 | Common/Neuter 13 | Animate/Inanimate 15 |

## **2\. Shared Graphemic and Lexical Elements**

The unity of cuneiform scholarship across these cultures was maintained through a shared signary and the preservation of Sumerian as a scholarly *lingua franca*.

### **2.1. Polyvalency of Shared Cuneiform Symbols**

The most significant challenge in cuneiform is polyvalency: a single sign having multiple phonetic values and logographic meanings.

#### **2.1.1. Case Study: The AN Sign (𒀭)**

Originally a pictograph of a star, the sign **AN** demonstrates the layered nature of cuneiform.

* **Sumerian:** Read as *an* (the god of heaven) or *dingir* (god).3  
* **Akkadian:** Read as *šamû* (heaven) or *ilu* (god). It also serves as the phonetic syllable *an*.19  
* **Hittite:** Used primarily as a determinative for deities (transliterated as ![][image2]).1  
* **Elamite:** Used as a determinative for gods, but with a simplified set of phonetic values in later periods.17

#### **2.1.2. Case Study: The KUR Sign (𒆳)**

* **Sumerian:** *kur* (mountain, underworld, foreign land).19  
* **Akkadian:** *šadû* (mountain) or *mātu* (land). It provides syllables *kur, mad, šad*.19  
* **Hittite:** Represents the Hittite word for "land/country" (*utnē*), often with phonetic complements to indicate case.12

### **Table 2: Polyvalent Values of Key Cuneiform Signs**

| Sign | Sumerian Logogram | Akkadian Phonetic | Hittite Function | Elamite Phonetic |
| :---- | :---- | :---- | :---- | :---- |
| **AN** (𒀭) | SKY / GOD 3 | *an* 19 | GOD (det.) 1 | *an* 20 |
| **UD** (𒌓) | SUN / DAY 3 | *ud, tam, tú, par, laḫ* 2 | DAY 14 | *ut* 20 |
| **DU** (𒁺) | GO / STAND 3 | *du, rá, gub* 21 | GO 14 | *du* 20 |
| **MI** (𒈪) | NIGHT / BLACK 11 | *mi, mé, g̃i6* 21 | DARK 12 | *mi* 20 |

### **2.2. Shared Lexemes and Loanwords**

Beyond the script, the languages share vocabulary through two primary channels: direct borrowing from Sumerian and the "Banana Language" substrate.

#### **2.2.1. Sumerian Loanwords in Akkadian and Hittite**

Technical, religious, and administrative terms were frequently borrowed. The Sumerian *lugal* ("king," literally "big man") became a standard logogram in all four languages, though each had its own spoken equivalent: Akkadian *šarru*, Hittite *haššuš*, and Elamite *sunki*.12

#### **2.2.2. The "Banana Language" Hypothesis**

Several non-Sumerian and non-Semitic names in early Mesopotamian records show a pattern of reduplicated final syllables (e.g., *Bunene, Zababa, Inana*). This substrate language is thought to have influenced both Sumerian and Elamite, suggesting a shared cultural layer in the fourth millennium BCE.18

## **3\. The Relationship Between Signs and Linguistic Codification**

The mapping of words to cuneiform symbols is not a simple 1:1 ratio. It is a dynamic system of logography, phonography, and semantic classification.

### **3.1. Logograms and Heterograms**

A logogram is a sign representing a word but not its pronunciation. In Hittite studies, these are often called "heterograms" because they involve a sign from Language A (Sumerian or Akkadian) being used to write a word in Language B (Hittite).12

* **Sumerograms:** Written in ALL CAPS (e.g., ![][image3]).1  
* **Akkadograms:** Written in *ITALIC ALL CAPS* (e.g., *ŠA* or *ANA*).12  
* **Phonetic Complements:** Small syllabic signs attached to logograms to indicate the grammatical ending of the target language. For example, ![][image4] in Hittite indicates the nominative singular animate *ha\\check{s}\\check{s}u\\check{s}*.14

### **3.2. Determinatives: Semantic Classifiers**

Determinatives are ancillary signs used to help the reader categorize the following or preceding word. They were not pronounced but are critical for data disambiguation.3

* **Deities:** ![][image2] (from *DINGIR*).1  
* **People:** ![][image5] (masculine) or ![][image6] (feminine).1  
* **Places:** ![][image7] (cities) or ![][image8] (lands).1  
* **Materials:** ![][image9] (wood), ![][image10] (copper), ![][image11] (stone).3

### **3.3. Ancient Sign Lists and Paradigms**

The relationship between these signs and languages was preserved by ancient scribes in standardized lists such as *Ea* and *Diri*.11 These lists provided a four-column mapping:

1. **Gloss:** Phonetic spelling of the Sumerian word (e.g., *ge-e* for 𒈪).  
2. **Sign Form:** The cuneiform character (𒈪).  
3. **Sign Name:** The official name of the sign (e.g., *gikkigu*).  
4. **Akkadian Translation:** The meaning in the target language (e.g., *mu\\check{s}u* "night").11

## **4\. Evolution of Languages and Script**

The history of cuneiform is a progression from pictographic concreteness to phonetic abstraction and, eventually, to extreme simplification.

### **4.1. Developmental Phases of the Script**

1. **Proto-Literate (c. 3100–3000 BCE):** Pictographic signs primarily for accounting.26  
2. **Archaic Sumerian (c. 3000–2500 BCE):** Signs begin to rotate 90 degrees and become abstract wedge-shaped marks.26  
3. **Sumero-Akkadian Synthesis (c. 2350–2000 BCE):** Full phoneticization via the rebus principle to accommodate Semitic Akkadian.2  
4. **Regional Diversification (c. 2000–1000 BCE):** Divergent "ductus" (handwriting styles) emerge. Assyrian script becomes more linear and simplified, while Hittite adopts an Old Babylonian variant.1  
5. **Achaemenid Elamite (c. 550–330 BCE):** The final stage of Elamite cuneiform, which reduced the signary to approximately 131 signs, with almost no polyphony or homophony.20

### **4.2. Language Evolution and Contact**

Sumerian died out as a spoken language around 2000 BCE but survived for two millennia as a language of religion and scholarship.6 Akkadian split into Assyrian (northern) and Babylonian (southern) dialects, eventually becoming the *lingua franca* of the entire Near East by the 14th century BCE.2 Elamite survived until the arrival of Alexander the Great, evolving from the complex Old Elamite to the streamlined Royal Achaemenid Elamite.17

### **Table 3: Chronological Signary Expansion and Reduction**

| Period | Typical Sign Count | Key Characteristic |
| :---- | :---- | :---- |
| **Uruk IV (Pictographic)** | \~1,500 1 | Purely logographic/accounting |
| **Ur III (Neo-Sumerian)** | \~600 1 | Balanced logo-syllabic system |
| **Neo-Assyrian** | \~570-800 20 | Standardized, complex polyphony |
| **Hittite (Hattusa)** | \~375 21 | High density of Sumerograms |
| **Achaemenid Elamite** | \~131 20 | Simplified, quasi-alphabetic |

## **5\. Cultural Contexts and Knowledge Preservation**

Cuneiform was not merely a writing system; it was the foundation of an entire educational and political infrastructure.

### **5.1. The Edubba and the Scribal Elite**

Education centered on the *edubba* ("House of Tablets"), where students spent 12 years mastering the script.31 The curriculum involved copying lexical lists and literary works like the *Epic of Gilgamesh*.27 In Babylon, Sumerian remained the only language permitted in some schools, creating a culture where scribes were a privileged elite, often holding more power than illiterate monarchs.27

### **5.2. Royal Libraries and Statecraft**

The Library of Ashurbanipal at Nineveh is the most significant archaeological source for our knowledge of cuneiform literature, containing over 30,000 fragments.27 Cuneiform was also the tool of international diplomacy, as seen in the Amarna Letters, where Pharaohs corresponded with Near Eastern kings in Babylonian cuneiform.2

### **5.3. Decipherment: The Trilingual Jackpot**

Our modern knowledge of these languages stems from trilingual inscriptions. The Bisitun Inscription, featuring Old Persian, Elamite, and Babylonian, provided the "Rosetta Stone" for cuneiform.1 The decipherment of Hittite was aided by the discovery of thousands of tablets at Boğazköy, which showed the language was Indo-European.12

## **6\. Challenges and the State of Understanding**

Despite three centuries of study, significant hurdles remain, particularly in the realm of isolates and fragmented data.

### **6.1. The Problem of Language Isolates**

Because Sumerian and Elamite have no known relatives, our understanding of their semantics and phonology is entirely dependent on bilingual texts and internal analysis.9 Linear Elamite and Proto-Elamite remain largely undeciphered, though recent breakthroughs by researchers like François Desset suggest that they may be purely phonetic systems.29

### **6.2. Fragmentation and Data Sparsity**

Most of the 500,000 excavated tablets are fragmented.36 Reconstructing the missing text requires profound familiarity with parallel passages and formulaic language.38 Furthermore, the lack of standardized tokenization for logo-syllabic scripts hinders the application of standard NLP techniques.37

## **7\. Architectural Requirements for a Translation Pipeline**

To design a schema that ties these languages together, one must move beyond character-level mapping to a multi-layered relational model.

### **7.1. Data Schema Components**

The schema should be based on the Open Richly Annotated Cuneiform Corpus (Oracc) and the Cuneiform Digital Library Initiative (CDLI) standards.39

#### **7.1.1. Physical Layer: The Artifact**

* **P-Number:** Unique identifier for each artifact.40  
* **Material and Condition:** Critical for image processing algorithms.37  
* **Metadata:** Provenience, period, and genre.40

#### **7.1.2. Graphemic Layer: The Sign**

* **Unicode Mapping:** Utilizing the U+12000 block.1  
* **GDL (Grapheme Description Language):** Formally defining complex signs and ligatures.42  
* **Wedge Topology:** For visual recognition, signs must be modeled as a configuration of horizontal, vertical, and diagonal wedges.1

#### **7.1.3. Linguistic Layer: The Lemmatization**

* **CBD (Corpus-Based Dictionary):** A unified glossary where a single lemma (headword) can link to various written forms across languages.42  
* **XCL (XML Chunks and Lemmas):** The format for linguistic annotation, mapping inflected forms back to the lemma.42  
* **Syntax Trees:** Modeling the dependencies of the Sumerian verbal chain or the Hittite enclitic chain.6

### **Table 4: Proposed Relational Data Schema for Cuneiform Pipeline**

| Table Name | Primary Keys | Foreign Keys | Key Attributes |
| :---- | :---- | :---- | :---- |
| **Artifacts** | P\_ID | \- | Provenience, Genre, Period 40 |
| **Graphemes** | G\_ID | \- | Unicode, Sign Name, Wedge Graph 42 |
| **SignInstances** | SI\_ID | P\_ID, G\_ID | Line\_No, Column, Condition 46 |
| **Lemmas** | L\_ID | \- | Language, PartOfSpeech, Root 25 |
| **Lemmatizations** | LEM\_ID | SI\_ID, L\_ID | Reading\_Value, Case/Tense 11 |
| **Translations** | TR\_ID | LEM\_ID | Target\_Language, Context\_Note 48 |

## **8\. Perspective on an "AlphaFold" for Cuneiform Signs**

The concept of an "AlphaFold" for cuneiform rests on the premise that sign interpretation is a structural prediction problem. Just as a protein's function is determined by its 3D fold, a sign's value is determined by its "contextual fold" across visual, syntactic, and historical dimensions.

### **8.1. ProtoSnap and Prototype Alignment**

Current research in AI for cuneiform uses "ProtoSnap," a method that aligns a prototype of a character to the individual variations on a tablet.36 This handles the problem of "ductus" (individual scribal handwriting) and physical deformation of the clay.36

### **8.2. Graph Neural Networks (GNNs) for Sign Topology**

Signs should not be treated as pixel arrays but as relational graphs of wedges. GNNs can model the distance and angle between wedges to classify signs even when they are partially obscured or broken.44 This is analogous to how AlphaFold models the distances between amino acids.49

### **8.3. The Multimodal "Folding" Model**

An advanced model would integrate three streams of data:

1. **Visual Stream:** CNNs or Diffusion models to extract the 3D topology of the sign.36  
2. **Syntactic Stream:** Transformers (like the T5 model used in the AICC corpus) to predict the most likely reading based on the surrounding sentence structure.52  
3. **Historical Stream:** A time-aware embedding that adjusts sign value probabilities based on the tablet's date (e.g., a sign that is polyvalent in Neo-Assyrian might be monovalent in Neo-Sumerian).20

## **9\. Synthesized Conclusions**

The fundamental differences between these languages are rooted in their typological origins—agglutinative isolates vs. inflected families—but their written expression is unified by the constraints of the cuneiform medium. Sumerian provides the structural foundation, Akkadian the phonetic flexibility, Hittite the heterographic complexity, and Elamite the simplified efficiency.

For the developer of a translation pipeline, the key insight is that cuneiform is a "language of relationships" rather than a "language of signs." A successful "AlphaFold" for this script must be able to "fold" a visual sign into its correct linguistic value by resolving the tensions between logography and phonography. This requires a data schema that treats every sign instance as a multimodal node linked to ancient sign lists, modern lexical databases, and the physical reality of the clay artifact.

The challenges of understanding isolates like Sumerian and Elamite, or the fragmented nature of the corpus, are not merely obstacles; they are the parameters that define the need for a structural, AI-driven approach to the ancient Near East. By integrating the insights of ancient scribes with the computational power of modern data science, we can ensure that the first three millennia of human history remain legible to the next three.

#### **Works cited**

1. Cuneiform \- Wikipedia, accessed February 13, 2026, [https://en.wikipedia.org/wiki/Cuneiform](https://en.wikipedia.org/wiki/Cuneiform)  
2. Cuneiform | Definition, History, & Facts \- Britannica, accessed February 13, 2026, [https://www.britannica.com/topic/cuneiform](https://www.britannica.com/topic/cuneiform)  
3. Cuneiform writing \- ETCSL, accessed February 13, 2026, [https://etcsl.orinst.ox.ac.uk/edition2/cuneiformwriting.php](https://etcsl.orinst.ox.ac.uk/edition2/cuneiformwriting.php)  
4. Classifying and Comparing Early Writing Systems (Chapter 2\) \- The Cambridge Handbook of Historical Orthography, accessed February 13, 2026, [https://www.cambridge.org/core/books/cambridge-handbook-of-historical-orthography/classifying-and-comparing-early-writing-systems/1FB931255299DED0DCF6C0E712E8A653](https://www.cambridge.org/core/books/cambridge-handbook-of-historical-orthography/classifying-and-comparing-early-writing-systems/1FB931255299DED0DCF6C0E712E8A653)  
5. Sumerian language \- Wikipedia, accessed February 13, 2026, [https://en.wikipedia.org/wiki/Sumerian\_language](https://en.wikipedia.org/wiki/Sumerian_language)  
6. UD-ETCSUX: Toward a Better Understanding of Sumerian Syntax \- ACL Anthology, accessed February 13, 2026, [https://aclanthology.org/2024.ml4al-1.19.pdf](https://aclanthology.org/2024.ml4al-1.19.pdf)  
7. akkadian\_adaption2\_endnote\_e, accessed February 13, 2026, [https://scholarworks.wm.edu/bitstreams/46d53f71-7179-40e3-a005-4bb69ad28d5c/download](https://scholarworks.wm.edu/bitstreams/46d53f71-7179-40e3-a005-4bb69ad28d5c/download)  
8. The Structure of Languages of the Ancient Orient \- ProQuest, accessed February 13, 2026, [https://search.proquest.com/openview/43b61cd65296774200a415c844892f39/1?pq-origsite=gscholar\&cbl=1817606](https://search.proquest.com/openview/43b61cd65296774200a415c844892f39/1?pq-origsite=gscholar&cbl=1817606)  
9. On the Old Babylonian Understanding of Sumerian Grammar, accessed February 13, 2026, [https://cdli.earth/articles/cdlp/1.1.pdf](https://cdli.earth/articles/cdlp/1.1.pdf)  
10. studies in akkadian grammar, accessed February 13, 2026, [https://isac.uchicago.edu/sites/default/files/uploads/shared/docs/as9.pdf](https://isac.uchicago.edu/sites/default/files/uploads/shared/docs/as9.pdf)  
11. Digital Corpus of Cuneiform Lexical Texts: Sign Lists \- Introduction to ..., accessed February 13, 2026, [https://oracc.museum.upenn.edu/dcclt/signlists/SignLists/index.html](https://oracc.museum.upenn.edu/dcclt/signlists/SignLists/index.html)  
12. Heterograms in Hittite, Palaic, and Luwian context \- Journal of ..., accessed February 13, 2026, [https://www.jolr.ru/files/(231)jlr2017-15-3-4(238-249).pdf](https://www.jolr.ru/files/\(231\)jlr2017-15-3-4\(238-249\).pdf)  
13. Introduction to the Lessons \- Eisenbrauns, accessed February 13, 2026, [https://www.eisenbrauns.org/sample\_chapter/Hoffner\_IntroductionPart2.pdf](https://www.eisenbrauns.org/sample_chapter/Hoffner_IntroductionPart2.pdf)  
14. The Proclamation of Anittas (Old Hittite) \- The Linguistics Research Center, accessed February 13, 2026, [https://lrc.la.utexas.edu/eieol/hitol/10](https://lrc.la.utexas.edu/eieol/hitol/10)  
15. Nominal Morphology \- CDLI Wiki, accessed February 13, 2026, [https://cdli.ox.ac.uk/wiki/doku.php?id=nominal\_morphology](https://cdli.ox.ac.uk/wiki/doku.php?id=nominal_morphology)  
16. IRAN vii. NON-IRANIAN LANGUAGES (3) Elamite \- Encyclopaedia Iranica, accessed February 13, 2026, [https://www.iranicaonline.org/articles/iran-vii3-elamite/](https://www.iranicaonline.org/articles/iran-vii3-elamite/)  
17. ELAM v. Elamite language \- Encyclopaedia Iranica, accessed February 13, 2026, [https://www.iranicaonline.org/articles/elam-v/](https://www.iranicaonline.org/articles/elam-v/)  
18. Was the Elamite language similar to the Sumerian language in terms of grammar and/or the writing system? \- Quora, accessed February 13, 2026, [https://www.quora.com/Was-the-Elamite-language-similar-to-the-Sumerian-language-in-terms-of-grammar-and-or-the-writing-system](https://www.quora.com/Was-the-Elamite-language-similar-to-the-Sumerian-language-in-terms-of-grammar-and-or-the-writing-system)  
19. Cuneiform | Oxford Classical Dictionary, accessed February 13, 2026, [https://oxfordre.com/classics/display/10.1093/acrefore/9780199381135.001.0001/acrefore-9780199381135-e-1952?d=%2F10.1093%2Facrefore%2F9780199381135.001.0001%2Facrefore-9780199381135-e-1952\&p=emailAybR0IwhIXAU6](https://oxfordre.com/classics/display/10.1093/acrefore/9780199381135.001.0001/acrefore-9780199381135-e-1952?d=/10.1093/acrefore/9780199381135.001.0001/acrefore-9780199381135-e-1952&p=emailAybR0IwhIXAU6)  
20. CUNEIFORM SCRIPT \- Encyclopaedia Iranica, accessed February 13, 2026, [https://www.iranicaonline.org/articles/cuneiform-script/](https://www.iranicaonline.org/articles/cuneiform-script/)  
21. Cuneiform signs \- Sumer Wikia | Fandom, accessed February 13, 2026, [https://sumer.fandom.com/wiki/Cuneiform\_signs](https://sumer.fandom.com/wiki/Cuneiform_signs)  
22. Akkadograms and Sumerograms in Hittite : r/Assyriology \- Reddit, accessed February 13, 2026, [https://www.reddit.com/r/Assyriology/comments/1qp0j59/akkadograms\_and\_sumerograms\_in\_hittite/](https://www.reddit.com/r/Assyriology/comments/1qp0j59/akkadograms_and_sumerograms_in_hittite/)  
23. (PDF) Sumerograms and Akkadograms in Hittite: Ideograms, Logograms, Allograms, or Heterograms? \- ResearchGate, accessed February 13, 2026, [https://www.researchgate.net/publication/311158186\_Sumerograms\_and\_Akkadograms\_in\_Hittite\_Ideograms\_Logograms\_Allograms\_or\_Heterograms](https://www.researchgate.net/publication/311158186_Sumerograms_and_Akkadograms_in_Hittite_Ideograms_Logograms_Allograms_or_Heterograms)  
24. 2140 \- writing systems \- York University, accessed February 13, 2026, [http://www.yorku.ca/kdenning/++2140%202006-7/2140writingsystems.htm](http://www.yorku.ca/kdenning/++2140%202006-7/2140writingsystems.htm)  
25. QPN: Oracc Linguistic Annotation for Proper Nouns, accessed February 13, 2026, [https://oracc.museum.upenn.edu/doc/help/languages/propernouns/index.html](https://oracc.museum.upenn.edu/doc/help/languages/propernouns/index.html)  
26. The Evolution of Writing | Denise Schmandt-Besserat \- The University of Texas at Austin, accessed February 13, 2026, [https://sites.utexas.edu/dsb/tokens/the-evolution-of-writing/](https://sites.utexas.edu/dsb/tokens/the-evolution-of-writing/)  
27. Cuneiform (article) | Ancient Near East \- Khan Academy, accessed February 13, 2026, [https://www.khanacademy.org/humanities/ancient-art-civilizations/ancient-near-east1/the-ancient-near-east-an-introduction/a/cuneiform](https://www.khanacademy.org/humanities/ancient-art-civilizations/ancient-near-east1/the-ancient-near-east-an-introduction/a/cuneiform)  
28. Cuneiform \- World History Encyclopedia, accessed February 13, 2026, [https://www.worldhistory.org/cuneiform/](https://www.worldhistory.org/cuneiform/)  
29. Have Scholars Finally Deciphered Linear Elamite, a Mysterious Ancient Script?, accessed February 13, 2026, [https://www.smithsonianmag.com/history/have-scholars-finally-deciphered-a-mysterious-ancient-script-180980497/](https://www.smithsonianmag.com/history/have-scholars-finally-deciphered-a-mysterious-ancient-script-180980497/)  
30. The Tablet-House: Learning Cuneiform in Ancient Mesopotamia \- alongthesilkroad.com, accessed February 13, 2026, [https://alongthesilkroad.com/2025/07/09/the-tablet-house-learning-cuneiform-in-ancient-mesopotamia/](https://alongthesilkroad.com/2025/07/09/the-tablet-house-learning-cuneiform-in-ancient-mesopotamia/)  
31. Mesopotamian Education and Schools \- History on the Net, accessed February 13, 2026, [https://www.historyonthenet.com/mesopotamian-education-and-schools](https://www.historyonthenet.com/mesopotamian-education-and-schools)  
32. A History of Education: Mesopotamia and the Sumerians \- AceReader Blog, accessed February 13, 2026, [https://blog.acereader.com/education/a-history-of-education-mesopotamia-and-the-sumerians/](https://blog.acereader.com/education/a-history-of-education-mesopotamia-and-the-sumerians/)  
33. Cuneiform \- Sumerian, Akkadian, Scripts | Britannica, accessed February 13, 2026, [https://www.britannica.com/topic/cuneiform/Decipherment-of-cuneiform](https://www.britannica.com/topic/cuneiform/Decipherment-of-cuneiform)  
34. Cuneiform \- Hittite, Sumerian, Akkadian | Britannica, accessed February 13, 2026, [https://www.britannica.com/topic/cuneiform/Hittite-and-other-languages](https://www.britannica.com/topic/cuneiform/Hittite-and-other-languages)  
35. Decoding Linear Elamite and the lost scripts of the ancient world | National Geographic, accessed February 13, 2026, [https://www.nationalgeographic.com/history/article/decoding-ancient-languages-linear-elamite](https://www.nationalgeographic.com/history/article/decoding-ancient-languages-linear-elamite)  
36. AI Models Makes Precise Copies of Cuneiform Characters \- Cornell Tech, accessed February 13, 2026, [https://tech.cornell.edu/news/ai-models-cuneiform/](https://tech.cornell.edu/news/ai-models-cuneiform/)  
37. (PDF) Cuneiform Text Dialect Identification Using Machine Learning Algorithms and Natural Language Processing (NLP) \- ResearchGate, accessed February 13, 2026, [https://www.researchgate.net/publication/383678981\_Cuneiform\_Text\_Dialect\_Identification\_Using\_Machine\_Learning\_Algorithms\_and\_Natural\_Language\_Processing\_NLP](https://www.researchgate.net/publication/383678981_Cuneiform_Text_Dialect_Identification_Using_Machine_Learning_Algorithms_and_Natural_Language_Processing_NLP)  
38. Extensive Review of State-of-the-Art Classification Techniques for Cuneiform SymbolImaging: Open Issues and Challenges, accessed February 13, 2026, [https://ijcsm.researchcommons.org/cgi/viewcontent.cgi?article=1096\&context=ijcsm](https://ijcsm.researchcommons.org/cgi/viewcontent.cgi?article=1096&context=ijcsm)  
39. Oracc: The Open Richly Annotated Cuneiform Corpus, accessed February 13, 2026, [https://oracc.museum.upenn.edu/](https://oracc.museum.upenn.edu/)  
40. The Cuneiform Digital Library Initiative: A Primer, accessed February 13, 2026, [https://iaassyriology.com/the-cuneiform-digital-library-initiative-a-primer/](https://iaassyriology.com/the-cuneiform-digital-library-initiative-a-primer/)  
41. Deciphering Cuneiform with Artificial Intelligence | DSI \- Data Science Institute, accessed February 13, 2026, [https://datascience.uchicago.edu/research/deciphering-cuneiform-with-artificial-intelligence/](https://datascience.uchicago.edu/research/deciphering-cuneiform-with-artificial-intelligence/)  
42. The Open Richly Annotated Cuneiform Corpus \- Oracc schemas, accessed February 13, 2026, [https://oracc.museum.upenn.edu/doc/about/standards/schemas/index.html](https://oracc.museum.upenn.edu/doc/about/standards/schemas/index.html)  
43. Cuneiform (Unicode block) \- Wikipedia, accessed February 13, 2026, [https://en.wikipedia.org/wiki/Cuneiform\_(Unicode\_block)](https://en.wikipedia.org/wiki/Cuneiform_\(Unicode_block\))  
44. Recognizing Cuneiform Signs Using Graph Based Methods \- Semantic Scholar, accessed February 13, 2026, [https://www.semanticscholar.org/paper/Recognizing-Cuneiform-Signs-Using-Graph-Based-Kriege-Fey/d6e9ba7ec3dcdb9da788b7f0e491884ec6b2b5f1](https://www.semanticscholar.org/paper/Recognizing-Cuneiform-Signs-Using-Graph-Based-Kriege-Fey/d6e9ba7ec3dcdb9da788b7f0e491884ec6b2b5f1)  
45. \[1802.05908\] Recognizing Cuneiform Signs Using Graph Based Methods \- arXiv, accessed February 13, 2026, [https://arxiv.org/abs/1802.05908](https://arxiv.org/abs/1802.05908)  
46. The Open Richly Annotated Cuneiform Corpus \- ATF Linkage \- Oracc, accessed February 13, 2026, [https://oracc.museum.upenn.edu/doc/help/editinginatf/linkage/](https://oracc.museum.upenn.edu/doc/help/editinginatf/linkage/)  
47. The Open Richly Annotated Cuneiform Corpus \- Lemmatisation primer \- Oracc, accessed February 13, 2026, [https://oracc.museum.upenn.edu/doc/help/lemmatising/primer/](https://oracc.museum.upenn.edu/doc/help/lemmatising/primer/)  
48. The Open Richly Annotated Cuneiform Corpus \- Translations \- Oracc, accessed February 13, 2026, [https://oracc.museum.upenn.edu/doc/help/editinginatf/translations/index.html](https://oracc.museum.upenn.edu/doc/help/editinginatf/translations/index.html)  
49. AlphaFold Protein Structure Database, accessed February 13, 2026, [https://alphafold.ebi.ac.uk/](https://alphafold.ebi.ac.uk/)  
50. Improved Deep Learning model for Ancient Cuneiform Symbols Classification \- ASPG, accessed February 13, 2026, [https://www.americaspg.com/article/pdf/3665](https://www.americaspg.com/article/pdf/3665)  
51. \[2505.04678\] Advanced Deep Learning Approaches for Automated Recognition of Cuneiform Symbols \- arXiv, accessed February 13, 2026, [https://arxiv.org/abs/2505.04678](https://arxiv.org/abs/2505.04678)  
52. I Built the World's Largest Translated Cuneiform Corpus using AI \- praeclarum, accessed February 13, 2026, [https://praeclarum.org/2023/06/09/cuneiform.html](https://praeclarum.org/2023/06/09/cuneiform.html)  
53. Advanced Deep Learning Approaches for Automated Recognition of Cuneiform Symbols, accessed February 13, 2026, [https://arxiv.org/html/2505.04678v1](https://arxiv.org/html/2505.04678v1)  
54. Advanced Deep Learning Approaches for Automated Recognition of Cuneiform Symbols, accessed February 13, 2026, [https://www.researchgate.net/publication/391575451\_Advanced\_Deep\_Learning\_Approaches\_for\_Automated\_Recognition\_of\_Cuneiform\_Symbols](https://www.researchgate.net/publication/391575451_Advanced_Deep_Learning_Approaches_for_Automated_Recognition_of_Cuneiform_Symbols)  
55. †Sumero-Akkadian Signary | The Online Cultural and Historical Research Environment, accessed February 13, 2026, [https://voices.uchicago.edu/ochre/project/%E2%80%A0sumero-akkadian-signary/](https://voices.uchicago.edu/ochre/project/%E2%80%A0sumero-akkadian-signary/)

[image1]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAFoAAAAYCAYAAAB6OOplAAAC2klEQVR4Xu2YS6hNURjH/5FXybMQcpWB54CEhFwyQglRXmMGlDwTA2SgPGZG3gN5jIhSZjIir6TketwrzyKUZ97/f99ZnbU/e997z+Dsc2L/6te9vm9v+1v7rvOttQ5QUFBQUFAHjKbTaK/Sv7vRQeW0MYU+oC/oq9LPx/QhbaZX6AraOdyQI2tpC6wu+ZQ+ok/oTboPKQPKken0Aj1Oj9C3dB09T2dH1yU4RX/TyVGsK11diu+P4nmjl/weVo/oQsfTW7DB1eJlT6Uv6agoppl8n/6kPaN4As1iDaajT8Bm0A86xCdyQM/UH1qzxLMKltvpE1WmA+yTv8YnyC563QcDg5E9GP2nH+kvOjSZyoXlsNr0kfTsgOUO+kSVmQh77hyfIAvpHh8MLIPduMEnyAxY7piL54Veop4/zsU1AZroJ9rgctVmEaymi7SHy6mNZdYTBqO+F6MbrsEWof4ulxdaqN/BXmxgAr0K64da7fOmD6yV6p19ppfoJtovvigNDUatYRvdTLfSE7CefZT2Ll+aK5odGsxrWFvTgMJiswXlxbEWzKLPYPUFn6OVhTn05xt0Xsm5tBGVDWQAHdhO0xbcNEJ/1jYv0JfepbdppyiehWaff36W2jVUgsahXZomaHjpuxNXRITBbHfxSlCB+gScbKcj7LY2OYT0/qzBKK4zQFtoF+Cfn+WC0j2tMQbJNhYYCavptE8EDsMuaHTxekCHE7UvP7CzsJpnunge3MHf9QS+0vU+GGimX2CHgHqiAfYy07acb2C5sT5RZbQh0CI4zCfIfPoNGZ/W4bCCL/tEHbASVttGF1df/l7Kqf7u9FziiuqxGPZcHbdjtM7dgx2gEqiBN8GOr5rN2qJoC6fNdq3RaUun1A+wurS1UwuJdz6hR+u7jjPIr+4DsGfr+40W2LZ4L6y+tAPVP4EWpSWwb87yYlL0u9rWUtjhpd7abkFBQUFBQcF/xR8MaKn3dNQWQAAAAABJRU5ErkJggg==>

[image2]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAgAAAAXCAYAAAA2jw7FAAAAhUlEQVR4XmNgIAM4APFpIJ6NJo4ClgBxLrogMngMxHrogtZA3AbEiUD8FogZkSVrgbgZyp4PxOuR5BgMgfgrEHNC+YuAuAAhzcBQA8T7kPiPgNgAic+QD8T9UDbIYe+BWBGIo2AKZBgg9mYDcRUQHwLiCUDMAVMAA4JQGuR6dmSJUTA4AACq/RJdG16URQAAAABJRU5ErkJggg==>

[image3]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAEcAAAAYCAYAAACoaOA9AAADV0lEQVR4Xu2XWahOURTH/+YyRWRKXEIZy/wiSeRBmR4kpJtQMkeSFxFCXsSDIaTIA2Uewy2UISUJmYkHZZ7JuP7WPvfus84+3z3f5UnnV/8631577W+vs9feex0gJyfnP6e2qLtouKil195Q1ML7XYieovG28V8wWHRf9FB01z3fEx33OzlOiB5D+1IPRHs8+2zRE6g/dVvU2rP7NBOtF30QXRZtFh0UrRM1F10U9SvvnU4N0XVRmTV4FBNjkAOiX6KR1mAYBO3HF1U9bvpDieiraLSoVtxUzhzRW9E2URNjWyh671TT2ELMgs7nhjUEyBpjgmeid6h8Qgugf8AAQ3SArnoaM6H+063Bwa30E/ryK6Op6Jrok+i5sYXIGmOMTtAJH7GGAIegfXlOhJgsWmkbHWOhgW+xBsNV0SLbGGATNEPviH5At1gaxcQYYyrUkVlRCG6jN9BVqmZsETtEQ22jUA/qx//pamwWZk1/22johYoz4zx0XJ5VaWSNMcEuqGMfazBwQuy31xo8uIp8EZZoO96yhgDtkf7yI8pEnd3zPujYPSrMCbLGmOApNCMKpSWZB/2DGdbgKIGuYogLUN9l1lAFJojWer+3Qsce4rVZssYYoyN04MPW4GgErUVIdNqnbYtS0XLb6HiN9NVtC82WEvfcTtTY7+BRX3RF1MBrWwMdO63WKSbGGNOgjrxCQ+yH1iRM81eil+45xHaEV4+3wzfRF2tw7Badgdo5F9YiU2I9KlgNLQP8eosZQT9mdoisMSbgxOgYOgC7iY66Z16x7JdWOLWCFmPBFRBuQv2Dk3Aw9Xkt17EGB2+cs0guzkTo2KtMe0TWGBPw7g8VXJzgSej+JnWhK8urPMQx6AqlwcqXExxjDY7oqj1lDR78j762URgG9WXmhsgaYwx+k4SyobfoNLS092+endAXxD0awQNuiWij1xaCZwS3wgtRF2PjdxQzgnNZbGyEQayAfmaEGAD1ZaCWYmPEQOh30UeoI1P5EXTyPFNYqH1HciUYBFeWK7EBmg2XRPOR7RZoA03hz9BxlkKv2HPQYo5j2qt2LvSMoQ/PLVs5s2CknTHws4VbcwSqHuNfw9SeBC320m6VQvATY5RoHLTSTvsGy8nJycnJyUnwGxNw3x2Qj9HGAAAAAElFTkSuQmCC>

[image4]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAHMAAAAYCAYAAADJcMJ/AAAEqklEQVR4Xu2YechnUxjHv/ZdRPblJWSd7EoIEZH1DwlpCFnHmpCSNWuy/GGJGWWyln1fppBBpMmWMYzBH8q+k/X5vM+58zv3ec/9vfcd+fXqvZ/61v2d59zzO8+55zznOUfq6Ojo6JhALG7awrSvafWsfHnTatnvfmxlOiwWTkR2N31ommv6ID3PMT2ZV0o8ZZonr4s+Mt2X2aeYPpW/j943rZXZc1Yx3WD60fSa6RbTw6brTKuaXjFtP792M4uY3jLNiIaMsfg4XllqlN81HjL9bTogGgK7yuvxYReum4YZMv1mOsi0WN00n1NN35luN60UbGebfkhaNNhKnCLvzzvRUKCtj+MNxvll08WmtU3XmJ6p1Qh8bvpeow/gWfIB4YOU2EC+qpo4Wf7+CdGQILT+JZ8so7GyaZbpZ9MXwVairY/jkWVMt8nH5lrTEnVzj43kA/xYNBR4RF6Xfa7E0abLYmHiEHlnbo2GwJumc2JhgZvlEWC26U95yG1iLD6OZ9aLBZFj5Y6y6vrBcv9WvgoWCraKO0x7xkL5zOI9/mezYIuwKneIhYGt1dvzXpK3y17bRFsfB8WKpp01cqsiIVwylFXwIfczba7m8dd0uaPbRkOAAaTe/dGQwSrhw0Wq8PxeNBRYX306m5hh2iQ9PyBve1LPPIK2Pg6C3eRj+KjpnmAjmbsqlMGFphfkSSbvXF039/hMvuL6hSk4XT4gJ0VDYki+SkrMlL97UTQsAIer7gx7CW3vkZVF2vr4X8P/k7wsbbrb9ElmY3LixxFZGZD0sNezmoFTwNs9c48N5Q0wS0qsIF/6UGWDTWFysumSWJj4Rs2rZ135ahxKz4STquORZU2vm5bLyq6Ut9101hyLjxGSpTVaiuPWaOD/ZHm7X5qmZbYT5f1kDHJIFsk1zjCtKZ+0W9ZqJI6TN8CRoMSD8k4S9r42fZWeS0xVeXXQ8d9Nv0ZD4i7T83I7feEseEytRo8r5Mea/LzLiuM9IkeJtj6W4EKC/rXRNLXPlPeW92mfrOxe1VdqBX37SV4f3Vg396ATVCglHGy0j6dnjgzUazpoMzOJ900z/F35+02DBoRCjhlNaTcZKftGnEyEJdq+PJRXtPVxkNwkP0vnZ3GOTuztJbYzXSq/iMGXGIqHoYHSAZ0BfVq+PwExnpXD0aTEE/IV0AQ3O3Ti4GhIVEeHZ6Mhg//Aqche8nenRkOirY+DZKY8GlVsLPfhePlZ/dxUfr08UlVw5cmlzKFZ2TCEkNJq28b0nPyqLc9M75R/UPaYCjb0C+QzrR/scYRG9olNg417WFYcfTkv2IBBZ1Zy7VdiJ/m7fJjIWH0cFOQflT8cTxg/+rmj6Xz5sQXINbgpq8DX2cq+wS7ye9UqDhPaPpYPNnsim+0fGjnTGXRWDjOduM1qe9V0ptplievIQ9ov8nZItwkrL8oP/7QZjw6nyfdI3mHfjTdDXDBgxwdmLKF6fy24j4OCzHWufAt4Q57kzErPlFUcJR8fMlg+Kv4PZfZ/DaHuSPnlQFPW2Q/CyIHyUMFNUtMd7kSALL66NCcXYGziRQILhXpNlwkdHR0dHR0dHR0d/0P+AXp3I5S9xCSZAAAAAElFTkSuQmCC>

[image5]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAA0AAAAXCAYAAADQpsWBAAAArElEQVR4XmNgGJ6AA4jrgdgDiHWBuAaI+4CYG4jjgLgbiAPgqqEgF4g1gfg3lA0Ca4H4GBArA7EMEH8AYlaoHBiYArEzEJ9HEtsIxElQtjoQvwFiRoQ0BDQzQJwEAkxA/A6IFaD8ciBeBGWjgENA7AtlGwDxA4QUwxEg9gPifAYk20CMV0DMB+WnA/EUmCQDxKmtQKyFJAYGoJCCAZCHmZH4IMCPxh8Fo2BAAABC9hWvhUQJBwAAAABJRU5ErkJggg==>

[image6]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAkAAAAXCAYAAADZTWX7AAAAjUlEQVR4XmNgwA6YgJgZXRAZqAPxciA+D8QsaHJwsBCIo4F4GroEDIB0fgNiEXQJGPAE4rlA/BOIJwCxCao0BIAcmwjE24GYA4gZUaURoBuIW9EF0cEeIA5GF0QHb4BYEV0QGcgD8St0QWQgxACxZj66BAzoAfEDIJ4FxOaoUgjABsSVQOyLLjEKBgoAAAQAD/Hx7+tFAAAAAElFTkSuQmCC>

[image7]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAXCAYAAADgKtSgAAABFElEQVR4Xu3SvyvEcRzH8fflVxSlk40Sg3JZ3HBlwnw2uwyICSkGJHfbUVey2dQpmzIpdYMMF3+DTFYDt97z3ed93+9b3SrL51WPen9+fj+f7/crEvNf2cARMtZeQs7V55jBLtatX9tnKFi7D5tWJ1nBHN4xZX2vmEc/DnGFF8ziA90oYxU3YYkU8Wh1kjym8Snh5MP4lnCSLCbwLGGxPkwPoHMmUcOWhFzg2OpfOcC11cuouzHd8AdDrk/Tiy+MW/sNC+lwmlusWV1FCTsSNlhEw8Z89Lb6ijQjaGIU28kMi572Hnuo4E7Cx9PorU6t9unCE/ZxggdcYsxPakev32P1oOsfkPQv6hT/uvy6mJiYmD9JC8rcJarQD1eMAAAAAElFTkSuQmCC>

[image8]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABcAAAAXCAYAAADgKtSgAAABKklEQVR4Xu3SzStEURjH8cfrGEnKxkSJbLxkpagpxEIpynbshNjJykuJsrVVrGTBP2BhQ5oMSvkDxMbCf8Da9+n8MHOH3WV1f/Wp85zndO65516zf8ggbnASbcSVA2xEJ+PKI7LRyTjSinfUYgDb6FZvErvIqO7EtMbj2EMvVrGo+ZLkcIEJC5tdYQHtWMYR5rXWN9tEGuvYxy368YIKrfvKIZ4wq9pPXW3hRPV4RY96DxhGMzpQwJSFh3VpTUn8vv1klxZOXJwhPGvcZOH66lT7hl43qi5LC95QgzmcWviwI+ov4VjjGVxj1MLvO4Z79X6Mv9KZxn3IY+u7bW24wwp2cG7h3v1u1zT3a/zE/nqf8TuuKqo9lWjQ2P+olMa+tuwDJkmSJMlf5gPa8SmIw47oPgAAAABJRU5ErkJggg==>

[image9]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABMAAAAXCAYAAADpwXTaAAABKElEQVR4Xu3SPyiFURjH8Z8/UZcUiukyKIOUgVIy0mUysVkkgxgwGNiwmKXMSgYlf4rVqGyyKwOL3SK+j+e87z33ZbgslvdXn+4573POfc+fV/qHlNAf9YvhtyZqV519DEf9KZziDGPR8z/HVtSRfZjEipuYwwSaUcAWZqNxljbMYxu9mZo6cSl/0wA+5BPW0IOX8tCvXKFdvt29TE03WAntETyE9hCWcBj6llo84wjT8h2kacE7ukJ/Q37gSe5Uecj2Z+M4wZv8hWka8Ip6NMonz4RaH57QikXU4VHlmz3HYGinWcAuduTnldxSN27lq7Xt2Hd1jGUcYD2MS2PLtkGWUdxHNUtTpm+xy7FVfsu1/HOwLV5gsrL8u9hk28aqfth/njx5qs0nlH8nogrSPlcAAAAASUVORK5CYII=>

[image10]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAACUAAAAXCAYAAACMLIalAAABwElEQVR4Xu2TP0jVURTHj5RmYYIoTRZJDUElSg5CS+rgVE1BCEE1qBiZGoKGf9C0Kc0gXSIECRIcgkAIBNFAHETnRtGlJcKhXP18Oec9f+8hrQ7+PvCBc89993fvPec+sxPMHdzAj3n5Y+czPs9PHje7WJ2f/B9tOIgFMW7CG4l4Aq9jD7ZGXuPXWB/jM9gecYbb+Aaf4G87/P5ZfIR9WIc1kc/yAG/hNl6N3Kb5B7W4H2dw3fymO3gax/GxeVvEXVyKWOiSOrSYxa8Ra+13bMZz+BOfxVwWnfQa/jK/SRn+Nb95OVbhmvmmOqQOrt9cwS/YYc4kDkVca/4N/V7MYVfE6spKxEKXvJkYZ1EZP0V8D1cTc/rwPyxN5EQR7uGlGG9hQ8QDuByx0MaZFqmamcNftty25jCPTyN+j2PYbb5xo/nfOR9VV5uJCtzHC+ateIHvYk4t/2Ne8RbzNt6PuU78hg9jPgdVR5Mv8S0umD9qoSqORJzklHk1enEYF/EDXsRK83ekA77CHziFxebVnDZv56j5+9L7OxK1qTDi84m8HuOR5Q2SbU2uE3p7Quv1RjNon5KIddCUlJSUlJQTzQF4mkXChWxIdAAAAABJRU5ErkJggg==>

[image11]: <data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAABYAAAAXCAYAAAAP6L+eAAABCklEQVR4Xu3Sv0sCcRjH8acwStPoT7jWINCUxiCXQggnyyWIEBQsbWwoh0BHN/8MEcKhH4vi5uLaXFvQ1NjS++v3Ofpe6BYNcR94cc9zz3F33++dSJi/yCqayGEL12gh7lwTxQmukEHSmc3NOTbxiQs910VJ6wjusY8YnlHVmZ+FH/00aWQxcc494kjrMgbfI3kRuzI/y+g7fSC3aGu9jg8ktH9CQ2sP7xJ8w1OMnT6QIQ61PsYDtrGLHvI6q+EORWwghR2MdB6Iefob1rQ/ELsVFe330MGl2JWZ/b7BEs70mpk3NjF/hhuzDYtOb27i/yUrevRQF/sCZt/Nx/3VFPAqdqVhwoT5n/kCvawkOno1AC4AAAAASUVORK5CYII=>