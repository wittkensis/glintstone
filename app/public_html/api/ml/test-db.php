<?php
// Test with database
error_reporting(E_ALL);
ini_set('display_errors', 1);

header('Content-Type: application/json');
echo json_encode(['step' => 'Headers sent']) . "\n";

require_once __DIR__ . '/../../includes/db.php';
echo json_encode(['step' => 'DB included']) . "\n";

$db = getDB();
echo json_encode(['step' => 'DB connection created']) . "\n";

$stmt = $db->prepare("SELECT COUNT(*) as count FROM artifacts");
echo json_encode(['step' => 'Query prepared']) . "\n";

$result = $stmt->execute();
echo json_encode(['step' => 'Query executed']) . "\n";

$row = $result->fetchArray(SQLITE3_ASSOC);
echo json_encode(['step' => 'Result fetched', 'count' => $row['count']]) . "\n";

echo json_encode(['status' => 'success']) . "\n";
