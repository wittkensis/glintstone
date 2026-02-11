<?php
/**
 * Save ML Detection Results
 * Saves ML-predicted sign annotations to the database
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use function Glintstone\app;

requireMethod('POST');

// Parse JSON body
$input = json_decode(file_get_contents('php://input'), true);

if (!$input) {
    JsonResponse::badRequest('Invalid JSON input');
}

$pNumber = $input['p_number'] ?? null;
$detections = $input['detections'] ?? [];
$source = $input['source'] ?? 'ebl_ocr';
$imageWidth = $input['image_width'] ?? null;
$imageHeight = $input['image_height'] ?? null;
$replaceExisting = $input['replace_existing'] ?? false;

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format');
}

if (!is_array($detections) || count($detections) === 0) {
    JsonResponse::badRequest('No detections provided');
}

// Need write access
$dbPath = defined('DB_PATH') ? DB_PATH : dirname(__DIR__, 3) . '/database/glintstone.db';
$db = new SQLite3($dbPath, SQLITE3_OPEN_READWRITE);
$db->enableExceptions(true);
$db->busyTimeout(5000);

$db->exec('BEGIN TRANSACTION');

try {
    if ($replaceExisting) {
        $deleteStmt = $db->prepare("DELETE FROM sign_annotations WHERE p_number = :p AND source = :source");
        $deleteStmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
        $deleteStmt->bindValue(':source', $source, SQLITE3_TEXT);
        $deleteStmt->execute();
    }

    $insertStmt = $db->prepare("
        INSERT INTO sign_annotations (
            p_number, sign_label, bbox_x, bbox_y, bbox_width, bbox_height,
            confidence, surface, source, image_type, ref_image_width, ref_image_height
        ) VALUES (
            :p_number, :sign_label, :bbox_x, :bbox_y, :bbox_width, :bbox_height,
            :confidence, :surface, :source, :image_type, :ref_width, :ref_height
        )
    ");

    $inserted = 0;

    foreach ($detections as $det) {
        $bbox = $det['bbox'] ?? [];
        if (count($bbox) !== 4) continue;

        // Convert from xyxy to xywh
        $x = $bbox[0];
        $y = $bbox[1];
        $width = $bbox[2] - $bbox[0];
        $height = $bbox[3] - $bbox[1];

        // Convert to percentages if image dimensions provided
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
        SET has_sign_annotations = 1, ocr_model = :model, last_updated = datetime('now')
        WHERE p_number = :p
    ");
    $pipelineStmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
    $pipelineStmt->bindValue(':model', $source, SQLITE3_TEXT);
    $pipelineStmt->execute();

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
    $db->close();

    JsonResponse::success([
        'p_number' => $pNumber,
        'inserted' => $inserted,
        'source' => $source,
        'message' => "Saved $inserted sign annotations"
    ]);

} catch (Exception $e) {
    $db->exec('ROLLBACK');
    $db->close();
    JsonResponse::serverError('Database error');
}
