<?php
/**
 * Filter Helper Functions
 * URL building and filter state management for list views
 */

/**
 * Build URL with current filters, adding or removing specific values
 */
function buildFilterUrl(array $add = [], array $remove = []): string {
    $params = $_GET;
    unset($params['page']); // Reset to page 1 when changing filters

    foreach ($add as $key => $value) {
        if (!isset($params[$key])) {
            $params[$key] = [];
        }
        if (!is_array($params[$key])) {
            $params[$key] = [$params[$key]];
        }
        if (!in_array($value, $params[$key])) {
            $params[$key][] = $value;
        }
    }

    foreach ($remove as $key => $value) {
        if (isset($params[$key])) {
            if (is_array($params[$key])) {
                $params[$key] = array_diff($params[$key], [$value]);
                if (empty($params[$key])) {
                    unset($params[$key]);
                }
            } elseif ($params[$key] === $value) {
                unset($params[$key]);
            }
        }
    }

    return '?' . http_build_query($params);
}

/**
 * Check if a filter value is currently active
 */
function isFilterActive(string $key, string $value): bool {
    if (!isset($_GET[$key])) return false;
    $values = is_array($_GET[$key]) ? $_GET[$key] : [$_GET[$key]];
    return in_array($value, $values);
}
