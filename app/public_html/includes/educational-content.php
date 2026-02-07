<?php
/**
 * Educational Content for Library Browser
 * Help text, tooltips, and explanations adapted by user level
 *
 * User Levels:
 * - student: Full explanations with examples and analogies
 * - scholar: Concise technical definitions
 * - expert: Minimal/no help text (tooltips hidden by default)
 */

return [
    /**
     * Field Help Text
     * Used on word detail pages and throughout the library
     */
    'field_help' => [
        'headword' => [
            'student' => 'The <strong>headword</strong> is the standard dictionary form of the word. In Sumerian, this is the base form without grammatical suffixes. Think of it like looking up "go" instead of "going" in an English dictionary.',
            'scholar' => 'Dictionary lemma in citation form.',
            'expert' => null
        ],
        'citation_form' => [
            'student' => 'The <strong>citation form</strong> (CF) is how scholars reference this word in publications. It\'s usually the same as the headword but may differ for verbs or irregular forms.',
            'scholar' => 'Scholarly reference form (CF).',
            'expert' => null
        ],
        'guide_word' => [
            'student' => 'The <strong>guide word</strong> (GW) is the English meaning that helps you identify which word this is. Ancient languages often have multiple words spelled the same way (homonyms), so the guide word distinguishes them.<br><br>Example: "a" could mean "water" or "arm" depending on context. Guide words help: a[water] vs a[arm]',
            'scholar' => 'English gloss used to disambiguate homonyms.',
            'expert' => null
        ],
        'part_of_speech' => [
            'student' => '<strong>Part of speech</strong> (POS) tells you how the word functions grammatically:<ul><li><strong>N</strong> = Noun (person, place, thing)</li><li><strong>V</strong> = Verb (action or state)</li><li><strong>AJ</strong> = Adjective (describes a noun)</li><li><strong>AV</strong> = Adverb (describes a verb)</li></ul><a href="/library/glossary#pos">See all POS codes</a>',
            'scholar' => 'Grammatical category. See <a href="/library/glossary#pos">full POS list</a>.',
            'expert' => null
        ],
        'language' => [
            'student' => '<strong>Language codes:</strong><ul><li><strong>sux</strong> = Sumerian (non-Semitic, isolated language)</li><li><strong>akk</strong> = Akkadian (Semitic language)</li><li><strong>akk-x-stdbab</strong> = Standard Babylonian Akkadian</li><li><strong>akk-x-oldbab</strong> = Old Babylonian Akkadian</li></ul>Sumerian and Akkadian were both used in ancient Mesopotamia, often appearing together in bilingual texts.',
            'scholar' => 'Language code per ORACC standard. See <a href="/library/glossary#languages">full list</a>.',
            'expert' => null
        ],
        'frequency' => [
            'student' => '<strong>Frequency</strong> (also called "icount" = instance count) shows how often this word appears in the ORACC corpus.<br><br>Higher frequency = more common word. This helps you:<ul><li>Prioritize learning common words first</li><li>Assess how well-attested a word is</li><li>Understand which words are typical vs rare</li></ul>Range: 1 (hapax legomenon - only once) to 1000+ (very common)',
            'scholar' => 'Instance count in ORACC corpus. Higher = better attested.',
            'expert' => null
        ],
        'variant_forms' => [
            'student' => '<strong>Variant spellings</strong> occur because:<ul><li>Different time periods used different conventions</li><li>Different scribal schools had different practices</li><li>Grammatical suffixes change the word\'s form</li><li>Phonetic complements (extra signs) clarify pronunciation</li></ul>All variants map to the same base word (headword).',
            'scholar' => 'Orthographic variants from corpus with frequency counts.',
            'expert' => null
        ],
        'cuneiform_signs' => [
            'student' => 'Cuneiform is a <strong>logosyllabic writing system</strong>:<ul><li><strong>Logographic</strong>: One sign = whole word (like "lugal" = king)</li><li><strong>Syllabic</strong>: Multiple signs spell out sounds (like "ka-la-am" = kalam)</li></ul>Click any sign to see all its possible readings and other words that use it.',
            'scholar' => 'Sign breakdown with Unicode mappings. Click for OGSL details.',
            'expert' => null
        ],
        'corpus_examples' => [
            'student' => '<strong>Corpus examples</strong> show how this word appears in actual ancient tablets. Each example includes:<ul><li><strong>P-number</strong>: Unique tablet ID (e.g., P123456)</li><li><strong>Context</strong>: Period, genre, provenience</li><li><strong>Line reference</strong>: Where on the tablet (obv. i 3 = obverse, column 1, line 3)</li><li><strong>Transliteration</strong>: How the cuneiform is read</li><li><strong>Translation</strong>: English meaning</li></ul>',
            'scholar' => 'Attestations from lemmatized corpus. Click P-number to view tablet.',
            'expert' => null
        ],
        'meanings' => [
            'student' => 'Many ancient words have <strong>multiple related meanings</strong> (called "polysemy"). The meaning depends on context. Each sense shows its usage percentage based on corpus analysis.',
            'scholar' => 'Polysemic senses with usage frequencies when available.',
            'expert' => null
        ]
    ],

    /**
     * Part of Speech (POS) Codes
     * Full table with labels, definitions, and examples
     */
    'pos_codes' => [
        'N' => [
            'label' => 'Noun',
            'definition' => 'Person, place, thing, or concept',
            'example' => 'lugal (king), e₂ (house)'
        ],
        'V' => [
            'label' => 'Verb',
            'definition' => 'Action or state',
            'example' => 'dug₄ (to speak), gub (to stand)'
        ],
        'V/i' => [
            'label' => 'Verb (intransitive)',
            'definition' => 'Action without a direct object',
            'example' => 'ŋen (to go)'
        ],
        'V/t' => [
            'label' => 'Verb (transitive)',
            'definition' => 'Action with a direct object',
            'example' => 'šum₂ (to give)'
        ],
        'AJ' => [
            'label' => 'Adjective',
            'definition' => 'Describes or modifies a noun',
            'example' => 'gal (big), maḫ (great)'
        ],
        'AV' => [
            'label' => 'Adverb',
            'definition' => 'Describes or modifies a verb',
            'example' => 'gibil (anew), kal-la (mightily)'
        ],
        'DP' => [
            'label' => 'Demonstrative Pronoun',
            'definition' => 'Points to specific things',
            'example' => 'bi (that), ne (this)'
        ],
        'PP' => [
            'label' => 'Personal Pronoun',
            'definition' => 'Refers to people',
            'example' => 'ŋu₁₀ (my), zu (your)'
        ],
        'RP' => [
            'label' => 'Relative Pronoun',
            'definition' => 'Introduces relative clause',
            'example' => ''
        ],
        'REL' => [
            'label' => 'Relative',
            'definition' => 'Relative clause marker',
            'example' => ''
        ],
        'MOD' => [
            'label' => 'Modal',
            'definition' => 'Expresses modality',
            'example' => 'ḫe₂- (let, may)'
        ],
        'PRP' => [
            'label' => 'Preposition',
            'definition' => 'Shows relationship between words',
            'example' => 'šà (in), igi (before)'
        ],
        'CNJ' => [
            'label' => 'Conjunction',
            'definition' => 'Connects words or clauses',
            'example' => 'u₃ (and)'
        ],
        'J' => [
            'label' => 'Interjection',
            'definition' => 'Exclamation',
            'example' => 'a-na (alas!)'
        ],
        'DN' => [
            'label' => 'Divine Name',
            'definition' => 'Name of a god or goddess',
            'example' => 'inana, utu, enlil'
        ],
        'PN' => [
            'label' => 'Personal Name',
            'definition' => 'Name of a person',
            'example' => ''
        ],
        'RN' => [
            'label' => 'Royal Name',
            'definition' => 'Name of a king or ruler',
            'example' => 'šulgi, ur-namma'
        ],
        'GN' => [
            'label' => 'Geographic Name',
            'definition' => 'Place name',
            'example' => 'nibru (Nippur), unug (Uruk)'
        ],
        'TN' => [
            'label' => 'Temple Name',
            'definition' => 'Name of a temple',
            'example' => 'e₂-kur'
        ],
        'ON' => [
            'label' => 'Object Name',
            'definition' => 'Name of an artifact or object',
            'example' => ''
        ],
        'WN' => [
            'label' => 'Water Name',
            'definition' => 'Name of a body of water',
            'example' => ''
        ],
        'MN' => [
            'label' => 'Month Name',
            'definition' => 'Name of a month',
            'example' => ''
        ],
        'YN' => [
            'label' => 'Year Name',
            'definition' => 'Year designation',
            'example' => ''
        ],
        'FN' => [
            'label' => 'Field Name',
            'definition' => 'Name of an agricultural field',
            'example' => ''
        ]
    ],

    /**
     * Language Codes
     * With historical context and usage periods
     */
    'language_codes' => [
        'sux' => [
            'label' => 'Sumerian',
            'description' => 'Language isolate (no known relatives). Spoken ~3500-2000 BCE, continued as scholarly language until ~100 CE. Used for religious, literary, and administrative texts.',
            'family' => 'Isolate'
        ],
        'sux-x-emesal' => [
            'label' => 'Emesal',
            'description' => 'Sumerian dialect used primarily in liturgical and poetic contexts, especially in texts spoken by female deities.',
            'family' => 'Sumerian variant'
        ],
        'akk' => [
            'label' => 'Akkadian',
            'description' => 'Semitic language spoken ~2500 BCE - 100 CE. Includes Old Akkadian, Babylonian, and Assyrian dialects.',
            'family' => 'Semitic'
        ],
        'akk-x-stdbab' => [
            'label' => 'Standard Babylonian',
            'description' => 'Literary and scholarly dialect of Akkadian, used ~1500-100 BCE.',
            'family' => 'Akkadian dialect'
        ],
        'akk-x-oldbab' => [
            'label' => 'Old Babylonian',
            'description' => 'Akkadian dialect ~2000-1600 BCE. Rich literary and administrative corpus.',
            'family' => 'Akkadian dialect'
        ],
        'akk-x-neoass' => [
            'label' => 'Neo-Assyrian',
            'description' => 'Akkadian dialect ~911-612 BCE. Used in Assyrian royal inscriptions.',
            'family' => 'Akkadian dialect'
        ],
        'hit' => [
            'label' => 'Hittite',
            'description' => 'Indo-European language of the Hittite Empire (~1650-1180 BCE).',
            'family' => 'Indo-European'
        ],
        'uga' => [
            'label' => 'Ugaritic',
            'description' => 'Semitic language from Ugarit (Syria), ~1400-1200 BCE.',
            'family' => 'Semitic'
        ],
        'qpc' => [
            'label' => 'Proto-Cuneiform',
            'description' => 'Earliest cuneiform writing system, ~3200-3000 BCE. Language uncertain.',
            'family' => 'Unknown'
        ],
        'qpn' => [
            'label' => 'Proper Nouns',
            'description' => 'Generic category for proper names of uncertain language.',
            'family' => 'Various'
        ],
        'elx' => [
            'label' => 'Elamite',
            'description' => 'Language of Elam (SW Iran), ~2800-300 BCE. Language isolate.',
            'family' => 'Isolate'
        ],
        'xhu' => [
            'label' => 'Hurrian',
            'description' => 'Language of the Hurrians, northern Mesopotamia, ~2500-1000 BCE.',
            'family' => 'Hurro-Urartian'
        ]
    ],

    /**
     * Welcome Overlay Content
     * First-time visitor introduction
     */
    'welcome_overlay' => [
        'title' => 'Welcome to the Cuneiform Dictionary!',
        'body' => 'This browser lets you explore 21,000+ words from ancient Sumerian and Akkadian languages.<br><br>• Search by ancient word form (e.g., "lugal") OR English meaning (e.g., "king")<br>• Filter by language, grammar, or frequency<br>• Click any word to see variants, meanings, and usage examples',
        'buttons' => [
            'tour' => 'Show guided tour',
            'start' => 'Start browsing'
        ]
    ],

    /**
     * Cuneiform Writing System Guide
     * For /library/glossary page
     */
    'cuneiform_basics' => [
        'logographic' => [
            'title' => 'Logographic (Word Signs)',
            'description' => 'One sign represents a complete word or concept.',
            'example' => 'The sign 𒈗 (LUGAL) means "king" in Sumerian. When you see this sign in a text, you read it as "lugal" (the Sumerian word for king).'
        ],
        'syllabic' => [
            'title' => 'Syllabic (Sound Signs)',
            'description' => 'Signs represent syllables (sounds), and you combine multiple signs to spell out words phonetically.',
            'example' => 'The word "kalam" (land) is spelled with three signs: 𒅗 (ka) + 𒆷 (la) + 𒀀 (am). Each sign represents just a sound, not a meaning.'
        ],
        'both' => [
            'title' => 'The Same Sign Can Do Both!',
            'description' => 'This is what makes cuneiform complex. The sign 𒅗 (KA) can be used:',
            'examples' => [
                '<strong>Logographically</strong>: As the word "ka" meaning "mouth"',
                '<strong>Syllabically</strong>: As the sound /ka/ in words like "ka-la-am" (kalam/land)'
            ],
            'note' => 'Context determines which reading is correct!'
        ],
        'determinatives' => [
            'title' => 'Determinatives',
            'description' => 'Some signs aren\'t pronounced at all! They\'re "semantic classifiers" that tell you what kind of word follows.',
            'example' => '{d}inana: {d} = determinative meaning "divine name", inana = the goddess Inana. You read this as just "Inana", but the {d} tells you she\'s a deity.',
            'common' => [
                '{d} = divine name',
                '{giš} = wooden object',
                '{ki} = place name',
                '{munus} = female person'
            ]
        ]
    ],

    /**
     * Grammar Basics
     * SOV word order, case systems, etc.
     */
    'grammar_basics' => [
        'sumerian_word_order' => [
            'title' => 'Sumerian Word Order (SOV)',
            'description' => 'Sumerian follows strict Subject-Object-Verb order:',
            'structure' => [
                'Subject comes first (who/what is doing the action)',
                'Object comes second (what is being acted upon)',
                'Verb comes last (the action itself)'
            ],
            'example' => '"lugal e₂ dù" = "king house build" = "the king builds a house"',
            'comparison' => 'This is different from English (SVO: "The king builds a house") but similar to Japanese, Turkish, and Korean.'
        ],
        'akkadian_flexibility' => [
            'title' => 'Akkadian Word Order',
            'description' => 'Akkadian word order is more flexible than Sumerian, but typically verb-final. Case endings (nominative, accusative, genitive) indicate grammatical function.',
            'example' => ''
        ]
    ],

    /**
     * Research Conventions
     * Citations, transliterations, abbreviations
     */
    'research_conventions' => [
        'p_numbers' => [
            'title' => 'P-Numbers (Tablet IDs)',
            'description' => 'Unique identifiers for each cuneiform tablet in the CDLI database.',
            'format' => 'P + 6 digits (e.g., P123456)',
            'example' => 'P526829 = a specific Ur III administrative tablet from Umma'
        ],
        'line_references' => [
            'title' => 'Line References',
            'description' => 'Indicate where on a tablet a text appears.',
            'format' => 'surface + column + line number',
            'examples' => [
                'obv. i 3 = obverse (front), column 1, line 3',
                'rev. ii 12 = reverse (back), column 2, line 12',
                'edge = edge of tablet',
                'seal = seal impression'
            ]
        ],
        'transliteration' => [
            'title' => 'Reading Transliterations',
            'description' => 'Conventions for representing cuneiform in Latin alphabet.',
            'symbols' => [
                'Subscript numbers (₂, ₃) = distinguish homophonic signs',
                '{ } = determinatives (not pronounced)',
                '[ ] = damaged/missing text (restored by editor)',
                '< > = text omitted by scribe (added by editor)',
                '# = broken sign (unidentifiable)',
                '? = uncertain reading',
                '! = error by ancient scribe (corrected by editor)'
            ]
        ],
        'citations' => [
            'title' => 'Common Abbreviations',
            'description' => 'Standard abbreviations for text collections.',
            'examples' => [
                'ARM = Archives Royales de Mari',
                'VAB = Vorderasiatische Bibliothek',
                'CT = Cuneiform Texts from Babylonian Tablets',
                'ABL = Assyrian and Babylonian Letters',
                'TCL = Textes Cunéiformes du Louvre'
            ]
        ]
    ]
];
