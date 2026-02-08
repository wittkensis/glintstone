<?php
/**
 * Collections Helper Functions
 *
 * Helper functions for working with collections data
 */

require_once __DIR__ . '/../db.php';

/**
 * Get random collections with preview tablets
 *
 * Fetches a random selection of collections from the database,
 * ensuring each has at least one tablet, and includes preview
 * tablet data for displaying thumbnail grids.
 *
 * @param int $limit Number of collections to fetch (default 3)
 * @return array Array of collections with preview_tablets included
 */
function getRandomCollections(int $limit = 3): array {
    $db = getDB();

    // Query collections with tablet count, excluding empty collections
    $stmt = $db->prepare("
        SELECT
            c.collection_id,
            c.name,
            c.description,
            COUNT(cm.p_number) as tablet_count
        FROM collections c
        LEFT JOIN collection_members cm ON c.collection_id = cm.collection_id
        GROUP BY c.collection_id
        HAVING tablet_count > 0
        ORDER BY RANDOM()
        LIMIT :limit
    ");
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);
    $result = $stmt->execute();

    $collections = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        // Fetch preview tablets for 2x2 thumbnail grid
        $previewTablets = getCollectionPreviewTablets((int)$row['collection_id'], 4);

        $collection = [
            'collection_id' => (int)$row['collection_id'],
            'name' => $row['name'],
            'description' => $row['description'],
            'tablet_count' => (int)$row['tablet_count'],
            'preview_tablets' => $previewTablets
        ];

        $collections[] = $collection;
    }

    return $collections;
}

// Note: getCollectionPreviewTablets() is already defined in db.php
// and is used directly by getRandomCollections() above
