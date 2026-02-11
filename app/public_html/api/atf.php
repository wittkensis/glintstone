<?php
/**
 * ATF (transliteration) API
 * Returns ATF data for a tablet, fetching from CDLI if not available locally
 *
 * Parameters:
 *   p       - P-number (required)
 *   fetch   - If set, fetch from CDLI if not available locally
 *   parsed  - If set, return parsed ATF structure for interactive display
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
    require_once __DIR__ . '/../includes/ATFParser.php';
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Failed to load dependencies',
        'message' => $e->getMessage()
    ]);
    exit;
}

try {
    $pNumber = $_GET['p'] ?? null;
    $fetchRemote = isset($_GET['fetch']);
    $returnParsed = isset($_GET['parsed']);

    if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
        http_response_code(400);
        echo json_encode(['error' => 'Invalid P-number format']);
        exit;
    }

    // Check local database first
    $db = getDB();
    $stmt = $db->prepare("SELECT atf, source FROM inscriptions WHERE p_number = :p AND is_latest = 1");
    $stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
} catch (Throwable $e) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Database error',
        'message' => $e->getMessage()
    ]);
    exit;
}

if ($row && $row['atf']) {
    $response = [
        'p_number' => $pNumber,
        'atf' => $row['atf'],
        'source' => $row['source'] ?? 'local',
        'cached' => true
    ];

    // Add parsed structure if requested
    if ($returnParsed) {
        try {
            $parser = new ATFParser();
            $response['parsed'] = $parser->parse($row['atf']);
            $response['legend'] = $parser->getLegendItems();
        } catch (Throwable $e) {
            http_response_code(500);
            echo json_encode([
                'error' => 'Parser error',
                'message' => $e->getMessage()
            ]);
            exit;
        }
    }

    echo json_encode($response);
    exit;
}

// If not found locally and fetch requested, try CDLI
if ($fetchRemote) {
    $atf = fetchFromCDLI($pNumber);

    if ($atf) {
        // Store locally for future use
        storeATF($pNumber, $atf, 'cdli-api');

        $response = [
            'p_number' => $pNumber,
            'atf' => $atf,
            'source' => 'cdli-api',
            'cached' => false
        ];

        // Add parsed structure if requested
        if ($returnParsed) {
            $parser = new ATFParser();
            $response['parsed'] = $parser->parse($atf);
            $response['legend'] = $parser->getLegendItems();
        }

        echo json_encode($response);
        exit;
    }
}

// Not found
http_response_code(404);
echo json_encode([
    'error' => 'ATF not available',
    'p_number' => $pNumber,
    'hint' => $fetchRemote ? 'Not found on CDLI either' : 'Add ?fetch=1 to try fetching from CDLI'
]);

/**
 * Fetch ATF from CDLI API
 */
function fetchFromCDLI(string $pNumber): ?string {
    // CDLI API endpoint for ATF
    $url = "https://cdli.earth/artifacts/{$pNumber}/inscription";

    $context = stream_context_create([
        'http' => [
            'timeout' => 10,
            'user_agent' => 'Glintstone/1.0 (Cuneiform Research Platform)',
            'header' => 'Accept: text/plain'
        ]
    ]);

    $response = @file_get_contents($url, false, $context);

    if ($response === false || strlen($response) < 10) {
        // Try alternative ATF endpoint
        $altUrl = "https://cdli.ucla.edu/P/$pNumber/atf";
        $response = @file_get_contents($altUrl, false, $context);
    }

    if ($response && strlen($response) > 10 && strpos($response, '<!DOCTYPE') === false) {
        return $response;
    }

    return null;
}

/**
 * Store fetched ATF in local database
 */
function storeATF(string $pNumber, string $atf, string $source): void {
    // Need write access - open new connection
    $dbPath = dirname(__DIR__, 3) . '/database/glintstone.db';
    $db = new SQLite3($dbPath, SQLITE3_OPEN_READWRITE);

    // Insert or update inscription
    $stmt = $db->prepare("
        INSERT INTO inscriptions (p_number, atf, source, is_latest)
        VALUES (:p, :atf, :source, 1)
        ON CONFLICT(p_number, source) DO UPDATE SET
            atf = :atf,
            is_latest = 1
    ");
    $stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
    $stmt->bindValue(':atf', $atf, SQLITE3_TEXT);
    $stmt->bindValue(':source', $source, SQLITE3_TEXT);

    // Handle case where constraint doesn't exist
    try {
        $stmt->execute();
    } catch (Exception $e) {
        // Fallback: simple insert/update
        $db->exec("DELETE FROM inscriptions WHERE p_number = '$pNumber' AND source = '$source'");
        $stmt = $db->prepare("INSERT INTO inscriptions (p_number, atf, source, is_latest) VALUES (:p, :atf, :source, 1)");
        $stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
        $stmt->bindValue(':atf', $atf, SQLITE3_TEXT);
        $stmt->bindValue(':source', $source, SQLITE3_TEXT);
        $stmt->execute();
    }

    // Update pipeline status
    $db->exec("
        INSERT INTO pipeline_status (p_number, has_atf, atf_source)
        VALUES ('$pNumber', 1, '$source')
        ON CONFLICT(p_number) DO UPDATE SET
            has_atf = 1,
            atf_source = '$source',
            quality_score = (
                COALESCE(has_image, 0) * 0.2 +
                1 * 0.3 +
                COALESCE(has_lemmas, 0) * 0.25 +
                COALESCE(has_translation, 0) * 0.25
            ),
            last_updated = CURRENT_TIMESTAMP
    ");

    $db->close();
}
