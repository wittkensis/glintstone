<?php
/**
 * Library Dictionary Browser
 *
 * Main landing page for browsing dictionary entries with:
 * - Search by word or meaning
 * - Faceted filters (language, POS, frequency)
 * - Card-based grid display
 * - Pagination
 * - Educational welcome overlay (first-time users)
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/header.php';

// Get filter parameters
$search = $_GET['search'] ?? '';
$language = $_GET['lang'] ?? '';
$pos = $_GET['pos'] ?? '';
$min_freq = isset($_GET['min_freq']) ? (int)$_GET['min_freq'] : 0;
$max_freq = isset($_GET['max_freq']) ? (int)$_GET['max_freq'] : 10000;
$sort = $_GET['sort'] ?? 'icount'; // icount, headword, language
$per_page = isset($_GET['per_page']) ? min((int)$_GET['per_page'], 200) : 50;
$page = isset($_GET['page']) ? max(1, (int)$_GET['page']) : 1;
$offset = ($page - 1) * $per_page;

// Build query
$db = get_db();
$where_clauses = [];
$bind_params = [];

if (!empty($search)) {
    $where_clauses[] = "(headword LIKE :search OR citation_form LIKE :search OR guide_word LIKE :search)";
    $bind_params[':search'] = '%' . $search . '%';
}

if (!empty($language)) {
    if ($language === 'sux') {
        $where_clauses[] = "language = 'sux'";
    } elseif ($language === 'akk') {
        $where_clauses[] = "language LIKE 'akk%'";
    } else {
        $where_clauses[] = "language = :language";
        $bind_params[':language'] = $language;
    }
}

if (!empty($pos)) {
    $where_clauses[] = "pos = :pos";
    $bind_params[':pos'] = $pos;
}

if ($min_freq > 0 || $max_freq < 10000) {
    $where_clauses[] = "icount >= :min_freq AND icount <= :max_freq";
    $bind_params[':min_freq'] = $min_freq;
    $bind_params[':max_freq'] = $max_freq;
}

$where_sql = !empty($where_clauses) ? 'WHERE ' . implode(' AND ', $where_clauses) : '';

// Build ORDER BY
$order_by = match($sort) {
    'headword' => 'headword ASC',
    'language' => 'language ASC, headword ASC',
    default => 'icount DESC'
};

// Count total
$count_sql = "SELECT COUNT(*) as total FROM glossary_entries $where_sql";
$stmt = $db->prepare($count_sql);
foreach ($bind_params as $key => $value) {
    $stmt->bindValue($key, $value, is_int($value) ? SQLITE3_INTEGER : SQLITE3_TEXT);
}
$result = $stmt->execute();
$total_row = $result->fetchArray(SQLITE3_ASSOC);
$total = (int)$total_row['total'];

// Get entries
$sql = "
    SELECT entry_id, headword, citation_form, guide_word, pos, language, icount
    FROM glossary_entries
    $where_sql
    ORDER BY $order_by
    LIMIT :limit OFFSET :offset
";

$stmt = $db->prepare($sql);
foreach ($bind_params as $key => $value) {
    $stmt->bindValue($key, $value, is_int($value) ? SQLITE3_INTEGER : SQLITE3_TEXT);
}
$stmt->bindValue(':limit', $per_page, SQLITE3_INTEGER);
$stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);
$result = $stmt->execute();

$entries = [];
while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    $entries[] = $row;
}

$total_pages = ceil($total / $per_page);
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Dictionary Browser - Cuneiform Library</title>
    <link rel="stylesheet" href="/assets/css/layout/site.css">
    <link rel="stylesheet" href="/assets/css/components/filter-sidebar.css">
    <link rel="stylesheet" href="/assets/css/components/library-browser.css">
    <link rel="stylesheet" href="/assets/css/components/educational-help.css">
</head>
<body>
    <div class="library-browser">
        <!-- Filter Sidebar -->
        <aside class="filter-sidebar">
            <div class="filter-header">
                <h2>Filters</h2>
                <?php if (!empty(array_filter([$search, $language, $pos, $min_freq]))): ?>
                    <a href="/library/" class="clear-filters">Clear all</a>
                <?php endif; ?>
            </div>

            <form method="GET" action="/library/" class="filter-form">
                <!-- Search -->
                <div class="filter-section">
                    <label for="search">Search</label>
                    <input type="text" id="search" name="search" value="<?= htmlspecialchars($search) ?>"
                           placeholder="Word or meaning...">
                </div>

                <!-- Language -->
                <div class="filter-section">
                    <label>Language</label>
                    <div class="filter-options">
                        <label class="filter-option">
                            <input type="radio" name="lang" value="" <?= empty($language) ? 'checked' : '' ?>>
                            All Languages
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="lang" value="sux" <?= $language === 'sux' ? 'checked' : '' ?>>
                            Sumerian
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="lang" value="akk" <?= $language === 'akk' ? 'checked' : '' ?>>
                            Akkadian
                        </label>
                    </div>
                </div>

                <!-- Part of Speech -->
                <div class="filter-section">
                    <label for="pos">Part of Speech</label>
                    <select id="pos" name="pos">
                        <option value="">All</option>
                        <option value="N" <?= $pos === 'N' ? 'selected' : '' ?>>Noun (N)</option>
                        <option value="V" <?= $pos === 'V' ? 'selected' : '' ?>>Verb (V)</option>
                        <option value="AJ" <?= $pos === 'AJ' ? 'selected' : '' ?>>Adjective (AJ)</option>
                        <option value="AV" <?= $pos === 'AV' ? 'selected' : '' ?>>Adverb (AV)</option>
                        <option value="DP" <?= $pos === 'DP' ? 'selected' : '' ?>>Demonstrative (DP)</option>
                        <option value="PP" <?= $pos === 'PP' ? 'selected' : '' ?>>Preposition (PP)</option>
                        <option value="CNJ" <?= $pos === 'CNJ' ? 'selected' : '' ?>>Conjunction (CNJ)</option>
                    </select>
                </div>

                <!-- Frequency Range -->
                <div class="filter-section">
                    <label>Frequency Range</label>
                    <div class="freq-inputs">
                        <input type="number" name="min_freq" value="<?= $min_freq ?>" placeholder="Min" min="0">
                        <span>to</span>
                        <input type="number" name="max_freq" value="<?= $max_freq ?>" placeholder="Max" min="0">
                    </div>
                </div>

                <!-- Sort -->
                <div class="filter-section">
                    <label for="sort">Sort By</label>
                    <select id="sort" name="sort">
                        <option value="icount" <?= $sort === 'icount' ? 'selected' : '' ?>>Frequency (High to Low)</option>
                        <option value="headword" <?= $sort === 'headword' ? 'selected' : '' ?>>Alphabetical</option>
                        <option value="language" <?= $sort === 'language' ? 'selected' : '' ?>>Language</option>
                    </select>
                </div>

                <!-- Per Page -->
                <div class="filter-section">
                    <label for="per_page">Results per page</label>
                    <select id="per_page" name="per_page">
                        <option value="25" <?= $per_page === 25 ? 'selected' : '' ?>>25</option>
                        <option value="50" <?= $per_page === 50 ? 'selected' : '' ?>>50</option>
                        <option value="100" <?= $per_page === 100 ? 'selected' : '' ?>>100</option>
                        <option value="200" <?= $per_page === 200 ? 'selected' : '' ?>>200</option>
                    </select>
                </div>

                <button type="submit" class="filter-apply">Apply Filters</button>
            </form>
        </aside>

        <!-- Main Content -->
        <main class="library-main">
            <header class="library-header">
                <h1>Dictionary Browser</h1>
                <p class="library-description">
                    Explore <?= number_format($total) ?> words from ancient Sumerian and Akkadian
                </p>
            </header>

            <!-- Results Header -->
            <div class="results-header">
                <p class="results-count">
                    Showing <?= number_format($offset + 1) ?>-<?= number_format(min($offset + $per_page, $total)) ?>
                    of <?= number_format($total) ?> results
                </p>
            </div>

            <!-- Results Grid -->
            <div class="entries-grid">
                <?php foreach ($entries as $entry): ?>
                    <a href="/library/word/<?= urlencode($entry['entry_id']) ?>" class="entry-card">
                        <div class="entry-card__header">
                            <h3 class="entry-headword"><?= htmlspecialchars($entry['headword']) ?></h3>
                            <?php if ($entry['guide_word']): ?>
                                <span class="entry-guide-word">[<?= htmlspecialchars($entry['guide_word']) ?>]</span>
                            <?php endif; ?>
                        </div>
                        <div class="entry-card__meta">
                            <span class="badge badge--pos"><?= htmlspecialchars($entry['pos']) ?></span>
                            <span class="badge badge--language">
                                <?= $entry['language'] === 'sux' ? 'Sumerian' : 'Akkadian' ?>
                            </span>
                        </div>
                        <div class="entry-card__stats">
                            <span class="entry-frequency"><?= number_format($entry['icount']) ?> attestations</span>
                        </div>
                    </a>
                <?php endforeach; ?>

                <?php if (empty($entries)): ?>
                    <div class="no-results">
                        <p>No entries match your filters.</p>
                        <a href="/library/" class="btn">Clear filters</a>
                    </div>
                <?php endif; ?>
            </div>

            <!-- Pagination -->
            <?php if ($total_pages > 1): ?>
                <nav class="pagination" aria-label="Pagination">
                    <?php
                    $query_params = $_GET;
                    unset($query_params['page']);
                    $base_url = '/library/?' . http_build_query($query_params);
                    ?>

                    <?php if ($page > 1): ?>
                        <a href="<?= $base_url ?>&page=<?= $page - 1 ?>" class="pagination-prev">← Previous</a>
                    <?php endif; ?>

                    <span class="pagination-info">Page <?= $page ?> of <?= $total_pages ?></span>

                    <?php if ($page < $total_pages): ?>
                        <a href="<?= $base_url ?>&page=<?= $page + 1 ?>" class="pagination-next">Next →</a>
                    <?php endif; ?>
                </nav>
            <?php endif; ?>
        </main>
    </div>

    <!-- JavaScript -->
    <script src="/assets/js/modules/educational-help.js"></script>
    <script src="/assets/js/modules/dictionary-search.js"></script>
    <script>
        // Initialize search autocomplete
        const searchInput = document.getElementById('search');
        if (searchInput) {
            new DictionarySearch(searchInput, {
                minChars: 2,
                maxSuggestions: 8
            });
        }
    </script>
</body>
</html>
