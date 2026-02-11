<?php
/**
 * Collection Repository
 * Handles user collection queries
 */

declare(strict_types=1);

namespace Glintstone\Repository;

final class CollectionRepository extends BaseRepository
{
    /**
     * Get all collections with tablet counts
     */
    public function getAll(): array
    {
        return $this->query("
            SELECT
                c.collection_id,
                c.name,
                c.description,
                c.image_path,
                c.created_at,
                c.updated_at,
                COUNT(cm.p_number) as tablet_count
            FROM collections c
            LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
            GROUP BY c.collection_id
            ORDER BY c.created_at DESC
        ");
    }

    /**
     * Get collection by ID
     */
    public function findById(int $collectionId): ?array
    {
        $stmt = $this->prepare("
            SELECT
                c.*,
                COUNT(cm.p_number) as tablet_count
            FROM collections c
            LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
            WHERE c.collection_id = :id
            GROUP BY c.collection_id
        ", ['id' => $collectionId]);

        return $this->fetchOne($stmt);
    }

    /**
     * Get tablets in a collection
     */
    public function getTablets(int $collectionId, int $limit = 24, int $offset = 0): array
    {
        // Get total count
        $countStmt = $this->prepare("
            SELECT COUNT(*) FROM collection_members WHERE collection_id = :id
        ", ['id' => $collectionId]);
        $total = (int)$this->fetchScalar($countStmt);

        // Get paginated tablets
        $sql = "
            SELECT
                a.*,
                ps.has_image, ps.has_ocr, ps.has_atf, ps.has_lemmas,
                ps.has_translation, ps.has_sign_annotations, ps.quality_score,
                cm.added_at
            FROM collection_members cm
            JOIN artifacts a ON cm.p_number = a.p_number
            LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
            WHERE cm.collection_id = :id
            ORDER BY cm.added_at DESC
            LIMIT :limit OFFSET :offset
        ";

        $stmt = $this->db()->prepare($sql);
        $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
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
     * Get preview tablets for a collection (for thumbnail grid)
     */
    public function getPreviewTablets(int $collectionId, int $limit = 4): array
    {
        $sql = "
            SELECT a.p_number, a.designation
            FROM collection_members cm
            JOIN artifacts a ON cm.p_number = a.p_number
            WHERE cm.collection_id = :id
            ORDER BY cm.added_at DESC
            LIMIT :limit
        ";

        $stmt = $this->db()->prepare($sql);
        $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
        $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

        return $this->fetchAll($stmt);
    }

    /**
     * Create a new collection
     */
    public function create(string $name, ?string $description = null, ?string $imagePath = null): int
    {
        $writeDb = $this->getWriteConnection();

        $stmt = $writeDb->prepare("
            INSERT INTO collections (name, description, image_path, created_at, updated_at)
            VALUES (:name, :description, :image_path, datetime('now'), datetime('now'))
        ");
        $stmt->bindValue(':name', $name, SQLITE3_TEXT);
        $stmt->bindValue(':description', $description, SQLITE3_TEXT);
        $stmt->bindValue(':image_path', $imagePath, SQLITE3_TEXT);
        $stmt->execute();

        return (int)$writeDb->lastInsertRowID();
    }

    /**
     * Update a collection
     */
    public function update(int $collectionId, array $data): bool
    {
        $writeDb = $this->getWriteConnection();

        $sets = ['updated_at = datetime(\'now\')'];
        $params = ['id' => $collectionId];

        if (isset($data['name'])) {
            $sets[] = 'name = :name';
            $params['name'] = $data['name'];
        }

        if (array_key_exists('description', $data)) {
            $sets[] = 'description = :description';
            $params['description'] = $data['description'];
        }

        if (array_key_exists('image_path', $data)) {
            $sets[] = 'image_path = :image_path';
            $params['image_path'] = $data['image_path'];
        }

        $sql = "UPDATE collections SET " . implode(', ', $sets) . " WHERE collection_id = :id";
        $stmt = $writeDb->prepare($sql);

        foreach ($params as $key => $val) {
            $stmt->bindValue(":{$key}", $val);
        }

        return $stmt->execute() !== false;
    }

    /**
     * Delete a collection
     */
    public function delete(int $collectionId): bool
    {
        $writeDb = $this->getWriteConnection();

        // Delete members first
        $memberStmt = $writeDb->prepare("DELETE FROM collection_members WHERE collection_id = :id");
        $memberStmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
        $memberStmt->execute();

        // Delete collection
        $stmt = $writeDb->prepare("DELETE FROM collections WHERE collection_id = :id");
        $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);

        return $stmt->execute() !== false;
    }

    /**
     * Add tablets to collection
     */
    public function addTablets(int $collectionId, array $pNumbers): int
    {
        $writeDb = $this->getWriteConnection();
        $added = 0;

        $stmt = $writeDb->prepare("
            INSERT OR IGNORE INTO collection_members (collection_id, p_number, added_at)
            VALUES (:collection_id, :p_number, datetime('now'))
        ");

        foreach ($pNumbers as $pNumber) {
            $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
            $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
            if ($stmt->execute()) {
                $added += $writeDb->changes();
            }
            $stmt->reset();
        }

        // Update collection timestamp
        $this->touchCollection($collectionId);

        return $added;
    }

    /**
     * Remove tablet from collection
     */
    public function removeTablet(int $collectionId, string $pNumber): bool
    {
        $writeDb = $this->getWriteConnection();

        $stmt = $writeDb->prepare("
            DELETE FROM collection_members
            WHERE collection_id = :collection_id AND p_number = :p_number
        ");
        $stmt->bindValue(':collection_id', $collectionId, SQLITE3_INTEGER);
        $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
        $result = $stmt->execute();

        if ($result !== false && $writeDb->changes() > 0) {
            $this->touchCollection($collectionId);
            return true;
        }

        return false;
    }

    /**
     * Check if tablet is in collection
     */
    public function hasTablet(int $collectionId, string $pNumber): bool
    {
        $stmt = $this->prepare("
            SELECT 1 FROM collection_members
            WHERE collection_id = :collection_id AND p_number = :p_number
        ", ['collection_id' => $collectionId, 'p_number' => $pNumber]);

        return $this->fetchOne($stmt) !== null;
    }

    /**
     * Update collection's updated_at timestamp
     */
    private function touchCollection(int $collectionId): void
    {
        $writeDb = $this->getWriteConnection();
        $stmt = $writeDb->prepare("
            UPDATE collections SET updated_at = datetime('now') WHERE collection_id = :id
        ");
        $stmt->bindValue(':id', $collectionId, SQLITE3_INTEGER);
        $stmt->execute();
    }
}
