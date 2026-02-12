<?php
/**
 * Pipeline Status Component
 * Unified visualization for tablet processing stages
 *
 * Required variables:
 * @var array $pipelineStatus - Status array from getPipelineStatus() or built from tablet data
 *
 * Optional variables:
 * @var string $variant - 'compact' (cards), 'expanded' (detail page), or 'inline' (header). Default: 'compact'
 */

$variant = $variant ?? 'compact';

// Stage definitions
$stages = ['image', 'signs', 'transliteration', 'lemmas', 'translation'];
$stageLabels = [
    'image' => 'Image',
    'signs' => 'Signs',
    'transliteration' => 'ATF',
    'lemmas' => 'Lemmas',
    'translation' => 'Translation'
];

// Calculate next step (first stage that needs attention)
$nextStage = null;
foreach ($stages as $stage) {
    $status = $pipelineStatus[$stage]['status'] ?? 'missing';
    // Skip "skipped" and "complete" stages
    if ($status !== 'complete' && $status !== 'skipped') {
        $nextStage = $stage;
        break;
    }
}

// Calculate completion count for aria-label
$completeCount = 0;
foreach ($stages as $stage) {
    if (($pipelineStatus[$stage]['status'] ?? 'missing') === 'complete') {
        $completeCount++;
    }
}

$ariaLabel = "Pipeline status: {$completeCount} of 5 stages complete";
if ($nextStage) {
    $ariaLabel .= ". Next: " . $stageLabels[$nextStage];
}

/**
 * Get display text for status
 */
if (!function_exists('getPipelineStatusDisplay')) {
    function getPipelineStatusDisplay(array $data): string {
        $status = $data['status'] ?? 'missing';
        $source = $data['source'] ?? null;
        $detail = $data['detail'] ?? null;

        return match($status) {
            'complete' => $source ?? 'Available',
            'partial' => ($detail ?? 'Partial') . ($source ? " ({$source})" : ''),
            'inferred' => 'Inferred',
            'skipped' => 'N/A',
            default => 'Missing'
        };
    }
}
?>

<?php if ($variant === 'compact'): ?>
<div class="pipeline pipeline--compact" aria-label="<?= htmlspecialchars($ariaLabel) ?>">
    <?php foreach ($stages as $stage):
        $data = $pipelineStatus[$stage] ?? ['status' => 'missing'];
        $isNext = ($stage === $nextStage);
    ?>
    <span class="pipeline__segment <?= $isNext ? 'pipeline__segment--next' : '' ?>"
          data-stage="<?= $stage ?>"
          data-status="<?= htmlspecialchars($data['status'] ?? 'missing') ?>"
          <?php if (!empty($data['source'])): ?>data-source="<?= htmlspecialchars($data['source']) ?>"<?php endif; ?>
          <?php if (!empty($data['detail'])): ?>data-detail="<?= htmlspecialchars($data['detail']) ?>"<?php endif; ?>
          <?php if (!empty($data['next_step'])): ?>data-next="<?= htmlspecialchars($data['next_step']) ?>"<?php endif; ?>></span>
    <?php endforeach; ?>
</div>

<?php elseif ($variant === 'inline'): ?>
<?php
// Build next step label for inline display
$nextStepLabel = $nextStage ? 'Needs ' . $stageLabels[$nextStage] : 'Complete';
$nextStepHint = $nextStage ? ($pipelineStatus[$nextStage]['next_step'] ?? '') : '';
?>
<div class="pipeline pipeline--inline"
     aria-label="<?= htmlspecialchars($ariaLabel) ?>"
     title="<?= htmlspecialchars($nextStage ? "Next: {$nextStepLabel}" . ($nextStepHint ? " - {$nextStepHint}" : '') : 'Pipeline complete') ?>">
    <div class="pipeline__dots">
        <?php foreach ($stages as $stage):
            $data = $pipelineStatus[$stage] ?? ['status' => 'missing'];
            $isNext = ($stage === $nextStage);
        ?>
        <span class="pipeline__dot <?= $isNext ? 'pipeline__dot--next' : '' ?>"
              data-status="<?= htmlspecialchars($data['status'] ?? 'missing') ?>"></span>
        <?php endforeach; ?>
    </div>
    <span class="pipeline__next-label"><?= htmlspecialchars($nextStepLabel) ?></span>
</div>

<?php else: /* expanded variant */ ?>
<nav class="pipeline pipeline--expanded" aria-label="<?= htmlspecialchars($ariaLabel) ?>">
    <?php foreach ($stages as $stage):
        $data = $pipelineStatus[$stage] ?? ['status' => 'missing'];
        $isNext = ($stage === $nextStage);
        $statusDisplay = getPipelineStatusDisplay($data);
    ?>
    <div class="pipeline__segment <?= $isNext ? 'pipeline__segment--next' : '' ?>"
         data-stage="<?= $stage ?>"
         data-status="<?= htmlspecialchars($data['status'] ?? 'missing') ?>"
         <?php if (!empty($data['source'])): ?>data-source="<?= htmlspecialchars($data['source']) ?>"<?php endif; ?>
         <?php if (!empty($data['detail'])): ?>data-detail="<?= htmlspecialchars($data['detail']) ?>"<?php endif; ?>
         <?php if (!empty($data['next_step'])): ?>data-next="<?= htmlspecialchars($data['next_step']) ?>"<?php endif; ?>>
        <span class="pipeline__bar"></span>
        <div class="pipeline__body">
            <span class="pipeline__label"><?= $stageLabels[$stage] ?></span>
            <span class="pipeline__status"><?= htmlspecialchars($statusDisplay) ?></span>
            <?php if ($isNext): ?>
            <span class="pipeline__next-hint">Next step</span>
            <?php endif; ?>
        </div>
    </div>
    <?php endforeach; ?>
</nav>

<!-- Pipeline Popover (shared, positioned via JS) -->
<div class="pipeline-popover" id="pipeline-popover" aria-hidden="true">
    <div class="pipeline-popover__header"></div>
    <div class="pipeline-popover__status"></div>
    <div class="pipeline-popover__source"></div>
    <div class="pipeline-popover__next"></div>
</div>
<?php endif; ?>
