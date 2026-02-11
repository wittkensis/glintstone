<?php
/**
 * Library Sign Detail API
 *
 * Returns comprehensive data for a single cuneiform sign including:
 * - Base sign information
 * - All values/readings grouped by type (logographic, syllabic, determinative)
 * - Words that use this sign
 * - Usage statistics
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\SignRepository;
use function Glintstone\app;

$params = getRequestParams();
$sign_id = $params['sign_id'] ?? '';

if (empty($sign_id)) {
    JsonResponse::badRequest('Missing required parameter: sign_id');
}

$repo = app()->get(SignRepository::class);

$sign = $repo->findById($sign_id);
if (!$sign) {
    JsonResponse::notFound('Sign not found');
}

// Get all values grouped by type
$allValues = $repo->getValues($sign_id);

$values = [
    'logographic' => [],
    'syllabic' => [],
    'determinative' => [],
    'other' => []
];

foreach ($allValues as $row) {
    $value_data = [
        'value' => $row['value'],
        'frequency' => $row['frequency'] ? (int)$row['frequency'] : 0
    ];
    $type = $row['value_type'] ?? 'other';
    if (isset($values[$type])) {
        $values[$type][] = $value_data;
    } else {
        $values['other'][] = $value_data;
    }
}

// Words that use this sign
$wordRows = $repo->getWordUsage($sign_id, 100);
$words_using_sign = [];
foreach ($wordRows as $row) {
    $words_using_sign[] = [
        'sign_value' => $row['sign_value'],
        'value_type' => $row['value_type'],
        'usage_count' => (int)$row['usage_count'],
        'entry' => [
            'entry_id' => $row['entry_id'],
            'headword' => $row['headword'],
            'guide_word' => $row['guide_word'],
            'pos' => $row['pos'],
            'language' => $row['language'],
            'icount' => (int)$row['icount']
        ]
    ];
}

// Usage statistics
$stats = $repo->getStats($sign_id);

JsonResponse::success([
    'sign' => [
        'sign_id' => $sign['sign_id'],
        'utf8' => $sign['utf8'],
        'sign_type' => $sign['sign_type'],
        'most_common_value' => $sign['most_common_value']
    ],
    'values' => $values,
    'words' => [
        'sample' => $words_using_sign,
        'total_unique_words' => $stats['total_unique_words'],
        'showing' => count($words_using_sign)
    ],
    'statistics' => [
        'total_values' => count($values['logographic']) + count($values['syllabic']) + count($values['determinative']) + count($values['other']),
        'logographic_values' => count($values['logographic']),
        'syllabic_values' => count($values['syllabic']),
        'determinative_values' => count($values['determinative']),
        'total_words_using_sign' => $stats['total_unique_words'],
        'total_corpus_occurrences' => $stats['total_corpus_occurrences']
    ]
]);
