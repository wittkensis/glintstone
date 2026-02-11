<?php
/**
 * Library Word Detail API
 *
 * Returns comprehensive data for a single dictionary entry including:
 * - Base fields (headword, citation_form, guide_word, pos, language, icount)
 * - Variant forms with frequencies
 * - Related words (translations, synonyms, cognates)
 * - Sign breakdown
 * - Sample corpus attestations
 * - CAD references (if available)
 * - Polysemic senses (if available)
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\GlossaryRepository;
use function Glintstone\app;

$params = getRequestParams();
$entry_id = $params['entry_id'] ?? '';

if (empty($entry_id)) {
    JsonResponse::badRequest('Missing required parameter: entry_id');
}

$repo = app()->get(GlossaryRepository::class);
$db = $repo->db();

// Main entry data
$stmt = $db->prepare("
    SELECT
        ge.entry_id, ge.headword, ge.citation_form, ge.guide_word,
        ge.pos, ge.language, ge.icount, ge.normalized_headword, ge.semantic_category
    FROM glossary_entries ge
    WHERE ge.entry_id = :entry_id
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();
$entry = $result->fetchArray(SQLITE3_ASSOC);

if (!$entry) {
    JsonResponse::notFound('Entry not found');
}

// Language family matching
$langBase = explode('-x-', $entry['language'])[0];
$langFamily = $langBase . '-x-%';

// Variant forms with frequencies
$stmt = $db->prepare("
    SELECT
        gf.form,
        gf.count as stored_count,
        COALESCE(COUNT(DISTINCT l.p_number), 0) as occurrence_count,
        COALESCE(gf.count, 0) as sort_count
    FROM glossary_forms gf
    LEFT JOIN lemmas l ON (
        gf.form = l.form
        AND l.cf = :cf
        AND (l.lang = :lang OR l.lang = :lang_base OR l.lang LIKE :lang_family)
    )
    WHERE gf.entry_id = :entry_id
    GROUP BY gf.form
    ORDER BY occurrence_count DESC, sort_count DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
$stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
$stmt->bindValue(':lang_base', $langBase, SQLITE3_TEXT);
$stmt->bindValue(':lang_family', $langFamily, SQLITE3_TEXT);
$result = $stmt->execute();

$variants = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $variants[] = [
        'form' => $row['form'],
        'count' => (int)$row['occurrence_count'] ?: (int)$row['stored_count']
    ];
}

// Related words
$stmt = $db->prepare("
    SELECT
        gr.relationship_type, gr.notes, gr.confidence,
        ge2.entry_id, ge2.headword, ge2.guide_word, ge2.pos, ge2.language, ge2.icount
    FROM glossary_relationships gr
    JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
    WHERE gr.from_entry_id = :entry_id
    ORDER BY gr.relationship_type, ge2.icount DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$related_words = [
    'translations' => [], 'synonyms' => [], 'antonyms' => [],
    'cognates' => [], 'see_also' => []
];

while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $related_entry = [
        'entry_id' => $row['entry_id'],
        'headword' => $row['headword'],
        'guide_word' => $row['guide_word'],
        'pos' => $row['pos'],
        'language' => $row['language'],
        'icount' => (int)$row['icount'],
        'notes' => $row['notes'],
        'confidence' => $row['confidence']
    ];
    $type = $row['relationship_type'];
    if (isset($related_words[$type])) {
        $related_words[$type][] = $related_entry;
    } else {
        $related_words['see_also'][] = $related_entry;
    }
}

// Signs used in this word
$stmt = $db->prepare("
    SELECT swu.sign_id, swu.sign_value, swu.value_type, swu.usage_count, s.utf8, s.sign_type
    FROM sign_word_usage swu
    JOIN signs s ON swu.sign_id = s.sign_id
    WHERE swu.entry_id = :entry_id
    ORDER BY swu.usage_count DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$signs = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $signs[] = [
        'sign_id' => $row['sign_id'],
        'sign_value' => $row['sign_value'],
        'value_type' => $row['value_type'],
        'usage_count' => (int)$row['usage_count'],
        'utf8' => $row['utf8'],
        'sign_type' => $row['sign_type']
    ];
}

// Polysemic senses
$stmt = $db->prepare("
    SELECT sense_number, guide_word, definition, usage_context,
           semantic_category, frequency_percentage, example_lemma_ids
    FROM glossary_senses
    WHERE entry_id = :entry_id
    ORDER BY sense_number
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$senses = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $senses[] = [
        'sense_number' => (int)$row['sense_number'],
        'guide_word' => $row['guide_word'],
        'definition' => $row['definition'],
        'usage_context' => $row['usage_context'],
        'semantic_category' => $row['semantic_category'],
        'frequency_percentage' => $row['frequency_percentage'] ? (float)$row['frequency_percentage'] : null,
        'example_lemma_ids' => $row['example_lemma_ids'] ? json_decode($row['example_lemma_ids'], true) : []
    ];
}

// All corpus attestations
$stmt = $db->prepare("
    SELECT DISTINCT l.p_number, l.form, a.period, a.provenience, a.genre
    FROM lemmas l
    LEFT JOIN artifacts a ON l.p_number = a.p_number
    WHERE l.cf = :cf
      AND (l.lang = :lang OR l.lang = :lang_base OR l.lang LIKE :lang_family)
    ORDER BY l.p_number
");
$stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
$stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
$stmt->bindValue(':lang_base', $langBase, SQLITE3_TEXT);
$stmt->bindValue(':lang_family', $langFamily, SQLITE3_TEXT);
$result = $stmt->execute();

$attestations = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $attestations[] = [
        'p_number' => $row['p_number'],
        'form' => $row['form'],
        'period' => $row['period'],
        'provenience' => $row['provenience'],
        'genre' => $row['genre']
    ];
}

// CAD entry (Akkadian words only)
$cad_entry = null;
if (strpos($entry['language'], 'akk') === 0) {
    $stmt = $db->prepare("
        SELECT volume, page_start, page_end, etymology, semantic_notes,
               pdf_url, extraction_quality, human_verified
        FROM cad_entries
        WHERE oracc_entry_id = :entry_id
        LIMIT 1
    ");
    $stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    $cad_row = $result->fetchArray(SQLITE3_ASSOC);

    if ($cad_row) {
        $cad_entry = [
            'volume' => $cad_row['volume'],
            'page_start' => (int)$cad_row['page_start'],
            'page_end' => $cad_row['page_end'] ? (int)$cad_row['page_end'] : null,
            'etymology' => $cad_row['etymology'],
            'semantic_notes' => $cad_row['semantic_notes'],
            'pdf_url' => $cad_row['pdf_url'],
            'extraction_quality' => $cad_row['extraction_quality'] ? (float)$cad_row['extraction_quality'] : null,
            'human_verified' => (bool)$cad_row['human_verified']
        ];
    }
}

// Semantic fields
$stmt = $db->prepare("
    SELECT sf.id, sf.name, sf.description
    FROM glossary_semantic_fields gsf
    JOIN semantic_fields sf ON gsf.field_id = sf.id
    WHERE gsf.entry_id = :entry_id
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$semantic_fields = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $semantic_fields[] = [
        'id' => (int)$row['id'],
        'name' => $row['name'],
        'description' => $row['description']
    ];
}

// Position in frequency sort
$stmt = $db->prepare("
    SELECT COUNT(*) as position FROM glossary_entries
    WHERE icount > :current_icount
       OR (icount = :current_icount AND citation_form < :current_citation_form)
");
$stmt->bindValue(':current_icount', $entry['icount'], SQLITE3_INTEGER);
$stmt->bindValue(':current_citation_form', $entry['citation_form'], SQLITE3_TEXT);
$result = $stmt->execute();
$position_frequency = (int)$result->fetchArray(SQLITE3_ASSOC)['position'];

// Position in alpha sort
$stmt = $db->prepare("
    SELECT COUNT(*) as position FROM glossary_entries
    WHERE citation_form < :current_citation_form
       OR (citation_form = :current_citation_form AND headword < :current_headword)
");
$stmt->bindValue(':current_citation_form', $entry['citation_form'], SQLITE3_TEXT);
$stmt->bindValue(':current_headword', $entry['headword'], SQLITE3_TEXT);
$result = $stmt->execute();
$position_alpha = (int)$result->fetchArray(SQLITE3_ASSOC)['position'];

JsonResponse::success([
    'entry' => [
        'entry_id' => $entry['entry_id'],
        'headword' => $entry['headword'],
        'citation_form' => $entry['citation_form'],
        'guide_word' => $entry['guide_word'],
        'pos' => $entry['pos'],
        'language' => $entry['language'],
        'icount' => (int)$entry['icount'],
        'normalized_headword' => $entry['normalized_headword'],
        'semantic_category' => $entry['semantic_category']
    ],
    'position' => [
        'frequency' => $position_frequency,
        'alpha' => $position_alpha
    ],
    'variants' => $variants,
    'related_words' => $related_words,
    'signs' => $signs,
    'senses' => $senses,
    'attestations' => [
        'sample' => $attestations,
        'total_count' => (int)$entry['icount'],
        'showing' => count($attestations)
    ],
    'cad' => $cad_entry,
    'semantic_fields' => $semantic_fields
]);
