<?php
/**
 * Application Configuration
 * Central place for app-wide settings
 */

declare(strict_types=1);

return [
    // Debug mode (shows detailed errors in API responses)
    'debug' => getenv('APP_DEBUG') ?: false,

    // Cache settings
    'cache' => [
        'enabled' => true,
        'directory' => CACHE_ROOT,
    ],

    // Database settings
    'database' => [
        'path' => DB_PATH,
        'readonly_by_default' => true,
    ],

    // Pagination defaults
    'pagination' => [
        'tablets_per_page' => 24,
        'dictionary_per_page' => 50,
        'max_per_page' => 200,
    ],
];
