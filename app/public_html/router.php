<?php
/**
 * Router script for PHP dev server
 * Bypasses some dev server bugs by controlling request handling
 */

// Disable output buffering (can cause memory issues)
ini_set('output_buffering', 'Off');
ini_set('zlib.output_compression', 'Off');

// Set memory limit
ini_set('memory_limit', '256M');

// Get the requested URI
$uri = $_SERVER['REQUEST_URI'];

// Remove query string
$path = parse_url($uri, PHP_URL_PATH);

// Serve static files directly
if ($path !== '/' && file_exists(__DIR__ . $path)) {
    return false; // Let PHP dev server handle it
}

// For PHP files, include them normally
if (file_exists(__DIR__ . $path)) {
    require __DIR__ . $path;
    exit;
}

// 404 for everything else
http_response_code(404);
echo json_encode(['error' => 'Not found']);
