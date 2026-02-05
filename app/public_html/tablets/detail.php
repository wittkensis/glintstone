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
$composites = getComposites($pNumber);

$pageTitle = $tablet['p_number'];

// Calculate image path - prefer local, fall back to CDLI
$localImagePath = "/images/{$pNumber}.jpg";
$localImageExists = file_exists(dirname(__DIR__) . "/images/{$pNumber}.jpg");
$cdliImageUrl = "https://cdli.ucla.edu/dl/photo/{$pNumber}.jpg";
$cdliLineartUrl = "https://cdli.ucla.edu/dl/lineart/{$pNumber}.jpg";

// Use local if available, otherwise CDLI
$imagePath = $localImageExists ? $localImagePath : $cdliImageUrl;
$imageSource = $localImageExists ? 'Local (CDLI)' : 'CDLI (Remote)';

require_once __DIR__ . '/../includes/header.php';
?>

<main class="container">
    <div class="detail-header">
        <h1><?= htmlspecialchars($tablet['p_number']) ?></h1>
        <p class="designation"><?= htmlspecialchars($tablet['designation'] ?? 'Unknown') ?></p>
        <div class="detail-meta">
            <?php if ($tablet['museum_no']): ?>
                <span title="Museum Number"><?= htmlspecialchars($tablet['museum_no']) ?></span>
            <?php endif; ?>
            <?php if ($tablet['excavation_no']): ?>
                <span title="Excavation Number"><?= htmlspecialchars($tablet['excavation_no']) ?></span>
            <?php endif; ?>
            <?php if ($tablet['material']): ?>
                <span title="Material"><?= htmlspecialchars($tablet['material']) ?></span>
            <?php endif; ?>
            <?php if ($tablet['language']): ?>
                <span title="Language"><?= htmlspecialchars($tablet['language']) ?></span>
            <?php endif; ?>
            <?php if ($tablet['width'] && $tablet['height']): ?>
                <span title="Dimensions"><?= $tablet['width'] ?>×<?= $tablet['height'] ?>×<?= $tablet['thickness'] ?? '?' ?> mm</span>
            <?php endif; ?>
        </div>
    </div>

    <!-- Pipeline View -->
    <section class="pipeline-view">
        <h2>Translation Pipeline</h2>
        <div class="pipeline-stages">
            <div class="pipeline-stage">
                <div class="stage-icon <?= $tablet['has_image'] ? 'complete' : 'missing' ?>">
                    <?= $tablet['has_image'] ? '✓' : '✗' ?>
                </div>
                <span class="stage-label">Image</span>
            </div>
            <div class="pipeline-stage">
                <div class="stage-icon <?= $tablet['has_ocr'] ? ($tablet['ocr_confidence'] > 0.8 ? 'complete' : 'partial') : 'missing' ?>">
                    <?= $tablet['has_ocr'] ? '⚠' : '✗' ?>
                </div>
                <span class="stage-label">OCR</span>
            </div>
            <div class="pipeline-stage">
                <div class="stage-icon <?= $tablet['has_atf'] ? 'complete' : 'missing' ?>">
                    <?= $tablet['has_atf'] ? '✓' : '✗' ?>
                </div>
                <span class="stage-label">ATF</span>
            </div>
            <div class="pipeline-stage">
                <div class="stage-icon <?= $tablet['has_lemmas'] ? 'complete' : 'missing' ?>">
                    <?= $tablet['has_lemmas'] ? '✓' : '✗' ?>
                </div>
                <span class="stage-label">Lemmas</span>
            </div>
            <div class="pipeline-stage">
                <div class="stage-icon <?= $tablet['has_translation'] ? 'complete' : 'missing' ?>">
                    <?= $tablet['has_translation'] ? '✓' : '✗' ?>
                </div>
                <span class="stage-label">Translation</span>
            </div>
        </div>
        <div class="quality-bar">
            <label>Quality Score: <?= round(($tablet['quality_score'] ?? 0) * 100) ?>%</label>
            <div class="progress-bar">
                <div class="progress-fill" style="width: <?= ($tablet['quality_score'] ?? 0) * 100 ?>%"></div>
            </div>
        </div>
    </section>

    <div class="detail-content">
        <!-- Image Panel -->
        <section class="tablet-image">
            <h3>1. Image</h3>
            <div class="image-container">
                <img src="<?= htmlspecialchars($imagePath) ?>"
                     alt="<?= htmlspecialchars($tablet['designation']) ?>"
                     data-local="<?= htmlspecialchars($localImagePath) ?>"
                     data-cdli-photo="<?= htmlspecialchars($cdliImageUrl) ?>"
                     data-cdli-lineart="<?= htmlspecialchars($cdliLineartUrl) ?>"
                     onerror="handleImageError(this)"
                     loading="lazy">
                <div class="image-loading">Loading image...</div>
            </div>
            <p class="image-source">Source: <?= $imageSource ?></p>
            <div class="image-options">
                <button class="btn btn-small" onclick="switchImage('photo')">Photo</button>
                <button class="btn btn-small btn-secondary" onclick="switchImage('lineart')">Line Art</button>
                <a href="https://cdli.ucla.edu/search/archival_view.php?ObjectID=<?= urlencode($pNumber) ?>"
                   target="_blank" class="btn btn-small btn-secondary">View on CDLI</a>
            </div>
        </section>

        <!-- Text Panel -->
        <section class="tablet-text">
            <h3>3. ATF (Transliteration)</h3>
            <?php if ($inscription && $inscription['atf']): ?>
                <div class="atf-display">
<?php
// Format ATF with syntax highlighting
$atf = htmlspecialchars($inscription['atf']);
$lines = explode("\n", $atf);
foreach ($lines as $line) {
    $line = trim($line);
    if (strpos($line, '&') === 0) {
        echo "<span class='directive'>$line</span>\n";
    } elseif (strpos($line, '@') === 0) {
        echo "<span class='directive'>$line</span>\n";
    } elseif (strpos($line, '#') === 0) {
        echo "<span class='directive'>$line</span>\n";
    } elseif (strpos($line, '$') === 0) {
        echo "<span class='directive'>$line</span>\n";
    } elseif (strpos($line, '>>') === 0) {
        echo "<span class='composite-ref'>$line</span>\n";
    } else {
        echo "$line\n";
    }
}
?>
                </div>
                <p class="atf-source">Source: <?= htmlspecialchars($tablet['atf_source'] ?? 'CDLI') ?></p>
            <?php else: ?>
                <div class="no-atf">
                    <p>No transliteration available</p>
                    <div class="contribute-buttons">
                        <button class="btn">Add Transliteration</button>
                        <button class="btn btn-secondary">Generate from OCR</button>
                    </div>
                </div>
            <?php endif; ?>
        </section>
    </div>

    <!-- Composites -->
    <?php if ($composites): ?>
    <section class="composites-section">
        <h3>Composite Texts</h3>
        <ul class="composite-list">
            <?php foreach ($composites as $comp): ?>
                <li>
                    <span class="q-number"><?= htmlspecialchars($comp['q_number']) ?></span>
                    <span class="comp-designation"><?= htmlspecialchars($comp['designation'] ?? '') ?></span>
                </li>
            <?php endforeach; ?>
        </ul>
    </section>
    <?php endif; ?>

    <!-- Actions -->
    <section class="actions-section">
        <h3>Contribute</h3>
        <div class="action-buttons">
            <button class="btn" disabled>Verify OCR</button>
            <button class="btn" disabled>Add Lemmatization</button>
            <button class="btn" disabled>Add Translation</button>
            <button class="btn btn-secondary" disabled>Start Discussion</button>
        </div>
        <p class="coming-soon">Contribution features coming soon</p>
    </section>
</main>

<style>
.designation {
    font-size: 1.25rem;
    color: var(--color-text-muted);
    margin-bottom: var(--space-4);
}

.quality-bar {
    margin-top: var(--space-4);
}

.quality-bar label {
    display: block;
    margin-bottom: var(--space-2);
    font-size: 0.875rem;
    color: var(--color-text-muted);
}

.progress-bar {
    height: 8px;
    background: var(--color-surface);
    border-radius: 4px;
    overflow: hidden;
}

.progress-fill {
    height: 100%;
    background: var(--color-accent);
    transition: width 0.3s;
}

.tablet-text h3,
.tablet-image h3 {
    margin-bottom: var(--space-4);
}

.image-source,
.atf-source {
    font-size: 0.75rem;
    color: var(--color-text-subtle);
    margin-top: var(--space-2);
}

.no-image,
.no-atf {
    padding: var(--space-8);
    text-align: center;
    color: var(--color-text-muted);
    background: var(--color-surface);
    border-radius: var(--radius-md);
}

.contribute-buttons {
    display: flex;
    gap: var(--space-2);
    justify-content: center;
    margin-top: var(--space-4);
}

.btn-secondary {
    background: var(--color-surface);
    color: var(--color-text);
    border: 1px solid var(--color-border);
}

.btn-secondary:hover {
    background: var(--color-bg-subtle);
}

.composites-section {
    margin-top: var(--space-8);
}

.composite-list {
    list-style: none;
    padding: 0;
}

.composite-list li {
    padding: var(--space-3);
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-sm);
    margin-bottom: var(--space-2);
}

.q-number {
    font-family: var(--font-mono);
    color: var(--color-success);
    margin-right: var(--space-4);
}

.actions-section {
    margin-top: var(--space-8);
    padding: var(--space-6);
    background: var(--color-bg-elevated);
    border: 1px solid var(--color-border);
    border-radius: var(--radius-lg);
}

.action-buttons {
    display: flex;
    flex-wrap: wrap;
    gap: var(--space-3);
    margin-bottom: var(--space-4);
}

.coming-soon {
    font-size: 0.875rem;
    color: var(--color-text-subtle);
    font-style: italic;
}

.btn:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

/* Image container */
.image-container {
    position: relative;
    min-height: 200px;
    background: var(--color-surface);
    border-radius: var(--radius-md);
    overflow: hidden;
}

.image-container img {
    width: 100%;
    height: auto;
    display: block;
}

.image-container img.loading {
    opacity: 0;
}

.image-container img.loaded {
    opacity: 1;
    transition: opacity 0.3s;
}

.image-container img.error {
    display: none;
}

.image-loading {
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    color: var(--color-text-muted);
    font-size: 0.875rem;
}

.image-container img.loaded + .image-loading {
    display: none;
}

.image-options {
    display: flex;
    gap: var(--space-2);
    margin-top: var(--space-3);
    flex-wrap: wrap;
}

.btn-small {
    padding: var(--space-1) var(--space-3);
    font-size: 0.75rem;
}

.image-error {
    padding: var(--space-6);
    text-align: center;
    color: var(--color-text-muted);
}
</style>

<script>
// Image error handling with fallback chain
let currentImageType = 'photo';

function handleImageError(img) {
    const cdliPhoto = img.dataset.cdliPhoto;
    const cdliLineart = img.dataset.cdliLineart;
    const currentSrc = img.src;

    // Try fallback chain: local -> cdli photo -> cdli lineart -> error
    if (currentSrc !== cdliPhoto && currentImageType === 'photo') {
        img.src = cdliPhoto;
        updateImageSource('CDLI (Remote)');
    } else if (currentSrc !== cdliLineart) {
        img.src = cdliLineart;
        currentImageType = 'lineart';
        updateImageSource('CDLI Line Art');
    } else {
        // All sources failed
        img.classList.add('error');
        img.parentElement.innerHTML = `
            <div class="image-error">
                <p>No image available from CDLI</p>
                <a href="https://cdli.ucla.edu/search/archival_view.php?ObjectID=${img.alt}"
                   target="_blank" class="btn btn-secondary">Check CDLI directly</a>
            </div>
        `;
    }
}

function switchImage(type) {
    const img = document.querySelector('.image-container img');
    if (!img) return;

    currentImageType = type;
    if (type === 'photo') {
        img.src = img.dataset.cdliPhoto;
        updateImageSource('CDLI Photo');
    } else {
        img.src = img.dataset.cdliLineart;
        updateImageSource('CDLI Line Art');
    }
}

function updateImageSource(source) {
    const sourceEl = document.querySelector('.image-source');
    if (sourceEl) {
        sourceEl.textContent = 'Source: ' + source;
    }
}

// Add loaded class when image loads and trigger thumbnail caching
document.addEventListener('DOMContentLoaded', function() {
    const img = document.querySelector('.image-container img');
    if (img) {
        img.classList.add('loading');
        img.onload = function() {
            this.classList.remove('loading');
            this.classList.add('loaded');

            // Trigger thumbnail generation in background if image loaded from CDLI
            if (this.src.includes('cdli.ucla.edu')) {
                cacheThumbnail();
            }
        };
    }
});

// Cache thumbnail in background when viewing from CDLI
function cacheThumbnail() {
    const pNumber = '<?= htmlspecialchars($pNumber) ?>';
    // Prefetch thumbnail to cache it for list views
    const thumbnailUrl = `/api/thumbnail.php?p=${pNumber}&size=200`;
    fetch(thumbnailUrl, { method: 'GET' })
        .then(response => {
            if (response.ok) {
                console.log('Thumbnail cached for', pNumber);
            }
        })
        .catch(() => {
            // Silent fail - thumbnail caching is non-critical
        });
}
</script>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
