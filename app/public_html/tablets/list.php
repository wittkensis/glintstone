<?php
/**
 * Tablet list page with left sidebar filters
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';
require_once __DIR__ . '/../includes/helpers/filters.php';

$pageTitle = 'Tablets';

// Get filter parameters (support multiple selections via arrays)
$languages = isset($_GET['lang']) ? (is_array($_GET['lang']) ? $_GET['lang'] : [$_GET['lang']]) : [];
$periods = isset($_GET['period']) ? (is_array($_GET['period']) ? $_GET['period'] : [$_GET['period']]) : [];
$sites = isset($_GET['site']) ? (is_array($_GET['site']) ? $_GET['site'] : [$_GET['site']]) : [];
$genres = isset($_GET['genre']) ? (is_array($_GET['genre']) ? $_GET['genre'] : [$_GET['genre']]) : [];
$pipeline = $_GET['pipeline'] ?? null;

$page = max(1, intval($_GET['page'] ?? 1));
$perPage = 24;
$offset = ($page - 1) * $perPage;

// Load filter stats
$languageStats = getLanguageStats();
$periodStats = getPeriodStats();
$provenienceStats = getProvenienceStats();
$genreStats = getGenreStats();

// Build query
$db = getDB();
$where = [];
$params = [];

// Language filter - use LIKE for each selected language
if (!empty($languages)) {
    $langConditions = [];
    foreach ($languages as $i => $lang) {
        $langConditions[] = "a.language LIKE :lang{$i}";
        $params[":lang{$i}"] = '%' . $lang . '%';
    }
    $where[] = '(' . implode(' OR ', $langConditions) . ')';
}

// Period filter
if (!empty($periods)) {
    $periodConditions = [];
    foreach ($periods as $i => $period) {
        $periodConditions[] = "a.period = :period{$i}";
        $params[":period{$i}"] = $period;
    }
    $where[] = '(' . implode(' OR ', $periodConditions) . ')';
}

// Provenience filter - use LIKE to match partial site names
if (!empty($sites)) {
    $siteConditions = [];
    foreach ($sites as $i => $site) {
        $siteConditions[] = "a.provenience LIKE :site{$i}";
        $params[":site{$i}"] = '%' . $site . '%';
    }
    $where[] = '(' . implode(' OR ', $siteConditions) . ')';
}

// Genre filter - use LIKE to catch variations
if (!empty($genres)) {
    $genreConditions = [];
    foreach ($genres as $i => $genre) {
        $genreConditions[] = "a.genre LIKE :genre{$i}";
        $params[":genre{$i}"] = '%' . $genre . '%';
    }
    $where[] = '(' . implode(' OR ', $genreConditions) . ')';
}

// Pipeline status filters
if ($pipeline) {
    switch ($pipeline) {
        case 'complete':
            $where[] = "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1";
            break;
        case 'has_image':
            $where[] = "ps.has_image = 1";
            break;
        case 'has_atf':
            $where[] = "ps.has_atf = 1";
            break;
        case 'has_lemmas':
            $where[] = "ps.has_lemmas = 1";
            break;
        case 'has_translation':
            $where[] = "ps.has_translation = 1";
            break;
        case 'missing_image':
            $where[] = "(ps.has_image IS NULL OR ps.has_image = 0)";
            break;
        case 'missing_atf':
            $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0)";
            break;
        case 'missing_lemmas':
            $where[] = "(ps.has_lemmas IS NULL OR ps.has_lemmas = 0)";
            break;
        case 'missing_translation':
            $where[] = "(ps.has_translation IS NULL OR ps.has_translation = 0)";
            break;
        // Text digitization filters
        case 'human_transcription':
            $where[] = "ps.has_atf = 1";
            break;
        case 'machine_ocr':
            $where[] = "ps.has_sign_annotations = 1";
            break;
        case 'any_digitization':
            $where[] = "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)";
            break;
        case 'no_digitization':
            $where[] = "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)";
            break;
    }
}

$whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

// Get total count
$countSql = "SELECT COUNT(*) FROM artifacts a LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number $whereClause";
$stmt = $db->prepare($countSql);
foreach ($params as $key => $val) {
    $stmt->bindValue($key, $val);
}
$totalCount = $stmt->execute()->fetchArray()[0];
$totalPages = ceil($totalCount / $perPage);

// Get tablets
$sql = "
    SELECT a.*, ps.has_image, ps.has_atf, ps.has_lemmas, ps.has_translation, ps.has_sign_annotations, ps.lemma_coverage
    FROM artifacts a
    LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
    $whereClause
    ORDER BY a.p_number
    LIMIT :limit OFFSET :offset
";
$stmt = $db->prepare($sql);
foreach ($params as $key => $val) {
    $stmt->bindValue($key, $val);
}
$stmt->bindValue(':limit', $perPage, SQLITE3_INTEGER);
$stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
$tablets = $stmt->execute();

// Get all active filters for display
$activeFilters = [];
foreach ($languages as $lang) {
    $activeFilters[] = ['type' => 'lang', 'value' => $lang, 'label' => $lang];
}
foreach ($periods as $period) {
    $activeFilters[] = ['type' => 'period', 'value' => $period, 'label' => $period];
}
foreach ($sites as $site) {
    $activeFilters[] = ['type' => 'site', 'value' => $site, 'label' => $site];
}
foreach ($genres as $genre) {
    $activeFilters[] = ['type' => 'genre', 'value' => $genre, 'label' => $genre];
}

require_once __DIR__ . '/../includes/header.php';
?>

<!-- Filter Components -->
<link rel="stylesheet" href="/assets/css/components/filter-sidebar.css">
<link rel="stylesheet" href="/assets/css/components/filter-active.css">
<link rel="stylesheet" href="/assets/css/components/cards-overlay.css">
<link rel="stylesheet" href="/assets/css/components/pagination.css">

<main class="page-with-sidebar">
    <?php
    // Set up filter sidebar variables
    $clearAllUrl = 'list.php';
    include __DIR__ . '/../includes/components/filter-sidebar.php';
    ?>

    <div class="main-content">
        <div class="page-header">
            <h1>Tablets</h1>
            <p class="subtitle">
                <?php if (!empty($activeFilters)): ?>
                Showing <?= number_format($totalCount) ?> tablets
                <?php else: ?>
                <?= number_format($totalCount) ?> tablets in database
                <?php endif; ?>
            </p>
        </div>

        <?php if (!empty($activeFilters)): ?>
        <div class="active-filters">
            <?php foreach ($activeFilters as $filter): ?>
            <a href="<?= htmlspecialchars(buildFilterUrl([], [$filter['type'] => $filter['value']])) ?>"
               class="filter-chip">
                <?= htmlspecialchars($filter['label']) ?>
                <span class="chip-remove">×</span>
            </a>
            <?php endforeach; ?>
        </div>
        <?php endif; ?>

        <div class="tablet-grid">
            <?php while ($tablet = $tablets->fetchArray(SQLITE3_ASSOC)): ?>
                <?php include __DIR__ . '/../includes/components/tablet-card.php'; ?>
            <?php endwhile; ?>
        </div>

        <?php if ($totalPages > 1): ?>
        <nav class="pagination">
            <?php
            // Build pagination URL preserving filters
            $paginationParams = $_GET;
            unset($paginationParams['page']);
            $baseUrl = '?' . http_build_query($paginationParams) . (empty($paginationParams) ? '' : '&');
            ?>
            <?php if ($page > 1): ?>
                <a href="<?= $baseUrl ?>page=<?= $page - 1 ?>" class="btn">Previous</a>
            <?php endif; ?>
            <span class="page-info">Page <?= $page ?> of <?= number_format($totalPages) ?></span>
            <?php if ($page < $totalPages): ?>
                <a href="<?= $baseUrl ?>page=<?= $page + 1 ?>" class="btn">Next</a>
            <?php endif; ?>
        </nav>
        <?php endif; ?>
    </div>
</main>

<script src="/assets/js/filters.js"></script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
