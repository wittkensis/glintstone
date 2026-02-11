<?php
/**
 * API Bootstrap
 * Shared initialization for all API endpoints
 * Provides standardized error handling and response utilities
 */

declare(strict_types=1);

// Start output buffering for clean error handling
ob_start();

// Set JSON content type
header('Content-Type: application/json; charset=utf-8');

// Load application core
require_once dirname(__DIR__, 2) . '/src/Bootstrap.php';

use Glintstone\Http\JsonResponse;

// Global error handler - convert PHP errors to JSON responses
set_error_handler(function (int $errno, string $errstr, string $errfile, int $errline): bool {
    // Don't handle suppressed errors
    if (!(error_reporting() & $errno)) {
        return false;
    }

    ob_end_clean();
    JsonResponse::serverError(
        'Server error',
        new \ErrorException($errstr, 0, $errno, $errfile, $errline)
    );
});

// Global exception handler
set_exception_handler(function (\Throwable $e): void {
    ob_end_clean();
    JsonResponse::serverError('Server error', $e);
});

// Shutdown handler for fatal errors
register_shutdown_function(function (): void {
    $error = error_get_last();

    if ($error !== null && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR], true)) {
        ob_end_clean();
        JsonResponse::serverError('Fatal server error');
    }
});

// CORS headers for API access (adjust as needed)
if (isset($_SERVER['HTTP_ORIGIN'])) {
    header('Access-Control-Allow-Origin: ' . $_SERVER['HTTP_ORIGIN']);
    header('Access-Control-Allow-Credentials: true');
}

if ($_SERVER['REQUEST_METHOD'] === 'OPTIONS') {
    header('Access-Control-Allow-Methods: GET, POST, PUT, DELETE, OPTIONS');
    header('Access-Control-Allow-Headers: Content-Type, Authorization');
    header('Access-Control-Max-Age: 86400');
    exit(0);
}

/**
 * Helper function to get request parameters from both GET and POST
 */
function getRequestParams(): array
{
    $params = $_GET;

    // Merge POST data if present
    if ($_SERVER['REQUEST_METHOD'] === 'POST') {
        $contentType = $_SERVER['CONTENT_TYPE'] ?? '';

        if (strpos($contentType, 'application/json') !== false) {
            $input = file_get_contents('php://input');
            $json = json_decode($input, true);
            if (is_array($json)) {
                $params = array_merge($params, $json);
            }
        } else {
            $params = array_merge($params, $_POST);
        }
    }

    return $params;
}

/**
 * Helper function to require specific HTTP method
 */
function requireMethod(string ...$methods): void
{
    if (!in_array($_SERVER['REQUEST_METHOD'], $methods, true)) {
        JsonResponse::error(
            'Method not allowed. Allowed: ' . implode(', ', $methods),
            405
        );
    }
}

// Make app() available
use function Glintstone\app;
