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
     * Get signs that share reading values with the given sign (homophones)
     */
    public function getHomophones(string $signId, int $limit = 20): array
    {
        $stmt = $this->prepare("
            SELECT
                s2.sign_id,
                s2.utf8,
                s2.sign_type,
                s2.most_common_value,
                sv1.value as shared_value,
                (SELECT COUNT(*) FROM sign_values WHERE sign_id = s2.sign_id) as value_count,
                (SELECT COUNT(DISTINCT entry_id) FROM sign_word_usage WHERE sign_id = s2.sign_id) as word_count,
                (SELECT COALESCE(SUM(usage_count), 0) FROM sign_word_usage WHERE sign_id = s2.sign_id) as total_occurrences
            FROM sign_values sv1
            JOIN sign_values sv2 ON sv1.value = sv2.value
            JOIN signs s2 ON sv2.sign_id = s2.sign_id
            WHERE sv1.sign_id = :sign_id
              AND sv2.sign_id != :sign_id
            GROUP BY s2.sign_id, sv1.value
            ORDER BY s2.sign_id ASC
            LIMIT :limit
        ", ['sign_id' => $signId]);
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

        return $this->fetchAll($stmt);
    }

    /**
     * Get group counts for the signs groupings panel
     */
    public function getGroupCounts(): array
    {
        // Use sign_usage_summary view for efficiency
        $rows = $this->query("
            SELECT
                s.sign_id,
                s.sign_type,
                s.utf8,
                COALESCE(sus.value_count, 0) as value_count,
                COALESCE(sus.word_count, 0) as word_count,
                COALESCE(sus.total_occurrences, 0) as total_occurrences
            FROM signs s
            LEFT JOIN sign_usage_summary sus ON s.sign_id = sus.sign_id
        ");

        $counts = [
            'total' => count($rows),
            'polyphony' => ['1' => 0, '2-5' => 0, '6-10' => 0, '11-20' => 0, '20+' => 0, '0' => 0],
            'usage' => ['0' => 0, '1-10' => 0, '11-100' => 0, '101-1000' => 0, '1000+' => 0],
            'word_count' => ['0' => 0, '1-5' => 0, '6-20' => 0, '20+' => 0],
            'sign_type' => ['simple' => 0, 'compound' => 0, 'variant' => 0],
            'has_glyph' => ['yes' => 0, 'no' => 0],
        ];

        foreach ($rows as $row) {
            $vc = (int)$row['value_count'];
            $wc = (int)$row['word_count'];
            $occ = (int)$row['total_occurrences'];

            // Polyphony (value count)
            if ($vc === 0) $counts['polyphony']['0']++;
            elseif ($vc === 1) $counts['polyphony']['1']++;
            elseif ($vc <= 5) $counts['polyphony']['2-5']++;
            elseif ($vc <= 10) $counts['polyphony']['6-10']++;
            elseif ($vc <= 20) $counts['polyphony']['11-20']++;
            else $counts['polyphony']['20+']++;

            // Usage (occurrences)
            if ($occ === 0) $counts['usage']['0']++;
            elseif ($occ <= 10) $counts['usage']['1-10']++;
            elseif ($occ <= 100) $counts['usage']['11-100']++;
            elseif ($occ <= 1000) $counts['usage']['101-1000']++;
            else $counts['usage']['1000+']++;

            // Word count
            if ($wc === 0) $counts['word_count']['0']++;
            elseif ($wc <= 5) $counts['word_count']['1-5']++;
            elseif ($wc <= 20) $counts['word_count']['6-20']++;
            else $counts['word_count']['20+']++;

            // Sign type
            $type = $row['sign_type'] ?? 'simple';
            if (isset($counts['sign_type'][$type])) {
                $counts['sign_type'][$type]++;
            }

            // Has glyph
            $counts['has_glyph'][!empty($row['utf8']) ? 'yes' : 'no']++;
        }

        return $counts;
    }

    /**
     * Browse signs with filters, grouping, and pagination
     */
    public function browse(array $filters, int $limit = 50, int $offset = 0): array
    {
        $where = [];
        $having = [];
        $params = [];

        if (!empty($filters['search'])) {
            $where[] = "(s.sign_id LIKE :search OR sv.value LIKE :search)";
            $params['search'] = '%' . $filters['search'] . '%';
        }

        if (!empty($filters['sign_type'])) {
            $where[] = "s.sign_type = :sign_type";
            $params['sign_type'] = $filters['sign_type'];
        }

        if (!empty($filters['has_glyph'])) {
            $where[] = ($filters['has_glyph'] === 'yes')
                ? "s.utf8 IS NOT NULL AND s.utf8 != ''"
                : "(s.utf8 IS NULL OR s.utf8 = '')";
        }

        // Group-based filters (applied as HAVING on aggregated values)
        if (!empty($filters['group_type']) && isset($filters['group_value'])) {
            $gv = $filters['group_value'];
            switch ($filters['group_type']) {
                case 'polyphony':
                    $having[] = match ($gv) {
                        '0' => 'value_count = 0',
                        '1' => 'value_count = 1',
                        '2-5' => 'value_count BETWEEN 2 AND 5',
                        '6-10' => 'value_count BETWEEN 6 AND 10',
                        '11-20' => 'value_count BETWEEN 11 AND 20',
                        '20+' => 'value_count > 20',
                        default => '1=1',
                    };
                    break;
                case 'usage':
                    $having[] = match ($gv) {
                        '0' => 'total_occurrences = 0',
                        '1-10' => 'total_occurrences BETWEEN 1 AND 10',
                        '11-100' => 'total_occurrences BETWEEN 11 AND 100',
                        '101-1000' => 'total_occurrences BETWEEN 101 AND 1000',
                        '1000+' => 'total_occurrences > 1000',
                        default => '1=1',
                    };
                    break;
                case 'word_count':
                    $having[] = match ($gv) {
                        '0' => 'word_count = 0',
                        '1-5' => 'word_count BETWEEN 1 AND 5',
                        '6-20' => 'word_count BETWEEN 6 AND 20',
                        '20+' => 'word_count > 20',
                        default => '1=1',
                    };
                    break;
            }
        }

        $minFreq = (int)($filters['min_frequency'] ?? 0);
        if ($minFreq > 0) {
            $having[] = "total_occurrences >= :min_frequency";
        }

        $whereClause = $where ? 'WHERE ' . implode(' AND ', $where) : '';
        $havingClause = $having ? 'HAVING ' . implode(' AND ', $having) : '';

        // Sort
        $orderBy = match ($filters['sort'] ?? 'sign_id') {
            'frequency' => 'total_occurrences DESC, s.sign_id ASC',
            'value_count' => 'value_count DESC, s.sign_id ASC',
            'word_count' => 'word_count DESC, s.sign_id ASC',
            default => 's.sign_id ASC',
        };

        // Subquery-based count (needed because HAVING changes the count)
        $innerSql = "
            SELECT s.sign_id,
                COUNT(DISTINCT sv.value) as value_count,
                COUNT(DISTINCT swu.entry_id) as word_count,
                COALESCE(SUM(swu.usage_count), 0) as total_occurrences
            FROM signs s
            LEFT JOIN sign_values sv ON s.sign_id = sv.sign_id
            LEFT JOIN sign_word_usage swu ON s.sign_id = swu.sign_id
            {$whereClause}
            GROUP BY s.sign_id
            {$havingClause}
        ";

        $countSql = "SELECT COUNT(*) FROM ({$innerSql})";
        $countStmt = $this->db()->prepare($countSql);
        foreach ($params as $key => $val) {
            $countStmt->bindValue(":{$key}", $val);
        }
        if ($minFreq > 0) {
            $countStmt->bindValue(':min_frequency', $minFreq, SQLITE3_INTEGER);
        }
        $total = (int)$this->fetchScalar($countStmt);

        // Main query
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
            {$havingClause}
            ORDER BY {$orderBy}
            LIMIT :limit OFFSET :offset
        ";

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
