<?php
/**
 * Artifact Repository
 * Handles all tablet/artifact-related database queries
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class ArtifactRepository extends BaseRepository
{
    /**
     * Get artifact by P-number with pipeline status
     */
    public function findByPNumber(string $pNumber): ?array
    {
        $stmt = $this->prepare("
            SELECT a.*, ps.has_image, ps.has_ocr, ps.ocr_confidence, ps.has_atf,
                   ps.atf_source, ps.has_lemmas, ps.lemma_coverage, ps.has_translation,
                   ps.has_sign_annotations, ps.quality_score
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE a.p_number = :p_number
        ", ['p_number' => $pNumber]);

        return $this->fetchOne($stmt);
    }

    /**
     * Get composites for an artifact
     */
    public function getComposites(string $pNumber): array
    {
        $stmt = $this->prepare("
            SELECT c.* FROM composites c
            JOIN artifact_composites ac ON c.q_number = ac.q_number
            WHERE ac.p_number = :p_number
        ", ['p_number' => $pNumber]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get tablets in a composite
     */
    public function getTabletsInComposite(string $qNumber): array
    {
        $stmt = $this->prepare("
            SELECT
                a.p_number,
                a.designation,
                a.period,
                ps.has_image,
                ac.line_ref
            FROM artifact_composites ac
            JOIN artifacts a ON ac.p_number = a.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE ac.q_number = :q_number
            ORDER BY a.p_number ASC
        ", ['q_number' => $qNumber]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get composite metadata by Q-number
     */
    public function findComposite(string $qNumber): ?array
    {
        $stmt = $this->prepare(
            "SELECT * FROM composites WHERE q_number = :q_number",
            ['q_number' => $qNumber]
        );
        return $this->fetchOne($stmt);
    }

    /**
     * Search artifacts with filters
     *
     * @param array $filters Filter criteria
     * @param int $limit Results per page
     * @param int $offset Pagination offset
     */
    public function search(array $filters, int $limit = 24, int $offset = 0): array
    {
        $where = [];
        $params = [];
        $inscriptionJoin = '';

        // Language filter
        if (!empty($filters['languages'])) {
            $conditions = [];
            foreach ($filters['languages'] as $i => $lang) {
                $conditions[] = "a.language LIKE :lang{$i}";
                $params[":lang{$i}"] = '%' . $lang . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Period filter
        if (!empty($filters['periods'])) {
            $conditions = [];
            foreach ($filters['periods'] as $i => $period) {
                $conditions[] = "a.period = :period{$i}";
                $params[":period{$i}"] = $period;
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Site (provenience) filter
        if (!empty($filters['sites'])) {
            $conditions = [];
            foreach ($filters['sites'] as $i => $site) {
                $conditions[] = "a.provenience LIKE :site{$i}";
                $params[":site{$i}"] = '%' . $site . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Genre filter
        if (!empty($filters['genres'])) {
            $conditions = [];
            foreach ($filters['genres'] as $i => $genre) {
                $conditions[] = "a.genre LIKE :genre{$i}";
                $params[":genre{$i}"] = '%' . $genre . '%';
            }
            $where[] = '(' . implode(' OR ', $conditions) . ')';
        }

        // Pipeline filter
        if (!empty($filters['pipeline'])) {
            $pipelineCondition = $this->buildPipelineCondition($filters['pipeline']);
            if ($pipelineCondition) {
                $where[] = $pipelineCondition;
            }
        }

        // Search filter
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

        // Get total count
        $countSql = "
            SELECT COUNT(DISTINCT a.p_number) as total
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {$inscriptionJoin}
            {$whereClause}
        ";

        $countStmt = $this->db()->prepare($countSql);
        foreach ($params as $key => $val) {
            $countStmt->bindValue($key, $val);
        }
        $total = (int)$this->fetchScalar($countStmt);

        // Get paginated results
        $sql = "
            SELECT DISTINCT
                a.*,
                ps.has_image, ps.has_ocr, ps.has_atf, ps.has_lemmas,
                ps.has_translation, ps.has_sign_annotations, ps.quality_score
            FROM artifacts a
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            {$inscriptionJoin}
            {$whereClause}
            ORDER BY a.p_number ASC
            LIMIT :limit OFFSET :offset
        ";

        $stmt = $this->db()->prepare($sql);
        foreach ($params as $key => $val) {
            $stmt->bindValue($key, $val);
        }
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
        $stmt->bindValue(':offset', $offset, SQLITE3_INTEGER);

        return [
            'items' => $this->fetchAll($stmt),
            'total' => $total,
            'offset' => $offset,
            'limit' => $limit,
        ];
    }

    /**
     * Get total artifact count
     */
    public function getTotalCount(): int
    {
        $result = $this->db()->querySingle("SELECT COUNT(*) FROM artifacts");
        return (int)$result;
    }

    /**
     * Build pipeline status WHERE condition
     */
    private function buildPipelineCondition(string $pipeline): ?string
    {
        return match ($pipeline) {
            'complete' => "ps.has_image = 1 AND ps.has_atf = 1 AND ps.has_lemmas = 1 AND ps.has_translation = 1",
            'has_image' => "ps.has_image = 1",
            'has_translation' => "ps.has_translation = 1",
            'has_atf' => "ps.has_atf = 1",
            'has_lemmas' => "ps.has_lemmas = 1",
            'any_digitization' => "(ps.has_atf = 1 OR ps.has_sign_annotations = 1)",
            'human_transcription' => "ps.has_atf = 1",
            'machine_ocr' => "ps.has_sign_annotations = 1",
            'no_digitization' => "(ps.has_atf IS NULL OR ps.has_atf = 0) AND (ps.has_sign_annotations IS NULL OR ps.has_sign_annotations = 0)",
            'needs_signs' => "(ps.has_image = 1) AND (ps.has_atf IS NULL OR ps.has_atf = 0)",
            'needs_atf' => "(ps.has_sign_annotations = 1 OR ps.has_ocr = 1) AND (ps.has_atf IS NULL OR ps.has_atf = 0)",
            'needs_translation' => "(ps.has_atf = 1) AND (ps.has_translation IS NULL OR ps.has_translation = 0)",
            default => null,
        };
    }
}
