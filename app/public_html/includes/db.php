<?php
/**
 * Database connection for Glintstone
 */

define('DB_PATH', dirname(__DIR__, 2) . '/glintstone.db');

function getDB(): SQLite3 {
    static $db = null;

    if ($db === null) {
        $db = new SQLite3(DB_PATH, SQLITE3_OPEN_READONLY);
        $db->enableExceptions(true);
    }

    return $db;
}

/**
 * Get artifact by P-number
 */
function getArtifact(string $pNumber): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT a.*, ps.has_image, ps.has_ocr, ps.ocr_confidence, ps.has_atf,
               ps.atf_source, ps.has_lemmas, ps.lemma_coverage, ps.has_translation,
               ps.quality_score
        FROM artifacts a
        LEFT JOIN pipeline_status ps ON a.p_number = ps.p_number
        WHERE a.p_number = :p_number
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get inscription for artifact
 */
function getInscription(string $pNumber): ?array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT * FROM inscriptions
        WHERE p_number = :p_number AND is_latest = 1
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();
    $row = $result->fetchArray(SQLITE3_ASSOC);
    return $row ?: null;
}

/**
 * Get composites for artifact
 */
function getComposites(string $pNumber): array {
    $db = getDB();
    $stmt = $db->prepare("
        SELECT c.* FROM composites c
        JOIN artifact_composites ac ON c.q_number = ac.q_number
        WHERE ac.p_number = :p_number
    ");
    $stmt->bindValue(':p_number', $pNumber, SQLITE3_TEXT);
    $result = $stmt->execute();

    $composites = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $composites[] = $row;
    }
    return $composites;
}

/**
 * Search glossary
 */
function searchGlossary(string $term, ?string $language = null, int $limit = 20): array {
    $db = getDB();

    $sql = "SELECT * FROM glossary_entries WHERE headword LIKE :term";
    if ($language) {
        $sql .= " AND language = :lang";
    }
    $sql .= " ORDER BY icount DESC LIMIT :limit";

    $stmt = $db->prepare($sql);
    $stmt->bindValue(':term', "%$term%", SQLITE3_TEXT);
    if ($language) {
        $stmt->bindValue(':lang', $language, SQLITE3_TEXT);
    }
    $stmt->bindValue(':limit', $limit, SQLITE3_INTEGER);

    $result = $stmt->execute();
    $entries = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $entries[] = $row;
    }
    return $entries;
}

/**
 * Get sign by ID
 */
function getSign(string $signId): ?array {
    $db = getDB();
    $stmt = $db->prepare("SELECT * FROM signs WHERE sign_id = :id");
    $stmt->bindValue(':id', $signId, SQLITE3_TEXT);
    $result = $stmt->execute();
    return $result->fetchArray(SQLITE3_ASSOC) ?: null;
}

/**
 * Get sign values
 */
function getSignValues(string $signId): array {
    $db = getDB();
    $stmt = $db->prepare("SELECT value FROM sign_values WHERE sign_id = :id");
    $stmt->bindValue(':id', $signId, SQLITE3_TEXT);
    $result = $stmt->execute();

    $values = [];
    while ($row = $result->fetchArray(SQLITE3_ASSOC)) {
        $values[] = $row['value'];
    }
    return $values;
}
