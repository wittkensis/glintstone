<?php
/**
 * Centralized Dictionary Label Definitions
 *
 * DEPRECATED: This file now re-exports from src/Data/Labels.php
 * New code should use Glintstone\Data\Labels directly.
 *
 * Maintained for backward compatibility with existing includes.
 */

// Load the canonical source
require_once dirname(__DIR__, 2) . '/src/Bootstrap.php';

use Glintstone\Data\Labels;

// Re-export as global variables for backward compatibility
$POS_LABELS = Labels::POS;
$NAME_TYPE_LABELS = Labels::NAME_TYPES;
$LANGUAGE_LABELS = Labels::LANGUAGES;
$FREQUENCY_LABELS = Labels::FREQUENCY_RANGES;
$NAME_TYPE_CODES = Labels::NAME_TYPE_CODES;
$HIDDEN_LANGUAGES = Labels::HIDDEN_LANGUAGES;

/**
 * Output labels as JavaScript constants
 * Call this in a <script> tag to make labels available to JS
 *
 * @deprecated Use Labels::toJavaScript() instead
 */
function outputLabelsAsJavaScript(): void {
    echo Glintstone\Data\Labels::toJavaScript();
}
