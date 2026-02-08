<?php
/**
 * Homepage Helper Functions
 *
 * Query functions for homepage KPIs, showcases, and activity feed
 */

require_once __DIR__ . '/../db.php';

/**
 * Get KPI metrics for dashboard
 *
 * @return array Associative array with all KPI data
 */
function getKPIMetrics(): array {
    $db = getDB();

    // Total tablets
    $totalTablets = $db->querySingle("SELECT COUNT(*) FROM artifacts");

    // Pipeline status distribution
    $pipelineStats = $db->query("
        SELECT
            COUNT(CASE WHEN has_image = 1 THEN 1 END) as image_count,
            COUNT(CASE WHEN has_atf = 1 THEN 1 END) as atf_count,
            COUNT(CASE WHEN has_lemmas = 1 THEN 1 END) as lemma_count,
            COUNT(CASE WHEN has_translation = 1 THEN 1 END) as translation_count,
            COUNT(CASE WHEN has_image = 1 AND has_atf = 1 AND has_lemmas = 1 AND has_translation = 1 THEN 1 END) as complete_count
        FROM pipeline_status
    ")->fetchArray(SQLITE3_ASSOC);

    // Calculate percentages
    $digitizationPct = ($pipelineStats['atf_count'] / $totalTablets) * 100;
    $translationPct = ($pipelineStats['translation_count'] / $totalTablets) * 100;
    $imagePct = ($pipelineStats['image_count'] / $totalTablets) * 100;

    // Quality distribution
    $qualityStats = $db->query("
        SELECT
            COUNT(CASE WHEN quality_score < 0.25 THEN 1 END) as q1_count,
            COUNT(CASE WHEN quality_score >= 0.25 AND quality_score < 0.5 THEN 1 END) as q2_count,
            COUNT(CASE WHEN quality_score >= 0.5 AND quality_score < 0.75 THEN 1 END) as q3_count,
            COUNT(CASE WHEN quality_score >= 0.75 THEN 1 END) as q4_count
        FROM pipeline_status
        WHERE quality_score IS NOT NULL
    ")->fetchArray(SQLITE3_ASSOC);

    // Recent activity count
    $recentCount = $db->querySingle("
        SELECT COUNT(*)
        FROM pipeline_status
        WHERE last_updated >= datetime('now', '-30 days')
    ");

    // Top 5 languages
    $topLanguages = [];
    $langResult = $db->query("
        SELECT language, tablet_count
        FROM language_stats
        WHERE language IS NOT NULL AND language != ''
        ORDER BY tablet_count DESC
        LIMIT 5
    ");
    while ($row = $langResult->fetchArray(SQLITE3_ASSOC)) {
        $topLanguages[] = $row;
    }

    // Top 5 periods
    $topPeriods = [];
    $periodResult = $db->query("
        SELECT period, tablet_count
        FROM period_stats
        WHERE period IS NOT NULL AND period != ''
        ORDER BY tablet_count DESC
        LIMIT 5
    ");
    while ($row = $periodResult->fetchArray(SQLITE3_ASSOC)) {
        $topPeriods[] = $row;
    }

    // Top 5 genres
    $topGenres = [];
    $genreResult = $db->query("
        SELECT genre, tablet_count
        FROM genre_stats
        WHERE genre IS NOT NULL AND genre != ''
        ORDER BY tablet_count DESC
        LIMIT 5
    ");
    while ($row = $genreResult->fetchArray(SQLITE3_ASSOC)) {
        $topGenres[] = $row;
    }

    return [
        'total_tablets' => $totalTablets,
        'digitization_pct' => round($digitizationPct, 1),
        'translation_pct' => round($translationPct, 1),
        'image_pct' => round($imagePct, 1),
        'pipeline' => [
            'images' => [
                'count' => $pipelineStats['image_count'],
                'percent' => round($imagePct, 1)
            ],
            'atf' => [
                'count' => $pipelineStats['atf_count'],
                'percent' => round($digitizationPct, 1)
            ],
            'lemmas' => [
                'count' => $pipelineStats['lemma_count'],
                'percent' => round(($pipelineStats['lemma_count'] / $totalTablets) * 100, 1)
            ],
            'translations' => [
                'count' => $pipelineStats['translation_count'],
                'percent' => round($translationPct, 1)
            ],
            'complete' => [
                'count' => $pipelineStats['complete_count'],
                'percent' => round(($pipelineStats['complete_count'] / $totalTablets) * 100, 1)
            ]
        ],
        'quality_distribution' => $qualityStats,
        'recent_activity_count' => $recentCount,
        'top_languages' => $topLanguages,
        'top_periods' => $topPeriods,
        'top_genres' => $topGenres
    ];
}

/**
 * Get dummy activity data for social feed preview
 *
 * @param int $limit Number of activities to generate
 * @return array Array of activity items
 */
function getDummyActivities(int $limit = 10): array {
    $activityTypes = [
        [
            'type' => 'translation',
            'icon' => '📝',
            'template' => '%s added translation to %s',
            'detail_template' => '%s'
        ],
        [
            'type' => 'sign_detection',
            'icon' => '🔍',
            'template' => '%s identified signs in %s',
            'detail_template' => 'Identified %d cuneiform signs'
        ],
        [
            'type' => 'collation',
            'icon' => '✍️',
            'template' => '%s added collation notes to %s',
            'detail_template' => '%s'
        ],
        [
            'type' => 'join_discovered',
            'icon' => '🔗',
            'template' => '%s discovered join between %s',
            'detail_template' => '%s'
        ],
        [
            'type' => 'cross_reference',
            'icon' => '⭐',
            'template' => '%s linked %s to %s',
            'detail_template' => 'Added scholarly cross-reference'
        ],
        [
            'type' => 'image_upload',
            'icon' => '📷',
            'template' => '%s uploaded image for %s',
            'detail_template' => '%s'
        ],
        [
            'type' => 'transliteration',
            'icon' => '📖',
            'template' => '%s added transliteration to %s',
            'detail_template' => '%s'
        ],
        [
            'type' => 'lemmatization',
            'icon' => '🏷️',
            'template' => '%s completed lemmatization of %s',
            'detail_template' => 'Analyzed %d words'
        ]
    ];

    $names = [
        'Sarah Chen', 'Marcus Weber', 'Lisa Park', 'David Kim',
        'Anna Schmidt', 'James Liu', 'Emma Wilson', 'Robert Chen',
        'Maria Garcia', 'John Anderson', 'Fatima Hassan', 'Carlos Mendez',
        'Priya Patel', 'Thomas Mueller', 'Yuki Tanaka'
    ];

    $periods = [
        'Old Babylonian', 'Ur III', 'Neo-Assyrian', 'Old Akkadian',
        'Neo-Babylonian', 'Middle Babylonian', 'Kassite', 'Sargonic',
        'Early Dynastic III', 'Old Assyrian'
    ];

    $genres = [
        'administrative text', 'royal inscription', 'literary work',
        'legal document', 'lexical list', 'mathematical text',
        'letter', 'incantation', 'omen text', 'hymn'
    ];

    $composites = [
        'Epic of Gilgamesh Tablet XI',
        'Enuma Elish Tablet I',
        'Atrahasis',
        'Code of Hammurabi',
        'Descent of Ishtar',
        'Sumerian King List',
        'Instructions of Shuruppak'
    ];

    $timestamps = [
        '2 hours ago', '5 hours ago', '8 hours ago', '1 day ago',
        '2 days ago', '3 days ago', '4 days ago', '5 days ago',
        '1 week ago', '10 days ago'
    ];

    $activities = [];
    for ($i = 0; $i < $limit; $i++) {
        $type = $activityTypes[array_rand($activityTypes)];
        $user = $names[array_rand($names)];
        $pNumber = 'P' . str_pad(rand(100000, 999999), 6, '0', STR_PAD_LEFT);
        $timestamp = $timestamps[min($i, count($timestamps) - 1)];
        $period = $periods[array_rand($periods)];
        $genre = $genres[array_rand($genres)];

        $activity = [
            'type' => $type['type'],
            'icon' => $type['icon'],
            'user' => $user,
            'tablet' => $pNumber,
            'timestamp' => $timestamp
        ];

        // Type-specific details
        switch ($type['type']) {
            case 'sign_detection':
                $signCount = rand(10, 50);
                $activity['description'] = sprintf($type['template'], $user, $pNumber);
                $activity['detail'] = sprintf($type['detail_template'], $signCount);
                break;

            case 'join_discovered':
                $pNumber2 = 'P' . str_pad(rand(100000, 999999), 6, '0', STR_PAD_LEFT);
                $activity['description'] = sprintf($type['template'], $user, "$pNumber and $pNumber2");
                $activity['detail'] = sprintf($type['detail_template'], "$period administrative archive");
                $activity['tablets'] = [$pNumber, $pNumber2];
                break;

            case 'cross_reference':
                $composite = $composites[array_rand($composites)];
                $activity['description'] = sprintf($type['template'], $user, $pNumber, $composite);
                $activity['detail'] = $type['detail_template'];
                $activity['composite'] = $composite;
                break;

            case 'lemmatization':
                $wordCount = rand(50, 200);
                $activity['description'] = sprintf($type['template'], $user, $pNumber);
                $activity['detail'] = sprintf($type['detail_template'], $wordCount);
                break;

            default:
                $activity['description'] = sprintf($type['template'], $user, $pNumber);
                $activity['detail'] = sprintf($type['detail_template'], "$period $genre");
        }

        $activities[] = $activity;
    }

    return $activities;
}

/**
 * Format a relative timestamp for display
 */
function formatRelativeTime(string $datetime): string {
    $now = new DateTime();
    $past = new DateTime($datetime);
    $diff = $now->diff($past);

    if ($diff->y > 0) return $diff->y . ' year' . ($diff->y > 1 ? 's' : '') . ' ago';
    if ($diff->m > 0) return $diff->m . ' month' . ($diff->m > 1 ? 's' : '') . ' ago';
    if ($diff->d >= 7) {
        $weeks = floor($diff->d / 7);
        return $weeks . ' week' . ($weeks > 1 ? 's' : '') . ' ago';
    }
    if ($diff->d > 0) return $diff->d . ' day' . ($diff->d > 1 ? 's' : '') . ' ago';
    if ($diff->h > 0) return $diff->h . ' hour' . ($diff->h > 1 ? 's' : '') . ' ago';
    if ($diff->i > 0) return $diff->i . ' minute' . ($diff->i > 1 ? 's' : '') . ' ago';
    return 'just now';
}
