<?php
/**
 * Display Helper Functions
 * Formatting and display logic for tablet cards and list views
 */

/**
 * Get abbreviated language indicator for display badge
 */
function getLanguageAbbreviation(?string $language): ?string {
    if (!$language) return null;

    $langLower = strtolower($language);

    // Check for undetermined/uncertain first - no badge
    if (strpos($langLower, 'undetermined') !== false ||
        strpos($langLower, 'uncertain') !== false ||
        strpos($langLower, 'uninscribed') !== false ||
        strpos($langLower, 'no linguistic') !== false) {
        return null;
    }

    $abbreviations = [];

    // Sumerian
    if (strpos($langLower, 'sumerian') !== false) {
        $abbreviations[] = 'Su';
    }

    // Akkadian (includes Babylonian, Assyrian dialects)
    if (strpos($langLower, 'akkadian') !== false ||
        strpos($langLower, 'babylonian') !== false ||
        strpos($langLower, 'assyrian') !== false) {
        $abbreviations[] = 'Ak';
    }

    // Elamite
    if (strpos($langLower, 'elamite') !== false) {
        $abbreviations[] = 'El';
    }

    // Anatolian languages
    if (strpos($langLower, 'hittite') !== false ||
        strpos($langLower, 'luwian') !== false ||
        strpos($langLower, 'hurrian') !== false ||
        strpos($langLower, 'palaic') !== false) {
        $abbreviations[] = 'An';
    }

    // Northwest Semitic
    if (strpos($langLower, 'eblaite') !== false ||
        strpos($langLower, 'ugaritic') !== false ||
        strpos($langLower, 'aramaic') !== false ||
        strpos($langLower, 'hebrew') !== false ||
        strpos($langLower, 'phoenician') !== false) {
        $abbreviations[] = 'NW';
    }

    // Indo-European (non-Anatolian)
    if (strpos($langLower, 'persian') !== false ||
        strpos($langLower, 'greek') !== false) {
        $abbreviations[] = 'IE';
    }

    if (empty($abbreviations)) return null;

    // Return joined with slash for mixed languages
    return implode('/', array_unique($abbreviations));
}

/**
 * Get pipeline segment status for compact display
 * Returns: 'complete', 'partial', 'inferred', 'skipped', or 'missing'
 *
 * "skipped" means: intermediate step not captured, but downstream data exists
 * (tablet is fully studied, just missing this intermediate data)
 */
function getPipelineSegmentStatus(string $stage, array $tablet): string {
    $hasAtf = !empty($tablet['has_atf']);
    $hasOcr = !empty($tablet['has_sign_annotations']);
    $hasLemmas = !empty($tablet['has_lemmas']);
    $hasTrans = !empty($tablet['has_translation']);

    // If tablet has translation, it's "fully studied"
    $fullyStudied = $hasTrans;
    $partiallyStudied = $hasLemmas || $hasAtf;

    switch ($stage) {
        case 'image':
            return !empty($tablet['has_image']) ? 'complete' : 'missing';

        case 'signs':
            if ($hasOcr) return 'complete';
            // If downstream data exists, signs just weren't captured
            if ($fullyStudied || $partiallyStudied) return 'skipped';
            return 'missing';

        case 'transliteration':
            if ($hasAtf) return 'complete';
            if ($hasLemmas || $hasTrans) return 'inferred';
            return 'missing';

        case 'lemmas':
            if ($hasLemmas) {
                $coverage = $tablet['lemma_coverage'] ?? 1.0;
                return ($coverage < 1.0) ? 'partial' : 'complete';
            }
            // Has translation but no lemmas - scholarly work done, just not in ORACC
            if ($fullyStudied) return 'skipped';
            return 'missing';

        case 'translation':
            return $hasTrans ? 'complete' : 'missing';

        default:
            return 'missing';
    }
}

/**
 * Truncate text for card display
 */
function truncateText(?string $text, int $maxLen = 20): string {
    if (!$text) return '';
    if (strlen($text) <= $maxLen) return $text;
    return substr($text, 0, $maxLen - 1) . '…';
}
