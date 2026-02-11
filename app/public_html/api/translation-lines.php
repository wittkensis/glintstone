<?php
/**
 * Translation Lines API
 * Parses translations into line-by-line mappings for side-by-side display
 *
 * Parameters:
 *   p     - P-number (required)
 *   lang  - Language filter (optional, default: 'en')
 */

require_once __DIR__ . '/_bootstrap.php';

use Glintstone\Http\JsonResponse;
use Glintstone\Repository\InscriptionRepository;
use function Glintstone\app;

// Get parameters
$params = getRequestParams();
$pNumber = $params['p'] ?? null;
$language = $params['lang'] ?? 'en';

// Validate P-number format
if (!$pNumber || !preg_match('/^P\d{6}$/', $pNumber)) {
    JsonResponse::badRequest('Invalid P-number format');
}

// Get translations
$repo = app()->get(InscriptionRepository::class);
$translations = $repo->getTranslations($pNumber);

if (empty($translations)) {
    JsonResponse::success([
        'p_number' => $pNumber,
        'has_translation' => false,
        'message' => 'No translation available'
    ]);
}

// Find best translation (prefer requested language)
$translation = null;
foreach ($translations as $t) {
    if ($t['language'] === $language) {
        $translation = $t;
        break;
    }
}
// Fall back to first available
if (!$translation) {
    $translation = $translations[0];
}

// Parse translation into structured lines
$lines = parseTranslationLines($translation['translation'] ?? '');

JsonResponse::success([
    'p_number' => $pNumber,
    'has_translation' => true,
    'language' => $translation['language'],
    'source' => $translation['source'],
    'lines' => $lines,
    'raw' => $translation['translation']
]);

/**
 * Parse translation text into line-by-line structure
 * Handles various formats:
 * - Numbered lines: "1. text" or "(1) text"
 * - Surface markers: "@obverse", "@reverse"
 * - Column markers: "Column 1:", "Col. i:"
 */
function parseTranslationLines(string $text): array {
    $result = [];
    $currentSurface = 'obverse';
    $currentColumn = 1;

    $lines = explode("\n", $text);

    foreach ($lines as $line) {
        $line = trim($line);
        if (empty($line)) continue;

        // Check for surface markers
        if (preg_match('/^@?(obverse|reverse|left|right|top|bottom|edge)/i', $line, $m)) {
            $currentSurface = strtolower($m[1]);
            continue;
        }

        // Check for column markers
        if (preg_match('/^(?:column|col\.?)\s*(\d+|[ivx]+)/i', $line, $m)) {
            $currentColumn = parseColumnNumber($m[1]);
            continue;
        }

        // Check for numbered lines: "1. text", "(1) text", "1: text", "1' text"
        if (preg_match('/^(\d+[\'"]?)[\.\:\)\s]+(.+)$/', $line, $m)) {
            $lineNum = $m[1] . '.';
            $content = trim($m[2]);

            $key = "{$currentSurface}_{$currentColumn}_{$lineNum}";
            $result[$key] = [
                'surface' => $currentSurface,
                'column' => $currentColumn,
                'line' => $lineNum,
                'text' => $content
            ];
            continue;
        }

        // Check for range: "1-3. text" or "1-3: text"
        if (preg_match('/^(\d+)\s*[-–]\s*(\d+)[\.\:\)\s]+(.+)$/', $line, $m)) {
            $startLine = (int)$m[1];
            $endLine = (int)$m[2];
            $content = trim($m[3]);

            // Store under the start line
            $lineNum = $startLine . '.';
            $key = "{$currentSurface}_{$currentColumn}_{$lineNum}";
            $result[$key] = [
                'surface' => $currentSurface,
                'column' => $currentColumn,
                'line' => $lineNum,
                'lineEnd' => $endLine . '.',
                'text' => $content
            ];
            continue;
        }
    }

    return $result;
}

/**
 * Parse column number (handles roman numerals and arabic)
 */
function parseColumnNumber(string $num): int {
    $num = strtolower(trim($num));

    // Roman numerals
    $romans = [
        'i' => 1, 'ii' => 2, 'iii' => 3, 'iv' => 4, 'v' => 5,
        'vi' => 6, 'vii' => 7, 'viii' => 8, 'ix' => 9, 'x' => 10
    ];

    if (isset($romans[$num])) {
        return $romans[$num];
    }

    return (int)$num ?: 1;
}
