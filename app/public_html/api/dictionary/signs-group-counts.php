<?php
/**
 * Signs Group Counts API
 * Returns counts for the signs browser groupings panel
 */

require_once __DIR__ . '/../_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\SignRepository;
use function Glintstone\app;

$repo = app()->get(SignRepository::class);
$counts = $repo->getGroupCounts();

JsonResponse::success($counts);
