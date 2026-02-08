<?php
/**
 * Library Sign Detail Page
 *
 * Complete information about a cuneiform sign:
 * - Large cuneiform character
 * - All values grouped by type (logographic, syllabic, determinative)
 * - Words using this sign
 * - Usage statistics
 */

require_once __DIR__ . '/../includes/header.php';

// Get sign_id from URL path
$path = parse_url($_SERVER['REQUEST_URI'], PHP_URL_PATH);
$path_parts = explode('/', trim($path, '/'));
$sign_id = end($path_parts);

if (empty($sign_id)) {
    http_response_code(404);
    echo '<h1>Sign not found</h1>';
    exit;
}
?>

<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Sign Detail - Cuneiform Library</title>
    <link rel="stylesheet" href="/assets/css/layout/site.css">
    <link rel="stylesheet" href="/assets/css/components/sign-grid.css">
    <link rel="stylesheet" href="/assets/css/components/word-detail.css">
    <link rel="stylesheet" href="/assets/css/components/educational-help.css">
</head>
<body>
    <div class="library-sign-detail">
        <div class="sign-detail-container" id="sign-detail-container">
            <!-- Loading state -->
            <div class="loading-state">
                <p>Loading sign...</p>
            </div>
        </div>

        <!-- Back to browse -->
        <div class="sign-actions">
            <a href="/library/signs.php" class="btn btn--secondary">← Back to Sign Library</a>
        </div>
    </div>

    <!-- JavaScript -->
    <script src="/assets/js/modules/educational-help.js"></script>
    <script>
        (async function() {
            const signId = <?= json_encode($sign_id) ?>;
            const container = document.getElementById('sign-detail-container');

            try {
                // Fetch sign data from API
                const response = await fetch(`/api/library/sign-detail.php?sign_id=${encodeURIComponent(signId)}`);

                if (!response.ok) {
                    throw new Error('Failed to load sign');
                }

                const data = await response.json();

                // Render sign detail
                const html = `
                    <header class="sign-detail__header">
                        <div class="sign-detail__cuneiform">
                            ${data.sign.utf8 || ''}
                        </div>
                        <div class="sign-detail__info">
                            <h1>${escapeHtml(data.sign.sign_id)}</h1>
                            ${data.sign.most_common_value ? `<p class="sign-common-value">Most common: ${escapeHtml(data.sign.most_common_value)}</p>` : ''}
                            ${data.sign.sign_type ? `<span class="badge badge--sign-type">${escapeHtml(data.sign.sign_type)}</span>` : ''}
                        </div>
                    </header>

                    <section class="sign-detail__statistics">
                        <h2>Usage Statistics</h2>
                        <div class="stats-grid">
                            <div class="stat-item">
                                <span class="stat-label">Total Values</span>
                                <span class="stat-value">${data.statistics.total_values}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Logographic</span>
                                <span class="stat-value">${data.statistics.logographic_values}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Syllabic</span>
                                <span class="stat-value">${data.statistics.syllabic_values}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Words Using Sign</span>
                                <span class="stat-value">${data.statistics.total_words_using_sign}</span>
                            </div>
                            <div class="stat-item">
                                <span class="stat-label">Total Occurrences</span>
                                <span class="stat-value">${data.statistics.total_corpus_occurrences.toLocaleString()}</span>
                            </div>
                        </div>
                    </section>

                    ${renderValues(data.values)}
                    ${renderWords(data.words)}
                `;

                container.innerHTML = html;

                // Update page title
                document.title = `${data.sign.sign_id} - Cuneiform Sign Library`;

            } catch (error) {
                console.error('Error loading sign detail:', error);
                container.innerHTML = `
                    <div class="error-state">
                        <h2>Error loading sign</h2>
                        <p>${error.message}</p>
                        <a href="/library/signs.php" class="btn">Return to sign library</a>
                    </div>
                `;
            }

            function renderValues(values) {
                let html = '<section class="sign-detail__values"><h2>Readings and Values</h2>';

                // Logographic
                if (values.logographic && values.logographic.length > 0) {
                    html += `
                        <div class="value-group">
                            <h3>Logographic</h3>
                            <p class="value-group-description">Complete word meanings</p>
                            <ul class="value-list">
                                ${values.logographic.map(v => `
                                    <li class="value-item">
                                        <span class="value-text">${escapeHtml(v.value)}</span>
                                        ${v.frequency ? `<span class="value-frequency">${v.frequency.toLocaleString()} uses</span>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `;
                }

                // Syllabic
                if (values.syllabic && values.syllabic.length > 0) {
                    html += `
                        <div class="value-group">
                            <h3>Syllabic</h3>
                            <p class="value-group-description">Phonetic sound values</p>
                            <ul class="value-list">
                                ${values.syllabic.map(v => `
                                    <li class="value-item">
                                        <span class="value-text">${escapeHtml(v.value)}</span>
                                        ${v.frequency ? `<span class="value-frequency">${v.frequency.toLocaleString()} uses</span>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `;
                }

                // Determinative
                if (values.determinative && values.determinative.length > 0) {
                    html += `
                        <div class="value-group">
                            <h3>Determinative</h3>
                            <p class="value-group-description">Semantic classifiers (unpronounced)</p>
                            <ul class="value-list">
                                ${values.determinative.map(v => `
                                    <li class="value-item">
                                        <span class="value-text">${escapeHtml(v.value)}</span>
                                        ${v.frequency ? `<span class="value-frequency">${v.frequency.toLocaleString()} uses</span>` : ''}
                                    </li>
                                `).join('')}
                            </ul>
                        </div>
                    `;
                }

                html += '</section>';
                return html;
            }

            function renderWords(words) {
                if (!words.sample || words.sample.length === 0) {
                    return '<section class="sign-detail__words"><h2>Words Using This Sign</h2><p>No words found.</p></section>';
                }

                const wordsHtml = words.sample.map(word => `
                    <div class="word-usage-item">
                        <a href="/library/word/${encodeURIComponent(word.entry.entry_id)}" class="word-link">
                            <strong>${escapeHtml(word.entry.headword)}</strong>
                            ${word.entry.guide_word ? `<span class="guide-word">[${escapeHtml(word.entry.guide_word)}]</span>` : ''}
                        </a>
                        <div class="word-usage-meta">
                            <span class="badge badge--language">${escapeHtml(word.entry.language)}</span>
                            <span class="word-usage-type">${escapeHtml(word.value_type || 'unknown')}: ${escapeHtml(word.sign_value)}</span>
                            <span class="word-usage-count">${word.usage_count} occurrences</span>
                        </div>
                    </div>
                `).join('');

                return `
                    <section class="sign-detail__words">
                        <h2>Words Using This Sign</h2>
                        <p class="section-description">
                            Showing ${words.showing} of ${words.total_unique_words.toLocaleString()} words
                        </p>
                        <div class="word-usage-list">
                            ${wordsHtml}
                        </div>
                    </section>
                `;
            }

            function escapeHtml(text) {
                if (!text) return '';
                const div = document.createElement('div');
                div.textContent = text;
                return div.innerHTML;
            }
        })();
    </script>
</body>
</html>
