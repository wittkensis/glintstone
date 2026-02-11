<?php
/**
 * Save ML Detection Results
 * Saves ML-predicted sign annotations to the database
 */

require_once __DIR__ . '/../../includes/db.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle CORS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

if ($_SERVER['REQUEST_METHOD'] !== 'POST') {
    http_response_code(405);
    echo json_encode(['error' => 'Method not allowed']);
    exit;
}

// Parse JSON body
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid JSON input']);
    exit;
}

$pNumber = $input['p_number'] ?? null;
$detections = $input['detections'] ?? [];
$source = $input['source'] ?? 'ebl_ocr';
$imageWidth = $input['image_width'] ?? null;
$imageHeight = $input['image_height'] ?? null;
$replaceExisting = $input['replace_existing'] ?? false;

// Validate P-number
if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid P-number format']);
    exit;
}

// Validate detections
if (!is_array($detections) || count($detections) === 0) {
    http_response_code(400);
    echo json_encode(['error' => 'No detections provided']);
    exit;
}

$db = getDB();

// Start transaction
$db->exec('BEGIN TRANSACTION');

try {
    // Optionally delete existing annotations from this source
    if ($replaceExisting) {
        $deleteStmt = $db->prepare("DELETE FROM sign_annotations WHERE p_number = :p AND source = :source");
        $deleteStmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
        $deleteStmt->bindValue(':source', $source, SQLITE3_TEXT);
        $deleteStmt->execute();
    }

    // Prepare insert statement
    $insertStmt = $db->prepare("
        INSERT INTO sign_annotations (
            p_number,
            sign_label,
            bbox_x,
            bbox_y,
            bbox_width,
            bbox_height,
            confidence,
            surface,
            source,
            image_type,
            ref_image_width,
            ref_image_height
        ) VALUES (
            :p_number,
            :sign_label,
            :bbox_x,
            :bbox_y,
            :bbox_width,
            :bbox_height,
            :confidence,
            :surface,
            :source,
            :image_type,
            :ref_width,
            :ref_height
        )
    ");

    $inserted = 0;

    foreach ($detections as $det) {
        // Extract bounding box - detections have bbox as [x_min, y_min, x_max, y_max]
        $bbox = $det['bbox'] ?? [];
        if (count($bbox) !== 4) {
            continue;
        }

        // Convert from xyxy to xywh for storage
        $x = $bbox[0];
        $y = $bbox[1];
        $width = $bbox[2] - $bbox[0];
        $height = $bbox[3] - $bbox[1];

        // Convert to percentages if we have image dimensions
        if ($imageWidth && $imageHeight) {
            $x = ($x / $imageWidth) * 100;
            $y = ($y / $imageHeight) * 100;
            $width = ($width / $imageWidth) * 100;
            $height = ($height / $imageHeight) * 100;
        }

        $insertStmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
        $insertStmt->bindValue(':sign_label', $det['class_name'] ?? '', SQLITE3_TEXT);
        $insertStmt->bindValue(':bbox_x', $x, SQLITE3_FLOAT);
        $insertStmt->bindValue(':bbox_y', $y, SQLITE3_FLOAT);
        $insertStmt->bindValue(':bbox_width', $width, SQLITE3_FLOAT);
        $insertStmt->bindValue(':bbox_height', $height, SQLITE3_FLOAT);
        $insertStmt->bindValue(':confidence', $det['confidence'] ?? null, SQLITE3_FLOAT);
        $insertStmt->bindValue(':surface', $det['surface'] ?? 'obverse', SQLITE3_TEXT);
        $insertStmt->bindValue(':source', $source, SQLITE3_TEXT);
        $insertStmt->bindValue(':image_type', 'photo', SQLITE3_TEXT);
        $insertStmt->bindValue(':ref_width', $imageWidth, SQLITE3_INTEGER);
        $insertStmt->bindValue(':ref_height', $imageHeight, SQLITE3_INTEGER);

        $insertStmt->execute();
        $insertStmt->reset();
        $inserted++;
    }

    // Update pipeline_status
    $pipelineStmt = $db->prepare("
        UPDATE pipeline_status
        SET has_sign_annotations = 1,
            ocr_model = :model,
            last_updated = datetime('now')
        WHERE p_number = :p
    ");
    $pipelineStmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
    $pipelineStmt->bindValue(':model', $source, SQLITE3_TEXT);
    $pipelineStmt->execute();

    // If no pipeline_status row exists, create one
    if ($db->changes() === 0) {
        $createStmt = $db->prepare("
            INSERT OR IGNORE INTO pipeline_status (p_number, has_sign_annotations, ocr_model, last_updated)
            VALUES (:p, 1, :model, datetime('now'))
        ");
        $createStmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
        $createStmt->bindValue(':model', $source, SQLITE3_TEXT);
        $createStmt->execute();
    }

    $db->exec('COMMIT');

    echo json_encode([
        'success' => true,
        'p_number' => $pNumber,
        'inserted' => $inserted,
        'source' => $source,
        'message' => "Saved $inserted sign annotations"
    ]);

} catch (Exception $e) {
    $db->exec('ROLLBACK');
    http_response_code(500);
    echo json_encode([
        'error' => 'Database error',
        'detail' => $e->getMessage()
    ]);
}
