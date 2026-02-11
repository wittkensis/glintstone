<?php
/**
 * ML Sign Detection Proxy
 * Proxies requests to the local FastAPI ML service
 */

// Enable error logging for debugging
error_reporting(E_ALL);
ini_set('display_errors', 1);
ini_set('log_errors', 1);

require_once __DIR__ . '/../../includes/db.php';

header('Content-Type: application/json');
header('Access-Control-Allow-Origin: *');
header('Access-Control-Allow-Methods: GET, POST, OPTIONS');
header('Access-Control-Allow-Headers: Content-Type');

// Handle CORS preflight
if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    http_response_code(204);
    exit;
}

// ML service configuration
// Use Modal endpoint if set in environment, otherwise fall back to local service
$MODAL_ENDPOINT = getenv('MODAL_ENDPOINT');
$ML_SERVICE_URL = $MODAL_ENDPOINT ?: 'http://localhost:8000';

// Log which endpoint we're using
error_log("ML Service: Using endpoint " . $ML_SERVICE_URL);

// Get P-number from query
$pNumber = $_GET['p'] ?? null;
$confidenceThreshold = $_GET['confidence'] ?? 0.3;

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    http_response_code(400);
    echo json_encode(['error' => 'Invalid P-number format', 'expected' => 'P######']);
    exit;
}

// Get image path from database
$db = getDB();
$stmt = $db->prepare("SELECT image_path FROM artifacts WHERE p_number = :p");
$stmt->bindValue(':p', $pNumber, SQLITE3_TEXT);
$result = $stmt->execute();
$row = $result->fetchArray(SQLITE3_ASSOC);

$imagePath = $row ? $row['image_path'] : null;
$fullImagePath = null;
$isTemporary = false;

// Try to resolve local image path
if ($imagePath) {
    $fullImagePath = realpath(__DIR__ . '/../../' . $imagePath);

    // Also check database/images directory
    if (!$fullImagePath || !file_exists($fullImagePath)) {
        $altPath = realpath(__DIR__ . '/../../../database/images/' . basename($imagePath));
        if ($altPath && file_exists($altPath)) {
            $fullImagePath = $altPath;
        }
    }
}

// If no local image, try to download from CDLI
if (!$fullImagePath || !file_exists($fullImagePath)) {
    $cdliUrl = "https://cdli.earth/dl/photo/{$pNumber}.jpg";

    // Create temporary directory if it doesn't exist
    $tempDir = sys_get_temp_dir() . '/cuneiform_ml';
    if (!is_dir($tempDir)) {
        mkdir($tempDir, 0755, true);
    }

    $tempPath = $tempDir . "/{$pNumber}.jpg";

    // Download image from CDLI - stream directly to file to avoid memory issues
    // Open file handle for writing
    $fp = fopen($tempPath, 'wb');
    if (!$fp) {
        http_response_code(500);
        echo json_encode([
            'error' => 'Failed to create temporary file',
            'p_number' => $pNumber,
            'path' => $tempPath
        ]);
        exit;
    }

    $ch = curl_init($cdliUrl);
    curl_setopt_array($ch, [
        CURLOPT_FILE => $fp,  // Write directly to file (streaming)
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_USERAGENT => 'CUNEIFORM/1.0',
        CURLOPT_BUFFERSIZE => 128 * 1024,
        CURLOPT_NOPROGRESS => false,
        // Progress callback to enforce size limit during download
        CURLOPT_PROGRESSFUNCTION => function($resource, $downloadSize, $downloaded, $uploadSize, $uploaded) {
            // Abort if download exceeds 50MB
            if ($downloaded > 50 * 1024 * 1024) {
                return 1; // Non-zero aborts the transfer
            }
            return 0;
        }
    ]);

    $success = curl_exec($ch);
    $curlError = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    $downloadedBytes = curl_getinfo($ch, CURLINFO_SIZE_DOWNLOAD);
    curl_close($ch);
    fclose($fp);

    // Check for cURL errors
    if (!$success || $curlError) {
        @unlink($tempPath);
        http_response_code(502);
        echo json_encode([
            'error' => 'Failed to download image',
            'p_number' => $pNumber,
            'detail' => $curlError ?: 'Download failed',
            'url' => $cdliUrl
        ]);
        exit;
    }

    // Validate response
    if ($httpCode === 200 && file_exists($tempPath)) {
        // Get actual file size
        $dataSize = filesize($tempPath);

        // Validate size
        if ($dataSize < 1000) {
            @unlink($tempPath);
            http_response_code(502);
            echo json_encode([
                'error' => 'Downloaded image too small',
                'p_number' => $pNumber,
                'size' => $dataSize,
                'url' => $cdliUrl
            ]);
            exit;
        }

        if ($dataSize > 50 * 1024 * 1024) {
            @unlink($tempPath);
            http_response_code(502);
            echo json_encode([
                'error' => 'Downloaded image too large',
                'p_number' => $pNumber,
                'size' => $dataSize,
                'url' => $cdliUrl
            ]);
            exit;
        }

        // Validate it's actually an image by checking magic bytes
        $fp = fopen($tempPath, 'rb');
        $header = fread($fp, 10);
        fclose($fp);

        $imageSignatures = [
            "\xFF\xD8\xFF" => 'jpeg',
            "\x89\x50\x4E\x47" => 'png',
            "GIF87a" => 'gif',
            "GIF89a" => 'gif',
        ];

        $isValidImage = false;
        foreach ($imageSignatures as $signature => $type) {
            if (substr($header, 0, strlen($signature)) === $signature) {
                $isValidImage = true;
                break;
            }
        }

        if (!$isValidImage) {
            @unlink($tempPath);
            http_response_code(502);
            echo json_encode([
                'error' => 'Downloaded file is not a valid image',
                'p_number' => $pNumber,
                'size' => $dataSize,
                'url' => $cdliUrl
            ]);
            exit;
        }

        // File is valid and saved
        $fullImagePath = $tempPath;
        $isTemporary = true;
    } else {
        @unlink($tempPath);
        http_response_code(404);
        echo json_encode([
            'error' => 'No image available',
            'p_number' => $pNumber,
            'tried_local' => $imagePath ?: '(none)',
            'tried_cdli' => $cdliUrl,
            'cdli_status' => $httpCode,
            'content_type' => $contentType
        ]);
        exit;
    }
}

if (!$fullImagePath || !file_exists($fullImagePath)) {
    http_response_code(404);
    echo json_encode([
        'error' => 'Image file not found',
        'p_number' => $pNumber,
        'path' => $imagePath
    ]);
    exit;
}

// Register cleanup for temporary file
if ($isTemporary) {
    register_shutdown_function(function() use ($fullImagePath) {
        if (file_exists($fullImagePath)) {
            @unlink($fullImagePath);
        }
    });
}

// Call ML service using file path endpoint
$mlUrl = sprintf(
    '%s/detect-signs-by-path?image_path=%s&confidence_threshold=%s',
    $ML_SERVICE_URL,
    urlencode($fullImagePath),
    $confidenceThreshold
);

$ch = curl_init();
curl_setopt_array($ch, [
    CURLOPT_URL => $mlUrl,
    CURLOPT_POST => true,
    CURLOPT_RETURNTRANSFER => true,
    CURLOPT_TIMEOUT => 180,  // 3 minute timeout for Modal cold starts + model loading
    CURLOPT_CONNECTTIMEOUT => 10,  // Longer connect timeout for Modal
]);

$response = curl_exec($ch);
$httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    http_response_code(503);
    echo json_encode([
        'error' => 'ML service unavailable',
        'detail' => $error,
        'hint' => 'Ensure the ML service is running: cd ml-service && python app.py'
    ]);
    exit;
}

if ($httpCode !== 200) {
    http_response_code($httpCode);
    echo json_encode([
        'error' => 'ML service error',
        'http_code' => $httpCode,
        'response' => json_decode($response, true)
    ]);
    exit;
}

// Parse and enhance response
$mlResult = json_decode($response, true);

if (!$mlResult) {
    http_response_code(500);
    echo json_encode(['error' => 'Invalid response from ML service']);
    exit;
}

// Add P-number to response
$mlResult['p_number'] = $pNumber;
$mlResult['image_path'] = $imagePath;
$mlResult['source'] = $isTemporary ? 'cdli_remote' : 'local';

echo json_encode($mlResult);
