<?php
/**
 * Glossary browse API endpoint
 * Returns paginated dictionary entries with search and filtering
 *
 * Parameters:
 *   search   - Search query (optional, searches headword, citation_form, guide_word)
 *   language - Filter by language (optional, e.g., 'akk', 'sux')
 *   pos      - Filter by part of speech (optional, e.g., 'N', 'V')
 *   offset   - Pagination offset (default: 0)
 *   limit    - Results per page (default: 50, max: 100)
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Service\DictionaryService;
use function Glintstone\app;

// Get parameters
$params = getRequestParams();
$offset = max(0, (int)($params['offset'] ?? 0));
$limit = min(100, max(1, (int)($params['limit'] ?? 50)));

// Parse filters
$filters = DictionaryService::parseFilters($params);

// Get dictionary service and browse
$service = app()->get(DictionaryService::class);
$result = $service->browse($filters, $limit, $offset);

// Build response
JsonResponse::success([
    'entries' => $result['items'],
    'total' => $result['total'],
    'offset' => $result['offset'],
    'limit' => $result['limit'],
    'hasMore' => ($result['offset'] + count($result['items'])) < $result['total'],
    'filters' => $filters
]);
