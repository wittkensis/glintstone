<?php
/**
 * KPI Dashboard Component
 *
 * Displays collection overview metrics including:
 * - Total tablets, digitization %, translation %, image availability
 * - Pipeline visualization with progress bars
 * - Collapsible details for language/period/genre breakdowns
 *
 * Required variables:
 * @var array $kpiData - KPI metrics from getKPIMetrics()
 */

if (!isset($kpiData)) {
    throw new Exception('KPI Dashboard component requires $kpiData variable');
}
?>

<section class="kpi-dashboard" role="region" aria-label="Collection Statistics">
    <div class="section-header">
        <div class="section-header__content">
            <h2>Collection Overview</h2>
            <p class="section-description">
                Comprehensive statistics on <?= number_format($kpiData['total_tablets']) ?> cuneiform tablets
                from archaeological sites across Mesopotamia
            </p>
        </div>
    </div>

    <!-- Primary Metrics Grid -->
    <div class="kpi-grid">
        <div class="kpi-card">
            <div class="kpi-value"><?= number_format($kpiData['total_tablets']) ?></div>
            <div class="kpi-label">Total Tablets</div>
            <div class="kpi-sublabel">In Collection</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-value"><?= $kpiData['digitization_pct'] ?>%</div>
            <div class="kpi-label">Digitized</div>
            <div class="kpi-sublabel"><?= number_format($kpiData['pipeline']['atf']['count']) ?> with transcriptions</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-value"><?= $kpiData['translation_pct'] ?>%</div>
            <div class="kpi-label">Translated</div>
            <div class="kpi-sublabel"><?= number_format($kpiData['pipeline']['translations']['count']) ?> in English</div>
        </div>

        <div class="kpi-card">
            <div class="kpi-value"><?= $kpiData['image_pct'] ?>%</div>
            <div class="kpi-label">Photographed</div>
            <div class="kpi-sublabel"><?= number_format($kpiData['pipeline']['images']['count']) ?> with images</div>
        </div>
    </div>

    <!-- Pipeline Progress Visualization -->
    <div class="pipeline-progress">
        <h3 class="pipeline-heading">Digitization Pipeline</h3>
        <p class="pipeline-description">
            Tablets progress through stages from photography to full translation
        </p>

        <div class="pipeline-bars">
            <div class="pipeline-row">
                <div class="pipeline-row-label">
                    <span class="pipeline-icon">📷</span>
                    <span class="pipeline-name">Images</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" role="progressbar"
                         aria-valuenow="<?= $kpiData['pipeline']['images']['percent'] ?>"
                         aria-valuemin="0"
                         aria-valuemax="100"
                         style="width: <?= $kpiData['pipeline']['images']['percent'] ?>%">
                    </div>
                </div>
                <div class="pipeline-row-stat">
                    <span class="stat-count"><?= number_format($kpiData['pipeline']['images']['count']) ?></span>
                    <span class="stat-percent"><?= $kpiData['pipeline']['images']['percent'] ?>%</span>
                </div>
            </div>

            <div class="pipeline-row">
                <div class="pipeline-row-label">
                    <span class="pipeline-icon">📝</span>
                    <span class="pipeline-name">Transliteration</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" role="progressbar"
                         aria-valuenow="<?= $kpiData['pipeline']['atf']['percent'] ?>"
                         aria-valuemin="0"
                         aria-valuemax="100"
                         style="width: <?= $kpiData['pipeline']['atf']['percent'] ?>%">
                    </div>
                </div>
                <div class="pipeline-row-stat">
                    <span class="stat-count"><?= number_format($kpiData['pipeline']['atf']['count']) ?></span>
                    <span class="stat-percent"><?= $kpiData['pipeline']['atf']['percent'] ?>%</span>
                </div>
            </div>

            <div class="pipeline-row">
                <div class="pipeline-row-label">
                    <span class="pipeline-icon">🏷️</span>
                    <span class="pipeline-name">Lemmas</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" role="progressbar"
                         aria-valuenow="<?= $kpiData['pipeline']['lemmas']['percent'] ?>"
                         aria-valuemin="0"
                         aria-valuemax="100"
                         style="width: <?= $kpiData['pipeline']['lemmas']['percent'] ?>%">
                    </div>
                </div>
                <div class="pipeline-row-stat">
                    <span class="stat-count"><?= number_format($kpiData['pipeline']['lemmas']['count']) ?></span>
                    <span class="stat-percent"><?= $kpiData['pipeline']['lemmas']['percent'] ?>%</span>
                </div>
            </div>

            <div class="pipeline-row">
                <div class="pipeline-row-label">
                    <span class="pipeline-icon">🌍</span>
                    <span class="pipeline-name">Translation</span>
                </div>
                <div class="progress-bar-container">
                    <div class="progress-bar" role="progressbar"
                         aria-valuenow="<?= $kpiData['pipeline']['translations']['percent'] ?>"
                         aria-valuemin="0"
                         aria-valuemax="100"
                         style="width: <?= $kpiData['pipeline']['translations']['percent'] ?>%">
                    </div>
                </div>
                <div class="pipeline-row-stat">
                    <span class="stat-count"><?= number_format($kpiData['pipeline']['translations']['count']) ?></span>
                    <span class="stat-percent"><?= $kpiData['pipeline']['translations']['percent'] ?>%</span>
                </div>
            </div>
        </div>
    </div>

    <!-- Collapsible Details -->
    <details class="kpi-details">
        <summary class="kpi-details-toggle">
            <span class="toggle-text">Show detailed breakdown</span>
            <span class="toggle-icon" aria-hidden="true">▼</span>
        </summary>

        <div class="kpi-details-content">
            <div class="kpi-details-grid">
                <!-- Top Languages -->
                <div class="kpi-detail-section">
                    <h4>Top Languages</h4>
                    <ul class="detail-list">
                        <?php foreach ($kpiData['top_languages'] as $lang): ?>
                        <li class="detail-item">
                            <span class="detail-label"><?= htmlspecialchars($lang['language']) ?></span>
                            <span class="detail-value"><?= number_format($lang['tablet_count']) ?></span>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                </div>

                <!-- Top Periods -->
                <div class="kpi-detail-section">
                    <h4>Top Periods</h4>
                    <ul class="detail-list">
                        <?php foreach ($kpiData['top_periods'] as $period): ?>
                        <li class="detail-item">
                            <span class="detail-label"><?= htmlspecialchars($period['period']) ?></span>
                            <span class="detail-value"><?= number_format($period['tablet_count']) ?></span>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                </div>

                <!-- Top Genres -->
                <div class="kpi-detail-section">
                    <h4>Top Genres</h4>
                    <ul class="detail-list">
                        <?php foreach ($kpiData['top_genres'] as $genre): ?>
                        <li class="detail-item">
                            <span class="detail-label"><?= htmlspecialchars($genre['genre']) ?></span>
                            <span class="detail-value"><?= number_format($genre['tablet_count']) ?></span>
                        </li>
                        <?php endforeach; ?>
                    </ul>
                </div>
            </div>

            <div class="kpi-details-footer">
                <p class="kpi-footer-note">
                    <strong><?= number_format($kpiData['recent_activity_count']) ?> tablets</strong>
                    updated in the last 30 days
                </p>
            </div>
        </div>
    </details>
</section>
