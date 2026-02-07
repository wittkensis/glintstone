<?php
/**
 * Tablet detail page with pipeline view
 */

require_once __DIR__ . '/../includes/db.php';

$pNumber = $_GET['p'] ?? null;

if (!$pNumber) {
    header('Location: list.php');
    exit;
}

$tablet = getArtifact($pNumber);

if (!$tablet) {
    http_response_code(404);
    $pageTitle = 'Tablet Not Found';
    require_once __DIR__ . '/../includes/header.php';
    echo '<main class="container"><h1>Tablet Not Found</h1><p>The requested tablet does not exist.</p></main>';
    require_once __DIR__ . '/../includes/footer.php';
    exit;
}

$inscription = getInscription($pNumber);
$translations = getTranslations($pNumber);
$composites = getComposites($pNumber);

// Parse museum and excavation codes for enhanced display
$museumDisplay = null;
$excavationDisplay = null;

if ($tablet['museum_no']) {
    $parsed = parseMuseumNumber($tablet['museum_no']);
    if ($parsed['code']) {
        $museumInfo = getMuseumName($parsed['code']);
        if ($museumInfo) {
            $museumDisplay = [
                'name' => $museumInfo['name'],
                'full' => $tablet['museum_no']
            ];
        }
    }
}

if ($tablet['excavation_no']) {
    $parsed = parseExcavationNumber($tablet['excavation_no']);
    if ($parsed['code']) {
        $siteInfo = getExcavationSiteName($parsed['code']);
        if ($siteInfo) {
            $excavationDisplay = [
                'name' => $siteInfo['ancient_name'] ?? $siteInfo['name'],
                'full' => $tablet['excavation_no']
            ];
        }
    }
}

$pageTitle = $tablet['p_number'];

/**
 * Calculate pipeline status with inference logic
 *
 * Status types:
 * - complete: Data is available
 * - partial: Data is available but incomplete
 * - inferred: Data can be inferred from downstream stages
 * - skipped: Intermediate step not captured, but downstream stages exist (not an error)
 * - missing: Data is truly missing
 */
function getPipelineStatus(array $tablet, bool $localImageExists): array {
    $pipeline = [];

    $hasAtf = !empty($tablet['has_atf']);
    $hasOcr = !empty($tablet['has_sign_annotations']);
    $hasLemmas = !empty($tablet['has_lemmas']);
    $hasTrans = !empty($tablet['has_translation']);

    // Determine if tablet has been "fully studied" (has translation or lemmas)
    // If so, missing intermediate steps are "not captured" rather than "missing"
    $fullyStudied = $hasTrans;
    $partiallyStudied = $hasLemmas || $hasAtf;

    // STAGE 1: Image
    $pipeline['image'] = [
        'status' => $tablet['has_image'] ? 'complete' : 'missing',
        'source' => $localImageExists ? 'Local' : ($tablet['has_image'] ? 'CDLI' : null),
        'next_step' => !$tablet['has_image'] ? 'Needs image capture or CDLI link' : null
    ];

    // STAGE 2: Sign Detection (ML - optional enrichment)
    // Signs are optional ML data; if translation/lemmas exist without signs, it's "not captured"
    $signStatus = 'missing';
    $signSource = null;
    $signHint = null;
    if ($hasOcr) {
        $signStatus = 'complete';
        $signSource = 'CompVis ML';
    } elseif ($fullyStudied || $partiallyStudied) {
        // Tablet was studied without ML sign detection - that's fine
        $signStatus = 'skipped';
        $signHint = 'ML not run';
    } else {
        $signHint = 'Requires image';
    }
    $pipeline['signs'] = [
        'status' => $signStatus,
        'source' => $signSource,
        'next_step' => $signHint
    ];

    // STAGE 3: Transliteration (human reading)
    $translitStatus = 'missing';
    $translitSource = null;
    $translitHint = null;
    if ($hasAtf) {
        $translitStatus = 'complete';
        $translitSource = $tablet['atf_source'] ?? 'CDLI';
    } elseif ($hasLemmas || $hasTrans) {
        // Has downstream data, so transliteration must exist somewhere
        $translitStatus = 'inferred';
        $translitSource = 'Exists (not imported)';
    } else {
        $translitHint = 'Not available';
    }
    $pipeline['transliteration'] = [
        'status' => $translitStatus,
        'source' => $translitSource,
        'next_step' => $translitHint
    ];

    // STAGE 4: Lemmatization
    $lemmaStatus = 'missing';
    $lemmaSource = null;
    $lemmaDetail = null;
    $lemmaHint = null;
    if ($hasLemmas) {
        $coverage = $tablet['lemma_coverage'] ?? 1.0;
        $lemmaStatus = ($coverage < 1.0) ? 'partial' : 'complete';
        $lemmaDetail = ($coverage < 1.0) ? round($coverage * 100) . '%' : null;
        $lemmaSource = 'ORACC';
    } elseif ($fullyStudied) {
        // Has translation but no lemmas - scholarly work done, just not in ORACC
        $lemmaStatus = 'skipped';
        $lemmaHint = 'Not in ORACC';
    } else {
        $lemmaHint = 'Requires transliteration';
    }
    $pipeline['lemmas'] = [
        'status' => $lemmaStatus,
        'source' => $lemmaSource,
        'detail' => $lemmaDetail,
        'next_step' => $lemmaHint
    ];

    // STAGE 5: Translation
    $pipeline['translation'] = [
        'status' => $hasTrans ? 'complete' : 'missing',
        'source' => $hasTrans ? 'CDLI' : null,
        'next_step' => !$hasTrans ? 'No translation available' : null
    ];

    return $pipeline;
}


// Calculate image path - prefer local, fall back to CDLI
$localImagePath = "/images/{$pNumber}.jpg";
$localImageExists = file_exists(dirname(__DIR__) . "/images/{$pNumber}.jpg");
$cdliImageUrl = "https://cdli.ucla.edu/dl/photo/{$pNumber}.jpg";
$cdliLineartUrl = "https://cdli.ucla.edu/dl/lineart/{$pNumber}.jpg";
$imagePath = $localImageExists ? $localImagePath : $cdliImageUrl;
$imageSource = $localImageExists ? 'Local (CDLI)' : 'CDLI (Remote)';

// Calculate pipeline status
$pipelineStatus = getPipelineStatus($tablet, $localImageExists);

// Determine default viewer state based on data availability
$hasData = !empty($inscription['atf']) || !empty($tablet['has_lemmas']) || !empty($tablet['has_translation']);
$defaultViewerState = $hasData ? 'collapsed' : 'expanded';

require_once __DIR__ . '/../includes/header.php';
?>
<!-- Shared Components -->
<link rel="stylesheet" href="/assets/css/components/atf-words.css">
<link rel="stylesheet" href="/assets/css/components/empty-states.css">

<!-- Tablet Layout -->
<link rel="stylesheet" href="/assets/css/layout/immersive.css">

<!-- Tablet Components -->
<link rel="stylesheet" href="/assets/css/components/tablet-header.css">
<link rel="stylesheet" href="/assets/css/components/composite-panel.css">
<link rel="stylesheet" href="/assets/css/components/tablet-metadata.css">
<link rel="stylesheet" href="/assets/css/components/tablet-sections.css">
<link rel="stylesheet" href="/assets/css/components/ocr-box.css">
<link rel="stylesheet" href="/assets/css/components/tablet-translation.css">

<!-- ATF Viewer Components -->
<link rel="stylesheet" href="/assets/css/components/atf-viewer-core.css">
<link rel="stylesheet" href="/assets/css/components/atf-content.css">
<link rel="stylesheet" href="/assets/css/components/knowledge-sidebar-compact.css">
<link rel="stylesheet" href="/assets/css/components/atf-parallel.css">

<!-- Zoombox Components -->
<link rel="stylesheet" href="/assets/css/components/zoombox-core.css">
<link rel="stylesheet" href="/assets/css/components/zoombox-minimap.css">

<div class="tablet-detail-page">
<main class="container">
    <!-- Composite Panel (full width) -->
    <?php if (!empty($composites)): ?>
    <div class="composite-panel" id="composite-panel" data-q-number="<?= htmlspecialchars($composites[0]['q_number']) ?>">
        <div class="composite-panel__header">
            <div class="composite-panel__title-group">
                <h2 class="composite-panel__title"><?= htmlspecialchars($composites[0]['name'] ?? $composites[0]['q_number']) ?></h2>
                <?php if (!empty($composites[0]['name'])): ?>
                    <span class="composite-panel__subtitle"><?= htmlspecialchars($composites[0]['q_number']) ?></span>
                <?php endif; ?>
            </div>
            <span class="composite-panel__count" id="composite-count">Loading...</span>
        </div>
        <div class="composite-panel__list" id="composite-list">
            <div class="composite-panel__loading">Loading tablets...</div>
        </div>
    </div>
    <?php endif; ?>

    <!-- Inner container for header/meta (constrained width) -->
    <div class="container-inner">
    <!-- Compact Header -->
    <header class="tablet-header">
        <div class="tablet-header__main">
            <div class="tablet-header__identity">
                <h1 class="tablet-header__pnumber"><?= htmlspecialchars($tablet['p_number']) ?></h1>
            </div>
            <div class="tablet-header__badges">
                <?php if ($tablet['language']): ?>
                    <span class="language-badge"><?= htmlspecialchars($tablet['language']) ?></span>
                <?php endif; ?>
            </div>
        </div>
        <div class="tablet-header__actions">
            <?php if (!empty($composites)): ?>
                <button class="btn btn--icon-left btn--toggle" id="composite-toggle" aria-expanded="false" aria-controls="composite-panel" title="View composite text">
                    <?= icon('layers') ?>
                    <span><?= htmlspecialchars($composites[0]['name'] ?? $composites[0]['q_number']) ?></span>
                </button>
            <?php endif; ?>
            <div class="actions-menu">
                <button class="actions-menu__trigger" aria-haspopup="true" aria-expanded="false">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                        <circle cx="12" cy="12" r="1"/><circle cx="12" cy="5" r="1"/><circle cx="12" cy="19" r="1"/>
                    </svg>
                </button>
                <div class="actions-menu__dropdown">
                    <a href="https://cdli.ucla.edu/search/archival_view.php?ObjectID=<?= urlencode($pNumber) ?>"
                       target="_blank" class="actions-menu__item">
                        <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <path d="M18 13v6a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2V8a2 2 0 0 1 2-2h6"/>
                            <polyline points="15 3 21 3 21 9"/><line x1="10" y1="14" x2="21" y2="3"/>
                        </svg>
                        View on CDLI
                    </a>
                </div>
            </div>
        </div>
    </header>

    <!-- Primary Metadata -->
    <?php
    // Check if we have secondary metadata to show
    $hasSecondary = $museumDisplay || $tablet['museum_no'] || $tablet['genre'] || ($tablet['width'] && $tablet['height']);
    ?>
    <div class="tablet-meta">
        <dl class="tablet-meta__row">
            <?php if ($tablet['period']): ?>
                <div class="meta-item">
                    <dt>Period</dt>
                    <dd><?= htmlspecialchars($tablet['period']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($tablet['provenience']): ?>
                <div class="meta-item">
                    <dt>Provenience</dt>
                    <dd><?= htmlspecialchars($tablet['provenience']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($excavationDisplay): ?>
                <div class="meta-item">
                    <dt>Excavation</dt>
                    <dd>
                        <span class="meta-name"><?= htmlspecialchars($excavationDisplay['name']) ?></span>
                        <span class="meta-code">(<?= htmlspecialchars($excavationDisplay['full']) ?>)</span>
                    </dd>
                </div>
            <?php elseif ($tablet['excavation_no']): ?>
                <div class="meta-item">
                    <dt>Excavation</dt>
                    <dd><?= htmlspecialchars($tablet['excavation_no']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($hasSecondary): ?>
                <div class="meta-item">
                    <button class="tablet-meta__toggle" id="meta-toggle" aria-expanded="false" aria-controls="meta-secondary">
                        <svg class="tablet-meta__toggle-icon" width="10" height="10" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
                            <polyline points="9 18 15 12 9 6"/>
                        </svg>
                        More
                    </button>
                </div>
            <?php endif; ?>
        </dl>
        <?php if ($hasSecondary): ?>
        <dl class="tablet-meta__secondary" id="meta-secondary">
            <?php if ($tablet['designation']): ?>
                <div class="meta-item">
                    <dt>Designation</dt>
                    <dd><?= htmlspecialchars($tablet['designation']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($museumDisplay): ?>
                <div class="meta-item">
                    <dt>Museum</dt>
                    <dd>
                        <span class="meta-name"><?= htmlspecialchars($museumDisplay['name']) ?></span>
                        <span class="meta-code">(<?= htmlspecialchars($museumDisplay['full']) ?>)</span>
                    </dd>
                </div>
            <?php elseif ($tablet['museum_no']): ?>
                <div class="meta-item">
                    <dt>Museum</dt>
                    <dd><?= htmlspecialchars($tablet['museum_no']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($tablet['genre']): ?>
                <div class="meta-item">
                    <dt>Genre</dt>
                    <dd><?= htmlspecialchars($tablet['genre']) ?></dd>
                </div>
            <?php endif; ?>
            <?php if ($tablet['width'] && $tablet['height']): ?>
                <div class="meta-item">
                    <dt>Dimensions</dt>
                    <dd><?= $tablet['width'] ?>×<?= $tablet['height'] ?>×<?= $tablet['thickness'] ?? '?' ?> mm</dd>
                </div>
            <?php endif; ?>
        </dl>
        <?php endif; ?>
    </div>

    <!-- Pipeline Status -->
    <?php
    // Get status label for display
    function getStatusLabel($status): string {
        return match($status['status']) {
            'complete' => $status['source'] ?? '✓',
            'partial' => $status['detail'] ?? 'Partial',
            'inferred' => 'Inferred',
            'skipped' => 'N/A',
            default => 'Missing'
        };
    }
    // Get tooltip text
    function getPipelineTooltip($stage, $status): string {
        $text = ucfirst($stage) . ': ' . match($status['status']) {
            'complete' => 'Available',
            'partial' => 'Partial (' . ($status['detail'] ?? '') . ')',
            'inferred' => 'Inferred from downstream data',
            'skipped' => 'Not captured (tablet fully studied)',
            default => 'Missing'
        };
        if ($status['source']) $text .= ' · Source: ' . $status['source'];
        if ($status['next_step']) $text .= ' · ' . $status['next_step'];
        return $text;
    }
    ?>
    <nav class="pipeline-chevron" aria-label="Data pipeline status">
        <div class="pipeline-chevron__step pipeline-chevron__step--<?= $pipelineStatus['image']['status'] ?>"
             title="<?= htmlspecialchars(getPipelineTooltip('image', $pipelineStatus['image'])) ?>">
            <span class="pipeline-chevron__label">Image</span>
            <span class="pipeline-chevron__status"><?= getStatusLabel($pipelineStatus['image']) ?></span>
        </div>
        <div class="pipeline-chevron__step pipeline-chevron__step--<?= $pipelineStatus['signs']['status'] ?>"
             title="<?= htmlspecialchars(getPipelineTooltip('signs', $pipelineStatus['signs'])) ?>">
            <span class="pipeline-chevron__label">Signs</span>
            <span class="pipeline-chevron__status"><?= getStatusLabel($pipelineStatus['signs']) ?></span>
        </div>
        <div class="pipeline-chevron__step pipeline-chevron__step--<?= $pipelineStatus['transliteration']['status'] ?>"
             title="<?= htmlspecialchars(getPipelineTooltip('ATF', $pipelineStatus['transliteration'])) ?>">
            <span class="pipeline-chevron__label">ATF</span>
            <span class="pipeline-chevron__status"><?= getStatusLabel($pipelineStatus['transliteration']) ?></span>
        </div>
        <div class="pipeline-chevron__step pipeline-chevron__step--<?= $pipelineStatus['lemmas']['status'] ?>"
             title="<?= htmlspecialchars(getPipelineTooltip('lemmas', $pipelineStatus['lemmas'])) ?>">
            <span class="pipeline-chevron__label">Lemmas</span>
            <span class="pipeline-chevron__status"><?= getStatusLabel($pipelineStatus['lemmas']) ?></span>
        </div>
        <div class="pipeline-chevron__step pipeline-chevron__step--<?= $pipelineStatus['translation']['status'] ?>"
             title="<?= htmlspecialchars(getPipelineTooltip('translation', $pipelineStatus['translation'])) ?>">
            <span class="pipeline-chevron__label">Translation</span>
            <span class="pipeline-chevron__status"><?= getStatusLabel($pipelineStatus['translation']) ?></span>
        </div>
    </nav>
    </div><!-- .container-inner -->
</main>

<div class="tablet-detail-fullpage">
    <div class="tablet-detail-viewer"
         data-state="<?= $defaultViewerState ?>"
         data-p-number="<?= htmlspecialchars($pNumber) ?>">

        <div class="viewer-panel">
            <section class="tablet-image">
            <!-- Zoombox Component -->
            <div class="zoombox" id="tablet-zoombox"
                 data-p-number="<?= htmlspecialchars($pNumber) ?>"
                 data-local="<?= htmlspecialchars($localImagePath) ?>"
                 data-cdli-photo="<?= htmlspecialchars($cdliImageUrl) ?>"
                 data-cdli-lineart="<?= htmlspecialchars($cdliLineartUrl) ?>">

                <div class="zoombox__viewport">
                    <div class="zoombox__transform">
                        <img class="zoombox__image is-loading"
                             src=""
                             alt="<?= htmlspecialchars($tablet['designation']) ?>">
                        <div class="zoombox__overlays"></div>
                    </div>

                    <div class="zoombox__loading">Loading image...</div>
                    <div class="zoombox__placeholder">
                        <span class="zoombox__placeholder-icon">𒀭</span>
                        <span>No image available</span>
                    </div>
                </div>

                <!-- Zoom controls (top-left) -->
                <div class="zoombox__controls">
                    <button class="zoombox__btn" data-action="zoom-out" title="Zoom out (-)">−</button>
                    <button class="zoombox__btn" data-action="zoom-in" title="Zoom in (+)">+</button>
                    <button class="zoombox__btn zoombox__btn--reset" data-action="reset" title="Reset (0)">↺</button>
                </div>

                <!-- Minimap (top-right) -->
                <div class="zoombox__minimap-container">
                    <div class="zoombox__minimap">
                        <canvas class="zoombox__minimap-canvas"></canvas>
                        <div class="zoombox__minimap-viewport"></div>
                    </div>
                </div>
            </div>

            <p class="image-source" id="image-source">Source: <?= $imageSource ?></p>
            <div class="image-options">
                <label class="annotation-toggle btn btn-small" id="annotation-toggle" style="display: none;">
                    <input type="checkbox" id="annotation-checkbox">
                    <span>Signs</span>
                    <span class="annotation-badge" id="annotation-count"></span>
                </label>
            </div>
        </section>
        </div>

        <div class="atf-panel">
            <!-- ATF Content -->
            <?php if ($inscription && $inscription['atf']): ?>
                <div class="atf-viewer-container" id="atf-viewer" data-p-number="<?= htmlspecialchars($pNumber) ?>"></div>
                <p class="atf-source">Source: <?= htmlspecialchars($tablet['atf_source'] ?? 'CDLI') ?></p>
            <?php else: ?>
                <!-- Viewer Toggle (only for tablets without ATF) -->
                <button class="viewer-toggle" aria-label="Toggle viewer size" title="Expand/collapse tablet image">
                    <?= icon('expand', 'viewer-toggle__icon-expand') ?>
                    <?= icon('collapse', 'viewer-toggle__icon-collapse') ?>
                </button>

                <div class="no-atf" id="atf-container">
                    <p>No transliteration available</p>
                    <div class="contribute-buttons">
                        <button class="btn btn-secondary" disabled>Add Transliteration</button>
                    </div>
                </div>
            <?php endif; ?>
        </div>
    </div>
</div>
</div>

<script src="/assets/js/zoombox.js"></script>
<script src="/assets/js/atf-viewer.js"></script>
<script src="/assets/js/tablet-detail.js"></script>
