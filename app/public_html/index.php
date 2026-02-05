<?php
/**
 * Glintstone - Collaborative Cuneiform Research Platform
 * Main entry point
 */

require_once __DIR__ . '/includes/db.php';
require_once __DIR__ . '/includes/header.php';

// Get some stats
$db = getDB();
$stats = [
    'tablets' => $db->querySingle("SELECT COUNT(*) FROM artifacts"),
    'signs' => $db->querySingle("SELECT COUNT(*) FROM signs"),
    'glossary' => $db->querySingle("SELECT COUNT(*) FROM glossary_entries"),
];
?>

<main class="container">
    <section class="hero">
        <h1>Glintstone</h1>
        <p class="tagline">Collaborative Cuneiform Research Platform</p>
    </section>

    <section class="stats-grid">
        <div class="stat-card">
            <span class="stat-number"><?= number_format($stats['tablets']) ?></span>
            <span class="stat-label">Tablets</span>
        </div>
        <div class="stat-card">
            <span class="stat-number"><?= number_format($stats['signs']) ?></span>
            <span class="stat-label">Signs</span>
        </div>
        <div class="stat-card">
            <span class="stat-number"><?= number_format($stats['glossary']) ?></span>
            <span class="stat-label">Dictionary Entries</span>
        </div>
    </section>

    <section class="quick-search">
        <h2>Quick Search</h2>
        <form action="/tablets/search.php" method="GET">
            <div class="search-box">
                <input type="text" name="q" placeholder="Search tablets, signs, or words..." autofocus>
                <button type="submit">Search</button>
            </div>
        </form>
    </section>

    <section class="recent-tablets">
        <h2>Sample Tablets</h2>
        <div class="tablet-grid">
            <?php
            $tablets = $db->query("
                SELECT a.p_number, a.designation, a.museum_no, a.material, a.language,
                       ps.quality_score, ps.has_image, ps.has_atf
                FROM artifacts a
                LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
                ORDER BY a.p_number
                LIMIT 6
            ");
            while ($tablet = $tablets->fetchArray(SQLITE3_ASSOC)):
            ?>
            <a href="/tablets/detail.php?p=<?= urlencode($tablet['p_number']) ?>" class="tablet-card">
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
                        <span class="status-dot missing" title="Lemmas"></span>
                        <span class="status-dot missing" title="Translation"></span>
                    </div>
                </div>
            </a>
            <?php endwhile; ?>
        </div>
        <div class="view-all">
            <a href="/tablets/list.php" class="btn">View All Tablets</a>
        </div>
    </section>
</main>

<?php require_once __DIR__ . '/includes/footer.php'; ?>
