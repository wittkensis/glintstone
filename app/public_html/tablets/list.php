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
    <aside class="filter-sidebar">
        <div class="filter-header">
            <h2>Filters</h2>
            <?php if (!empty($activeFilters)): ?>
            <a href="list.php" class="clear-all">Clear all</a>
            <?php endif; ?>
        </div>

        <!-- Language Filter -->
        <div class="filter-section" data-filter="language">
            <button class="filter-section-header" aria-expanded="true">
                <span class="filter-title">Language</span>
                <span class="filter-toggle">−</span>
            </button>
            <div class="filter-content">
                <?php foreach ($languageStats as $group): ?>
                <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                    <button class="filter-group-header" aria-expanded="false">
                        <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                        <span class="group-count"><?= number_format($group['total']) ?></span>
                        <span class="group-toggle">+</span>
                    </button>
                    <div class="filter-group-content">
                        <?php foreach ($group['items'] as $item): ?>
                        <label class="filter-option">
                            <input type="checkbox"
                                   name="lang[]"
                                   value="<?= htmlspecialchars($item['value']) ?>"
                                   <?= isFilterActive('lang', $item['value']) ? 'checked' : '' ?>
                                   data-url-add="<?= htmlspecialchars(buildFilterUrl(['lang' => $item['value']])) ?>"
                                   data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['lang' => $item['value']])) ?>">
                            <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                            <span class="option-count"><?= number_format($item['count']) ?></span>
                        </label>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Period Filter -->
        <div class="filter-section" data-filter="period">
            <button class="filter-section-header" aria-expanded="false">
                <span class="filter-title">Period</span>
                <span class="filter-toggle">+</span>
            </button>
            <div class="filter-content" hidden>
                <?php foreach ($periodStats as $group): ?>
                <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                    <button class="filter-group-header" aria-expanded="false">
                        <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                        <span class="group-count"><?= number_format($group['total']) ?></span>
                        <span class="group-toggle">+</span>
                    </button>
                    <div class="filter-group-content">
                        <?php foreach ($group['items'] as $item): ?>
                        <label class="filter-option">
                            <input type="checkbox"
                                   name="period[]"
                                   value="<?= htmlspecialchars($item['value']) ?>"
                                   <?= isFilterActive('period', $item['value']) ? 'checked' : '' ?>
                                   data-url-add="<?= htmlspecialchars(buildFilterUrl(['period' => $item['value']])) ?>"
                                   data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['period' => $item['value']])) ?>">
                            <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                            <span class="option-count"><?= number_format($item['count']) ?></span>
                        </label>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Provenience/Site Filter -->
        <div class="filter-section" data-filter="site">
            <button class="filter-section-header" aria-expanded="false">
                <span class="filter-title">Discovery Site</span>
                <span class="filter-toggle">+</span>
            </button>
            <div class="filter-content" hidden>
                <?php foreach ($provenienceStats as $group): ?>
                <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                    <button class="filter-group-header" aria-expanded="false">
                        <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                        <span class="group-count"><?= number_format($group['total']) ?></span>
                        <span class="group-toggle">+</span>
                    </button>
                    <div class="filter-group-content">
                        <?php foreach (array_slice($group['items'], 0, 20) as $item): ?>
                        <label class="filter-option">
                            <input type="checkbox"
                                   name="site[]"
                                   value="<?= htmlspecialchars($item['value']) ?>"
                                   <?= isFilterActive('site', $item['value']) ? 'checked' : '' ?>
                                   data-url-add="<?= htmlspecialchars(buildFilterUrl(['site' => $item['value']])) ?>"
                                   data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['site' => $item['value']])) ?>">
                            <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                            <span class="option-count"><?= number_format($item['count']) ?></span>
                        </label>
                        <?php endforeach; ?>
                        <?php if (count($group['items']) > 20): ?>
                        <button class="show-more" data-group="<?= htmlspecialchars($group['group']) ?>">
                            Show <?= count($group['items']) - 20 ?> more...
                        </button>
                        <div class="more-items" hidden>
                            <?php foreach (array_slice($group['items'], 20) as $item): ?>
                            <label class="filter-option">
                                <input type="checkbox"
                                       name="site[]"
                                       value="<?= htmlspecialchars($item['value']) ?>"
                                       <?= isFilterActive('site', $item['value']) ? 'checked' : '' ?>
                                       data-url-add="<?= htmlspecialchars(buildFilterUrl(['site' => $item['value']])) ?>"
                                       data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['site' => $item['value']])) ?>">
                                <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                                <span class="option-count"><?= number_format($item['count']) ?></span>
                            </label>
                            <?php endforeach; ?>
                        </div>
                        <?php endif; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Genre Filter -->
        <div class="filter-section" data-filter="genre">
            <button class="filter-section-header" aria-expanded="false">
                <span class="filter-title">Genre</span>
                <span class="filter-toggle">+</span>
            </button>
            <div class="filter-content" hidden>
                <?php foreach ($genreStats as $group): ?>
                <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                    <button class="filter-group-header" aria-expanded="false">
                        <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                        <span class="group-count"><?= number_format($group['total']) ?></span>
                        <span class="group-toggle">+</span>
                    </button>
                    <div class="filter-group-content">
                        <?php foreach ($group['items'] as $item): ?>
                        <label class="filter-option">
                            <input type="checkbox"
                                   name="genre[]"
                                   value="<?= htmlspecialchars($item['value']) ?>"
                                   <?= isFilterActive('genre', $item['value']) ? 'checked' : '' ?>
                                   data-url-add="<?= htmlspecialchars(buildFilterUrl(['genre' => $item['value']])) ?>"
                                   data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['genre' => $item['value']])) ?>">
                            <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                            <span class="option-count"><?= number_format($item['count']) ?></span>
                        </label>
                        <?php endforeach; ?>
                    </div>
                </div>
                <?php endforeach; ?>
            </div>
        </div>

        <!-- Pipeline Status Filter -->
        <div class="filter-section" data-filter="pipeline">
            <button class="filter-section-header" aria-expanded="false">
                <span class="filter-title">Data Status</span>
                <span class="filter-toggle">+</span>
            </button>
            <div class="filter-content" hidden>
                <div class="filter-group-content" style="display: block;">
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="" <?= !$pipeline ? 'checked' : '' ?>>
                        <span class="option-label">All</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="complete" <?= $pipeline === 'complete' ? 'checked' : '' ?>>
                        <span class="option-label">Complete (all data)</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="has_image" <?= $pipeline === 'has_image' ? 'checked' : '' ?>>
                        <span class="option-label">Has Image</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="has_translation" <?= $pipeline === 'has_translation' ? 'checked' : '' ?>>
                        <span class="option-label">Has Translation</span>
                    </label>

                    <div class="filter-subsection">
                        <span class="subsection-label">Text Digitization</span>
                        <label class="filter-option">
                            <input type="radio" name="pipeline" value="any_digitization" <?= $pipeline === 'any_digitization' ? 'checked' : '' ?>>
                            <span class="option-label">Any Digitization</span>
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="pipeline" value="human_transcription" <?= $pipeline === 'human_transcription' ? 'checked' : '' ?>>
                            <span class="option-label">Human Transcription (ATF)</span>
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="pipeline" value="machine_ocr" <?= $pipeline === 'machine_ocr' ? 'checked' : '' ?>>
                            <span class="option-label">Machine OCR (Sign Detection)</span>
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="pipeline" value="no_digitization" <?= $pipeline === 'no_digitization' ? 'checked' : '' ?>>
                            <span class="option-label">No Digitization</span>
                        </label>
                    </div>
                </div>
            </div>
        </div>
    </aside>

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
            <?php $langAbbr = getLanguageAbbreviation($tablet['language']); ?>
            <a href="detail.php?p=<?= urlencode($tablet['p_number']) ?>" class="tablet-card">
                <!-- Pipeline Status Bar -->
                <div class="card-pipeline-bar">
                    <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('image', $tablet) ?>" title="Image"></span>
                    <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('signs', $tablet) ?>" title="Sign Detection"></span>
                    <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('transliteration', $tablet) ?>" title="Transliteration"></span>
                    <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('lemmas', $tablet) ?>" title="Lemmas"></span>
                    <span class="pipeline-segment" data-status="<?= getPipelineSegmentStatus('translation', $tablet) ?>" title="Translation"></span>
                </div>

                <!-- Language Badge -->
                <?php if ($langAbbr): ?>
                <span class="lang-badge" title="<?= htmlspecialchars($tablet['language']) ?>"><?= $langAbbr ?></span>
                <?php endif; ?>

                <!-- Full-card Image -->
                <div class="card-image">
                    <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=200"
                         alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
                         loading="lazy"
                         onerror="this.parentElement.classList.add('no-image')">
                    <div class="card-placeholder">
                        <span class="cuneiform-icon">𒀭</span>
                    </div>
                </div>

                <!-- Overlay Info Panel -->
                <div class="card-overlay">
                    <span class="card-p-number"><?= htmlspecialchars($tablet['p_number']) ?></span>
                    <?php if ($tablet['period']): ?>
                    <span class="meta-period"><?= htmlspecialchars(truncateText($tablet['period'], 25)) ?></span>
                    <?php endif; ?>
                    <?php if ($tablet['provenience']): ?>
                    <span class="meta-site"><?= htmlspecialchars(truncateText($tablet['provenience'], 20)) ?></span>
                    <?php endif; ?>
                    <?php if ($tablet['genre']): ?>
                    <span class="meta-genre"><?= htmlspecialchars(truncateText($tablet['genre'], 20)) ?></span>
                    <?php endif; ?>
                    <div class="card-designation"><?= htmlspecialchars($tablet['designation'] ?? 'Unknown') ?></div>
                </div>
            </a>
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
