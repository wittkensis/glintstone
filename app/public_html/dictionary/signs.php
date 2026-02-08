<?php
/**
 * Sign Library Browser
 *
 * Visual grid for browsing cuneiform signs with:
 * - Search by sign_id or value
 * - Filter by sign type and frequency
 * - Sort options
 * - Large cuneiform character display
 */

require_once __DIR__ . '/../includes/header.php';

// Get filter parameters
$search = $_GET['search'] ?? '';
$sign_type = $_GET['sign_type'] ?? '';
$min_frequency = isset($_GET['min_frequency']) ? (int)$_GET['min_frequency'] : 0;
$sort = $_GET['sort'] ?? 'sign_id'; // sign_id, frequency, value_count
$per_page = isset($_GET['per_page']) ? min((int)$_GET['per_page'], 200) : 50;
$page = isset($_GET['page']) ? max(1, (int)$_GET['page']) : 1;
$offset = ($page - 1) * $per_page;

// Build API URL
$api_params = [
    'search' => $search,
    'sign_type' => $sign_type,
    'min_frequency' => $min_frequency,
    'sort' => $sort,
    'limit' => $per_page,
    'offset' => $offset
];

$api_url = '/api/dictionary/signs-browse.php?' . http_build_query(array_filter($api_params));
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Library - Cuneiform Dictionary</title>
    <link rel="stylesheet" href="/assets/css/layout/site.css">
    <link rel="stylesheet" href="/assets/css/components/filter-sidebar.css">
    <link rel="stylesheet" href="/assets/css/components/sign-grid.css">
    <link rel="stylesheet" href="/assets/css/components/educational-help.css">
</head>
<body>
    <div class="dictionary-browser dictionary-signs-browser">
        <!-- Filter Sidebar -->
        <aside class="filter-sidebar">
            <div class="filter-header">
                <h2>Filters</h2>
                <?php if (!empty(array_filter([$search, $sign_type, $min_frequency]))): ?>
                    <a href="/dictionary/signs.php" class="clear-filters">Clear all</a>
                <?php endif; ?>
            </div>

            <form method="GET" action="/library/signs.php" class="filter-form">
                <!-- Search -->
                <div class="filter-section">
                    <label for="search">Search</label>
                    <input type="text" id="search" name="search" value="<?= htmlspecialchars($search) ?>"
                           placeholder="Sign ID or value...">
                </div>

                <!-- Sign Type -->
                <div class="filter-section">
                    <label>Sign Type</label>
                    <div class="filter-options">
                        <label class="filter-option">
                            <input type="radio" name="sign_type" value="" <?= empty($sign_type) ? 'checked' : '' ?>>
                            All Types
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="sign_type" value="simple" <?= $sign_type === 'simple' ? 'checked' : '' ?>>
                            Simple
                        </label>
                        <label class="filter-option">
                            <input type="radio" name="sign_type" value="compound" <?= $sign_type === 'compound' ? 'checked' : '' ?>>
                            Compound
                        </label>
                    </div>
                </div>

                <!-- Min Frequency -->
                <div class="filter-section">
                    <label for="min_frequency">Minimum Frequency</label>
                    <input type="number" id="min_frequency" name="min_frequency" value="<?= $min_frequency ?>" min="0">
                </div>

                <!-- Sort -->
                <div class="filter-section">
                    <label for="sort">Sort By</label>
                    <select id="sort" name="sort">
                        <option value="sign_id" <?= $sort === 'sign_id' ? 'selected' : '' ?>>Sign ID</option>
                        <option value="frequency" <?= $sort === 'frequency' ? 'selected' : '' ?>>Frequency</option>
                        <option value="value_count" <?= $sort === 'value_count' ? 'selected' : '' ?>>Number of Values</option>
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
        <main class="dictionary-main">
            <header class="dictionary-header">
                <h1>Sign Library</h1>
                <p class="dictionary-description">
                    Browse 3,300+ cuneiform signs with their values and usage
                </p>
            </header>

            <!-- Results will be loaded via JavaScript -->
            <div id="signs-results-container">
                <div class="loading-state">
                    <p>Loading signs...</p>
                </div>
            </div>
        </main>
    </div>

    <!-- JavaScript -->
    <script src="/assets/js/modules/educational-help.js"></script>
    <script>
        (async function() {
            const apiUrl = <?= json_encode($api_url) ?>;
            const container = document.getElementById('signs-results-container');

            try {
                const response = await fetch(apiUrl);
                if (!response.ok) throw new Error('Failed to load signs');

                const data = await response.json();

                // Render results header
                const headerHtml = `
                    <div class="results-header">
                        <p class="results-count">
                            Showing ${data.pagination.offset + 1}-${data.pagination.offset + data.pagination.showing}
                            of ${data.pagination.total.toLocaleString()} signs
                        </p>
                    </div>
                `;

                // Render signs grid
                const signsHtml = data.signs.map(sign => `
                    <a href="/library/sign/${encodeURIComponent(sign.sign_id)}" class="sign-card">
                        <div class="sign-card__cuneiform">
                            ${sign.utf8 || ''}
                        </div>
                        <div class="sign-card__info">
                            <h3 class="sign-id">${escapeHtml(sign.sign_id)}</h3>
                            ${sign.most_common_value ? `<p class="sign-value">${escapeHtml(sign.most_common_value)}</p>` : ''}
                        </div>
                        <div class="sign-card__stats">
                            <span class="sign-stat">${sign.value_count} values</span>
                            <span class="sign-stat">${sign.word_count} words</span>
                        </div>
                    </a>
                `).join('');

                // Render pagination
                const currentPage = <?= $page ?>;
                const totalPages = Math.ceil(data.pagination.total / data.pagination.limit);
                const queryParams = new URLSearchParams(<?= json_encode($_GET) ?>);
                queryParams.delete('page');
                const baseUrl = '/library/signs.php?' + queryParams.toString();

                let paginationHtml = '';
                if (totalPages > 1) {
                    paginationHtml = `
                        <nav class="pagination" aria-label="Pagination">
                            ${currentPage > 1 ? `<a href="${baseUrl}&page=${currentPage - 1}" class="pagination-prev">← Previous</a>` : ''}
                            <span class="pagination-info">Page ${currentPage} of ${totalPages}</span>
                            ${currentPage < totalPages ? `<a href="${baseUrl}&page=${currentPage + 1}" class="pagination-next">Next →</a>` : ''}
                        </nav>
                    `;
                }

                // Update container
                container.innerHTML = `
                    ${headerHtml}
                    <div class="signs-grid">
                        ${signsHtml || '<div class="no-results"><p>No signs match your filters.</p></div>'}
                    </div>
                    ${paginationHtml}
                `;

            } catch (error) {
                console.error('Error loading signs:', error);
                container.innerHTML = `
                    <div class="error-state">
                        <h2>Error loading signs</h2>
                        <p>${error.message}</p>
                    </div>
                `;
            }

            function escapeHtml(text) {
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        })();
    </script>
</body>
</html>
