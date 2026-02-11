<?php
/**
 * Base Repository
 * Shared database connection and query utilities for all repositories
 */

declare(strict_types=1);

namespace Glintstone\Repository;

use SQLite3;
use SQLite3Stmt;
use SQLite3Result;

abstract class BaseRepository
{
    private static ?SQLite3 $readDb = null;
    private static ?SQLite3 $writeDb = null;

    /**
     * Get read-only database connection (shared singleton)
     */
    protected function getReadConnection(): SQLite3
    {
        if (self::$readDb === null) {
            self::$readDb = new SQLite3(DB_PATH, SQLITE3_OPEN_READONLY);
            self::$readDb->enableExceptions(true);
            self::$readDb->busyTimeout(5000);
            self::$readDb->exec('PRAGMA journal_mode=WAL');
        }
        return self::$readDb;
    }

    /**
     * Get read-write database connection (shared singleton)
     */
    protected function getWriteConnection(): SQLite3
    {
        if (self::$writeDb === null) {
            self::$writeDb = new SQLite3(DB_PATH, SQLITE3_OPEN_READWRITE);
            self::$writeDb->enableExceptions(true);
            self::$writeDb->busyTimeout(5000);
            self::$writeDb->exec('PRAGMA journal_mode=WAL');
        }
        return self::$writeDb;
    }

    /**
     * Shorthand for read connection
     * Public to allow incremental migration of existing code
     */
    public function db(): SQLite3
    {
        return $this->getReadConnection();
    }

    /**
     * Execute query and return all rows as array
     */
    protected function fetchAll(SQLite3Stmt $stmt): array
    {
        $result = $stmt->execute();
        $rows = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $rows[] = $row;
        }
        return $rows;
    }

    /**
     * Execute query and return single row or null
     */
    protected function fetchOne(SQLite3Stmt $stmt): ?array
    {
        $result = $stmt->execute();
        $row = $result->fetchArray(SQLITE3_ASSOC);
        return $row ?: null;
    }

    /**
     * Execute query and return scalar value
     */
    protected function fetchScalar(SQLite3Stmt $stmt): mixed
    {
        $result = $stmt->execute();
        $row = $result->fetchArray(SQLITE3_NUM);
        return $row ? $row[0] : null;
    }

    /**
     * Execute a raw query and return all rows
     */
    protected function query(string $sql): array
    {
        $result = $this->db()->query($sql);
        $rows = [];
        while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
            $rows[] = $row;
        }
        return $rows;
    }

    /**
     * Prepare and bind parameters to a statement
     *
     * @param string $sql SQL with named placeholders
     * @param array $params Associative array of placeholder => value
     */
    protected function prepare(string $sql, array $params = []): SQLite3Stmt
    {
        $stmt = $this->db()->prepare($sql);

        foreach ($params as $key => $value) {
            $placeholder = str_starts_with($key, ':') ? $key : ":{$key}";
            $type = $this->inferType($value);
            $stmt->bindValue($placeholder, $value, $type);
        }

        return $stmt;
    }

    /**
     * Infer SQLite3 type constant from PHP value
     */
    private function inferType(mixed $value): int
    {
        return match (true) {
            is_int($value) => SQLITE3_INTEGER,
            is_float($value) => SQLITE3_FLOAT,
            is_null($value) => SQLITE3_NULL,
            default => SQLITE3_TEXT,
        };
    }

    /**
     * Build IN clause with proper parameter binding
     * Returns [clause, params] where clause is "IN (:p0, :p1, ...)"
     */
    protected function buildInClause(array $values, string $prefix = 'p'): array
    {
        if (empty($values)) {
            return ['IN (NULL)', []]; // Always false
        }

        $placeholders = [];
        $params = [];

        foreach ($values as $i => $value) {
            $key = ":{$prefix}{$i}";
            $placeholders[] = $key;
            $params[$key] = $value;
        }

        return ['IN (' . implode(', ', $placeholders) . ')', $params];
    }

    /**
     * Build LIKE clause for multiple values with OR
     * Returns [clause, params]
     */
    protected function buildLikeClause(string $column, array $values, string $prefix = 'like'): array
    {
        if (empty($values)) {
            return ['1=0', []]; // Always false
        }

        $conditions = [];
        $params = [];

        foreach ($values as $i => $value) {
            $key = ":{$prefix}{$i}";
            $conditions[] = "{$column} LIKE {$key}";
            $params[$key] = '%' . $value . '%';
        }

        return ['(' . implode(' OR ', $conditions) . ')', $params];
    }

    /**
     * Group results by a column into nested structure
     */
    protected function groupBy(array $rows, string $groupColumn, string $totalColumn = null): array
    {
        $grouped = [];
        $totals = [];

        foreach ($rows as $row) {
            $group = $row[$groupColumn];
            if (!isset($grouped[$group])) {
                $grouped[$group] = [];
                $totals[$group] = 0;
            }
            $grouped[$group][] = $row;
            if ($totalColumn && isset($row[$totalColumn])) {
                $totals[$group] += (int)$row[$totalColumn];
            }
        }

        // Sort by totals descending
        if ($totalColumn) {
            arsort($totals);
            $sortedGrouped = [];
            foreach (array_keys($totals) as $group) {
                $sortedGrouped[$group] = $grouped[$group];
            }
            $grouped = $sortedGrouped;
        }

        return ['grouped' => $grouped, 'totals' => $totals];
    }
}
