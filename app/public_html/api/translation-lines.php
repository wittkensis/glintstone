<?php
/**
 * Translation Lines API
 * Parses translations into line-by-line mappings for side-by-side display
 *
 * Parameters:
 *   p     - P-number (required)
 *   lang  - Language filter (optional, default: 'en')
 */

require_once __DIR__ . '/_error-handler.php';

try {
    require_once __DIR__ . '/../includes/db.php';
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode(['error' => 'Failed to load dependencies', 'message' => $e->getMessage()]);
    exit;
}

$pNumber = $_GET['p'] ?? null;
$language = $_GET['lang'] ?? 'en';

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid P-number format']);
    exit;
}

$db = getDB();

// Get translations for this tablet
$stmt = $db->prepare("
    SELECT translation, language, source
    FROM translations
    WHERE p_number = :p
    ORDER BY
        CASE WHEN language = :lang THEN 0 ELSE 1 END,
        source
    LIMIT 1
");
$stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
$stmt->bindValue(':lang', $language, SQLITE3_TEXT);
$result = $stmt->execute();
$row = $result->fetchArray(SQLITE3_ASSOC);

if (!$row) {
    http_response_code(404);
    echo json_encode([
        'p_number' => $pNumber,
        'has_translation' => false,
        'message' => 'No translation available'
    ]);
    exit;
}

// Parse translation into structured lines
$lines = parseTranslationLines($row['translation']);

echo json_encode([
    'p_number' => $pNumber,
    'has_translation' => true,
    'language' => $row['language'],
    'source' => $row['source'],
    'lines' => $lines,
    'raw' => $row['translation']
]);

/**
 * Parse translation text into line-by-line structure
 * Handles various formats:
 * - Numbered lines: "1. text" or "(1) text"
 * - Surface markers: "@obverse", "@reverse"
 * - Column markers: "Column 1:", "Col. i:"
 */
function parseTranslationLines(string $text): array {
    $result = [];
    $currentSurface = 'obverse';
    $currentColumn = 1;

    $lines = explode("\n", $text);

    foreach ($lines as $line) {
        $line = trim($line);
        if (empty($line)) continue;

        // Check for surface markers
        if (preg_match('/^@?(obverse|reverse|left|right|top|bottom|edge)/i', $line, $m)) {
            $currentSurface = strtolower($m[1]);
            continue;
        }

        // Check for column markers
        if (preg_match('/^(?:column|col\.?)\s*(\d+|[ivx]+)/i', $line, $m)) {
            $currentColumn = parseColumnNumber($m[1]);
            continue;
        }

        // Check for numbered lines: "1. text", "(1) text", "1: text", "1' text"
        if (preg_match('/^(\d+[\'"]?)[\.\:\)\s]+(.+)$/', $line, $m)) {
            $lineNum = $m[1] . '.';
            $content = trim($m[2]);

            $key = "{$currentSurface}_{$currentColumn}_{$lineNum}";
            $result[$key] = [
                'surface' => $currentSurface,
                'column' => $currentColumn,
                'line' => $lineNum,
                'text' => $content
            ];
            continue;
        }

        // Check for range: "1-3. text" or "1-3: text"
        if (preg_match('/^(\d+)\s*[-–]\s*(\d+)[\.\:\)\s]+(.+)$/', $line, $m)) {
            $startLine = (int)$m[1];
            $endLine = (int)$m[2];
            $content = trim($m[3]);

            // Store under the start line
            $lineNum = $startLine . '.';
            $key = "{$currentSurface}_{$currentColumn}_{$lineNum}";
            $result[$key] = [
                'surface' => $currentSurface,
                'column' => $currentColumn,
                'line' => $lineNum,
                'lineEnd' => $endLine . '.',
                'text' => $content
            ];
            continue;
        }

        // Continuation or unmarked line - append to previous if exists
        // (Some translations don't have line numbers)
    }

    return $result;
}

/**
 * Parse column number (handles roman numerals and arabic)
 */
function parseColumnNumber(string $num): int {
    $num = strtolower(trim($num));

    // Roman numerals
    $romans = [
        'i' => 1, 'ii' => 2, 'iii' => 3, 'iv' => 4, 'v' => 5,
        'vi' => 6, 'vii' => 7, 'viii' => 8, 'ix' => 9, 'x' => 10
    ];

    if (isset($romans[$num])) {
        return $romans[$num];
    }

    return (int)$num ?: 1;
}
