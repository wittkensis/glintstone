<?php
/**
 * Dictionary Browser Layout Component
 * Main 3-column layout structure for dictionary browsing
 *
 * Required variables:
 * @var array $counts - Grouping counts from API
 *
 * Optional variables:
 * @var string $activeGroup - Currently active group type (default: 'all')
 * @var string $activeValue - Currently active group value (default: null)
 * @var string $searchQuery - Current search query (default: '')
 * @var string $selectedWordId - Currently selected word ID (default: null)
 * @var array $initialWords - Initial word list to render (default: [])
 * @var int $totalWords - Total count of words matching current filter (default: 0)
 * @var array $wordDetail - Full detail data for selected word (default: null)
 */

// Set defaults
$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;
$searchQuery = $searchQuery ?? '';
$selectedWordId = $selectedWordId ?? null;
$initialWords = $initialWords ?? [];
$totalWords = $totalWords ?? 0;
$wordDetail = $wordDetail ?? null;
?>

<div class="dict-browser" data-active-group="<?= htmlspecialchars($activeGroup) ?>" data-active-value="<?= htmlspecialchars($activeValue ?? '') ?>">
    <!-- Page Header -->
    <header class="dict-browser__header">
        <h1 class="dict-browser__title">Dictionary</h1>
        <div class="dict-browser__actions">
            <span class="dict-browser__sources">Sources: eBL, ORACC · CAD integration coming soon</span>
            <!-- Mobile groupings toggle -->
            <button class="dict-groupings__toggle" aria-label="Show groupings" data-action="toggle-groupings">
                <svg class="dict-groupings__toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M3 12h18M3 18h18"/>
                </svg>
            </button>
        </div>
    </header>

    <!-- Section Tabs -->
    <nav class="dict-browser__subnav" aria-label="Dictionary sections">
        <a href="/dictionary/signs/" class="dict-browser__subnav-link">Signs</a>
        <a href="/dictionary/" class="dict-browser__subnav-link active">Words</a>
    </nav>

    <!-- Column 1: Groupings Panel -->
    <aside class="dict-browser__groupings" data-open="false">
        <?php
        // expandedSections is calculated dynamically in groupings-panel.php based on active filter
        include __DIR__ . '/groupings-panel.php';
        ?>
    </aside>

    <!-- Mobile backdrop for groupings overlay -->
    <div class="dict-browser__groupings-backdrop" data-action="close-groupings"></div>

    <!-- Column 2: Word List -->
    <div class="dict-browser__words" data-loading="false" data-empty="<?= empty($initialWords) ? 'true' : 'false' ?>">
        <div class="dict-word-list">
            <!-- Search -->
            <div class="dict-word-list__search">
                <div class="dict-word-list__search-wrapper">
                    <svg class="dict-word-list__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="M21 21l-4.35-4.35"/>
                    </svg>
                    <input type="search"
                           class="dict-word-list__search-input"
                           placeholder="Search words..."
                           value="<?= htmlspecialchars($searchQuery) ?>"
                           data-action="search">
                    <button class="dict-word-list__search-clear" aria-label="Clear search" data-action="clear-search">
                        <svg class="dict-word-list__search-clear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <select class="dict-word-list__sort" data-action="sort">
                    <option value="frequency" selected>Sort by frequency</option>
                    <option value="alpha">Sort alphabetically</option>
                </select>
            </div>

            <!-- Word List Items -->
            <div class="dict-word-list__items" data-word-list>
                <?php foreach ($initialWords as $word): ?>
                    <?php
                    $isActive = $word['entry_id'] === $selectedWordId;
                    include __DIR__ . '/word-list-item.php';
                    ?>
                <?php endforeach; ?>
            </div>

            <!-- Empty State -->
            <div class="dict-word-list__empty">
                <svg class="dict-word-list__empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                </svg>
                <h3 class="dict-word-list__empty-title">No results found</h3>
                <p class="dict-word-list__empty-description">Try a different search term or adjust your filters.</p>
                <button class="dict-word-list__empty-action" data-action="clear-all">Clear all filters</button>
            </div>

            <!-- Loading Indicator -->
            <div class="dict-word-list__loading">
                <div class="dict-spinner"></div>
            </div>

            <!-- Footer -->
            <div class="dict-word-list__footer">
                <span class="dict-word-list__count" data-word-count>
                    Showing <?= count($initialWords) ?> of <?= number_format($totalWords) ?>
                </span>
                <button class="dict-word-list__load-more"
                        data-action="load-more"
                        data-hidden="<?= count($initialWords) >= $totalWords ? 'true' : 'false' ?>">
                    Load more
                </button>
            </div>
        </div>
    </div>

    <!-- Column 3: Word Detail -->
    <main class="dict-browser__detail" data-open="<?= $selectedWordId ? 'true' : 'false' ?>">
        <!-- Mobile handle for drag gestures -->
        <div class="dict-browser__detail-handle"></div>

        <?php if ($wordDetail): ?>
            <!-- Render word detail component -->
            <?php
            $entry = $wordDetail['entry'];
            $variants = $wordDetail['variants'];
            $signs = $wordDetail['signs'];
            $senses = $wordDetail['senses'];
            $attestations = $wordDetail['attestations'];
            $related = $wordDetail['related'];
            $cad = $wordDetail['cad'];
            $embedded = true;
            include __DIR__ . '/word-detail.php';
            ?>
        <?php else: ?>
            <!-- Placeholder when no word selected -->
            <div class="dict-detail-placeholder">
                <svg class="dict-detail-placeholder__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <path d="M4 19.5A2.5 2.5 0 0 1 6.5 17H20"/>
                    <path d="M6.5 2H20v20H6.5A2.5 2.5 0 0 1 4 19.5v-15A2.5 2.5 0 0 1 6.5 2z"/>
                    <path d="M8 7h8M8 11h8M8 15h4"/>
                </svg>
                <h3 class="dict-detail-placeholder__title">Select a word</h3>
                <p class="dict-detail-placeholder__description">
                    Choose a word from the list to see its full definition, variants, and corpus examples.
                </p>
            </div>
        <?php endif; ?>

        <!-- Loading overlay -->
        <div class="dict-loading-overlay">
            <div class="dict-spinner"></div>
        </div>
    </main>
</div>
