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

require_once __DIR__ . '/../../includes/db.php';

header('Content-Type: application/json');

// Get query parameters
$search = $_GET['search'] ?? '';
$sign_type = $_GET['sign_type'] ?? '';
$min_frequency = isset($_GET['min_frequency']) ? (int)$_GET['min_frequency'] : 0;
$sort = $_GET['sort'] ?? 'sign_id'; // sign_id, frequency, value_count
$limit = isset($_GET['limit']) ? min((int)$_GET['limit'], 200) : 50;
$offset = isset($_GET['offset']) ? (int)$_GET['offset'] : 0;

try {
    $db = get_db();

    // Build WHERE clause
    $where_clauses = [];
    $bind_params = [];

    if (!empty($search)) {
        $where_clauses[] = "(s.sign_id LIKE :search OR sv.value LIKE :search)";
        $bind_params[':search'] = '%' . $search . '%';
    }

    if (!empty($sign_type)) {
        $where_clauses[] = "s.sign_type = :sign_type";
        $bind_params[':sign_type'] = $sign_type;
    }

    if ($min_frequency > 0) {
        // Will filter in HAVING clause instead
    }

    $where_sql = !empty($where_clauses) ? 'WHERE ' . implode(' AND ', $where_clauses) : '';

    // Build ORDER BY clause
    $order_by = match($sort) {
        'frequency' => 'total_occurrences DESC',
        'value_count' => 'value_count DESC',
        default => 's.sign_id ASC'
    };

    // Count total matching signs
    $count_sql = "
        SELECT COUNT(DISTINCT s.sign_id) as total
        FROM signs s
        LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
        LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
        $where_sql
    ";

    $stmt = $db->prepare($count_sql);
    foreach ($bind_params as $key => $value) {
        $stmt->bindValue($key, $value, SQLITE3_TEXT);
    }
    $result = $stmt->execute();
    $total_row = $result->fetchArray(SQLITE3_ASSOC);
    $total = (int)$total_row['total'];

    // Get paginated results with aggregated data
    $sql = "
        SELECT
            s.sign_id,
            s.utf8,
            s.sign_type,
            s.most_common_value,
            COUNT(DISTINCT sv.value) as value_count,
            COUNT(DISTINCT swu.entry_id) as word_count,
            COALESCE(SUM(swu.usage_count), 0) as total_occurrences
        FROM signs s
        LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
        LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
        $where_sql
        GROUP BY s.sign_id
    ";

    // Add frequency filter as HAVING clause if needed
    if ($min_frequency > 0) {
        $sql .= " HAVING total_occurrences >= :min_frequency";
    }

    $sql .= "
        ORDER BY $order_by
        LIMIT :limit OFFSET :offset
    ";

    $stmt = $db->prepare($sql);

    foreach ($bind_params as $key => $value) {
        $stmt->bindValue($key, $value, SQLITE3_TEXT);
    }

    if ($min_frequency > 0) {
        $stmt->bindValue(':min_frequency', $min_frequency, SQLITE3_INTEGER);
    }

    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);

    $result = $stmt->execute();

    $signs = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
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

    // Assemble response
    $response = [
        'signs' => $signs,
        'pagination' => [
            'total' => $total,
            'limit' => $limit,
            'offset' => $offset,
            'has_more' => ($offset + $limit) < $total,
            'showing' => count($signs)
        ],
        'filters' => [
            'search' => $search,
            'sign_type' => $sign_type,
            'min_frequency' => $min_frequency,
            'sort' => $sort
        ]
    ];

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
}
