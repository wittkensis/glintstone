<?php
/**
 * Example: New-style API endpoint using the refactored architecture
 *
 * This file demonstrates how to use the new service/repository pattern.
 * It can be deleted once the migration is complete.
 *
 * Key differences from old style:
 * 1. Uses _bootstrap.php for standardized error handling
 * 2. Uses JsonResponse for consistent response format
 * 3. Uses service classes instead of direct db.php functions
 * 4. Type-safe parameter handling
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Service\TabletService;
use Glintstone\Service\FilterService;
use function Glintstone\app;

// Require GET method
requireMethod('GET');

// Get request parameters
$params = getRequestParams();

// Example 1: Get tablet detail
if (isset($params['p'])) {
    $tabletService = app()->get(TabletService::class);
    $detail = $tabletService->getTabletDetail($params['p']);

    if (!$detail) {
        JsonResponse::notFound("Tablet not found: {$params['p']}");
    }

    JsonResponse::success($detail);
}

// Example 2: Get filter stats
if (isset($params['action']) && $params['action'] === 'filter-stats') {
    $filterService = app()->get(FilterService::class);

    // Check if filters are active
    $filters = FilterService::parseFilters($params);
    $hasActiveFilters = !empty(array_filter($filters));

    if ($hasActiveFilters) {
        // Get filtered stats (counts adjusted for active filters)
        $stats = $filterService->getAllFilteredStats($filters);
    } else {
        // Get static stats (cached)
        $stats = $filterService->getAllStats();
    }

    JsonResponse::success($stats);
}

// Example 3: Search tablets
if (isset($params['action']) && $params['action'] === 'search') {
    $tabletService = app()->get(TabletService::class);
    $filters = FilterService::parseFilters($params);

    $limit = JsonResponse::intParam($params, 'limit', 24);
    $offset = JsonResponse::intParam($params, 'offset', 0);

    $results = $tabletService->getFilteredTablets($filters, $limit, $offset);

    JsonResponse::paginated(
        $results['items'],
        $results['total'],
        $results['offset'],
        $results['limit']
    );
}

// No valid action specified
JsonResponse::badRequest('Missing or invalid action parameter');
