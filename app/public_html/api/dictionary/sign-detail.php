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

require_once __DIR__ . '/../../includes/db.php';

header('Content-Type: application/json');

// Get sign_id from query parameter
$sign_id = $_GET['sign_id'] ?? '';

if (empty($sign_id)) {
    http_response_code(400);
    echo json_encode(['error' => 'Missing required parameter: sign_id']);
    exit;
}

try {
    $db = getDB();

    // Main sign data
    $stmt = $db->prepare("
        SELECT
            sign_id,
            utf8,
            sign_type,
            most_common_value
        FROM signs
        WHERE sign_id = :sign_id
    ");
    $stmt->bindValue(':sign_id', $sign_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    $sign = $result->fetchArray(SQLITE3_ASSOC);

    if (!$sign) {
        http_response_code(404);
        echo json_encode(['error' => 'Sign not found']);
        exit;
    }

    // Get all values/readings for this sign
    $stmt = $db->prepare("
        SELECT
            value,
            value_type,
            frequency
        FROM sign_values
        WHERE sign_id = :sign_id
        ORDER BY
            CASE value_type
                WHEN 'logographic' THEN 1
                WHEN 'syllabic' THEN 2
                WHEN 'determinative' THEN 3
                ELSE 4
            END,
            frequency DESC,
            value ASC
    ");
    $stmt->bindValue(':sign_id', $sign_id, SQLITE3_TEXT);
    $result = $stmt->execute();

    $values = [
        'logographic' => [],
        'syllabic' => [],
        'determinative' => [],
        'other' => []
    ];

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
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

    // Get words that use this sign (with value breakdown)
    $stmt = $db->prepare("
        SELECT
            swu.sign_value,
            swu.value_type,
            swu.usage_count,
            ge.entry_id,
            ge.headword,
            ge.guide_word,
            ge.pos,
            ge.language,
            ge.icount
        FROM sign_word_usage swu
        JOIN glossary_entries ge ON swu.entry_id = ge.entry_id
        WHERE swu.sign_id = :sign_id
        ORDER BY swu.usage_count DESC, ge.icount DESC
        LIMIT 100
    ");
    $stmt->bindValue(':sign_id', $sign_id, SQLITE3_TEXT);
    $result = $stmt->execute();

    $words_using_sign = [];
    $total_word_count = 0;
    $total_usage_count = 0;

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
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
        $total_word_count++;
        $total_usage_count += (int)$row['usage_count'];
    }

    // Get total word count (not limited to 100)
    $stmt = $db->prepare("
        SELECT COUNT(DISTINCT entry_id) as total_words
        FROM sign_word_usage
        WHERE sign_id = :sign_id
    ");
    $stmt->bindValue(':sign_id', $sign_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    $count_row = $result->fetchArray(SQLITE3_ASSOC);
    $total_unique_words = (int)$count_row['total_words'];

    // Get total occurrences across all corpus
    $stmt = $db->prepare("
        SELECT SUM(usage_count) as total
        FROM sign_word_usage
        WHERE sign_id = :sign_id
    ");
    $stmt->bindValue(':sign_id', $sign_id, SQLITE3_TEXT);
    $result = $stmt->execute();
    $usage_row = $result->fetchArray(SQLITE3_ASSOC);
    $total_corpus_occurrences = (int)$usage_row['total'];

    // Assemble complete response
    $response = [
        'sign' => [
            'sign_id' => $sign['sign_id'],
            'utf8' => $sign['utf8'],
            'sign_type' => $sign['sign_type'],
            'most_common_value' => $sign['most_common_value']
        ],
        'values' => $values,
        'words' => [
            'sample' => $words_using_sign,
            'total_unique_words' => $total_unique_words,
            'showing' => count($words_using_sign)
        ],
        'statistics' => [
            'total_values' => count($values['logographic']) + count($values['syllabic']) + count($values['determinative']) + count($values['other']),
            'logographic_values' => count($values['logographic']),
            'syllabic_values' => count($values['syllabic']),
            'determinative_values' => count($values['determinative']),
            'total_words_using_sign' => $total_unique_words,
            'total_corpus_occurrences' => $total_corpus_occurrences
        ]
    ];

    echo json_encode($response, JSON_PRETTY_PRINT | JSON_UNESCAPED_UNICODE);

} catch (Exception $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Internal server error: ' . $e->getMessage()]);
}
