<?php
/**
 * Sign Annotations API
 * Returns bounding box annotations for a tablet from imported datasets (CompVis, eBL)
 */

require_once __DIR__ . '/../includes/db.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');

$pNumber = $_GET['p'] ?? null;
$surface = $_GET['surface'] ?? null;  // Optional filter: 'obverse', 'reverse'

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid P-number format']);
    exit;
}

$db = getDB();

// Build query with optional surface filter
$sql = "
    SELECT
        id,
        sign_label,
        bbox_x,
        bbox_y,
        bbox_width,
        bbox_height,
        confidence,
        surface,
        atf_line,
        source,
        ref_image_width,
        ref_image_height
    FROM sign_annotations
    WHERE p_number = :p
";

if ($surface) {
    $sql .= " AND (surface = :surface OR surface IS NULL)";
}

$sql .= " ORDER BY bbox_y, bbox_x";

$stmt = $db->prepare($sql);
$stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
if ($surface) {
    $stmt->bindValue(':surface', strtolower($surface), SQLITE3_TEXT);
}

$result = $stmt->execute();

$annotations = [];
$sources = [];
$refWidth = null;
$refHeight = null;

while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
    // Capture reference dimensions from first row (same for all annotations of a tablet)
    if ($refWidth === null && $row['ref_image_width']) {
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
    $sources[$row['source']] = true;
}

// Get summary stats
$stmt = $db->prepare("
    SELECT COUNT(*) as count, source
    FROM sign_annotations
    WHERE p_number = :p
    GROUP BY source
");
$stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
$statsResult = $stmt->execute();

$stats = [];
while ($row = $statsResult->fetchArray(SQLITE3_ASSOC)) {
    $stats[$row['source']] = (int)$row['count'];
}

echo json_encode([
    'p_number' => $pNumber,
    'count' => count($annotations),
    'sources' => array_keys($sources),
    'stats' => $stats,
    'ref_width' => $refWidth,
    'ref_height' => $refHeight,
    'annotations' => $annotations,
]);
