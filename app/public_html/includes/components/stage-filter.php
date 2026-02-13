<?php
/**
 * Stage Filter Component
 * Pill-shaped pipeline stage selector for filtering by data completeness
 *
 * Required Variables:
 * @var array $stages - Array of stage definitions, each with:
 *                      - 'label' (string): Display label (sentence case)
 *                      - 'value' (string): URL parameter value
 *
 * Optional Variables:
 * @var string|null $currentValue - Currently active filter value (default: null)
 * @var string $urlParam - URL parameter name (default: 'status')
 * @var string $ariaLabel - ARIA label for navigation (default: 'Filter by status')
 */

if (!isset($stages) || !is_array($stages)) {
    throw new InvalidArgumentException('Stage filter component requires $stages array');
}

$currentValue = $currentValue ?? null;
$urlParam = $urlParam ?? 'status';
$ariaLabel = $ariaLabel ?? 'Filter by status';

function buildStageFilterUrl($stageValue, $currentValue, $urlParam) {
    $params = $_GET;
    unset($params['page']);

    if ($stageValue === $currentValue || $stageValue === '') {
        unset($params[$urlParam]);
    } else {
        $params[$urlParam] = $stageValue;
    }

    return '?' . http_build_query($params);
}
?>

<nav class="stage-filter btn-group" aria-label="<?= htmlspecialchars($ariaLabel) ?>">
    <?php foreach ($stages as $stage): ?>
        <?php
        $isActive = ($stage['value'] === '') ? !$currentValue : ($currentValue === $stage['value']);
        $url = buildStageFilterUrl($stage['value'], $currentValue, $urlParam);
        ?>
        <a href="<?= htmlspecialchars($url) ?>"
           class="btn btn-group-item <?= $isActive ? 'btn-group-item--active' : '' ?>"
           <?= $isActive ? 'aria-current="true"' : '' ?>>
            <?= htmlspecialchars($stage['label']) ?>
        </a>
    <?php endforeach; ?>
</nav>
