<?php
// Standalone test - bypass server, test directly
echo "Testing PHP execution...\n";
echo "PHP Version: " . PHP_VERSION . "\n";
echo "Memory Limit: " . ini_get('memory_limit') . "\n";
echo "\n";

// Test database access
echo "Testing database access...\n";
require_once __DIR__ . '/includes/db.php';
$db = getDB();
$result = $db->query("SELECT COUNT(*) as count FROM artifacts");
$row = $result->fetchArray(SQLITE3_ASSOC);
echo "Artifact count: " . $row['count'] . "\n";
echo "\nAll tests passed!\n";
