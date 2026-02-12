<?php
/**
 * Dictionary Word Detail Page
 *
 * NOTE: This page now redirects to the unified dictionary browser.
 * The 3-column browser at /dictionary/ handles word detail display.
 *
 * Legacy URL: /dictionary/word.php?id=X
 * New URL: /dictionary/?word=X
 */

$entry_id = $_GET['id'] ?? null;

// Redirect to new unified browser URL
if ($entry_id) {
    header('Location: /dictionary/?word=' . urlencode($entry_id), true, 301);
    exit;
} else {
    header('Location: /dictionary/', true, 301);
    exit;
}

// ============================================================================
// LEGACY CODE BELOW - Kept for reference, no longer executed
// ============================================================================

require_once __DIR__ . '/../includes/db.php';

if (!$entry_id) {
    header('Location: /dictionary/');
    exit;
}

// Fetch entry data
$db = getDB();

// Main entry
$stmt = $db->prepare("
    SELECT
        ge.entry_id,
        ge.headword,
        ge.citation_form,
        ge.guide_word,
        ge.pos,
        ge.language,
        ge.icount,
        ge.normalized_headword,
        ge.semantic_category
    FROM glossary_entries ge
    WHERE ge.entry_id = :entry_id
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();
$entry = $result->fetchArray(SQLITE3_ASSOC);

if (!$entry) {
    http_response_code(404);
    $pageTitle = 'Word Not Found';
    require_once __DIR__ . '/../includes/header.php';
    echo '<main class="container"><h1>Word Not Found</h1><p>The requested dictionary entry does not exist.</p></main>';
    require_once __DIR__ . '/../includes/footer.php';
    exit;
}

// Variant forms with frequencies
$stmt = $db->prepare("
    SELECT
        gf.form,
        gf.count as stored_count,
        COUNT(DISTINCT l.p_number) as occurrence_count
    FROM glossary_forms gf
    LEFT JOIN lemmas l ON (
        gf.form = l.form
        AND l.cf = :cf
        AND l.lang = :lang
    )
    WHERE gf.entry_id = :entry_id
    GROUP BY gf.form
    ORDER BY occurrence_count DESC, stored_count DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
$stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
$result = $stmt->execute();

$variants = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $variants[] = [
        'form' => $row['form'],
        'count' => (int)$row['occurrence_count'] ?: (int)$row['stored_count']
    ];
}

// Signs used in this word
$stmt = $db->prepare("
    SELECT
        swu.sign_id,
        swu.sign_value,
        swu.value_type,
        swu.usage_count,
        s.utf8,
        s.sign_type
    FROM sign_word_usage swu
    JOIN signs s ON swu.sign_id = s.sign_id
    WHERE swu.entry_id = :entry_id
    ORDER BY swu.usage_count DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$signs = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $signs[] = $row;
}

// Polysemic senses
$stmt = $db->prepare("
    SELECT
        sense_number,
        guide_word,
        definition,
        usage_context,
        semantic_category,
        frequency_percentage
    FROM glossary_senses
    WHERE entry_id = :entry_id
    ORDER BY sense_number
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$senses = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $senses[] = $row;
}

// Sample attestations
$stmt = $db->prepare("
    SELECT DISTINCT
        l.p_number,
        l.form,
        a.period,
        a.provenience,
        a.genre
    FROM lemmas l
    LEFT JOIN artifacts a ON l.p_number = a.p_number
    WHERE l.cf = :cf
      AND l.lang = :lang
    ORDER BY l.p_number
    LIMIT 10
");
$stmt->bindValue(':cf', $entry['citation_form'], SQLITE3_TEXT);
$stmt->bindValue(':lang', $entry['language'], SQLITE3_TEXT);
$result = $stmt->execute();

$attestations = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $attestations[] = $row;
}

// CAD entry (for Akkadian)
$cad = null;
if (strpos($entry['language'], 'akk') === 0) {
    $stmt = $db->prepare("
        SELECT
            volume,
            page_start,
            page_end,
            etymology,
            semantic_notes,
            pdf_url,
            extraction_quality,
            human_verified
        FROM cad_entries
        WHERE oracc_entry_id = :entry_id
        LIMIT 1
    ");
    $stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    $cad = $result->fetchArray(SQLITE3_ASSOC);
}

// Related words
$stmt = $db->prepare("
    SELECT
        gr.relationship_type,
        gr.notes,
        ge2.entry_id,
        ge2.headword,
        ge2.guide_word,
        ge2.pos,
        ge2.language,
        ge2.icount
    FROM glossary_relationships gr
    JOIN glossary_entries ge2 ON gr.to_entry_id = ge2.entry_id
    WHERE gr.from_entry_id = :entry_id
    ORDER BY gr.relationship_type, ge2.icount DESC
");
$stmt->bindValue(':entry_id', $entry_id, SQLITE3_TEXT);
$result = $stmt->execute();

$related = [
    'translations' => [],
    'synonyms' => [],
    'cognates' => [],
    'see_also' => []
];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $type = $row['relationship_type'];
    if (isset($related[$type])) {
        $related[$type][] = $row;
    } else {
        $related['see_also'][] = $row;
    }
}

// Language labels
$languageLabels = [
    'sux' => 'Sumerian',
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Standard Babylonian',
    'akk-x-oldbab' => 'Old Babylonian',
    'akk-x-neoass' => 'Neo-Assyrian',
    'qpn' => 'Personal Name',
    'qpn-x-places' => 'Place Name'
];

// POS labels
$posLabels = [
    'N' => 'Noun',
    'V' => 'Verb',
    'AJ' => 'Adjective',
    'AV' => 'Adverb',
    'NU' => 'Number',
    'PRP' => 'Preposition',
    'CNJ' => 'Conjunction',
    'PN' => 'Personal Name',
    'GN' => 'Geographic Name',
    'DN' => 'Divine Name',
    'RN' => 'Royal Name'
];

$languageLabel = $languageLabels[$entry['language']] ?? $entry['language'];
$posLabel = $posLabels[$entry['pos']] ?? $entry['pos'];

$pageTitle = $entry['headword'] . ($entry['guide_word'] ? " [{$entry['guide_word']}]" : '');

require_once __DIR__ . '/../includes/header.php';
?>
<!-- Word Detail Styles -->
<link rel="stylesheet" href="/assets/css/tablet/metadata.css">
<link rel="stylesheet" href="/assets/css/dictionary/word-detail.css">
<link rel="stylesheet" href="/assets/css/components/badges.css">

<div class="word-detail-page">
<main class="container">
    <div class="container-inner">
        <!-- Page Header -->
        <div class="page-header word-header">
            <div class="page-header-main">
                <div class="page-header-title">
                    <a href="/dictionary/" class="back-link">← Back to Dictionary</a>
                    <h1><?= htmlspecialchars($entry['headword']) ?><?php if ($entry['guide_word']): ?><span class="guide-word">[<?= htmlspecialchars($entry['guide_word']) ?>]</span><?php endif; ?></h1>
                </div>
                <div class="page-header-actions">
                    <span class="badge badge--pos"><?= htmlspecialchars($posLabel) ?></span>
                    <span class="badge badge--language"><?= htmlspecialchars($languageLabel) ?></span>
                    <span class="badge badge--frequency"><?= number_format($entry['icount']) ?> attestations</span>
                </div>
            </div>
        </div>

        <!-- Core Metadata -->
        <div class="word-meta tablet-meta">
            <dl class="tablet-meta__row">
                <div class="meta-item">
                    <dt>Citation Form</dt>
                    <dd><?= htmlspecialchars($entry['citation_form']) ?></dd>
                </div>
                <?php if ($entry['guide_word']): ?>
                <div class="meta-item">
                    <dt>Guide Word</dt>
                    <dd><?= htmlspecialchars($entry['guide_word']) ?></dd>
                </div>
                <?php endif; ?>
                <div class="meta-item">
                    <dt>Part of Speech</dt>
                    <dd><?= htmlspecialchars($posLabel) ?></dd>
                </div>
                <div class="meta-item">
                    <dt>Language</dt>
                    <dd><?= htmlspecialchars($languageLabel) ?></dd>
                </div>
                <div class="meta-item">
                    <dt>Corpus Frequency</dt>
                    <dd><?= number_format($entry['icount']) ?> occurrences</dd>
                </div>
            </dl>
        </div>

        <!-- Meanings (Polysemic Senses) -->
        <?php if (!empty($senses)): ?>
        <section class="word-section">
            <h2>Meanings</h2>
            <ol class="meanings-list">
                <?php foreach ($senses as $sense): ?>
                <li class="meaning">
                    <div class="meaning__header">
                        <strong><?= htmlspecialchars($sense['guide_word']) ?></strong>
                        <?php if ($sense['frequency_percentage']): ?>
                        <span class="meaning__usage"><?= round($sense['frequency_percentage']) ?>% of uses</span>
                        <?php endif; ?>
                    </div>
                    <?php if ($sense['definition']): ?>
                    <p class="meaning__definition"><?= htmlspecialchars($sense['definition']) ?></p>
                    <?php endif; ?>
                    <?php if ($sense['usage_context']): ?>
                    <p class="meaning__context"><?= htmlspecialchars($sense['usage_context']) ?></p>
                    <?php endif; ?>
                </li>
                <?php endforeach; ?>
            </ol>
        </section>
        <?php endif; ?>

        <!-- Attested Forms -->
        <?php if (!empty($variants)): ?>
        <section class="word-section">
            <h2>Attested Forms</h2>
            <?php
            $maxCount = max(array_column($variants, 'count'));
            ?>
            <div class="variants-chart">
                <?php foreach ($variants as $variant): ?>
                <?php $percentage = $maxCount > 0 ? ($variant['count'] / $maxCount) * 100 : 0; ?>
                <div class="variant-bar">
                    <span class="variant-form"><?= htmlspecialchars($variant['form']) ?></span>
                    <div class="variant-frequency-container">
                        <div class="variant-frequency" style="width: <?= $percentage ?>%"></div>
                    </div>
                    <span class="variant-count"><?= $variant['count'] ?> times</span>
                </div>
                <?php endforeach; ?>
            </div>
        </section>
        <?php endif; ?>

        <!-- Cuneiform Signs -->
        <?php if (!empty($signs)): ?>
        <section class="word-section">
            <h2>Cuneiform Signs</h2>
            <div class="sign-breakdown">
                <?php foreach ($signs as $sign): ?>
                <a href="/dictionary/signs/?sign=<?= urlencode($sign['sign_id']) ?>" class="sign-item">
                    <span class="sign-cuneiform"><?= $sign['utf8'] ?? '' ?></span>
                    <span class="sign-id"><?= htmlspecialchars($sign['sign_id']) ?></span>
                    <span class="sign-value"><?= htmlspecialchars($sign['sign_value']) ?></span>
                    <?php if ($sign['value_type']): ?>
                    <span class="sign-type"><?= htmlspecialchars($sign['value_type']) ?></span>
                    <?php endif; ?>
                </a>
                <?php endforeach; ?>
            </div>
        </section>
        <?php endif; ?>

        <!-- Related Words -->
        <?php
        $hasRelated = !empty($related['translations']) || !empty($related['synonyms']) ||
                      !empty($related['cognates']) || !empty($related['see_also']);
        ?>
        <?php if ($hasRelated): ?>
        <section class="word-section">
            <h2>Related Words</h2>

            <?php if (!empty($related['translations'])): ?>
            <div class="related-group">
                <h3>Bilingual Equivalents</h3>
                <ul class="related-list">
                    <?php foreach ($related['translations'] as $rel): ?>
                    <li>
                        <a href="/dictionary/word.php?id=<?= urlencode($rel['entry_id']) ?>" class="related-word">
                            <strong><?= htmlspecialchars($rel['headword']) ?></strong>
                            <?php if ($rel['guide_word']): ?>
                            <span class="guide-word">[<?= htmlspecialchars($rel['guide_word']) ?>]</span>
                            <?php endif; ?>
                            <span class="badge badge--language"><?= htmlspecialchars($languageLabels[$rel['language']] ?? $rel['language']) ?></span>
                        </a>
                        <?php if ($rel['notes']): ?>
                        <span class="related-notes"><?= htmlspecialchars($rel['notes']) ?></span>
                        <?php endif; ?>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>

            <?php if (!empty($related['synonyms'])): ?>
            <div class="related-group">
                <h3>Synonyms</h3>
                <ul class="related-list">
                    <?php foreach ($related['synonyms'] as $rel): ?>
                    <li>
                        <a href="/dictionary/word.php?id=<?= urlencode($rel['entry_id']) ?>" class="related-word">
                            <strong><?= htmlspecialchars($rel['headword']) ?></strong>
                            <?php if ($rel['guide_word']): ?>
                            <span class="guide-word">[<?= htmlspecialchars($rel['guide_word']) ?>]</span>
                            <?php endif; ?>
                        </a>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>

            <?php if (!empty($related['cognates'])): ?>
            <div class="related-group">
                <h3>Cognates</h3>
                <ul class="related-list">
                    <?php foreach ($related['cognates'] as $rel): ?>
                    <li>
                        <a href="/dictionary/word.php?id=<?= urlencode($rel['entry_id']) ?>" class="related-word">
                            <strong><?= htmlspecialchars($rel['headword']) ?></strong>
                            <span class="badge badge--language"><?= htmlspecialchars($languageLabels[$rel['language']] ?? $rel['language']) ?></span>
                        </a>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>

            <?php if (!empty($related['see_also'])): ?>
            <div class="related-group">
                <h3>See Also</h3>
                <ul class="related-list">
                    <?php foreach ($related['see_also'] as $rel): ?>
                    <li>
                        <a href="/dictionary/word.php?id=<?= urlencode($rel['entry_id']) ?>" class="related-word">
                            <strong><?= htmlspecialchars($rel['headword']) ?></strong>
                            <?php if ($rel['guide_word']): ?>
                            <span class="guide-word">[<?= htmlspecialchars($rel['guide_word']) ?>]</span>
                            <?php endif; ?>
                        </a>
                    </li>
                    <?php endforeach; ?>
                </ul>
            </div>
            <?php endif; ?>
        </section>
        <?php endif; ?>

        <!-- Corpus Examples -->
        <?php if (!empty($attestations)): ?>
        <section class="word-section">
            <h2>Corpus Examples</h2>
            <div class="examples-list">
                <?php foreach ($attestations as $att): ?>
                <div class="example-item">
                    <div class="example-header">
                        <a href="/tablets/detail.php?p=<?= urlencode($att['p_number']) ?>" class="p-number"><?= htmlspecialchars($att['p_number']) ?></a>
                        <?php if ($att['period'] || $att['provenience']): ?>
                        <span class="example-meta"><?= htmlspecialchars(implode(' · ', array_filter([$att['period'], $att['provenience']]))) ?></span>
                        <?php endif; ?>
                    </div>
                    <div class="example-content">
                        <span class="transliteration"><?= htmlspecialchars($att['form']) ?></span>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
            <p class="examples-footer">
                Showing <?= count($attestations) ?> of <?= number_format($entry['icount']) ?> attestations
            </p>
        </section>
        <?php endif; ?>

        <!-- CAD Reference -->
        <?php if ($cad): ?>
        <section class="word-section">
            <h2>Chicago Assyrian Dictionary</h2>
            <div class="cad-content">
                <div class="cad-header">
                    <span class="volume-badge">CAD <?= htmlspecialchars($cad['volume']) ?>, pp. <?= $cad['page_start'] ?><?= $cad['page_end'] ? "-{$cad['page_end']}" : '' ?></span>
                    <?php if ($cad['pdf_url']): ?>
                    <a href="<?= htmlspecialchars($cad['pdf_url']) ?>/page/<?= $cad['page_start'] ?>" target="_blank" class="pdf-link">View PDF →</a>
                    <?php endif; ?>
                    <?php if ($cad['human_verified']): ?>
                    <span class="verified-badge">✓ Verified</span>
                    <?php endif; ?>
                </div>
                <?php if ($cad['etymology']): ?>
                <div class="cad-etymology">
                    <strong>Etymology:</strong> <?= htmlspecialchars($cad['etymology']) ?>
                </div>
                <?php endif; ?>
                <?php if ($cad['semantic_notes']): ?>
                <div class="cad-notes"><?= htmlspecialchars($cad['semantic_notes']) ?></div>
                <?php endif; ?>
            </div>
        </section>
        <?php endif; ?>
    </div>
</main>
</div>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
