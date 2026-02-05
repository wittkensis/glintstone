<?php
/**
 * Tablet list page
 */

require_once __DIR__ . '/../includes/db.php';

$pageTitle = 'Tablets';

// Get filter parameters
$language = $_GET['lang'] ?? null;
$material = $_GET['material'] ?? null;
$page = max(1, intval($_GET['page'] ?? 1));
$perPage = 24;
$offset = ($page - 1) * $perPage;

// Build query
$db = getDB();
$where = [];
$params = [];

if ($language) {
    $where[] = "a.language = :lang";
    $params[':lang'] = $language;
}
if ($material) {
    $where[] = "a.material = :material";
    $params[':material'] = $material;
}

$whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

// Get total count
$countSql = "SELECT COUNT(*) FROM artifacts a $whereClause";
$stmt = $db->prepare($countSql);
foreach ($params as $key => $val) {
    $stmt->bindValue($key, $val);
}
$totalCount = $stmt->execute()->fetchArray()[0];
$totalPages = ceil($totalCount / $perPage);

// Get tablets
$sql = "
    SELECT a.*, ps.quality_score, ps.has_image, ps.has_atf, ps.has_lemmas, ps.has_translation
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

require_once __DIR__ . '/../includes/header.php';
?>

<main class="container">
    <div class="page-header">
        <h1>Tablets</h1>
        <p class="subtitle"><?= number_format($totalCount) ?> tablets in database</p>
    </div>

    <div class="filters">
        <form method="GET" class="filter-form">
            <select name="lang" onchange="this.form.submit()">
                <option value="">All Languages</option>
                <option value="Sumerian" <?= $language === 'Sumerian' ? 'selected' : '' ?>>Sumerian</option>
                <option value="Akkadian" <?= $language === 'Akkadian' ? 'selected' : '' ?>>Akkadian</option>
                <option value="undetermined" <?= $language === 'undetermined' ? 'selected' : '' ?>>Undetermined</option>
            </select>
            <select name="material" onchange="this.form.submit()">
                <option value="">All Materials</option>
                <option value="clay" <?= $material === 'clay' ? 'selected' : '' ?>>Clay</option>
                <option value="stone" <?= $material === 'stone' ? 'selected' : '' ?>>Stone</option>
            </select>
        </form>
    </div>

    <div class="tablet-grid">
        <?php while ($tablet = $tablets->fetchArray(SQLITE3_ASSOC)): ?>
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
                    <?php if ($tablet['material']): ?>
                        <span><?= htmlspecialchars($tablet['material']) ?></span>
                    <?php endif; ?>
                </div>
                <div class="pipeline-status">
                    <span class="status-dot <?= $tablet['has_image'] ? 'complete' : 'missing' ?>" title="Image"></span>
                    <span class="status-dot <?= $tablet['has_atf'] ? 'complete' : 'missing' ?>" title="ATF"></span>
                    <span class="status-dot <?= $tablet['has_lemmas'] ? 'complete' : 'missing' ?>" title="Lemmas"></span>
                    <span class="status-dot <?= $tablet['has_translation'] ? 'complete' : 'missing' ?>" title="Translation"></span>
                </div>
            </div>
        </a>
        <?php endwhile; ?>
    </div>

    <?php if ($totalPages > 1): ?>
    <nav class="pagination">
        <?php if ($page > 1): ?>
            <a href="?page=<?= $page - 1 ?>&lang=<?= urlencode($language ?? '') ?>&material=<?= urlencode($material ?? '') ?>" class="btn">Previous</a>
        <?php endif; ?>
        <span class="page-info">Page <?= $page ?> of <?= $totalPages ?></span>
        <?php if ($page < $totalPages): ?>
            <a href="?page=<?= $page + 1 ?>&lang=<?= urlencode($language ?? '') ?>&material=<?= urlencode($material ?? '') ?>" class="btn">Next</a>
        <?php endif; ?>
    </nav>
    <?php endif; ?>
</main>

<style>
.page-header {
    margin-bottom: var(--space-6);
}

.subtitle {
    color: var(--color-text-muted);
}

.filters {
    margin-bottom: var(--space-6);
}

.filter-form {
    display: flex;
    gap: var(--space-4);
}

.filter-form select {
    background: var(--color-surface);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-md);
    padding: var(--space-2) var(--space-4);
    color: var(--color-text);
}

.pagination {
    display: flex;
    justify-content: center;
    align-items: center;
    gap: var(--space-4);
    margin-top: var(--space-8);
}

.page-info {
    color: var(--color-text-muted);
}

/* Thumbnail styles */
.tablet-thumbnail {
    position: relative;
    width: 100%;
    padding-bottom: 100%; /* 1:1 aspect ratio */
    background: var(--color-surface);
    border-radius: var(--radius-md) var(--radius-md) 0 0;
    overflow: hidden;
}

.tablet-thumbnail img {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    object-fit: cover;
    transition: transform 0.3s ease;
}

.tablet-card:hover .tablet-thumbnail img {
    transform: scale(1.05);
}

.thumbnail-placeholder {
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    display: flex;
    align-items: center;
    justify-content: center;
    background: var(--color-surface);
    z-index: -1;
}

.thumbnail-placeholder .cuneiform-icon {
    font-family: 'Noto Sans Cuneiform', serif;
    font-size: 3rem;
    color: var(--color-border);
    opacity: 0.5;
}

.tablet-thumbnail.no-image img {
    display: none;
}

.tablet-thumbnail.no-image .thumbnail-placeholder {
    z-index: 1;
}

.tablet-info {
    padding: var(--space-3);
}

/* Update tablet-card for thumbnail layout */
.tablet-card {
    display: flex;
    flex-direction: column;
    padding: 0;
    overflow: hidden;
}

.tablet-card .tablet-header {
    padding: 0;
    margin-bottom: var(--space-2);
}

.tablet-card .tablet-designation {
    padding: 0;
}

.tablet-card .tablet-meta {
    padding: 0;
    margin-top: var(--space-2);
}

.tablet-card .pipeline-status {
    margin-top: var(--space-2);
}
</style>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
