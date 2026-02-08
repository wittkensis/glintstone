<?php
/**
 * Library Word Detail Page
 *
 * Comprehensive view of a single dictionary entry with:
 * - Core information with educational tooltips
 * - Polysemic senses
 * - Variant forms
 * - Sign breakdown
 * - Related words
 * - Corpus examples
 * - CAD references (for Akkadian)
 */

require_once __DIR__ . '/../includes/header.php';

// Get entry_id from query parameter
$entry_id = $_GET['id'] ?? null;

if (empty($entry_id)) {
    header('Location: /dictionary/');
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Word Detail - Cuneiform Library</title>
    <link rel="stylesheet" href="/assets/css/layout/site.css">
    <link rel="stylesheet" href="/assets/css/components/word-detail.css">
    <link rel="stylesheet" href="/assets/css/components/educational-help.css">
</head>
<body>
    <div class="dictionary-word-detail">
        <div class="word-detail-container" id="word-detail-container">
            <!-- Loading state -->
            <div class="loading-state">
                <p>Loading entry...</p>
            </div>
        </div>

        <!-- Back to browse -->
        <div class="word-actions">
            <a href="/dictionary/" class="btn btn--secondary">← Back to Dictionary Browser</a>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/assets/js/modules/educational-help.js"></script>
    <script src="/assets/js/modules/word-detail-renderer.js"></script>
    <script>
        (async function() {
            const entryId = <?= json_encode($entry_id) ?>;
            const container = document.getElementById('word-detail-container');

            try {
                // Fetch word data from API
                const response = await fetch(`/api/dictionary/word-detail.php?entry_id=${encodeURIComponent(entryId)}`);

                if (!response.ok) {
                    throw new Error('Failed to load entry');
                }

                const data = await response.json();

                // Get help visibility from educational help system
                const showHelp = educationalHelp.helpVisible;

                // Render word detail
                const renderer = new WordDetailRenderer({
                    compact: false,
                    showHelp: showHelp
                });

                await renderer.render(data, container);

                // Update page title
                if (data.entry) {
                    document.title = `${data.entry.headword}${data.entry.guide_word ? ` [${data.entry.guide_word}]` : ''} - Cuneiform Library`;
                }

            } catch (error) {
                console.error('Error loading word detail:', error);
                container.innerHTML = `
                    <div class="error-state">
                        <h2>Error loading entry</h2>
                        <p>${error.message}</p>
                        <a href="/dictionary/" class="btn">Return to browser</a>
                    </div>
                `;
            }
        })();
    </script>
</body>
</html>
