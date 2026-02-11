<?php
/**
 * Dictionary Service
 * Handles dictionary/glossary operations
 */

declare(strict_types=1);

namespace Glintstone\Service;

use Glintstone\Repository\GlossaryRepository;
use Glintstone\Cache\FileCache;
use Glintstone\Cache\CacheKeys;

final class DictionaryService
{
    public function __construct(
        private GlossaryRepository $repo,
        private FileCache $cache
    ) {}

    /**
     * Search dictionary entries
     */
    public function search(string $term, ?string $language = null, int $limit = 20): array
    {
        return $this->repo->search($term, $language, $limit);
    }

    /**
     * Get word by headword
     */
    public function findByHeadword(string $headword, ?string $language = null): ?array
    {
        return $this->repo->findByHeadword($headword, $language);
    }

    /**
     * Get word detail with all related data
     */
    public function getWordDetail(string $entryId): ?array
    {
        return $this->repo->getWordDetail($entryId);
    }

    /**
     * Browse dictionary with filters
     */
    public function browse(array $filters, int $limit = 50, int $offset = 0): array
    {
        return $this->repo->browse($filters, $limit, $offset);
    }

    /**
     * Get grouping counts (cached)
     */
    public function getCounts(): array
    {
        return $this->cache->remember(
            CacheKeys::DICTIONARY_COUNTS,
            CacheKeys::TTL_DICTIONARY_COUNTS,
            fn() => $this->repo->getCounts()
        );
    }

    /**
     * Quick glossary lookup for word glossing
     * Returns guide_word for a headword, or null if not found
     */
    public function getGloss(string $headword): ?string
    {
        $entry = $this->repo->findByHeadword($headword);
        return $entry['guide_word'] ?? null;
    }

    /**
     * Batch lookup glosses for multiple words
     */
    public function getGlosses(array $headwords): array
    {
        $glosses = [];
        foreach ($headwords as $headword) {
            $glosses[$headword] = $this->getGloss($headword);
        }
        return $glosses;
    }

    /**
     * Parse browse filters from request
     */
    public static function parseFilters(array $params): array
    {
        return [
            'search' => $params['search'] ?? null,
            'language' => $params['language'] ?? null,
            'pos' => $params['pos'] ?? null,
            'frequency' => $params['frequency'] ?? null,
        ];
    }
}
