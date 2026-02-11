<?php
/**
 * Centralized Dictionary Label Definitions
 * Single source of truth for all POS, language, and frequency labels
 * Used by both PHP templates and JavaScript (via JSON output)
 */

// Parts of Speech (linguistic categories)
$POS_LABELS = [
    // Basic POS
    'N' => 'Noun',
    'V' => 'Verb',
    'V/t' => 'Transitive Verb',
    'V/i' => 'Intransitive Verb',
    'AJ' => 'Adjective',
    'AV' => 'Adverb',
    'NU' => 'Number',

    // Function words
    'PRP' => 'Preposition',
    'PP' => 'Possessive Pronoun',
    'CNJ' => 'Conjunction',

    // Pronouns and determiners
    'DP' => 'Demonstrative',
    'IP' => 'Pronoun',
    'RP' => 'Reflexive',
    'XP' => 'Indefinite Pronoun',
    'REL' => 'Relative',
    'QP' => 'Interrogative',
    'DET' => 'Determiner',

    // Modifiers and particles
    'MOD' => 'Modal',
    'J' => 'Interjection',
    'SBJ' => 'Subjunction',
    'MA' => 'Auxiliary',

    // Other
    'M' => 'Morpheme',
    'O' => 'Other'
];

// Proper Noun Types (name categories)
// These are stored in the POS field but represent name classifications
$NAME_TYPE_LABELS = [
    'PN' => 'Personal Name',
    'DN' => 'Divine Name',
    'GN' => 'Geographic Name',
    'SN' => 'Settlement Name',
    'TN' => 'Temple Name',
    'WN' => 'Watercourse Name',
    'RN' => 'Royal Name',
    'EN' => 'Ethnic Name',
    'CN' => 'Celestial Name',
    'ON' => 'Object Name',
    'MN' => 'Month Name',
    'LN' => 'Line Name',
    'FN' => 'Field Name',
    'AN' => 'Artifact Name'
];

// Language labels
$LANGUAGE_LABELS = [
    'akk' => 'Akkadian',
    'akk-x-stdbab' => 'Standard Babylonian',
    'akk-x-oldbab' => 'Old Babylonian',
    'akk-x-neoass' => 'Neo-Assyrian',
    'sux' => 'Sumerian',
    'sux-x-emesal' => 'Emesal (Sumerian)',
    'xhu' => 'Hurrian',
    'uga' => 'Ugaritic',
    'elx' => 'Elamite'
];

// Frequency range labels
$FREQUENCY_LABELS = [
    '1' => 'Hapax (1)',
    '2-10' => 'Rare (2-10)',
    '11-100' => 'Uncommon (11-100)',
    '101-500' => 'Common (101-500)',
    '500+' => 'Very Common (500+)'
];

// List of codes that are name types (to separate from true POS)
$NAME_TYPE_CODES = ['PN', 'DN', 'GN', 'SN', 'TN', 'WN', 'RN', 'EN', 'CN', 'ON', 'MN', 'LN', 'FN', 'AN'];

// Languages to hide from the Language section
$HIDDEN_LANGUAGES = ['qpn', 'qpn-x-places'];

/**
 * Output labels as JavaScript constants
 * Call this in a <script> tag to make labels available to JS
 */
function outputLabelsAsJavaScript() {
    global $POS_LABELS, $NAME_TYPE_LABELS, $LANGUAGE_LABELS, $FREQUENCY_LABELS;

    // Merge POS and name types for JavaScript
    $allPosLabels = array_merge($POS_LABELS, $NAME_TYPE_LABELS);

    echo "window.DICTIONARY_LABELS = " . json_encode([
        'pos' => $allPosLabels,
        'language' => $LANGUAGE_LABELS,
        'frequency' => $FREQUENCY_LABELS
    ], JSON_PRETTY_PRINT) . ";\n";
}
