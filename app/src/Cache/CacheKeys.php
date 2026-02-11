<?php
/**
 * Cache Key Definitions
 * Centralized definitions for all cache keys and TTLs
 */

declare(strict_types=1);

namespace Glintstone\Cache;

final class CacheKeys
{
    // Filter statistics
    public const FILTER_STATS_LANGUAGE = 'filter_stats:language';
    public const FILTER_STATS_PERIOD = 'filter_stats:period';
    public const FILTER_STATS_PROVENIENCE = 'filter_stats:provenience';
    public const FILTER_STATS_GENRE = 'filter_stats:genre';

    // Composite metadata
    public const COMPOSITE_METADATA = 'composites:%s:metadata';

    // Homepage KPI
    public const KPI_METRICS = 'homepage:kpi_metrics';

    // Dictionary
    public const DICTIONARY_COUNTS = 'dictionary:counts';

    // TTLs in seconds
    public const TTL_FILTER_STATS = 3600;       // 1 hour
    public const TTL_COMPOSITE = 86400;          // 24 hours
    public const TTL_KPI = 1800;                 // 30 minutes
    public const TTL_DICTIONARY_COUNTS = 3600;   // 1 hour

    /**
     * Get composite metadata cache key for a specific Q-number
     */
    public static function compositeMetadata(string $qNumber): string
    {
        return sprintf(self::COMPOSITE_METADATA, $qNumber);
    }

    /**
     * Get all filter stats cache keys
     */
    public static function allFilterStats(): array
    {
        return [
            self::FILTER_STATS_LANGUAGE,
            self::FILTER_STATS_PERIOD,
            self::FILTER_STATS_PROVENIENCE,
            self::FILTER_STATS_GENRE,
        ];
    }
}
