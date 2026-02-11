<?php
// Minimal test - no database, no includes
header('Content-Type: application/json');
echo json_encode([
    'status' => 'ok',
    'php_version' => PHP_VERSION,
    'message' => 'This endpoint works'
]);
