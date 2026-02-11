<?php
/**
 * Lemmas API endpoint
 * Returns lemma data for a tablet indexed by line and word position
 *
 * Parameters:
 *   p - P-number (required, format: P000001)
 *
 * Returns:
 *   {
 *     "p_number": "P000001",
 *     "lemmas": {
 *       "0": { "0": {...}, "1": {...} },
 *       "1": { ... }
 *     },
 *     "count": 24
 *   }
 */

// Set JSON header FIRST before any includes
header('Content-Type: application/json');

// Catch all errors and return as JSON
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Server error',
        'message' => $errstr,
        'file' => basename($errfile),
        'line' => $errline
    ]);
    exit;
});

// Wrap everything in try-catch
try {
    require_once __DIR__ . '/../includes/db.php';

    $pNumber = $_GET['p'] ?? null;

    if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid P-number format. Expected format: P000001']);
        exit;
    }

    $db = getDB();

    $stmt = $db->prepare("
        SELECT line_no, word_no, form, cf, gw, pos, lang
        FROM lemmas
        WHERE p_number = :p
        ORDER BY line_no ASC, word_no ASC
    ");
    $stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();

    $lemmas = new stdClass();
    $count = 0;

    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $lineNo = strval($row['line_no']);
        $wordNo = strval($row['word_no']);

        if (!isset($lemmas->$lineNo)) {
            $lemmas->$lineNo = new stdClass();
        }

        $lemmas->$lineNo->$wordNo = [
            'form' => $row['form'],
            'cf' => $row['cf'],
            'gw' => $row['gw'],
            'pos' => $row['pos'],
            'lang' => $row['lang']
        ];
        $count++;
    }

    echo json_encode([
        'p_number' => $pNumber,
        'lemmas' => $lemmas,
        'count' => $count
    ], JSON_PRETTY_PRINT);

} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Database error',
        'message' => $e->getMessage()
    ]);
    exit;
}
