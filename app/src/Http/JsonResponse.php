<?php
/**
 * JSON Response Helper
 * Provides standardized JSON API response format
 */

declare(strict_types=1);

namespace Glintstone\Http;

final class JsonResponse
{
    /**
     * Send a success response and exit
     */
    public static function success(mixed $data, int $status = 200): never
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');

        echo json_encode([
            'success' => true,
            'data' => $data,
        ], JSON_UNESCAPED_UNICODE);

        exit;
    }

    /**
     * Send an error response and exit
     */
    public static function error(string $message, int $status = 400, ?array $details = null): never
    {
        http_response_code($status);
        header('Content-Type: application/json; charset=utf-8');

        $response = [
            'success' => false,
            'error' => $message,
        ];

        if ($details !== null) {
            $response['details'] = $details;
        }

        echo json_encode($response, JSON_UNESCAPED_UNICODE);

        exit;
    }

    /**
     * Send a 404 Not Found response
     */
    public static function notFound(string $message = 'Resource not found'): never
    {
        self::error($message, 404);
    }

    /**
     * Send a 400 Bad Request response
     */
    public static function badRequest(string $message = 'Bad request'): never
    {
        self::error($message, 400);
    }

    /**
     * Send a 500 Server Error response
     */
    public static function serverError(string $message = 'Internal server error', ?\Throwable $e = null): never
    {
        $details = null;

        // Include exception details in development mode
        if ($e !== null && (getenv('APP_DEBUG') || defined('APP_DEBUG') && APP_DEBUG)) {
            $details = [
                'exception' => get_class($e),
                'message' => $e->getMessage(),
                'file' => basename($e->getFile()),
                'line' => $e->getLine(),
            ];
        }

        self::error($message, 500, $details);
    }

    /**
     * Send a 403 Forbidden response
     */
    public static function forbidden(string $message = 'Forbidden'): never
    {
        self::error($message, 403);
    }

    /**
     * Send a 401 Unauthorized response
     */
    public static function unauthorized(string $message = 'Unauthorized'): never
    {
        self::error($message, 401);
    }

    /**
     * Send a paginated success response
     */
    public static function paginated(array $items, int $total, int $offset, int $limit): never
    {
        self::success([
            'items' => $items,
            'total' => $total,
            'offset' => $offset,
            'limit' => $limit,
            'hasMore' => ($offset + count($items)) < $total,
        ]);
    }

    /**
     * Validate required parameters exist
     * Returns error response if any are missing
     */
    public static function requireParams(array $params, array $required): void
    {
        $missing = [];

        foreach ($required as $param) {
            if (!isset($params[$param]) || $params[$param] === '') {
                $missing[] = $param;
            }
        }

        if (!empty($missing)) {
            self::badRequest('Missing required parameters: ' . implode(', ', $missing));
        }
    }

    /**
     * Get a parameter with optional default
     */
    public static function param(array $params, string $key, mixed $default = null): mixed
    {
        return $params[$key] ?? $default;
    }

    /**
     * Get an integer parameter with optional default
     */
    public static function intParam(array $params, string $key, int $default = 0): int
    {
        return isset($params[$key]) ? (int)$params[$key] : $default;
    }

    /**
     * Get a boolean parameter
     */
    public static function boolParam(array $params, string $key, bool $default = false): bool
    {
        if (!isset($params[$key])) {
            return $default;
        }
        return filter_var($params[$key], FILTER_VALIDATE_BOOLEAN);
    }
}
