<?php
/**
 * Sign Annotations API
 * Returns bounding box annotations for a tablet from imported datasets (CompVis, eBL)
 *
 * Parameters:
 *   p       - P-number (required, format: P000001)
 *   surface - Optional filter: 'obverse', 'reverse'
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Service\TabletService;
use function Glintstone\app;

// Get parameters
$params = getRequestParams();
$pNumber = $params['p'] ?? null;
$surface = $params['surface'] ?? null;

// Validate P-number format
if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format');
}

// Get annotations via service
$service = app()->get(TabletService::class);
$rawAnnotations = $service->getAnnotations($pNumber, $surface ? strtolower($surface) : null);

// Format annotations for response
$annotations = [];
$sources = [];
$stats = [];
$refWidth = null;
$refHeight = null;

foreach ($rawAnnotations as $row) {
    // Capture reference dimensions from first row
    if ($refWidth === null && !empty($row['ref_image_width'])) {
        $refWidth = (int)$row['ref_image_width'];
        $refHeight = (int)$row['ref_image_height'];
    }

    $annotations[] = [
        'id' => (int)$row['id'],
        'sign' => $row['sign_label'],
        'x' => round((float)$row['bbox_x'], 2),
        'y' => round((float)$row['bbox_y'], 2),
        'width' => round((float)$row['bbox_width'], 2),
        'height' => round((float)$row['bbox_height'], 2),
        'confidence' => $row['confidence'] ? round((float)$row['confidence'], 3) : null,
        'surface' => $row['surface'],
        'atfLine' => $row['atf_line'] ? (int)$row['atf_line'] : null,
        'source' => $row['source'],
    ];

    // Track sources
    $source = $row['source'];
    $sources[$source] = true;
    $stats[$source] = ($stats[$source] ?? 0) + 1;
}

JsonResponse::success([
    'p_number' => $pNumber,
    'count' => count($annotations),
    'sources' => array_keys($sources),
    'stats' => $stats,
    'ref_width' => $refWidth,
    'ref_height' => $refHeight,
    'annotations' => $annotations,
]);
