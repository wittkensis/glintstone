<?php
/**
 * Collections & Composites List Page
 * Displays user collections and scholarly composite texts
 */

require_once __DIR__ . '/../includes/db.php';
require_once __DIR__ . '/../includes/helpers/display.php';
require_once __DIR__ . '/../includes/helpers/smart-collections.php';

$pageTitle = 'Collections & Composites';

// Get all user collections
$collections = getCollections();

// Get preview tablets for each collection (first 4)
foreach ($collections as &$collection) {
    $collection['preview_tablets'] = getCollectionPreviewTablets($collection['collection_id'], 4);
}
unset($collection); // Break reference

// Get all Smart Collections
$smartCollections = getAllSmartCollections();

// Get preview tablets and counts for each Smart Collection
foreach ($smartCollections as &$smartCollection) {
    $tablets = executeSmartCollection($smartCollection['smart_collection_id'], 4);
    $smartCollection['preview_tablets'] = $tablets;
    $smartCollection['tablet_count'] = getSmartCollectionCount($smartCollection['smart_collection_id']);
}
unset($smartCollection);

// Get all composites with aggregated metadata (cached)
$composites = getCompositesWithMetadata();

require_once __DIR__ . '/../includes/header.php';
?>

<link rel="stylesheet" href="/assets/css/layout/page-header.css">
<link rel="stylesheet" href="/assets/css/components/collection-cards.css">
<link rel="stylesheet" href="/assets/css/components/empty-states.css">
<link rel="stylesheet" href="/assets/css/components/section-header.css">
<link rel="stylesheet" href="/assets/css/components/tabs.css">
<link rel="stylesheet" href="/assets/css/components/composites-table.css">

<main class="collections-page">
    <div class="page-header">
        <div class="page-header-main">
            <div class="page-header-title">
                <h1>Collections</h1>
            </div>
        </div>
    </div>

    <!-- Tabbed Interface -->
    <div class="tabs-container">
        <nav class="tabs-nav" role="tablist">
            <button class="tab-button" data-tab="collections" role="tab" aria-selected="true" tabindex="0">
                Curated Collections
                <span class="count-badge"><?= count($collections) ?></span>
            </button>
            <button class="tab-button" data-tab="smart-collections" role="tab" aria-selected="false" tabindex="-1">
                Smart Collections
                <span class="count-badge"><?= count($smartCollections) ?></span>
            </button>
            <button class="tab-button" data-tab="composites" role="tab" aria-selected="false" tabindex="-1">
                Composites
                <span class="count-badge"><?= count($composites) ?></span>
            </button>
        </nav>

        <div class="tab-panels">
            <!-- Collections Tab Panel -->
            <section id="collections" class="tab-panel" role="tabpanel">
                <div class="section-header">
                    <div class="section-header__content">
                        <h2>Curated Collections</h2>
                        <p class="section-description">Some of the most fascinating and impactful tablets available.</p>
                    </div>
                    <div class="header-actions">
                        <a href="/collections/new.php" class="btn btn-primary">New</a>
                    </div>
                </div>

        <?php if (empty($collections)): ?>
            <!-- Empty State -->
            <div class="empty-state">
                <div class="empty-icon">📚</div>
                <h3>No collections yet</h3>
                <p>Create your first collection to organize tablets by theme, period, or research topic.</p>
                <a href="/collections/new.php" class="btn-primary">Create Collection</a>
            </div>
        <?php else: ?>
            <!-- Collections Grid -->
            <div class="collection-grid">
                <?php foreach ($collections as $collection): ?>
                    <?php include __DIR__ . '/../includes/components/collection-card.php'; ?>
                <?php endforeach; ?>
            </div>
        <?php endif; ?>
            </section>

            <!-- Smart Collections Tab Panel -->
            <section id="smart-collections" class="tab-panel" role="tabpanel" hidden>
                <div class="section-header">
                    <div class="section-header__content">
                        <h2>Smart Collections</h2>
                        <p class="section-description">Dynamically curated collections that automatically update based on tablet metadata, quality scores, and scholarly significance. These collections surface the most valuable tablets for research and contribution.</p>
                    </div>
                </div>

                <?php if (empty($smartCollections)): ?>
                    <!-- Empty State -->
                    <div class="empty-state">
                        <div class="empty-icon">✨</div>
                        <h3>No Smart Collections available</h3>
                        <p>Smart Collections have not been configured yet.</p>
                    </div>
                <?php else: ?>
                    <!-- Smart Collections Grid -->
                    <div class="collection-grid">
                        <?php foreach ($smartCollections as $collection): ?>
                            <?php
                            $is_smart_collection = true;
                            $show_auto_updating_badge = true;
                            ?>
                            <?php include __DIR__ . '/../includes/components/collection-card.php'; ?>
                        <?php endforeach; ?>
                    </div>
                <?php endif; ?>
            </section>

            <!-- Composites Tab Panel -->
            <section id="composites" class="tab-panel" role="tabpanel" hidden>
                <div class="section-header">
                    <div class="section-header__content">
                        <h2>Composite Texts</h2>
                        <p class="section-description">Scholarly reconstructions that combine information from multiple fragmentary tablets to recreate complete ancient texts. Each composite represents the collective evidence from all known exemplars.</p>
                    </div>
                </div>

                <?php if (empty($composites)): ?>
                    <!-- Empty State -->
                    <div class="empty-state">
                        <div class="empty-icon">📜</div>
                        <h3>No composites available</h3>
                        <p>Composite texts have not been imported yet.</p>
                    </div>
                <?php else: ?>
                    <!-- Composites Table -->
                    <div class="composites-table-container">
                        <div class="table-toolbar">
                            <input type="search" id="composite-search" placeholder="Search by Q-number or designation..." autocomplete="off">
                            <span class="table-count">Showing <?= count($composites) ?> composite<?= count($composites) !== 1 ? 's' : '' ?></span>
                        </div>

                        <table class="composites-table">
                            <thead>
                                <tr>
                                    <th data-sort="q_number" class="sortable">Q-Number</th>
                                    <th data-sort="designation" class="sortable">Designation</th>
                                    <th>Period(s)</th>
                                    <th>Provenience(s)</th>
                                    <th>Genre(s)</th>
                                    <th data-sort="exemplar_count" class="sortable">Exemplars</th>
                                </tr>
                            </thead>
                            <tbody>
                                <?php foreach ($composites as $composite): ?>
                                <tr class="composite-row" data-href="/composites/detail.php?q=<?= urlencode($composite['q_number']) ?>">
                                    <td class="q-number" data-label="Q-Number"><?= htmlspecialchars($composite['q_number']) ?></td>
                                    <td class="designation" data-label="Designation"><?= htmlspecialchars($composite['designation']) ?></td>
                                    <td class="metadata-badges" data-label="Periods">
                                        <?php if (!empty($composite['periods'])): ?>
                                            <?php foreach ($composite['periods'] as $period): ?>
                                                <span class="badge badge-period"><?= htmlspecialchars($period) ?></span>
                                            <?php endforeach; ?>
                                        <?php else: ?>
                                            <span class="empty-metadata">—</span>
                                        <?php endif; ?>
                                    </td>
                                    <td class="metadata-badges" data-label="Proveniences">
                                        <?php if (!empty($composite['proveniences'])): ?>
                                            <?php foreach ($composite['proveniences'] as $prov): ?>
                                                <span class="badge badge-provenience"><?= htmlspecialchars($prov) ?></span>
                                            <?php endforeach; ?>
                                        <?php else: ?>
                                            <span class="empty-metadata">—</span>
                                        <?php endif; ?>
                                    </td>
                                    <td class="metadata-badges" data-label="Genres">
                                        <?php if (!empty($composite['genres'])): ?>
                                            <?php foreach ($composite['genres'] as $genre): ?>
                                                <span class="badge badge-genre"><?= htmlspecialchars($genre) ?></span>
                                            <?php endforeach; ?>
                                        <?php else: ?>
                                            <span class="empty-metadata">—</span>
                                        <?php endif; ?>
                                    </td>
                                    <td class="exemplar-count" data-label="Exemplars"><?= $composite['exemplar_count'] ?></td>
                                </tr>
                                <?php endforeach; ?>
                            </tbody>
                        </table>
                    </div>
                <?php endif; ?>
            </section>

        </div><!-- .tab-panels -->
    </div><!-- .tabs-container -->
</main>

<script src="/assets/js/collections-tabs.js"></script>
<script src="/assets/js/composites-table.js"></script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
