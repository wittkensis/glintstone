<?php
/**
 * Centralized Label Definitions
 * Single source of truth for all POS, language, and frequency labels
 * Used by PHP templates, components, and JavaScript
 */

declare(strict_types=1);

namespace Glintstone\Data;

final class Labels
{
    /**
     * Parts of Speech (linguistic categories)
     */
    public const POS = [
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
        'O' => 'Other',
    ];

    /**
     * Proper Noun Types (name categories)
     * These are stored in the POS field but represent name classifications
     */
    public const NAME_TYPES = [
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
        'AN' => 'Artifact Name',
    ];

    /**
     * Language labels
     */
    public const LANGUAGES = [
        'akk' => 'Akkadian',
        'akk-x-stdbab' => 'Standard Babylonian',
        'akk-x-oldbab' => 'Old Babylonian',
        'akk-x-neoass' => 'Neo-Assyrian',
        'akk-x-oldakk' => 'Old Akkadian',
        'akk-x-midass' => 'Middle Assyrian',
        'akk-x-midbab' => 'Middle Babylonian',
        'akk-x-neobab' => 'Neo-Babylonian',
        'akk-x-ltebab' => 'Late Babylonian',
        'sux' => 'Sumerian',
        'sux-x-emesal' => 'Emesal (Sumerian)',
        'sux-x-udgalnun' => 'Udgalnun (Sumerian)',
        'xhu' => 'Hurrian',
        'uga' => 'Ugaritic',
        'elx' => 'Elamite',
        'arc' => 'Aramaic',
        'grc' => 'Greek',
        'qpn' => 'Proper Noun (Unclassified)',
        'qpn-x-places' => 'Place Name (Unclassified)',
    ];

    /**
     * Frequency range labels
     */
    public const FREQUENCY_RANGES = [
        '1' => 'Hapax (1)',
        '2-10' => 'Rare (2-10)',
        '11-100' => 'Uncommon (11-100)',
        '101-500' => 'Common (101-500)',
        '500+' => 'Very Common (500+)',
    ];

    /**
     * List of codes that are name types (to separate from true POS)
     */
    public const NAME_TYPE_CODES = ['PN', 'DN', 'GN', 'SN', 'TN', 'WN', 'RN', 'EN', 'CN', 'ON', 'MN', 'LN', 'FN', 'AN'];

    /**
     * Languages to hide from the Language section in UI
     */
    public const HIDDEN_LANGUAGES = ['qpn', 'qpn-x-places'];

    /**
     * Get label for a given type and code
     */
    public static function getLabel(string $type, ?string $code): string
    {
        if ($code === null) {
            return '';
        }

        return match ($type) {
            'pos' => self::POS[$code] ?? self::NAME_TYPES[$code] ?? $code,
            'language' => self::LANGUAGES[$code] ?? $code,
            'frequency' => self::FREQUENCY_RANGES[$code] ?? $code,
            'name_type' => self::NAME_TYPES[$code] ?? $code,
            default => $code,
        };
    }

    /**
     * Check if a POS code is actually a name type
     */
    public static function isNameType(string $pos): bool
    {
        return in_array($pos, self::NAME_TYPE_CODES, true);
    }

    /**
     * Check if a language should be hidden from UI
     */
    public static function isHiddenLanguage(string $lang): bool
    {
        return in_array($lang, self::HIDDEN_LANGUAGES, true);
    }

    /**
     * Get all POS labels (including name types) merged
     */
    public static function getAllPosLabels(): array
    {
        return array_merge(self::POS, self::NAME_TYPES);
    }

    /**
     * Get visible languages (excluding hidden ones)
     */
    public static function getVisibleLanguages(): array
    {
        return array_filter(
            self::LANGUAGES,
            fn($label, $code) => !in_array($code, self::HIDDEN_LANGUAGES, true),
            ARRAY_FILTER_USE_BOTH
        );
    }

    /**
     * Output labels as JavaScript constants
     * Call this in a <script> tag to make labels available to JS
     */
    public static function toJavaScript(): string
    {
        return 'window.DICTIONARY_LABELS = ' . json_encode([
            'pos' => self::getAllPosLabels(),
            'language' => self::LANGUAGES,
            'frequency' => self::FREQUENCY_RANGES,
            'nameTypeCodes' => self::NAME_TYPE_CODES,
            'hiddenLanguages' => self::HIDDEN_LANGUAGES,
        ], JSON_PRETTY_PRINT) . ';';
    }

    /**
     * Get labels as array for API responses
     */
    public static function toArray(): array
    {
        return [
            'pos' => self::getAllPosLabels(),
            'language' => self::LANGUAGES,
            'frequency' => self::FREQUENCY_RANGES,
            'nameTypeCodes' => self::NAME_TYPE_CODES,
        ];
    }
}
