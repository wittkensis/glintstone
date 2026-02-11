<?php
/**
 * Composite Text API
 * Returns composite metadata and all tablets that belong to it
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\ArtifactRepository;
use function Glintstone\app;

$params = getRequestParams();
$qNumber = $params['q'] ?? null;

if (!$qNumber) {
    JsonResponse::badRequest('Missing q parameter');
}

$repo = app()->get(ArtifactRepository::class);

$composite = $repo->findComposite($qNumber);
if (!$composite) {
    JsonResponse::notFound('Composite not found');
}

$tablets = $repo->getTabletsInComposite($qNumber);

JsonResponse::success([
    'composite' => $composite,
    'tablets' => $tablets,
    'count' => count($tablets)
]);
