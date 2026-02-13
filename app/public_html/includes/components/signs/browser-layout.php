<?php
/**
 * Signs Browser Layout Component
 * Main 3-column layout structure for sign browsing
 *
 * Required variables:
 * @var array $counts - Grouping counts from repository
 *
 * Optional variables:
 * @var string $activeGroup - Currently active group type (default: 'all')
 * @var string $activeValue - Currently active group value (default: null)
 * @var string $searchQuery - Current search query (default: '')
 * @var string $sortOrder - Current sort order (default: 'sign_id')
 * @var string $selectedSignId - Currently selected sign ID (default: null)
 * @var array $initialSigns - Initial sign list to render (default: [])
 * @var int $totalSigns - Total count of signs matching current filter (default: 0)
 * @var array $signDetail - Full detail data for selected sign (default: null)
 */

// Set defaults
$activeGroup = $activeGroup ?? 'all';
$activeValue = $activeValue ?? null;
$searchQuery = $searchQuery ?? '';
$sortOrder = $sortOrder ?? 'sign_id';
$selectedSignId = $selectedSignId ?? null;
$initialSigns = $initialSigns ?? [];
$totalSigns = $totalSigns ?? 0;
$signDetail = $signDetail ?? null;
?>

<div class="signs-browser" data-active-group="<?= htmlspecialchars($activeGroup) ?>" data-active-value="<?= htmlspecialchars($activeValue ?? '') ?>">
    <!-- Page Header -->
    <header class="signs-browser__header">
        <h1 class="signs-browser__title">Dictionary</h1>
        <div class="signs-browser__actions">
            <span class="signs-browser__sources">Source: ORACC Global Sign List</span>
            <!-- Mobile groupings toggle -->
            <button class="signs-groupings__toggle" aria-label="Show groupings" data-action="toggle-groupings">
                <svg class="signs-groupings__toggle-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <path d="M3 6h18M3 12h18M3 18h18"/>
                </svg>
            </button>
        </div>
    </header>

    <!-- Section Tabs -->
    <nav class="dict-browser__subnav" aria-label="Dictionary sections">
        <a href="/dictionary/signs/" class="dict-browser__subnav-link active">Signs</a>
        <a href="/dictionary/" class="dict-browser__subnav-link">Words</a>
    </nav>

    <!-- Column 1: Groupings Panel -->
    <aside class="signs-browser__groupings" data-open="false">
        <?php include __DIR__ . '/groupings-panel.php'; ?>
    </aside>

    <!-- Mobile backdrop for groupings overlay -->
    <div class="signs-browser__groupings-backdrop" data-action="close-groupings"></div>

    <!-- Column 2: Sign List -->
    <div class="signs-browser__list" data-loading="false" data-empty="<?= empty($initialSigns) ? 'true' : 'false' ?>">
        <div class="signs-list">
            <!-- Search -->
            <div class="signs-list__search">
                <div class="signs-list__search-wrapper">
                    <svg class="signs-list__search-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="11" cy="11" r="8"/>
                        <path d="M21 21l-4.35-4.35"/>
                    </svg>
                    <input type="search"
                           class="signs-list__search-input"
                           placeholder="Search signs..."
                           value="<?= htmlspecialchars($searchQuery) ?>"
                           data-action="search">
                    <button class="signs-list__search-clear" aria-label="Clear search" data-action="clear-search">
                        <svg class="signs-list__search-clear-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 6L6 18M6 6l12 12"/>
                        </svg>
                    </button>
                </div>
                <select class="signs-list__sort" data-action="sort">
                    <option value="sign_id" <?= $sortOrder === 'sign_id' ? 'selected' : '' ?>>Sort by ID</option>
                    <option value="frequency" <?= $sortOrder === 'frequency' ? 'selected' : '' ?>>Sort by frequency</option>
                    <option value="value_count" <?= $sortOrder === 'value_count' ? 'selected' : '' ?>>Sort by values</option>
                    <option value="word_count" <?= $sortOrder === 'word_count' ? 'selected' : '' ?>>Sort by words</option>
                </select>
            </div>

            <!-- Sign List Items -->
            <div class="signs-list__items" data-sign-list>
                <?php foreach ($initialSigns as $sign): ?>
                    <?php
                    $isActive = $sign['sign_id'] === $selectedSignId;
                    include __DIR__ . '/sign-list-item.php';
                    ?>
                <?php endforeach; ?>
            </div>

            <!-- Empty State -->
            <div class="signs-list__empty">
                <svg class="signs-list__empty-icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                    <circle cx="11" cy="11" r="8"/>
                    <path d="M21 21l-4.35-4.35"/>
                </svg>
                <h3 class="signs-list__empty-title">No signs found</h3>
                <p class="signs-list__empty-description">Try a different search term or adjust your filters.</p>
                <button class="signs-list__empty-action" data-action="clear-all">Clear all filters</button>
            </div>

            <!-- Loading Indicator -->
            <div class="signs-list__loading">
                <div class="dict-spinner"></div>
            </div>

            <!-- Footer -->
            <div class="signs-list__footer">
                <span class="signs-list__count" data-sign-count>
                    Showing <?= count($initialSigns) ?> of <?= number_format($totalSigns) ?>
                </span>
                <button class="signs-list__load-more"
                        data-action="load-more"
                        data-hidden="<?= count($initialSigns) >= $totalSigns ? 'true' : 'false' ?>">
                    Load more
                </button>
            </div>
        </div>
    </div>

    <!-- Column 3: Sign Detail -->
    <main class="signs-browser__detail" data-open="<?= $selectedSignId ? 'true' : 'false' ?>">
        <!-- Mobile handle for drag gestures -->
        <div class="signs-browser__detail-handle"></div>

        <?php if ($signDetail): ?>
            <?php include __DIR__ . '/sign-detail.php'; ?>
        <?php else: ?>
            <!-- Placeholder when no sign selected -->
            <div class="signs-detail-placeholder">
                <svg class="signs-detail-placeholder__icon" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.5">
                    <rect x="3" y="3" width="18" height="18" rx="2"/>
                    <path d="M7 7h10M7 12h10M7 17h4"/>
                </svg>
                <h3 class="signs-detail-placeholder__title">Select a sign</h3>
                <p class="signs-detail-placeholder__description">
                    Choose a sign from the list to see its readings, word usage, and related signs.
                </p>
            </div>
        <?php endif; ?>

        <!-- Loading overlay -->
        <div class="signs-loading-overlay">
            <div class="dict-spinner"></div>
        </div>
    </main>
</div>
