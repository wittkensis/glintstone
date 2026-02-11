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

require_once __DIR__ . '/_bootstrap.php';
require_once __DIR__ . '/../includes/ATFParser.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\InscriptionRepository;
use function Glintstone\app;

$params = getRequestParams();
$pNumber = $params['p'] ?? null;
$fetchRemote = isset($params['fetch']);
$returnParsed = isset($params['parsed']);

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format');
}

$repo = app()->get(InscriptionRepository::class);
$row = $repo->getLatest($pNumber);

if ($row && $row['atf']) {
    $response = [
        'p_number' => $pNumber,
        'atf' => $row['atf'],
        'source' => $row['source'] ?? 'local',
        'cached' => true
    ];

    if ($returnParsed) {
        $parser = new ATFParser();
        $response['parsed'] = $parser->parse($row['atf']);
        $response['legend'] = $parser->getLegendItems();
    }

    JsonResponse::success($response);
}

// Not found locally - try CDLI if requested
if ($fetchRemote) {
    $atf = fetchFromCDLI($pNumber);

    if ($atf) {
        storeATF($pNumber, $atf, 'cdli-api');

        $response = [
            'p_number' => $pNumber,
            'atf' => $atf,
            'source' => 'cdli-api',
            'cached' => false
        ];

        if ($returnParsed) {
            $parser = new ATFParser();
            $response['parsed'] = $parser->parse($atf);
            $response['legend'] = $parser->getLegendItems();
        }

        JsonResponse::success($response);
    }
}

JsonResponse::notFound('ATF not available');

/**
 * Fetch ATF from CDLI API
 */
function fetchFromCDLI(string $pNumber): ?string {
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
    $dbPath = defined('DB_PATH') ? DB_PATH : dirname(__DIR__, 3) . '/database/glintstone.db';
    $db = new SQLite3($dbPath, SQLITE3_OPEN_READWRITE);

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

    try {
        $stmt->execute();
    } catch (Exception $e) {
        $db->exec("DELETE FROM inscriptions WHERE p_number = '{$pNumber}' AND source = '{$source}'");
        $stmt = $db->prepare("INSERT INTO inscriptions (p_number, atf, source, is_latest) VALUES (:p, :atf, :source, 1)");
        $stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
        $stmt->bindValue(':atf', $atf, SQLITE3_TEXT);
        $stmt->bindValue(':source', $source, SQLITE3_TEXT);
        $stmt->execute();
    }

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
