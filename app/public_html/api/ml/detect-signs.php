<?php
/**
 * ML Sign Detection Proxy
 * Proxies requests to the local FastAPI ML service
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\ArtifactRepository;
use function Glintstone\app;

// ML service configuration
$MODAL_ENDPOINT = getenv('MODAL_ENDPOINT');
$ML_SERVICE_URL = $MODAL_ENDPOINT ?: 'http://localhost:8000';

error_log("ML Service: Using endpoint " . $ML_SERVICE_URL);

$params = getRequestParams();
$pNumber = $params['p'] ?? null;
$confidenceThreshold = $params['confidence'] ?? 0.3;

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format');
}

// Get image path from database
$repo = app()->get(ArtifactRepository::class);
$artifact = $repo->findByPNumber($pNumber);
$imagePath = $artifact ? ($artifact['image_path'] ?? null) : null;
$fullImagePath = null;
$isTemporary = false;

// Try to resolve local image path
if ($imagePath) {
    $fullImagePath = realpath(__DIR__ . '/../../' . $imagePath);
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

    $tempDir = sys_get_temp_dir() . '/cuneiform_ml';
    if (!is_dir($tempDir)) {
        mkdir($tempDir, 0755, true);
    }

    $tempPath = $tempDir . "/{$pNumber}.jpg";

    $fp = fopen($tempPath, 'wb');
    if (!$fp) {
        JsonResponse::serverError('Failed to create temporary file');
    }

    $ch = curl_init($cdliUrl);
    curl_setopt_array($ch, [
        CURLOPT_FILE => $fp,
        CURLOPT_FOLLOWLOCATION => true,
        CURLOPT_TIMEOUT => 30,
        CURLOPT_CONNECTTIMEOUT => 10,
        CURLOPT_USERAGENT => 'CUNEIFORM/1.0',
        CURLOPT_BUFFERSIZE => 128 * 1024,
        CURLOPT_NOPROGRESS => false,
        CURLOPT_PROGRESSFUNCTION => function($resource, $downloadSize, $downloaded, $uploadSize, $uploaded) {
            if ($downloaded > 50 * 1024 * 1024) {
                return 1;
            }
            return 0;
        }
    ]);

    $success = curl_exec($ch);
    $curlError = curl_error($ch);
    $httpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
    $contentType = curl_getinfo($ch, CURLINFO_CONTENT_TYPE);
    curl_close($ch);
    fclose($fp);

    if (!$success || $curlError) {
        @unlink($tempPath);
        JsonResponse::error('Failed to download image', 502, [
            'p_number' => $pNumber,
            'detail' => $curlError ?: 'Download failed'
        ]);
    }

    if ($httpCode === 200 && file_exists($tempPath)) {
        $dataSize = filesize($tempPath);

        if ($dataSize < 1000) {
            @unlink($tempPath);
            JsonResponse::error('Downloaded image too small', 502);
        }

        if ($dataSize > 50 * 1024 * 1024) {
            @unlink($tempPath);
            JsonResponse::error('Downloaded image too large', 502);
        }

        // Validate magic bytes
        $fpCheck = fopen($tempPath, 'rb');
        $header = fread($fpCheck, 10);
        fclose($fpCheck);

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
            JsonResponse::error('Downloaded file is not a valid image', 502);
        }

        $fullImagePath = $tempPath;
        $isTemporary = true;
    } else {
        @unlink($tempPath);
        JsonResponse::notFound('No image available');
    }
}

if (!$fullImagePath || !file_exists($fullImagePath)) {
    JsonResponse::notFound('Image file not found');
}

// Register cleanup for temporary file
if ($isTemporary) {
    register_shutdown_function(function() use ($fullImagePath) {
        if (file_exists($fullImagePath)) {
            @unlink($fullImagePath);
        }
    });
}

// Call ML service
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
    CURLOPT_TIMEOUT => 180,
    CURLOPT_CONNECTTIMEOUT => 10,
]);

$response = curl_exec($ch);
$mlHttpCode = curl_getinfo($ch, CURLINFO_HTTP_CODE);
$error = curl_error($ch);
curl_close($ch);

if ($error) {
    JsonResponse::error('ML service unavailable', 503, [
        'detail' => $error,
        'hint' => 'Ensure the ML service is running: cd ml-service && python app.py'
    ]);
}

if ($mlHttpCode !== 200) {
    JsonResponse::error('ML service error', $mlHttpCode, [
        'response' => json_decode($response, true)
    ]);
}

$mlResult = json_decode($response, true);

if (!$mlResult) {
    JsonResponse::serverError('Invalid response from ML service');
}

$mlResult['p_number'] = $pNumber;
$mlResult['image_path'] = $imagePath;
$mlResult['source'] = $isTemporary ? 'cdli_remote' : 'local';

// Output directly (ML results have their own structure)
echo json_encode($mlResult);
exit;
