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

// Calculate image path
$imagePath = "/images/photo/{$pNumber}.jpg";
$imageExists = file_exists(dirname(__DIR__) . "/images/photo/{$pNumber}.jpg");

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
            <?php if ($imageExists): ?>
                <img src="<?= $imagePath ?>" alt="<?= htmlspecialchars($tablet['designation']) ?>"
                     onerror="this.src='/assets/img/no-image.svg'">
                <p class="image-source">Source: CDLI</p>
            <?php else: ?>
                <div class="no-image">
                    <p>No image available</p>
                    <button class="btn btn-secondary" disabled>Upload Image</button>
                </div>
            <?php endif; ?>
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
</style>

<?php require_once __DIR__ . '/../includes/footer.php'; ?>
