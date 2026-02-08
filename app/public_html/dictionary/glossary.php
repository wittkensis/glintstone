<?php
/**
 * Library Glossary Page
 *
 * Central reference for all terminology used across the library:
 * - Parts of Speech (POS) codes
 * - Language codes
 * - Dictionary field explanations
 * - Cuneiform writing system basics
 * - Grammar concepts
 * - Research conventions
 */

require_once __DIR__ . '/../includes/header.php';
$educational_content = require __DIR__ . '/../includes/educational-content.php';
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Linguistic Glossary - Cuneiform Library</title>
    <link rel="stylesheet" href="/assets/css/layout/site.css">
    <link rel="stylesheet" href="/assets/css/components/word-detail.css">
    <link rel="stylesheet" href="/assets/css/components/educational-help.css">
    <style>
        .glossary-page {
            max-width: 900px;
            margin: 0 auto;
            padding: 2rem;
        }
        .glossary-nav {
            background: var(--color-surface);
            padding: 1rem;
            margin-bottom: 2rem;
            border-radius: 8px;
            position: sticky;
            top: 1rem;
        }
        .glossary-nav ul {
            list-style: none;
            padding: 0;
            margin: 0;
            display: flex;
            gap: 1rem;
            flex-wrap: wrap;
        }
        .glossary-nav a {
            color: var(--color-text);
            text-decoration: none;
            padding: 0.5rem 1rem;
            border-radius: 4px;
        }
        .glossary-nav a:hover {
            background: var(--color-accent);
        }
        .glossary-section {
            margin-bottom: 3rem;
            scroll-margin-top: 5rem;
        }
        .glossary-section h2 {
            border-bottom: 2px solid var(--color-accent);
            padding-bottom: 0.5rem;
            margin-bottom: 1.5rem;
        }
        .pos-table, .lang-table {
            width: 100%;
            border-collapse: collapse;
            margin-top: 1rem;
        }
        .pos-table th, .lang-table th {
            text-align: left;
            padding: 0.75rem;
            background: var(--color-surface);
            border-bottom: 2px solid var(--color-accent);
        }
        .pos-table td, .lang-table td {
            padding: 0.75rem;
            border-bottom: 1px solid var(--color-border);
        }
        .pos-table tr:hover, .lang-table tr:hover {
            background: var(--color-surface);
        }
    </style>
</head>
<body>
    <div class="glossary-page">
        <header>
            <h1>Linguistic Glossary</h1>
            <p class="description">
                Reference guide for all terminology used in the Cuneiform Library
            </p>
        </header>

        <!-- Navigation -->
        <nav class="glossary-nav" aria-label="Page sections">
            <ul>
                <li><a href="#pos">Parts of Speech</a></li>
                <li><a href="#languages">Language Codes</a></li>
                <li><a href="#fields">Dictionary Fields</a></li>
                <li><a href="#writing-system">Writing System</a></li>
                <li><a href="#grammar">Grammar Basics</a></li>
                <li><a href="#research">Research Conventions</a></li>
            </ul>
        </nav>

        <!-- Parts of Speech -->
        <section id="pos" class="glossary-section">
            <h2>Parts of Speech (POS) Codes</h2>
            <p>
                Grammatical categories that describe how words function in sentences.
                These codes follow ORACC CBD 2.0 standards.
            </p>

            <table class="pos-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Label</th>
                        <th>Definition</th>
                        <th>Example</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($educational_content['pos_codes'] as $code => $data): ?>
                        <tr>
                            <td><strong><?= htmlspecialchars($code) ?></strong></td>
                            <td><?= htmlspecialchars($data['label']) ?></td>
                            <td><?= htmlspecialchars($data['definition']) ?></td>
                            <td><?= htmlspecialchars($data['example']) ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </section>

        <!-- Language Codes -->
        <section id="languages" class="glossary-section">
            <h2>Language Codes</h2>
            <p>
                Mesopotamian cuneiform was used to write multiple languages over 3,000 years.
                These codes identify which language a word belongs to.
            </p>

            <table class="lang-table">
                <thead>
                    <tr>
                        <th>Code</th>
                        <th>Language</th>
                        <th>Description</th>
                    </tr>
                </thead>
                <tbody>
                    <?php foreach ($educational_content['language_codes'] as $code => $data): ?>
                        <tr>
                            <td><strong><?= htmlspecialchars($code) ?></strong></td>
                            <td><?= htmlspecialchars($data['label']) ?></td>
                            <td><?= htmlspecialchars($data['description']) ?></td>
                        </tr>
                    <?php endforeach; ?>
                </tbody>
            </table>
        </section>

        <!-- Dictionary Fields -->
        <section id="fields" class="glossary-section">
            <h2>Dictionary Fields Explained</h2>
            <p>
                Understanding the structure of dictionary entries helps you navigate
                and interpret word data effectively.
            </p>

            <dl class="field-list">
                <?php foreach ($educational_content['field_help'] as $field => $levels): ?>
                    <dt id="field-<?= htmlspecialchars($field) ?>">
                        <?= htmlspecialchars(ucwords(str_replace('_', ' ', $field))) ?>
                    </dt>
                    <dd>
                        <?= $levels['student'] ?? $levels['scholar'] ?? 'No description available.' ?>
                    </dd>
                <?php endforeach; ?>
            </dl>
        </section>

        <!-- Cuneiform Writing System -->
        <section id="writing-system" class="glossary-section">
            <h2>Cuneiform Writing System</h2>

            <h3>Three Types of Sign Usage</h3>

            <h4>1. Logographic</h4>
            <p>
                <strong>Definition:</strong> One sign represents a complete word or concept.
            </p>
            <p>
                <strong>Example:</strong> The sign LUGAL (𒈗) means "king" - it's read as the
                Sumerian word "lugal" or the Akkadian equivalent "šarru."
            </p>
            <p>
                <strong>Analogy:</strong> Like using "&amp;" for "and" in English, or "2" for "two."
                One symbol = one word.
            </p>

            <h4>2. Syllabic</h4>
            <p>
                <strong>Definition:</strong> Signs represent sounds (syllables), not meanings.
                Words are spelled out phonetically.
            </p>
            <p>
                <strong>Example:</strong> The Akkadian word "šarrum" (king) can be written
                syllabically as "ša-ar-ru-um" using four signs for their sound values.
            </p>
            <p>
                <strong>Analogy:</strong> Like how we use letters in English to spell out words.
            </p>

            <h4>3. Determinative</h4>
            <p>
                <strong>Definition:</strong> Unpronounced signs that classify the type of word
                (person, place, god, object, etc.).
            </p>
            <p>
                <strong>Example:</strong> {d} before a name indicates a deity: {d}Inana = "the goddess Inana."
                You don't pronounce the {d}, it just tells you it's a divine name.
            </p>
            <p>
                <strong>Analogy:</strong> Like capital letters in English indicating proper names,
                but more specific about the category.
            </p>

            <h3>Sign Variants</h3>
            <ul>
                <li><strong>@g (gunified)</strong>: Simplified or abbreviated form of a sign</li>
                <li><strong>@t (tenû)</strong>: Reduced or "thin" form used in Neo-Assyrian</li>
            </ul>
        </section>

        <!-- Grammar Basics -->
        <section id="grammar" class="glossary-section">
            <h2>Grammar Basics</h2>

            <h3>Sumerian Word Order (SOV)</h3>
            <p>
                Sumerian follows <strong>Subject-Object-Verb</strong> order:
            </p>
            <ul>
                <li>Subject comes first (who/what is doing the action)</li>
                <li>Object comes second (what is being acted upon)</li>
                <li>Verb comes last (the action itself)</li>
            </ul>
            <p>
                <strong>Example:</strong> "lugal e₂ dù" = "king house build" = "the king builds a house"
            </p>
            <p>
                This is different from English (SVO: "The king builds a house") but similar
                to Japanese, Turkish, and Korean.
            </p>

            <h3>Akkadian Case System</h3>
            <p>
                Akkadian nouns change their endings based on grammatical function:
            </p>
            <ul>
                <li><strong>Nominative (-u/-um)</strong>: Subject of the sentence</li>
                <li><strong>Accusative (-a/-am)</strong>: Direct object</li>
                <li><strong>Genitive (-i/-im)</strong>: Possession or "of"</li>
            </ul>

            <h3>Enclitic Particles</h3>
            <p>
                Small words that attach to the first word of a clause in Akkadian:
            </p>
            <ul>
                <li><strong>-ma</strong>: "and" or "then" (connects clauses)</li>
                <li><strong>-mi</strong>: Emphasizes or marks quotations</li>
            </ul>

            <h3>Compound Words</h3>
            <p>
                Words built from multiple elements where order matters:
            </p>
            <ul>
                <li><strong>e₂-gal</strong> = e₂ (house) + gal (big) = "palace" (big house)</li>
                <li><strong>nam-lugal</strong> = nam- (abstract prefix) + lugal (king) = "kingship"</li>
            </ul>
        </section>

        <!-- Research Conventions -->
        <section id="research" class="glossary-section">
            <h2>Research Conventions</h2>

            <h3>P-Numbers (Tablet IDs)</h3>
            <p>
                <strong>Format:</strong> P followed by 6 digits (e.g., P123456)
            </p>
            <p>
                Unique identifiers assigned by the Cuneiform Digital Library Initiative (CDLI)
                to every published cuneiform tablet. Used universally in scholarship.
            </p>

            <h3>Line References</h3>
            <p>
                <strong>Format:</strong> [side] [column] [line]
            </p>
            <p>
                <strong>Examples:</strong>
            </p>
            <ul>
                <li><strong>obv. i 3</strong> = Obverse (front), column 1, line 3</li>
                <li><strong>rev. ii 12</strong> = Reverse (back), column 2, line 12</li>
                <li><strong>edge</strong> = Text on the edge of the tablet</li>
            </ul>

            <h3>Transliteration Conventions</h3>
            <ul>
                <li><strong>Subscript numbers</strong>: Distinguish homophone signs (ba, ba₂, ba₃)</li>
                <li><strong>Hyphens</strong>: Separate syllabic signs (ka-la-am)</li>
                <li><strong>Periods</strong>: Separate word elements (lugal.maḫ)</li>
                <li><strong>[ ]</strong>: Restored (damaged) text</li>
                <li><strong>&lt; &gt;</strong>: Omitted by scribe, added by editor</li>
                <li><strong>(( ))</strong>: Uncertain reading</li>
            </ul>

            <h3>Common Abbreviations</h3>
            <ul>
                <li><strong>ARM</strong> = Archives Royales de Mari</li>
                <li><strong>VAB</strong> = Vorderasiatische Bibliothek</li>
                <li><strong>CAD</strong> = Chicago Assyrian Dictionary</li>
                <li><strong>ePSD</strong> = Electronic Pennsylvania Sumerian Dictionary</li>
                <li><strong>ORACC</strong> = Open Richly Annotated Cuneiform Corpus</li>
            </ul>
        </section>

        <!-- Back to Library -->
        <footer style="margin-top: 4rem; padding-top: 2rem; border-top: 1px solid var(--color-border);">
            <a href="/library/" class="btn">← Back to Dictionary Browser</a>
        </footer>
    </div>

    <script src="/assets/js/modules/educational-help.js"></script>
</body>
</html>
