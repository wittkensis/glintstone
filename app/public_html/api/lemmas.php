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

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Service\TabletService;
use function Glintstone\app;

// Get parameters
$params = getRequestParams();
$pNumber = $params['p'] ?? null;

// Validate P-number format
if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format. Expected format: P000001');
}

// Get lemmas via service
$service = app()->get(TabletService::class);
$lemmas = $service->getLemmas($pNumber);

// Convert to object format for JSON (maintains JS object structure)
$lemmasObject = new stdClass();
$count = 0;

foreach ($lemmas as $lineNo => $words) {
    $lemmasObject->$lineNo = new stdClass();
    foreach ($words as $wordNo => $lemmaData) {
        $lemmasObject->$lineNo->$wordNo = $lemmaData;
        $count++;
    }
}

JsonResponse::success([
    'p_number' => $pNumber,
    'lemmas' => $lemmasObject,
    'count' => $count
]);
