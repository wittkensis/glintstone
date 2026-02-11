<?php
/**
 * Tablet Service
 * Orchestrates tablet-related data and business logic
 */

declare(strict_types=1);

namespace Glintstone\Service;

use Glintstone\Repository\ArtifactRepository;
use Glintstone\Repository\InscriptionRepository;
use Glintstone\Cache\FileCache;
use Glintstone\Cache\CacheKeys;

final class TabletService
{
    public function __construct(
        private ArtifactRepository $artifacts,
        private InscriptionRepository $inscriptions,
        private FileCache $cache
    ) {}

    /**
     * Get complete tablet detail data
     * Single entry point for tablet detail page
     */
    public function getTabletDetail(string $pNumber): ?array
    {
        $tablet = $this->artifacts->findByPNumber($pNumber);
        if (!$tablet) {
            return null;
        }

        return [
            'tablet' => $tablet,
            'inscription' => $this->inscriptions->getLatest($pNumber),
            'translations' => $this->inscriptions->getTranslations($pNumber),
            'composites' => $this->artifacts->getComposites($pNumber),
            'pipeline' => $this->calculatePipelineStatus($tablet),
            'museum' => $this->resolveMuseumDisplay($tablet),
            'excavation' => $this->resolveExcavationDisplay($tablet),
        ];
    }

    /**
     * Get filtered tablets with pagination
     */
    public function getFilteredTablets(array $filters, int $limit = 24, int $offset = 0): array
    {
        return $this->artifacts->search($filters, $limit, $offset);
    }

    /**
     * Get lemmas for a tablet, indexed by line and word
     */
    public function getLemmas(string $pNumber): array
    {
        return $this->inscriptions->getLemmasIndexed($pNumber);
    }

    /**
     * Get sign annotations for a tablet
     */
    public function getAnnotations(string $pNumber, ?string $surface = null): array
    {
        return $this->inscriptions->getSignAnnotations($pNumber, $surface);
    }

    /**
     * Get translation lines for line-by-line display
     */
    public function getTranslationLines(string $pNumber): array
    {
        return $this->inscriptions->getTranslationLines($pNumber);
    }

    /**
     * Calculate pipeline status from tablet data
     */
    private function calculatePipelineStatus(array $tablet): array
    {
        return [
            'image' => [
                'status' => !empty($tablet['has_image']) ? 'complete' : 'missing',
                'available' => !empty($tablet['has_image']),
            ],
            'signs' => [
                'status' => $this->getSignsStatus($tablet),
                'available' => !empty($tablet['has_sign_annotations']) || !empty($tablet['has_ocr']),
                'confidence' => $tablet['ocr_confidence'] ?? null,
            ],
            'transliteration' => [
                'status' => !empty($tablet['has_atf']) ? 'complete' : 'missing',
                'available' => !empty($tablet['has_atf']),
                'source' => $tablet['atf_source'] ?? null,
            ],
            'lemmas' => [
                'status' => !empty($tablet['has_lemmas']) ? 'complete' : 'missing',
                'available' => !empty($tablet['has_lemmas']),
                'coverage' => $tablet['lemma_coverage'] ?? null,
            ],
            'translation' => [
                'status' => !empty($tablet['has_translation']) ? 'complete' : 'missing',
                'available' => !empty($tablet['has_translation']),
            ],
            'quality_score' => $tablet['quality_score'] ?? 0,
        ];
    }

    /**
     * Determine signs stage status
     */
    private function getSignsStatus(array $tablet): string
    {
        if (!empty($tablet['has_sign_annotations'])) {
            return 'complete';
        }
        if (!empty($tablet['has_ocr'])) {
            return 'partial';
        }
        return 'missing';
    }

    /**
     * Parse and resolve museum display information
     */
    private function resolveMuseumDisplay(array $tablet): ?array
    {
        if (empty($tablet['museum_no'])) {
            return null;
        }

        $museumNo = $tablet['museum_no'];

        // Parse museum code
        if (preg_match('/^([A-Za-z]+)\s+(.+)$/', trim($museumNo), $matches)) {
            return [
                'code' => $matches[1],
                'number' => $matches[2],
                'full' => $museumNo,
            ];
        }

        return [
            'code' => null,
            'number' => $museumNo,
            'full' => $museumNo,
        ];
    }

    /**
     * Parse and resolve excavation display information
     */
    private function resolveExcavationDisplay(array $tablet): ?array
    {
        if (empty($tablet['excavation_no'])) {
            return null;
        }

        $excavationNo = $tablet['excavation_no'];

        // Parse excavation code
        if (preg_match('/^([A-Za-z][A-Za-z0-9\-\.]*)\s+(.+)$/', trim($excavationNo), $matches)) {
            return [
                'code' => $matches[1],
                'number' => $matches[2],
                'full' => $excavationNo,
            ];
        }

        return [
            'code' => null,
            'number' => $excavationNo,
            'full' => $excavationNo,
        ];
    }
}
