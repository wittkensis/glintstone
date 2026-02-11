<?php
/**
 * Filter Stats Repository
 * Handles filter statistics for the tablet browser sidebar
 * Consolidates the 4 similar getFiltered*Stats functions
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class FilterStatsRepository extends BaseRepository
{
    /**
     * Filter type configurations
     */
    private const FILTER_CONFIG = [
        'language' => [
            'table' => 'language_stats',
            'groupColumn' => 'root_language',
            'valueColumn' => 'language',
            'artifactColumn' => 'language',
            'countColumn' => 'tablet_count',
        ],
        'period' => [
            'table' => 'period_stats',
            'groupColumn' => 'period_group',
            'valueColumn' => 'period',
            'artifactColumn' => 'period',
            'countColumn' => 'tablet_count',
            'sortColumn' => 'sort_order',
        ],
        'provenience' => [
            'table' => 'provenience_stats',
            'groupColumn' => 'region',
            'valueColumn' => 'provenience',
            'artifactColumn' => 'provenience',
            'countColumn' => 'tablet_count',
        ],
        'genre' => [
            'table' => 'genre_stats',
            'groupColumn' => 'category',
            'valueColumn' => 'genre',
            'artifactColumn' => 'genre',
            'countColumn' => 'tablet_count',
        ],
    ];

    /**
     * Get static stats (no filters applied)
     */
    public function getStats(string $filterType): array
    {
        $config = self::FILTER_CONFIG[$filterType] ?? null;
        if (!$config) {
            throw new \InvalidArgumentException("Unknown filter type: {$filterType}");
        }

        $orderBy = isset($config['sortColumn'])
            ? "{$config['sortColumn']} ASC, {$config['countColumn']} DESC"
            : "{$config['countColumn']} DESC";

        $sql = "
            SELECT {$config['valueColumn']}, {$config['groupColumn']}, {$config['countColumn']}
            FROM {$config['table']}
            ORDER BY {$orderBy}
        ";

        $rows = $this->query($sql);
        return $this->groupResults($rows, $config, isset($config['sortColumn']));
    }

    /**
     * Get all static stats at once
     */
    public function getAllStats(): array
    {
        return [
            'language' => $this->getStats('language'),
            'period' => $this->getStats('period'),
            'provenience' => $this->getStats('provenience'),
            'genre' => $this->getStats('genre'),
        ];
    }

    /**
     * Get filter-aware stats (counts updated based on active filters)
     * Excludes the filter type being counted from the WHERE clause
     */
    public function getFilteredStats(string $filterType, array $filters): array
    {
        $config = self::FILTER_CONFIG[$filterType] ?? null;
        if (!$config) {
            throw new \InvalidArgumentException("Unknown filter type: {$filterType}");
        }

        // Build WHERE clause (excluding the current filter type)
        [$whereClause, $params, $inscriptionJoin] = $this->buildWhereClause($filters, $filterType);

        // Query counts from artifacts table
        $sql = "
            SELECT a.{$config['artifactColumn']} as value, COUNT(DISTINCT a.p_number) as count
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {$inscriptionJoin}
            {$whereClause}
            GROUP BY a.{$config['artifactColumn']}
            HAVING count > 0
            ORDER BY count DESC
        ";

        $stmt = $this->db()->prepare($sql);
        foreach ($params as $key => $val) {
            $stmt->bindValue($key, $val);
        }
        $result = $stmt->execute();

        // Get counts keyed by value
        $counts = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            if (!empty($row['value'])) {
                $counts[$row['value']] = (int)$row['count'];
            }
        }

        // Get metadata for grouping
        $metaSql = "SELECT {$config['valueColumn']}, {$config['groupColumn']} FROM {$config['table']}";
        if (isset($config['sortColumn'])) {
            $metaSql .= " ORDER BY {$config['sortColumn']} ASC";
        }
        $metaRows = $this->query($metaSql);

        $metadata = [];
        $groupOrder = [];
        foreach ($metaRows as $i => $row) {
            $metadata[$row[$config['valueColumn']]] = $row[$config['groupColumn']];
            if (!isset($groupOrder[$row[$config['groupColumn']]])) {
                $groupOrder[$row[$config['groupColumn']]] = $i;
            }
        }

        // Group results
        $grouped = [];
        $rootTotals = [];

        foreach ($counts as $value => $count) {
            $group = $metadata[$value] ?? 'Other';

            if (!isset($grouped[$group])) {
                $grouped[$group] = [];
                $rootTotals[$group] = 0;
            }

            $grouped[$group][] = [
                'value' => $value,
                'count' => $count,
            ];
            $rootTotals[$group] += $count;
        }

        // Sort groups
        if (isset($config['sortColumn'])) {
            // Sort by predefined order (for periods)
            uksort($rootTotals, fn($a, $b) => ($groupOrder[$a] ?? 999) - ($groupOrder[$b] ?? 999));
        } else {
            // Sort by total count
            arsort($rootTotals);
        }

        // Sort items within each group
        foreach ($grouped as &$items) {
            usort($items, fn($a, $b) => $b['count'] - $a['count']);
        }
        unset($items);

        // Build final structure
        $stats = [];
        foreach ($rootTotals as $group => $total) {
            $stats[] = [
                'group' => $group,
                'total' => $total,
                'items' => $grouped[$group],
            ];
        }

        return $stats;
    }

    /**
     * Get all filtered stats at once
     */
    public function getAllFilteredStats(array $filters): array
    {
        return [
            'language' => $this->getFilteredStats('language', $filters),
            'period' => $this->getFilteredStats('period', $filters),
            'provenience' => $this->getFilteredStats('provenience', $filters),
            'genre' => $this->getFilteredStats('genre', $filters),
        ];
    }

    /**
     * Build WHERE clause from filters, excluding a specific filter type
     */
    private function buildWhereClause(array $filters, string $excludeType): array
    {
        $where = [];
        $params = [];
        $inscriptionJoin = '';

        // Language filter
        if ($excludeType !== 'language' && !empty($filters['languages'])) {
            $conditions = [];
            foreach ($filters['languages'] as $i => $lang) {
                $conditions[] = "a.language LIKE :lang{$i}";
                $params[":lang{$i}"] = '%' . $lang . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Period filter
        if ($excludeType !== 'period' && !empty($filters['periods'])) {
            $conditions = [];
            foreach ($filters['periods'] as $i => $period) {
                $conditions[] = "a.period = :period{$i}";
                $params[":period{$i}"] = $period;
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Site filter
        if ($excludeType !== 'provenience' && !empty($filters['sites'])) {
            $conditions = [];
            foreach ($filters['sites'] as $i => $site) {
                $conditions[] = "a.provenience LIKE :site{$i}";
                $params[":site{$i}"] = '%' . $site . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Genre filter
        if ($excludeType !== 'genre' && !empty($filters['genres'])) {
            $conditions = [];
            foreach ($filters['genres'] as $i => $genre) {
                $conditions[] = "a.genre LIKE :genre{$i}";
                $params[":genre{$i}"] = '%' . $genre . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Pipeline filter (never excluded)
        if (!empty($filters['pipeline'])) {
            $pipelineCondition = $this->buildPipelineCondition($filters['pipeline']);
            if ($pipelineCondition) {
                $where[] = $pipelineCondition;
            }
        }

        // Search filter (never excluded)
        if (!empty($filters['search'])) {
            $inscriptionJoin = "LEFT JOIN inscriptions i ON a.p_number = i.p_number AND i.is_latest = 1";
            $searchTerms = array_map('trim', explode('||', $filters['search']));

            if (count($searchTerms) > 1) {
                $searchConditions = [];
                foreach ($searchTerms as $i => $term) {
                    if (!empty($term)) {
                        $searchConditions[] = "(a.p_number LIKE :search{$i} OR a.designation LIKE :search{$i} OR i.transliteration_clean LIKE :search{$i})";
                        $params[":search{$i}"] = '%' . $term . '%';
                    }
                }
                if (!empty($searchConditions)) {
                    $where[] = "(" . implode(' OR ', $searchConditions) . ")";
                }
            } else {
                $where[] = "(a.p_number LIKE :search OR a.designation LIKE :search OR i.transliteration_clean LIKE :search)";
                $params[':search'] = '%' . $filters['search'] . '%';
            }
        }

        $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

        return [$whereClause, $params, $inscriptionJoin];
    }

    /**
     * Build pipeline status condition
     */
    private function buildPipelineCondition(string $pipeline): ?string
    {
        return match ($pipeline) {
            'complete' => "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1",
            'has_image' => "ps.has_image = 1",
            'has_translation' => "ps.has_translation = 1",
            'any_digitization' => "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)",
            'human_transcription' => "ps.has_atf = 1",
            'machine_ocr' => "ps.has_sign_annotations = 1",
            'no_digitization' => "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)",
            default => null,
        };
    }

    /**
     * Group query results by a column
     */
    private function groupResults(array $rows, array $config, bool $preserveOrder = false): array
    {
        $grouped = [];
        $rootTotals = [];
        $groupOrder = [];

        foreach ($rows as $i => $row) {
            $group = $row[$config['groupColumn']];
            $value = $row[$config['valueColumn']];
            $count = (int)$row[$config['countColumn']];

            if (!isset($grouped[$group])) {
                $grouped[$group] = [];
                $rootTotals[$group] = 0;
                $groupOrder[$group] = $i;
            }

            $grouped[$group][] = [
                'value' => $value,
                'count' => $count,
            ];
            $rootTotals[$group] += $count;
        }

        // Sort groups
        if ($preserveOrder) {
            uksort($rootTotals, fn($a, $b) => $groupOrder[$a] - $groupOrder[$b]);
        } else {
            arsort($rootTotals);
        }

        $stats = [];
        foreach ($rootTotals as $group => $total) {
            $stats[] = [
                'group' => $group,
                'total' => $total,
                'items' => $grouped[$group],
            ];
        }

        return $stats;
    }
}
