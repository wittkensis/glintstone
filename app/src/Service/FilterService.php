<?php
/**
 * Filter Service
 * Handles filter statistics with caching
 */

declare(strict_types=1);

namespace Glintstone\Service;

use Glintstone\Repository\FilterStatsRepository;
use Glintstone\Cache\FileCache;
use Glintstone\Cache\CacheKeys;

final class FilterService
{
    public function __construct(
        private FilterStatsRepository $repo,
        private FileCache $cache
    ) {}

    /**
     * Get language statistics (cached)
     */
    public function getLanguageStats(): array
    {
        return $this->cache->remember(
            CacheKeys::FILTER_STATS_LANGUAGE,
            CacheKeys::TTL_FILTER_STATS,
            fn() => $this->repo->getStats('language')
        );
    }

    /**
     * Get period statistics (cached)
     */
    public function getPeriodStats(): array
    {
        return $this->cache->remember(
            CacheKeys::FILTER_STATS_PERIOD,
            CacheKeys::TTL_FILTER_STATS,
            fn() => $this->repo->getStats('period')
        );
    }

    /**
     * Get provenience statistics (cached)
     */
    public function getProvenienceStats(): array
    {
        return $this->cache->remember(
            CacheKeys::FILTER_STATS_PROVENIENCE,
            CacheKeys::TTL_FILTER_STATS,
            fn() => $this->repo->getStats('provenience')
        );
    }

    /**
     * Get genre statistics (cached)
     */
    public function getGenreStats(): array
    {
        return $this->cache->remember(
            CacheKeys::FILTER_STATS_GENRE,
            CacheKeys::TTL_FILTER_STATS,
            fn() => $this->repo->getStats('genre')
        );
    }

    /**
     * Get all statistics (cached)
     */
    public function getAllStats(): array
    {
        return [
            'language' => $this->getLanguageStats(),
            'period' => $this->getPeriodStats(),
            'provenience' => $this->getProvenienceStats(),
            'genre' => $this->getGenreStats(),
        ];
    }

    /**
     * Get filtered language statistics (not cached - too many permutations)
     */
    public function getFilteredLanguageStats(array $filters): array
    {
        return $this->repo->getFilteredStats('language', $filters);
    }

    /**
     * Get filtered period statistics
     */
    public function getFilteredPeriodStats(array $filters): array
    {
        return $this->repo->getFilteredStats('period', $filters);
    }

    /**
     * Get filtered provenience statistics
     */
    public function getFilteredProvenienceStats(array $filters): array
    {
        return $this->repo->getFilteredStats('provenience', $filters);
    }

    /**
     * Get filtered genre statistics
     */
    public function getFilteredGenreStats(array $filters): array
    {
        return $this->repo->getFilteredStats('genre', $filters);
    }

    /**
     * Get all filtered statistics
     */
    public function getAllFilteredStats(array $filters): array
    {
        return $this->repo->getAllFilteredStats($filters);
    }

    /**
     * Clear filter statistics cache
     */
    public function clearCache(): void
    {
        foreach (CacheKeys::allFilterStats() as $key) {
            $this->cache->delete($key);
        }
    }

    /**
     * Parse filter parameters from request
     */
    public static function parseFilters(array $params): array
    {
        return [
            'languages' => self::parseArrayParam($params, 'lang'),
            'periods' => self::parseArrayParam($params, 'period'),
            'sites' => self::parseArrayParam($params, 'site'),
            'genres' => self::parseArrayParam($params, 'genre'),
            'pipeline' => $params['pipeline'] ?? null,
            'search' => $params['search'] ?? null,
        ];
    }

    /**
     * Parse array parameter from request (supports both array and comma-separated)
     */
    private static function parseArrayParam(array $params, string $key): array
    {
        if (!isset($params[$key])) {
            return [];
        }

        $value = $params[$key];

        // Already an array
        if (is_array($value)) {
            return array_filter($value, fn($v) => $v !== '');
        }

        // Comma-separated string
        if (is_string($value) && !empty($value)) {
            return array_filter(array_map('trim', explode(',', $value)));
        }

        return [];
    }
}
