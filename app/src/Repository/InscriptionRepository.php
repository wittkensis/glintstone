<?php
/**
 * Inscription Repository
 * Handles inscription, translation, and ATF-related queries
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class InscriptionRepository extends BaseRepository
{
    /**
     * Get latest inscription for artifact
     */
    public function getLatest(string $pNumber): ?array
    {
        $stmt = $this->prepare("
            SELECT * FROM inscriptions
            WHERE p_number = :p_number AND is_latest = 1
        ", ['p_number' => $pNumber]);

        return $this->fetchOne($stmt);
    }

    /**
     * Get all inscriptions for artifact (including history)
     */
    public function getAll(string $pNumber): array
    {
        $stmt = $this->prepare("
            SELECT * FROM inscriptions
            WHERE p_number = :p_number
            ORDER BY created_at DESC
        ", ['p_number' => $pNumber]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get translations for artifact
     */
    public function getTranslations(string $pNumber): array
    {
        $stmt = $this->prepare("
            SELECT * FROM translations
            WHERE p_number = :p_number
            ORDER BY language ASC
        ", ['p_number' => $pNumber]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get lemmas for artifact
     */
    public function getLemmas(string $pNumber): array
    {
        $stmt = $this->prepare("
            SELECT * FROM lemmas
            WHERE p_number = :p_number
            ORDER BY line_no ASC, word_no ASC
        ", ['p_number' => $pNumber]);

        return $this->fetchAll($stmt);
    }

    /**
     * Get lemmas indexed by line and word number
     * Returns nested array: [lineNo => [wordNo => lemmaData]]
     */
    public function getLemmasIndexed(string $pNumber): array
    {
        $lemmas = $this->getLemmas($pNumber);
        $indexed = [];

        foreach ($lemmas as $lemma) {
            $lineNo = (string)$lemma['line_no'];
            $wordNo = (string)$lemma['word_no'];

            if (!isset($indexed[$lineNo])) {
                $indexed[$lineNo] = [];
            }

            $indexed[$lineNo][$wordNo] = [
                'form' => $lemma['form'] ?? null,
                'cf' => $lemma['cf'] ?? null,
                'gw' => $lemma['gw'] ?? null,
                'pos' => $lemma['pos'] ?? null,
                'lang' => $lemma['lang'] ?? null,
            ];
        }

        return $indexed;
    }

    /**
     * Get sign annotations for artifact
     */
    public function getSignAnnotations(string $pNumber, ?string $surface = null): array
    {
        $sql = "
            SELECT * FROM sign_annotations
            WHERE p_number = :p_number
        ";
        $params = ['p_number' => $pNumber];

        if ($surface !== null) {
            $sql .= " AND surface = :surface";
            $params['surface'] = $surface;
        }

        $sql .= " ORDER BY bbox_y ASC, bbox_x ASC";

        $stmt = $this->prepare($sql, $params);
        return $this->fetchAll($stmt);
    }

    /**
     * Get translation lines keyed for line-matching
     * Returns array keyed as "surface_column_lineNo"
     */
    public function getTranslationLines(string $pNumber): array
    {
        $translations = $this->getTranslations($pNumber);
        $lines = [];

        foreach ($translations as $trans) {
            if (!empty($trans['lines'])) {
                $decoded = json_decode($trans['lines'], true);
                if (is_array($decoded)) {
                    foreach ($decoded as $key => $line) {
                        $lines[$key] = $line;
                    }
                }
            }
        }

        return $lines;
    }

    /**
     * Save inscription (create or update)
     */
    public function save(string $pNumber, string $atf, string $source = 'user'): bool
    {
        $writeDb = $this->getWriteConnection();

        // Mark existing as not latest
        $updateStmt = $writeDb->prepare("
            UPDATE inscriptions SET is_latest = 0 WHERE p_number = :p_number
        ");
        $updateStmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
        $updateStmt->execute();

        // Insert new inscription
        $insertStmt = $writeDb->prepare("
            INSERT INTO inscriptions (p_number, atf, source, is_latest, created_at)
            VALUES (:p_number, :atf, :source, 1, datetime('now'))
        ");
        $insertStmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
        $insertStmt->bindValue(':atf', $atf, SQLITE3_TEXT);
        $insertStmt->bindValue(':source', $source, SQLITE3_TEXT);

        return $insertStmt->execute() !== false;
    }
}
