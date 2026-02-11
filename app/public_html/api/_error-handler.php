<?php
/**
 * Shared error handler for all API endpoints
 * Include this at the very top of each API file (after opening PHP tag)
 *
 * Usage:
 *   require_once __DIR__ . '/_error-handler.php';
 */

// Start output buffering IMMEDIATELY to catch any stray output
ob_start();

// Set JSON header FIRST before any other includes
header('Content-Type: application/json');

// Catch all PHP errors (warnings, notices) and return as JSON
set_error_handler(function($errno, $errstr, $errfile, $errline) {
    http_response_code(500);
    echo json_encode([
        'error' => 'Server error',
        'message' => $errstr,
        'file' => basename($errfile),
        'line' => $errline,
        'type' => 'PHP Error'
    ]);
    exit;
});

// Catch fatal errors and exceptions
register_shutdown_function(function() {
    $error = error_get_last();

    // Clear output buffer and check for stray output
    $output = ob_get_clean();

    if ($error !== null && in_array($error['type'], [E_ERROR, E_PARSE, E_CORE_ERROR, E_COMPILE_ERROR])) {
        // Fatal error occurred - output JSON error
        header('Content-Type: application/json', true);
        http_response_code(500);
        echo json_encode([
            'error' => 'Fatal server error',
            'message' => $error['message'],
            'file' => basename($error['file']),
            'line' => $error['line'],
            'type' => 'Fatal Error',
            'stray_output' => !empty($output) ? substr($output, 0, 100) : null
        ]);
    } else {
        // No fatal error - check if output looks like an error
        // Only treat as stray output if it contains HTML tags or PHP error markers
        $isHtmlError = !empty($output) && (
            stripos($output, '<br') !== false ||
            stripos($output, '<b>') !== false ||
            stripos($output, 'Fatal error') !== false ||
            stripos($output, 'Warning:') !== false ||
            stripos($output, 'Notice:') !== false ||
            stripos($output, 'Parse error') !== false
        );

        if ($isHtmlError) {
            // Detected PHP error output - report it
            header('Content-Type: application/json', true);
            http_response_code(500);
            echo json_encode([
                'error' => 'Stray output detected',
                'message' => 'PHP error output occurred before JSON response',
                'output' => substr($output, 0, 200)
            ]);
        } else {
            // Normal execution - flush the buffer
            echo $output;
        }
    }
});

/**
 * Wrap dangerous operations in this function
 * Returns ['success' => true, 'data' => ...] or ['success' => false, 'error' => ...]
 */
function api_try(callable $fn): array {
    try {
        return ['success' => true, 'data' => $fn()];
    } catch (Throwable $e) {
        return [
            'success' => false,
            'error' => $e->getMessage(),
            'type' => get_class($e)
        ];
    }
}
