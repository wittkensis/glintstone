<?php
/**
 * Glossary Repository
 * Handles dictionary/glossary-related queries
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class GlossaryRepository extends BaseRepository
{
    /**
     * Search glossary entries
     */
    public function search(string $term, ?string $language = null, int $limit = 20): array
    {
        $sql = "SELECT * FROM glossary_entries WHERE headword LIKE :term";
        $params = ['term' => '%' . $term . '%'];

        if ($language !== null) {
            $sql .= " AND language = :lang";
            $params['lang'] = $language;
        }

        $sql .= " ORDER BY icount DESC LIMIT :limit";
        $params['limit'] = $limit;

        $stmt = $this->db()->prepare($sql);
        $stmt->bindValue(':term', $params['term'], SQLITE3_TEXT);
        if ($language !== null) {
            $stmt->bindValue(':lang', $language, SQLITE3_TEXT);
        }
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

        return $this->fetchAll($stmt);
    }

    /**
     * Get entry by headword (exact match)
     */
    public function findByHeadword(string $headword, ?string $language = null): ?array
    {
        $sql = "SELECT * FROM glossary_entries WHERE headword = :headword";
        $params = ['headword' => $headword];

        if ($language !== null) {
            $sql .= " AND language = :lang";
            $params['lang'] = $language;
        }

        $sql .= " ORDER BY icount DESC LIMIT 1";

        $stmt = $this->prepare($sql, $params);
        return $this->fetchOne($stmt);
    }

    /**
     * Get entry by ID
     */
    public function findById(string $entryId): ?array
    {
        $stmt = $this->prepare("
            SELECT * FROM glossary_entries WHERE entry_id = :entry_id
        ", ['entry_id' => $entryId]);

        return $this->fetchOne($stmt);
    }

    /**
     * Browse entries with filters
     */
    public function browse(array $filters, int $limit = 50, int $offset = 0): array
    {
        $where = [];
        $params = [];

        // Search filter
        if (!empty($filters['search'])) {
            $where[] = "(headword LIKE :search OR citation_form LIKE :search)";
            $params['search'] = '%' . $filters['search'] . '%';
        }

        // Language filter
        if (!empty($filters['language'])) {
            $where[] = "language = :language";
            $params['language'] = $filters['language'];
        }

        // POS filter
        if (!empty($filters['pos'])) {
            $where[] = "pos = :pos";
            $params['pos'] = $filters['pos'];
        }

        // Frequency filter
        if (!empty($filters['frequency'])) {
            $freqCondition = $this->buildFrequencyCondition($filters['frequency']);
            if ($freqCondition) {
                $where[] = $freqCondition;
            }
        }

        $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

        // Get total count
        $countSql = "SELECT COUNT(*) FROM glossary_entries {$whereClause}";
        $countStmt = $this->db()->prepare($countSql);
        foreach ($params as $key => $val) {
            $countStmt->bindValue(":{$key}", $val);
        }
        $total = (int)$this->fetchScalar($countStmt);

        // Get paginated results
        $sql = "
            SELECT * FROM glossary_entries
            {$whereClause}
            ORDER BY icount DESC, headword ASC
            LIMIT :limit OFFSET :offset
        ";

        $stmt = $this->db()->prepare($sql);
        foreach ($params as $key => $val) {
            $stmt->bindValue(":{$key}", $val);
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
     * Get word detail with related data
     */
    public function getWordDetail(string $entryId): ?array
    {
        $entry = $this->findById($entryId);
        if (!$entry) {
            return null;
        }

        return [
            'entry' => $entry,
            'variants' => $this->getVariants($entryId),
            'signs' => $this->getSigns($entryId),
            'senses' => $this->getSenses($entryId),
            'attestations' => $this->getAttestations($entryId, 50),
            'related' => $this->getRelatedWords($entryId),
        ];
    }

    /**
     * Get word variants
     */
    public function getVariants(string $entryId): array
    {
        $stmt = $this->prepare("
            SELECT form, icount FROM glossary_forms
            WHERE entry_id = :entry_id
            ORDER BY icount DESC
        ", ['entry_id' => $entryId]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get signs associated with word
     */
    public function getSigns(string $entryId): array
    {
        $stmt = $this->prepare("
            SELECT sign_id, usage_count FROM glossary_signs
            WHERE entry_id = :entry_id
            ORDER BY usage_count DESC
        ", ['entry_id' => $entryId]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get word senses/meanings
     */
    public function getSenses(string $entryId): array
    {
        $stmt = $this->prepare("
            SELECT sense, examples FROM glossary_senses
            WHERE entry_id = :entry_id
            ORDER BY sort_order ASC
        ", ['entry_id' => $entryId]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get attestations (tablet occurrences)
     */
    public function getAttestations(string $entryId, int $limit = 50): array
    {
        $stmt = $this->prepare("
            SELECT
                a.p_number,
                a.period,
                a.provenience,
                a.genre,
                ga.line_ref,
                ga.context
            FROM glossary_attestations ga
            JOIN artifacts a ON ga.p_number = a.p_number
            WHERE ga.entry_id = :entry_id
            ORDER BY a.p_number ASC
            LIMIT :limit
        ", ['entry_id' => $entryId]);
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

        return $this->fetchAll($stmt);
    }

    /**
     * Get related words
     */
    public function getRelatedWords(string $entryId): array
    {
        $stmt = $this->prepare("
            SELECT
                gr.related_entry_id,
                gr.relationship_type,
                ge.headword,
                ge.guide_word,
                ge.language,
                ge.pos
            FROM glossary_relations gr
            JOIN glossary_entries ge ON gr.related_entry_id = ge.entry_id
            WHERE gr.entry_id = :entry_id
        ", ['entry_id' => $entryId]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get counts for grouping panels
     */
    public function getCounts(): array
    {
        // POS counts
        $posResult = $this->query("
            SELECT pos, COUNT(*) as count
            FROM glossary_entries
            GROUP BY pos
            ORDER BY count DESC
        ");

        // Language counts
        $langResult = $this->query("
            SELECT language, COUNT(*) as count
            FROM glossary_entries
            GROUP BY language
            ORDER BY count DESC
        ");

        // Frequency distribution
        $freqResult = $this->query("
            SELECT
                CASE
                    WHEN icount = 1 THEN '1'
                    WHEN icount BETWEEN 2 AND 10 THEN '2-10'
                    WHEN icount BETWEEN 11 AND 100 THEN '11-100'
                    WHEN icount BETWEEN 101 AND 500 THEN '101-500'
                    ELSE '500+'
                END as frequency_range,
                COUNT(*) as count
            FROM glossary_entries
            GROUP BY frequency_range
            ORDER BY MIN(icount) ASC
        ");

        return [
            'pos' => $posResult,
            'language' => $langResult,
            'frequency' => $freqResult,
        ];
    }

    /**
     * Build frequency filter condition
     */
    private function buildFrequencyCondition(string $range): ?string
    {
        return match ($range) {
            '1' => "icount = 1",
            '2-10' => "icount BETWEEN 2 AND 10",
            '11-100' => "icount BETWEEN 11 AND 100",
            '101-500' => "icount BETWEEN 101 AND 500",
            '500+' => "icount > 500",
            default => null,
        };
    }
}
