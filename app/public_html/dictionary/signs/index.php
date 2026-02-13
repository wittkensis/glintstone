<?php
/**
 * Signs Browser
 *
 * 3-column master-detail view for browsing cuneiform signs:
 * - Column 1: Groupings (Polyphony, Usage, Word Count, Sign Type, Has Glyph)
 * - Column 2: Filterable sign list with search
 * - Column 3: Sign detail view
 *
 * URL Parameters:
 *   sign   - Selected sign_id
 *   group  - Active grouping type (polyphony, usage, word_count, sign_type, has_glyph)
 *   value  - Active grouping value
 *   search - Search query
 *   sort   - Sort order (sign_id, frequency, value_count, word_count)
 */

require_once __DIR__ . '/../../includes/db.php';
require_once __DIR__ . '/../../includes/helpers/display.php';
require_once dirname(__DIR__, 3) . '/src/Bootstrap.php';

use Glintstone\Repository\SignRepository;
use function Glintstone\app;

// Get URL parameters
$selectedSignId = $_GET['sign'] ?? null;
$activeGroup = $_GET['group'] ?? 'all';
$activeValue = $_GET['value'] ?? null;
$searchQuery = $_GET['search'] ?? '';
$sortOrder = $_GET['sort'] ?? 'sign_id';

// Validate activeGroup
$validGroups = ['all', 'polyphony', 'usage', 'word_count', 'sign_type', 'has_glyph'];
if (!in_array($activeGroup, $validGroups)) {
    $activeGroup = 'all';
    $activeValue = null;
}

$repo = app()->get(SignRepository::class);

// Fetch grouping counts
$counts = $repo->getGroupCounts();

// Fetch initial sign list with current filters
$filters = [
    'search' => $searchQuery,
    'sort' => $sortOrder,
    'group_type' => ($activeGroup !== 'all') ? $activeGroup : '',
    'group_value' => $activeValue ?? '',
];

// Sign type and has_glyph are direct filters, not group-based
if ($activeGroup === 'sign_type') {
    $filters['sign_type'] = $activeValue ?? '';
} elseif ($activeGroup === 'has_glyph') {
    $filters['has_glyph'] = $activeValue ?? '';
}

$result = $repo->browse($filters, 50, 0);
$initialSigns = $result['items'];
$totalSigns = $result['total'];

// Auto-select first sign if none selected and we have results
if (!$selectedSignId && !empty($initialSigns)) {
    $selectedSignId = $initialSigns[0]['sign_id'];
}

// Fetch sign detail data
$signDetail = null;
if ($selectedSignId) {
    $sign = $repo->findById($selectedSignId);
    if ($sign) {
        $values = $repo->getValues($selectedSignId);
        $wordUsage = $repo->getWordUsage($selectedSignId, 100);
        $stats = $repo->getStats($selectedSignId);
        $homophones = $repo->getHomophones($selectedSignId);

        // Group values by type
        $groupedValues = ['logographic' => [], 'syllabic' => [], 'determinative' => [], 'other' => []];
        foreach ($values as $v) {
            $type = $v['value_type'] ?? 'other';
            if (!isset($groupedValues[$type])) $type = 'other';
            $groupedValues[$type][] = $v;
        }

        $signDetail = [
            'sign' => $sign,
            'values' => $groupedValues,
            'words' => $wordUsage,
            'stats' => $stats,
            'homophones' => $homophones,
        ];
    }
}

// Page title and CSS
$pageTitle = 'Dictionary - Signs';
require_once __DIR__ . '/../../includes/css.php';
CSSLoader::enqueue('page-signs');
require_once __DIR__ . '/../../includes/header.php';

// Render the browser layout component
include __DIR__ . '/../../includes/components/signs/browser-layout.php';
?>

<!-- Signs Browser JavaScript -->
<script src="/assets/js/signs-browser.js"></script>
<script>
    document.addEventListener('DOMContentLoaded', function() {
        window.signsBrowser = new SignsBrowser({
            initialState: {
                groupType: '<?= htmlspecialchars($activeGroup) ?>',
                groupValue: <?= $activeValue ? "'" . htmlspecialchars($activeValue) . "'" : 'null' ?>,
                searchQuery: '<?= htmlspecialchars(addslashes($searchQuery)) ?>',
                selectedSignId: <?= $selectedSignId ? "'" . htmlspecialchars($selectedSignId) . "'" : 'null' ?>,
                sort: '<?= htmlspecialchars($sortOrder) ?>',
                offset: 0,
                total: <?= $totalSigns ?>
            }
        });
    });
</script>

<?php require_once __DIR__ . '/../../includes/footer.php'; ?>
