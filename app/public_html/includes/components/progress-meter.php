<?php
/**
 * Progress Meter Component
 * Radial visualization of digitization pipeline
 *
 * Displays total tablets in center with 3 concentric progress rings:
 * - Outer: Images (has_image)
 * - Middle: Transliterations (has_atf)
 * - Inner: Translations (has_translation)
 *
 * @requires $kpiData array from getKPIMetrics()
 */

// Extract metrics from KPI data
$totalTablets = number_format($kpiData['total_tablets']);
$totalRaw = $kpiData['total_tablets'];

// Pipeline metrics
$imageCount = number_format($kpiData['pipeline']['images']['count']);
$imagePct = $kpiData['pipeline']['images']['percent'];

$atfCount = number_format($kpiData['pipeline']['atf']['count']);
$atfPct = $kpiData['pipeline']['atf']['percent'];

$translationCount = number_format($kpiData['pipeline']['translations']['count']);
$translationPct = $kpiData['pipeline']['translations']['percent'];

// SVG circle calculations for progress rings
$radius1 = 200; // Outer ring (Images)
$radius2 = 170; // Middle ring (Transliterations)
$radius3 = 140; // Inner ring (Translations)

$circumference1 = 2 * pi() * $radius1;
$circumference2 = 2 * pi() * $radius2;
$circumference3 = 2 * pi() * $radius3;

// Calculate stroke-dashoffset for progress animation
$offset1 = $circumference1 * (1 - $imagePct / 100);
$offset2 = $circumference2 * (1 - $atfPct / 100);
$offset3 = $circumference3 * (1 - $translationPct / 100);
?>

<div class="progress-meter">
    <!-- Screen reader accessible description -->
    <div class="sr-only">
        Archive progress: <?= $totalTablets ?> tablets recorded.
        <?= $imagePct ?>% have images,
        <?= $atfPct ?>% have transliterations,
        <?= $translationPct ?>% have translations.
    </div>

    <!-- SVG Visualization -->
    <svg class="progress-rings" viewBox="0 0 500 500" role="img" aria-hidden="true">
        <title>Digitization Progress Visualization</title>

        <!-- Background circles (track) -->
        <circle class="ring-bg ring-bg-1" cx="250" cy="250" r="<?= $radius1 ?>" />
        <circle class="ring-bg ring-bg-2" cx="250" cy="250" r="<?= $radius2 ?>" />
        <circle class="ring-bg ring-bg-3" cx="250" cy="250" r="<?= $radius3 ?>" />

        <!-- Progress circles (animated) -->
        <circle class="ring-progress ring-1"
                cx="250" cy="250" r="<?= $radius1 ?>"
                stroke-dasharray="<?= $circumference1 ?>"
                stroke-dashoffset="<?= $offset1 ?>"
                data-percent="<?= $imagePct ?>" />

        <circle class="ring-progress ring-2"
                cx="250" cy="250" r="<?= $radius2 ?>"
                stroke-dasharray="<?= $circumference2 ?>"
                stroke-dashoffset="<?= $offset2 ?>"
                data-percent="<?= $atfPct ?>" />

        <circle class="ring-progress ring-3"
                cx="250" cy="250" r="<?= $radius3 ?>"
                stroke-dasharray="<?= $circumference3 ?>"
                stroke-dashoffset="<?= $offset3 ?>"
                data-percent="<?= $translationPct ?>" />

        <!-- Center monument text -->
        <text class="monument-number" x="250" y="240" text-anchor="middle">
            <?= $totalTablets ?>
        </text>
        <line class="monument-divider" x1="200" y1="255" x2="300" y2="255" />
        <text class="monument-label" x="250" y="275" text-anchor="middle">
            Tablets
        </text>
    </svg>

    <!-- Ring Labels (below SVG) - Side by side -->
    <div class="ring-labels">
        <div class="ring-label ring-label-1">
            <span class="label-name">Images</span>
            <span class="label-stat"><?= $imagePct ?>%</span>
            <span class="label-count"><?= $imageCount ?> tablets</span>
        </div>

        <div class="ring-label ring-label-2">
            <span class="label-name">Transliterations</span>
            <span class="label-stat"><?= $atfPct ?>%</span>
            <span class="label-count"><?= $atfCount ?> tablets</span>
        </div>

        <div class="ring-label ring-label-3">
            <span class="label-name">Translations</span>
            <span class="label-stat"><?= $translationPct ?>%</span>
            <span class="label-count"><?= $translationCount ?> tablets</span>
        </div>
    </div>
</div>
