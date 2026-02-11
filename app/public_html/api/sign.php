<?php
/**
 * Sign lookup API endpoint
 * Returns sign data from OGSL
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\SignRepository;
use function Glintstone\app;

$params = getRequestParams();
$query = $params['q'] ?? null;

if (!$query) {
    JsonResponse::badRequest('Missing query parameter');
}

$repo = app()->get(SignRepository::class);

$sign = $repo->findByQuery($query);

if ($sign) {
    $sign['values'] = $repo->getValueNames($sign['sign_id']);
    JsonResponse::success($sign);
} else {
    JsonResponse::notFound('Sign not found');
}
