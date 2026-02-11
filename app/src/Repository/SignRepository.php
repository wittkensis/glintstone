<?php
/**
 * Sign Repository
 * Handles cuneiform sign-related queries
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class SignRepository extends BaseRepository
{
    /**
     * Find sign by UTF-8 character, sign ID, or value
     */
    public function findByQuery(string $query): ?array
    {
        // Try exact UTF-8 match
        $stmt = $this->prepare(
            "SELECT * FROM signs WHERE utf8 = :q",
            ['q' => $query]
        );
        $sign = $this->fetchOne($stmt);
        if ($sign) return $sign;

        // Try sign ID
        $stmt = $this->prepare(
            "SELECT * FROM signs WHERE sign_id = :q",
            ['q' => $query]
        );
        $sign = $this->fetchOne($stmt);
        if ($sign) return $sign;

        // Try by value
        $stmt = $this->prepare("
            SELECT s.* FROM signs s
            JOIN sign_values sv ON s.sign_id = sv.sign_id
            WHERE sv.value = :q
            LIMIT 1
        ", ['q' => strtolower($query)]);

        return $this->fetchOne($stmt);
    }

    /**
     * Get sign by ID
     */
    public function findById(string $signId): ?array
    {
        $stmt = $this->prepare(
            "SELECT * FROM signs WHERE sign_id = :sign_id",
            ['sign_id' => $signId]
        );
        return $this->fetchOne($stmt);
    }

    /**
     * Get all values for a sign
     */
    public function getValues(string $signId): array
    {
        $stmt = $this->prepare("
            SELECT value, value_type, frequency
            FROM sign_values
            WHERE sign_id = :sign_id
            ORDER BY
                CASE value_type
                    WHEN 'logographic' THEN 1
                    WHEN 'syllabic' THEN 2
                    WHEN 'determinative' THEN 3
                    ELSE 4
                END,
                frequency DESC,
                value ASC
        ", ['sign_id' => $signId]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get simple value list for a sign (just value strings)
     */
    public function getValueNames(string $signId): array
    {
        $stmt = $this->prepare(
            "SELECT value FROM sign_values WHERE sign_id = :sign_id",
            ['sign_id' => $signId]
        );
        return array_column($this->fetchAll($stmt), 'value');
    }

    /**
     * Get words that use a sign
     */
    public function getWordUsage(string $signId, int $limit = 100): array
    {
        $stmt = $this->prepare("
            SELECT
                swu.sign_value,
                swu.value_type,
                swu.usage_count,
                ge.entry_id,
                ge.headword,
                ge.guide_word,
                ge.pos,
                ge.language,
                ge.icount
            FROM sign_word_usage swu
            JOIN glossary_entries ge ON swu.entry_id = ge.entry_id
            WHERE swu.sign_id = :sign_id
            ORDER BY swu.usage_count DESC, ge.icount DESC
            LIMIT :limit
        ", ['sign_id' => $signId]);
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

        return $this->fetchAll($stmt);
    }

    /**
     * Get usage statistics for a sign
     */
    public function getStats(string $signId): array
    {
        $countStmt = $this->prepare("
            SELECT COUNT(DISTINCT entry_id) as total_words
            FROM sign_word_usage WHERE sign_id = :sign_id
        ", ['sign_id' => $signId]);
        $totalWords = (int)$this->fetchScalar($countStmt);

        $usageStmt = $this->prepare("
            SELECT COALESCE(SUM(usage_count), 0) as total
            FROM sign_word_usage WHERE sign_id = :sign_id
        ", ['sign_id' => $signId]);
        $totalOccurrences = (int)$this->fetchScalar($usageStmt);

        return [
            'total_unique_words' => $totalWords,
            'total_corpus_occurrences' => $totalOccurrences,
        ];
    }

    /**
     * Browse signs with filters and pagination
     */
    public function browse(array $filters, int $limit = 50, int $offset = 0): array
    {
        $where = [];
        $params = [];

        if (!empty($filters['search'])) {
            $where[] = "(s.sign_id LIKE :search OR sv.value LIKE :search)";
            $params['search'] = '%' . $filters['search'] . '%';
        }

        if (!empty($filters['sign_type'])) {
            $where[] = "s.sign_type = :sign_type";
            $params['sign_type'] = $filters['sign_type'];
        }

        $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';

        // Count
        $countSql = "
            SELECT COUNT(DISTINCT s.sign_id) as total
            FROM signs s
            LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
            {$whereClause}
        ";
        $countStmt = $this->db()->prepare($countSql);
        foreach ($params as $key => $val) {
            $countStmt->bindValue(":{$key}", $val);
        }
        $total = (int)$this->fetchScalar($countStmt);

        // Sort
        $orderBy = match ($filters['sort'] ?? 'sign_id') {
            'frequency' => 'total_occurrences DESC',
            'value_count' => 'value_count DESC',
            default => 's.sign_id ASC',
        };

        // Query
        $sql = "
            SELECT
                s.sign_id, s.utf8, s.sign_type, s.most_common_value,
                COUNT(DISTINCT sv.value) as value_count,
                COUNT(DISTINCT swu.entry_id) as word_count,
                COALESCE(SUM(swu.usage_count), 0) as total_occurrences
            FROM signs s
            LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
            LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
            {$whereClause}
            GROUP BY s.sign_id
        ";

        $minFreq = (int)($filters['min_frequency'] ?? 0);
        if ($minFreq > 0) {
            $sql .= " HAVING total_occurrences >= :min_frequency";
        }

        $sql .= " ORDER BY {$orderBy} LIMIT :limit OFFSET :offset";

        $stmt = $this->db()->prepare($sql);
        foreach ($params as $key => $val) {
            $stmt->bindValue(":{$key}", $val);
        }
        if ($minFreq > 0) {
            $stmt->bindValue(':min_frequency', $minFreq, SQLITE3_INTEGER);
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
}
