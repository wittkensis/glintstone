<?php
/**
 * Educational Content API
 * Returns centralized educational text as JSON for JS consumers.
 * Source of truth: /includes/educational-content.php
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;

$content = require dirname(__DIR__) . '/includes/educational-content.php';

JsonResponse::success($content);
