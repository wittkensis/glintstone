<?php
/**
 * Chevron Filter Component
 * Horizontal chevron-style navigation filter for status/stage filtering
 *
 * Generic, reusable component for any filtered list page
 *
 * Required Variables:
 * @var array $stages - Array of stage definitions, each with:
 *                      - 'label' (string): Full label text
 *                      - 'value' (string): URL parameter value
 *                      - 'shortLabel' (string, optional): Abbreviated label for mobile
 *
 * Optional Variables:
 * @var string|null $currentValue - Currently active filter value (default: null)
 * @var string $urlParam - URL parameter name (default: 'status')
 * @var string $ariaLabel - ARIA label for navigation (default: 'Filter by status')
 *
 * Example Usage (Tablets):
 * $stages = [
 *     ['label' => 'Image', 'value' => 'has_image'],
 *     ['label' => 'Signs', 'value' => 'machine_ocr'],
 *     ['label' => 'ATF', 'value' => 'has_atf'],
 *     ['label' => 'Lemmas', 'value' => 'has_lemmas'],
 *     ['label' => 'Translation', 'value' => 'has_translation']
 * ];
 * $currentValue = $_GET['pipeline'] ?? null;
 * $urlParam = 'pipeline';
 * $ariaLabel = 'Filter by pipeline stage';
 * include 'components/chevron-filter.php';
 *
 * Example Usage (Dictionary):
 * $stages = [
 *     ['label' => 'Draft', 'value' => 'draft'],
 *     ['label' => 'Review', 'value' => 'review'],
 *     ['label' => 'Published', 'value' => 'published']
 * ];
 * $currentValue = $_GET['entry_status'] ?? null;
 * $urlParam = 'entry_status';
 * $ariaLabel = 'Filter by entry status';
 * include 'components/chevron-filter.php';
 */

// Validate required variables
if (!isset($stages) || !is_array($stages)) {
    throw new InvalidArgumentException('Chevron filter component requires $stages array');
}

// Set defaults for optional variables
$currentValue = $currentValue ?? null;
$urlParam = $urlParam ?? 'status';
$ariaLabel = $ariaLabel ?? 'Filter by status';

/**
 * Build URL for a filter stage
 * Clicking active stage clears filter; clicking inactive stage applies it
 *
 * @param string $stageValue The stage value to filter by
 * @param string|null $currentValue Currently active filter value
 * @param string $urlParam URL parameter name
 * @return string Generated URL with query parameters
 */
function buildChevronFilterUrl($stageValue, $currentValue, $urlParam) {
    $params = $_GET;
    unset($params['page']); // Reset pagination when changing filters

    if ($stageValue === $currentValue) {
        // Clicking active stage clears the filter
        unset($params[$urlParam]);
    } else {
        // Set new filter value
        $params[$urlParam] = $stageValue;
    }

    return '?' . http_build_query($params);
}
?>

<nav class="chevron-filter" aria-label="<?= htmlspecialchars($ariaLabel) ?>">
    <?php foreach ($stages as $stage): ?>
        <?php
        $isActive = $currentValue === $stage['value'];
        $url = buildChevronFilterUrl($stage['value'], $currentValue, $urlParam);
        $label = $stage['label'];
        $shortLabel = $stage['shortLabel'] ?? $label;
        ?>
        <a href="<?= htmlspecialchars($url) ?>"
           class="chevron-filter__step <?= $isActive ? 'is-active' : '' ?>"
           aria-current="<?= $isActive ? 'true' : 'false' ?>"
           title="<?= htmlspecialchars($label) ?>">
            <span class="chevron-filter__label"><?= htmlspecialchars($label) ?></span>
        </a>
    <?php endforeach; ?>
</nav>
