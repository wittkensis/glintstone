<?php
/**
 * Tablet Browser for Collections
 * Full-page browser for selecting and adding tablets to a collection
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';
require_once __DIR__ . '/../includes/helpers/filters.php';

// Get collection ID
$collectionId = (int)($_GET['collection_id'] ?? 0);

if ($collectionId <= 0) {
    header('Location: /collections/');
    exit;
}

// Get collection metadata
$collection = getCollection($collectionId);

if (!$collection) {
    header('Location: /collections/');
    exit;
}

// Get filter parameters (same as tablets/list.php)
$languages = isset($_GET['lang']) ? (is_array($_GET['lang']) ? $_GET['lang'] : [$_GET['lang']]) : [];
$periods = isset($_GET['period']) ? (is_array($_GET['period']) ? $_GET['period'] : [$_GET['period']]) : [];
$sites = isset($_GET['site']) ? (is_array($_GET['site']) ? $_GET['site'] : [$_GET['site']]) : [];
$genres = isset($_GET['genre']) ? (is_array($_GET['genre']) ? $_GET['genre'] : [$_GET['genre']]) : [];
$pipeline = $_GET['pipeline'] ?? null;
$search = trim($_GET['search'] ?? '');

// Build active filters array
$activeFilters = [];
if (!empty($search)) {
    $activeFilters[] = ['type' => 'search', 'value' => $search];
}
$activeFilters = array_merge(
    $activeFilters,
    array_map(fn($v) => ['type' => 'lang', 'value' => $v], $languages),
    array_map(fn($v) => ['type' => 'period', 'value' => $v], $periods),
    array_map(fn($v) => ['type' => 'site', 'value' => $v], $sites),
    array_map(fn($v) => ['type' => 'genre', 'value' => $v], $genres)
);
if ($pipeline) {
    $activeFilters[] = ['type' => 'pipeline', 'value' => $pipeline];
}

// Pagination with configurable per-page (default 24, max 200)
$page = max(1, (int)($_GET['page'] ?? 1));
$perPage = isset($_GET['per_page']) ? min(200, max(12, (int)$_GET['per_page'])) : 24;
$tabletsPerPage = $perPage;
$offset = ($page - 1) * $tabletsPerPage;

// Build SQL query with filters
$db = getDB();

// Add LEFT JOIN with inscriptions if search is present
$inscriptionJoin = !empty($search) ? "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1" : "";

$sql = "SELECT DISTINCT a.*, ps.has_image, ps.has_ocr, ps.ocr_confidence, ps.has_atf,
               ps.atf_source, ps.has_lemmas, ps.lemma_coverage, ps.has_translation,
               ps.has_sign_annotations, ps.quality_score
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        $inscriptionJoin
        WHERE 1=1";

$params = [];

// Apply filters (same logic as list.php)
if (!empty($languages)) {
    $langConditions = [];
    foreach ($languages as $i => $lang) {
        $langConditions[] = "a.language LIKE :lang{$i}";
        $params[":lang{$i}"] = '%' . $lang . '%';
    }
    $sql .= " AND (" . implode(' OR ', $langConditions) . ")";
}

if (!empty($periods)) {
    $periodConditions = [];
    foreach ($periods as $i => $period) {
        $periodConditions[] = "a.period = :period{$i}";
        $params[":period{$i}"] = $period;
    }
    $sql .= " AND (" . implode(' OR ', $periodConditions) . ")";
}

if (!empty($sites)) {
    $siteConditions = [];
    foreach ($sites as $i => $site) {
        $siteConditions[] = "a.provenience LIKE :site{$i}";
        $params[":site{$i}"] = '%' . $site . '%';
    }
    $sql .= " AND (" . implode(' OR ', $siteConditions) . ")";
}

if (!empty($genres)) {
    $genreConditions = [];
    foreach ($genres as $i => $genre) {
        $genreConditions[] = "a.genre LIKE :genre{$i}";
        $params[":genre{$i}"] = '%' . $genre . '%';
    }
    $sql .= " AND (" . implode(' OR ', $genreConditions) . ")";
}

if ($pipeline) {
    switch ($pipeline) {
        case 'complete':
            $sql .= " AND ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
            break;
        case 'has_image':
            $sql .= " AND ps.has_image = 1";
            break;
        case 'has_translation':
            $sql .= " AND ps.has_translation = 1";
            break;
        case 'any_digitization':
            $sql .= " AND (ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
            break;
        case 'human_transcription':
            $sql .= " AND ps.has_atf = 1";
            break;
        case 'machine_ocr':
            $sql .= " AND ps.has_sign_annotations = 1";
            break;
        case 'no_digitization':
            $sql .= " AND (ps.has_atf = 0 OR ps.has_atf IS NULL) AND (ps.has_sign_annotations = 0 OR ps.has_sign_annotations IS NULL)";
            break;
    }
}

// Search filter - searches p_number, designation, and transliteration text
// Supports OR operator: "P000001 || P000025 || P010663"
if (!empty($search)) {
    $searchTerms = array_map('trim', explode('||', $search));

    if (count($searchTerms) > 1) {
        // Multiple terms - build OR condition for each
        $searchConditions = [];
        foreach ($searchTerms as $i => $term) {
            if (!empty($term)) {
                $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                $params[":search{$i}"] = '%' . $term . '%';
            }
        }
        if (!empty($searchConditions)) {
            $sql .= " AND (" . implode(' OR ', $searchConditions) . ")";
        }
    } else {
        // Single term - use simple search
        $sql .= " AND (a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
        $params[':search'] = '%' . $search . '%';
    }
}

// Get total count
$countSql = "SELECT COUNT(*) as total FROM ($sql) AS filtered";
$countStmt = $db->prepare($countSql);
foreach ($params as $key => $value) {
    $countStmt->bindValue($key, $value, is_int($value) ? SQLITE3_INTEGER : SQLITE3_TEXT);
}
$countResult = $countStmt->execute();
$totalTablets = (int)$countResult->fetchArray(SQLITE3_ASSOC)['total'];
$totalPages = (int)ceil($totalTablets / $tabletsPerPage);

// Get paginated tablets
$sql .= " ORDER BY a.p_number LIMIT :limit OFFSET :offset";
$stmt = $db->prepare($sql);
foreach ($params as $key => $value) {
    $stmt->bindValue($key, $value, is_int($value) ? SQLITE3_INTEGER : SQLITE3_TEXT);
}
$stmt->bindValue(':limit', $tabletsPerPage, SQLITE3_INTEGER);
$stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
$tablets = $stmt->execute();

// Get filter stats (use filtered versions if any filters are active)
// NOTE: Skip expensive filtered stats when search is active to prevent timeouts
$hasActiveFilters = !empty($languages) || !empty($periods) || !empty($sites) || !empty($genres) || !empty($pipeline);
$hasSearch = !empty($search);

if ($hasActiveFilters && !$hasSearch) {
    // Use filtered stats only when we have filters but NO search
    $filterContext = [
        'languages' => $languages,
        'periods' => $periods,
        'sites' => $sites,
        'genres' => $genres,
        'pipeline' => $pipeline,
        'search' => ''
    ];
    $languageStats = getFilteredLanguageStats($filterContext);
    $periodStats = getFilteredPeriodStats($filterContext);
    $provenienceStats = getFilteredProvenienceStats($filterContext);
    $genreStats = getFilteredGenreStats($filterContext);
} else {
    // Use base stats when no filters OR when search is active
    // (filtered stats with search are too expensive due to inscription joins + LIKE patterns)
    $languageStats = getLanguageStats();
    $periodStats = getPeriodStats();
    $provenienceStats = getProvenienceStats();
    $genreStats = getGenreStats();
}

$pageTitle = 'Add Tablets to ' . htmlspecialchars($collection['name']);

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/components/filter-sidebar.css">
<link rel="stylesheet" href="/assets/css/components/filter-active.css">
<link rel="stylesheet" href="/assets/css/components/cards-overlay.css">
<link rel="stylesheet" href="/assets/css/components/cards-selectable.css">
<link rel="stylesheet" href="/assets/css/components/pagination.css">
<link rel="stylesheet" href="/assets/css/components/browser.css">

<main class="browser-page">
    <div class="browser-header">
        <div class="browser-title">
            <h1>Add Tablets to <?= htmlspecialchars($collection['name']) ?></h1>
        </div>

        <div class="header-controls">
            <button type="button" id="select-all" class="btn-ghost">Select All</button>
            <button type="button" id="clear-selection" class="btn-ghost">Clear Selection</button>
            <span class="selection-count">0 selected</span>
            <button type="submit" form="add-tablets-form" id="add-to-collection-btn" class="btn-primary" disabled>Add to Collection</button>
            <a href="/collections/detail.php?id=<?= $collectionId ?>" class="btn-secondary">Cancel</a>
        </div>
    </div>

    <div class="page-with-sidebar">
        <?php
        // Set up filter sidebar variables
        $clearAllUrl = "browser.php?collection_id=$collectionId";
        include __DIR__ . '/../includes/components/filter-sidebar.php';
        ?>

        <div class="main-content">
            <!-- Active Filters -->
            <?php if (!empty($activeFilters)): ?>
            <div class="active-filters">
                <?php foreach ($activeFilters as $filter): ?>
                <a href="<?= htmlspecialchars(buildFilterUrl([], [$filter['type'] => $filter['value']]) . "&collection_id=$collectionId") ?>" class="filter-chip">
                    <?= htmlspecialchars($filter['value']) ?>
                    <span class="chip-remove">×</span>
                </a>
                <?php endforeach; ?>
            </div>
            <?php endif; ?>

            <!-- Results Count and Per-Page Selector -->
            <div class="results-toolbar">
                <div class="results-info">
                    Showing <?= number_format($totalTablets) ?> tablets
                </div>
                <div class="per-page-selector">
                    <label for="per-page">Show:</label>
                    <select id="per-page" name="per_page" onchange="updatePerPage(this.value)">
                        <option value="12" <?= $perPage === 12 ? 'selected' : '' ?>>12</option>
                        <option value="24" <?= $perPage === 24 ? 'selected' : '' ?>>24</option>
                        <option value="48" <?= $perPage === 48 ? 'selected' : '' ?>>48</option>
                        <option value="96" <?= $perPage === 96 ? 'selected' : '' ?>>96</option>
                        <option value="200" <?= $perPage === 200 ? 'selected' : '' ?>>200</option>
                    </select>
                    <span class="per-page-label">per page</span>
                </div>
            </div>

            <!-- Tablet Grid with Selection -->
            <form id="add-tablets-form" method="POST" action="/collections/add-tablets.php">
                <input type="hidden" name="collection_id" value="<?= $collectionId ?>">

                <div class="tablet-grid">
                    <?php
                    $selectable = true; // Enable checkboxes on all cards
                    while ($tablet = $tablets->fetchArray(SQLITE3_ASSOC)):
                    ?>
                        <?php include __DIR__ . '/../includes/components/tablet-card.php'; ?>
                    <?php endwhile; ?>
                </div>

                <?php if ($totalPages > 1): ?>
                <nav class="pagination">
                    <?php if ($page > 1): ?>
                        <a href="?collection_id=<?= $collectionId ?>&page=<?= $page - 1 ?><?= !empty($activeFilters) ? '&' . http_build_query($_GET) : '' ?>" class="pagination-link">Previous</a>
                    <?php endif; ?>

                    <?php for ($i = 1; $i <= min($totalPages, 10); $i++): ?>
                        <?php if ($i === $page): ?>
                            <span class="pagination-link active"><?= $i ?></span>
                        <?php else: ?>
                            <a href="?collection_id=<?= $collectionId ?>&page=<?= $i ?><?= !empty($activeFilters) ? '&' . http_build_query($_GET) : '' ?>" class="pagination-link"><?= $i ?></a>
                        <?php endif; ?>
                    <?php endfor; ?>

                    <?php if ($page < $totalPages): ?>
                        <a href="?collection_id=<?= $collectionId ?>&page=<?= $page + 1 ?><?= !empty($activeFilters) ? '&' . http_build_query($_GET) : '' ?>" class="pagination-link">Next</a>
                    <?php endif; ?>
                </nav>
                <?php endif; ?>
            </form>
        </div>
    </div>
</main>

<script>
/**
 * Update per-page parameter and reload
 */
function updatePerPage(perPage) {
    const url = new URL(window.location.href);
    url.searchParams.set('per_page', perPage);
    url.searchParams.set('page', '1'); // Reset to first page when changing per-page
    window.location.href = url.toString();
}
</script>

<script src="/assets/js/filters.js"></script>
<script src="/assets/js/tablet-browser.js"></script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
