<?php
/**
 * Thumbnail generation and caching API
 * Generates square, center-cropped thumbnails for tablets
 */

// Configuration
define('THUMBNAIL_SIZE', 200);
define('DATABASE_ROOT', dirname(__DIR__, 3) . '/database');
define('IMAGE_DIR', DATABASE_ROOT . '/images');
define('THUMBNAIL_DIR', IMAGE_DIR . '/thumbnails');
define('LOCAL_IMAGE_DIR', IMAGE_DIR);

// Ensure thumbnail directory exists
if (!is_dir(THUMBNAIL_DIR)) {
    mkdir(THUMBNAIL_DIR, 0755, true);
}

$pNumber = $_GET['p'] ?? null;
$size = min(400, max(50, intval($_GET['size'] ?? THUMBNAIL_SIZE)));
$forceRegenerate = isset($_GET['refresh']);

if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    http_response_code(400);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Invalid P-number format']);
    exit;
}

$thumbnailPath = THUMBNAIL_DIR . "/{$pNumber}_{$size}.jpg";

// Return cached thumbnail if exists and not forcing regenerate
if (file_exists($thumbnailPath) && !$forceRegenerate) {
    header('Content-Type: image/jpeg');
    header('Cache-Control: public, max-age=604800'); // 1 week
    header('X-Thumbnail-Source: cache');
    readfile($thumbnailPath);
    exit;
}

// Try to find source image
$sourceImage = null;
$sourceType = null;

// 1. Check local storage first
$localPath = LOCAL_IMAGE_DIR . "/{$pNumber}.jpg";
if (file_exists($localPath)) {
    $sourceImage = $localPath;
    $sourceType = 'local';
}

// 2. Try CDLI photo (cdli.earth is the current domain)
if (!$sourceImage) {
    $cdliUrl = "https://cdli.earth/dl/photo/{$pNumber}.jpg";
    $sourceImage = fetchRemoteImage($cdliUrl);
    if ($sourceImage) {
        $sourceType = 'cdli-photo';
    }
}

// 3. Try CDLI lineart
if (!$sourceImage) {
    $cdliLineartUrl = "https://cdli.earth/dl/lineart/{$pNumber}.jpg";
    $sourceImage = fetchRemoteImage($cdliLineartUrl);
    if ($sourceImage) {
        $sourceType = 'cdli-lineart';
    }
}

// No source found
if (!$sourceImage) {
    http_response_code(404);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'No image available', 'p_number' => $pNumber]);
    exit;
}

// Generate thumbnail
$thumbnail = generateSquareThumbnail($sourceImage, $size, $sourceType !== 'local');

if ($thumbnail) {
    // Save to cache
    imagejpeg($thumbnail, $thumbnailPath, 85);

    // Update pipeline_status if we got image from CDLI
    if (str_starts_with($sourceType, 'cdli')) {
        updateImageStatus($pNumber, $sourceType);
    }

    // Output
    header('Content-Type: image/jpeg');
    header('Cache-Control: public, max-age=604800');
    header('X-Thumbnail-Source: ' . $sourceType);
    imagejpeg($thumbnail, null, 85);
    imagedestroy($thumbnail);
} else {
    http_response_code(500);
    header('Content-Type: application/json');
    echo json_encode(['error' => 'Failed to generate thumbnail']);
}

/**
 * Fetch remote image and return temp file path or false
 */
function fetchRemoteImage(string $url): ?string {
    $context = stream_context_create([
        'http' => [
            'timeout' => 10,
            'user_agent' => 'Glintstone/1.0 (Cuneiform Research Platform)'
        ]
    ]);

    $imageData = @file_get_contents($url, false, $context);

    if ($imageData === false || strlen($imageData) < 1000) {
        return null;
    }

    // Check if it's actually an image
    $finfo = new finfo(FILEINFO_MIME_TYPE);
    $mimeType = $finfo->buffer($imageData);

    if (!str_starts_with($mimeType, 'image/')) {
        return null;
    }

    // Save to temp file
    $tempFile = tempnam(sys_get_temp_dir(), 'cdli_');
    file_put_contents($tempFile, $imageData);

    return $tempFile;
}

/**
 * Generate a square, center-cropped thumbnail
 */
function generateSquareThumbnail(string $sourcePath, int $size, bool $isTemp = false): ?GdImage {
    // Load source image
    $imageInfo = @getimagesize($sourcePath);
    if (!$imageInfo) {
        if ($isTemp) unlink($sourcePath);
        return null;
    }

    $sourceWidth = $imageInfo[0];
    $sourceHeight = $imageInfo[1];
    $mimeType = $imageInfo['mime'];

    // Create source image resource
    $source = match($mimeType) {
        'image/jpeg' => @imagecreatefromjpeg($sourcePath),
        'image/png' => @imagecreatefrompng($sourcePath),
        'image/gif' => @imagecreatefromgif($sourcePath),
        'image/webp' => @imagecreatefromwebp($sourcePath),
        default => null
    };

    // Clean up temp file
    if ($isTemp) {
        unlink($sourcePath);
    }

    if (!$source) {
        return null;
    }

    // Calculate crop dimensions (center crop to square)
    $cropSize = min($sourceWidth, $sourceHeight);
    $cropX = ($sourceWidth - $cropSize) / 2;
    $cropY = ($sourceHeight - $cropSize) / 2;

    // Create thumbnail
    $thumbnail = imagecreatetruecolor($size, $size);

    // Set background color (dark theme)
    $bgColor = imagecolorallocate($thumbnail, 30, 30, 35);
    imagefill($thumbnail, 0, 0, $bgColor);

    // Enable better resampling
    imagealphablending($thumbnail, true);

    // Copy and resize with center crop
    imagecopyresampled(
        $thumbnail,
        $source,
        0, 0,           // Destination X, Y
        (int)$cropX, (int)$cropY,  // Source X, Y (center crop)
        $size, $size,   // Destination width, height
        $cropSize, $cropSize  // Source width, height (square crop)
    );

    imagedestroy($source);

    return $thumbnail;
}

/**
 * Update pipeline_status to mark image as available
 */
function updateImageStatus(string $pNumber, string $source): void {
    try {
        $dbPath = DATABASE_ROOT . '/glintstone.db';
        $db = new SQLite3($dbPath, SQLITE3_OPEN_READWRITE);

        // Update or insert pipeline status
        $db->exec("
            INSERT INTO pipeline_status (p_number, has_image)
            VALUES ('$pNumber', 1)
            ON CONFLICT(p_number) DO UPDATE SET
                has_image = 1,
                quality_score = (
                    1 * 0.2 +
                    COALESCE(has_atf, 0) * 0.3 +
                    COALESCE(has_lemmas, 0) * 0.25 +
                    COALESCE(has_translation, 0) * 0.25
                ),
                last_updated = CURRENT_TIMESTAMP
        ");

        $db->close();
    } catch (Exception $e) {
        // Silently fail - thumbnail still works even if DB update fails
        error_log("Failed to update image status for $pNumber: " . $e->getMessage());
    }
}
