<?php
/**
 * Tablet search page
 */

require_once __DIR__ . '/../includes/db.php';

$query = trim($_GET['q'] ?? '');
$pageTitle = $query ? "Search: $query" : "Search";

$results = [];
$totalResults = 0;

if ($query) {
    $db = getDB();

    // Search artifacts by P-number, designation, museum number
    $sql = "
        SELECT a.*, ps.quality_score, ps.has_image, ps.has_atf, ps.has_lemmas
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE a.p_number LIKE :q
           OR a.designation LIKE :q
           OR a.museum_no LIKE :q
           OR a.excavation_no LIKE :q
           OR a.provenience LIKE :q
           OR a.genre LIKE :q
        ORDER BY
            CASE WHEN a.p_number LIKE :exact THEN 0 ELSE 1 END,
            ps.quality_score DESC
        LIMIT 100
    ";

    $stmt = $db->prepare($sql);
    $searchTerm = "%$query%";
    $exactTerm = $query;
    $stmt->bindValue(':q', $searchTerm, SQLITE3_TEXT);
    $stmt->bindValue(':exact', $exactTerm, SQLITE3_TEXT);
    $result = $stmt->execute();

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $results[] = $row;
    }
    $totalResults = count($results);

    // Also search glossary for dictionary matches
    $glossaryMatches = searchGlossary($query, null, 5);
}

require_once __DIR__ . '/../includes/header.php';
?>
<link rel="stylesheet" href="/assets/css/pages/search.css">
<link rel="stylesheet" href="/assets/css/components/pagination.css">

<main class="container">
    <div class="search-header">
        <h1>Search</h1>
        <form action="" method="GET" class="search-form">
            <div class="search-box-large">
                <input type="text" name="q" value="<?= htmlspecialchars($query) ?>"
                       placeholder="Search tablets, signs, or words..." autofocus>
                <button type="submit">Search</button>
            </div>
        </form>
    </div>

    <?php if ($query): ?>
        <div class="search-results">
            <p class="results-count">
                Found <?= $totalResults ?> tablet<?= $totalResults !== 1 ? 's' : '' ?>
                matching "<?= htmlspecialchars($query) ?>"
            </p>

            <?php if (!empty($glossaryMatches)): ?>
            <section class="glossary-matches">
                <h3>Dictionary Matches</h3>
                <div class="glossary-grid">
                    <?php foreach ($glossaryMatches as $entry): ?>
                    <div class="glossary-match">
                        <strong><?= htmlspecialchars($entry['headword']) ?></strong>
                        <?php if ($entry['guide_word']): ?>
                            <span class="guide">"<?= htmlspecialchars($entry['guide_word']) ?>"</span>
                        <?php endif; ?>
                        <span class="lang"><?= htmlspecialchars($entry['language']) ?></span>
                    </div>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php endif; ?>

            <?php if ($results): ?>
            <section class="tablet-results">
                <h3>Tablets</h3>
                <div class="tablet-grid">
                    <?php foreach ($results as $tablet): ?>
                    <a href="detail.php?p=<?= urlencode($tablet['p_number']) ?>" class="tablet-card">
                        <div class="tablet-thumbnail">
                            <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=200"
                                 alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
                                 loading="lazy"
                                 onerror="this.parentElement.classList.add('no-image')">
                            <div class="thumbnail-placeholder">
                                <span class="cuneiform-icon">𒀭</span>
                            </div>
                        </div>
                        <div class="tablet-info">
                            <div class="tablet-header">
                                <span class="p-number"><?= htmlspecialchars($tablet['p_number']) ?></span>
                                <span class="quality-score" title="Quality Score">
                                    <?= round(($tablet['quality_score'] ?? 0) * 100) ?>%
                                </span>
                            </div>
                            <div class="tablet-designation">
                                <?= htmlspecialchars($tablet['designation'] ?? 'Unknown') ?>
                            </div>
                            <div class="tablet-meta">
                                <?php if ($tablet['museum_no']): ?>
                                    <span><?= htmlspecialchars($tablet['museum_no']) ?></span>
                                <?php endif; ?>
                                <?php if ($tablet['provenience']): ?>
                                    <span><?= htmlspecialchars($tablet['provenience']) ?></span>
                                <?php endif; ?>
                                <?php if ($tablet['period']): ?>
                                    <span><?= htmlspecialchars($tablet['period']) ?></span>
                                <?php endif; ?>
                            </div>
                            <div class="pipeline-status">
                                <span class="status-dot <?= $tablet['has_image'] ? 'complete' : 'missing' ?>" title="Image"></span>
                                <span class="status-dot <?= $tablet['has_atf'] ? 'complete' : 'missing' ?>" title="ATF"></span>
                                <span class="status-dot <?= $tablet['has_lemmas'] ? 'complete' : 'missing' ?>" title="Lemmas"></span>
                                <span class="status-dot missing" title="Translation"></span>
                            </div>
                        </div>
                    </a>
                    <?php endforeach; ?>
                </div>
            </section>
            <?php elseif ($query): ?>
            <p class="no-results">No tablets found. Try a different search term.</p>
            <?php endif; ?>
        </div>
    <?php else: ?>
        <div class="search-tips">
            <h3>Search Tips</h3>
            <ul>
                <li><strong>P-number:</strong> Search by CDLI identifier (e.g., "P000001")</li>
                <li><strong>Museum number:</strong> Search by museum accession (e.g., "BM 12345")</li>
                <li><strong>Provenience:</strong> Search by find location (e.g., "Nippur", "Ur")</li>
                <li><strong>Genre:</strong> Search by text type (e.g., "Lexical", "Administrative")</li>
                <li><strong>Word:</strong> Search for Sumerian or Akkadian terms (e.g., "lugal", "šarru")</li>
            </ul>
        </div>
    <?php endif; ?>
</main>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
