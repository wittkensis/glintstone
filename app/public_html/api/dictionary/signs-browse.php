<?php
/**
 * Library Signs Browse API
 *
 * Returns paginated grid of cuneiform signs with filters:
 * - Search by sign_id or value
 * - Filter by sign_type (simple, compound, variant)
 * - Filter by minimum frequency/usage
 * - Sort options (sign_id, frequency, value_count)
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\SignRepository;
use function Glintstone\app;

$params = getRequestParams();
$search = $params['search'] ?? '';
$sign_type = $params['sign_type'] ?? '';
$min_frequency = isset($params['min_frequency']) ? (int)$params['min_frequency'] : 0;
$sort = $params['sort'] ?? 'sign_id';
$limit = isset($params['limit']) ? min((int)$params['limit'], 200) : 50;
$offset = isset($params['offset']) ? (int)$params['offset'] : 0;
$group_type = $params['group_type'] ?? '';
$group_value = $params['group_value'] ?? '';
$has_glyph = $params['has_glyph'] ?? '';

$repo = app()->get(SignRepository::class);

$result = $repo->browse([
    'search' => $search,
    'sign_type' => $sign_type,
    'min_frequency' => $min_frequency,
    'sort' => $sort,
    'group_type' => $group_type,
    'group_value' => $group_value,
    'has_glyph' => $has_glyph,
], $limit, $offset);

$signs = [];
foreach ($result['items'] as $row) {
    $signs[] = [
        'sign_id' => $row['sign_id'],
        'utf8' => $row['utf8'],
        'sign_type' => $row['sign_type'],
        'most_common_value' => $row['most_common_value'],
        'value_count' => (int)$row['value_count'],
        'word_count' => (int)$row['word_count'],
        'total_occurrences' => (int)$row['total_occurrences']
    ];
}

JsonResponse::success([
    'signs' => $signs,
    'pagination' => [
        'total' => $result['total'],
        'limit' => $limit,
        'offset' => $offset,
        'has_more' => ($offset + $limit) < $result['total'],
        'showing' => count($signs)
    ],
    'filters' => [
        'search' => $search,
        'sign_type' => $sign_type,
        'min_frequency' => $min_frequency,
        'sort' => $sort
    ]
]);
