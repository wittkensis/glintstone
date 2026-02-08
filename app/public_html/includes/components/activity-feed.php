<?php
/**
 * Activity Feed Component
 *
 * Displays social collaboration activity with EXAMPLE overlay
 * Shows realistic dummy data as a preview of future social features
 *
 * Required variables:
 * @var array $activities - Array of activity items from getDummyActivities()
 *
 * Optional variables:
 * @var bool $showExample - Show EXAMPLE overlay (default: true)
 */

if (!isset($activities)) {
    throw new Exception('Activity Feed component requires $activities variable');
}

$showExample = $showExample ?? true;
?>

<section class="activity-feed-section <?= $showExample ? 'activity-feed--example' : '' ?>"
         role="<?= $showExample ? 'region' : 'feed' ?>"
         aria-label="Recent Activity">

    <?php if ($showExample): ?>
    <div class="example-overlay" aria-label="Example Data">
        <span class="example-badge">EXAMPLE</span>
    </div>
    <?php endif; ?>

    <div class="section-header">
        <div class="section-header__content">
            <h2>
                Recent Activity
                <?php if ($showExample): ?>
                <span class="coming-soon-badge">Coming Soon</span>
                <?php endif; ?>
            </h2>
            <p class="section-description">
                <?php if ($showExample): ?>
                Preview of collaborative features showing how researchers will contribute to the platform
                <?php else: ?>
                Community contributions and discoveries from cuneiform scholars worldwide
                <?php endif; ?>
            </p>
        </div>
    </div>

    <?php if (empty($activities)): ?>
    <div class="empty-state">
        <div class="empty-icon">💬</div>
        <h3>No recent activity</h3>
        <p>Check back soon to see the latest contributions from the community.</p>
    </div>
    <?php else: ?>
    <div class="activity-feed">
        <?php foreach ($activities as $activity): ?>
        <article class="activity-item activity-item--<?= htmlspecialchars($activity['type']) ?>">
            <div class="activity-icon" aria-hidden="true">
                <?= $activity['icon'] ?>
            </div>

            <div class="activity-content">
                <div class="activity-header">
                    <p class="activity-description">
                        <span class="activity-user"><?= htmlspecialchars($activity['user']) ?></span>
                        <?php
                        // Parse description to link tablet P-numbers
                        $desc = $activity['description'];

                        // Handle single tablet link
                        if (isset($activity['tablet'])) {
                            $pNumber = $activity['tablet'];
                            $desc = str_replace($pNumber,
                                '<a href="/tablets/detail.php?p=' . urlencode($pNumber) . '" class="activity-tablet-link">' . htmlspecialchars($pNumber) . '</a>',
                                $desc
                            );
                        }

                        // Handle multiple tablet links (for joins)
                        if (isset($activity['tablets'])) {
                            foreach ($activity['tablets'] as $pNumber) {
                                $desc = str_replace($pNumber,
                                    '<a href="/tablets/detail.php?p=' . urlencode($pNumber) . '" class="activity-tablet-link">' . htmlspecialchars($pNumber) . '</a>',
                                    $desc
                                );
                            }
                        }

                        echo $desc;
                        ?>
                    </p>
                    <time class="activity-timestamp" datetime="<?= $activity['timestamp'] ?>">
                        <?= htmlspecialchars($activity['timestamp']) ?>
                    </time>
                </div>

                <?php if (isset($activity['detail']) && $activity['detail']): ?>
                <p class="activity-detail">
                    <?= htmlspecialchars($activity['detail']) ?>
                </p>
                <?php endif; ?>
            </div>
        </article>
        <?php endforeach; ?>
    </div>

    <div class="activity-feed-footer">
        <?php if ($showExample): ?>
        <button class="btn btn--ghost" disabled aria-disabled="true">
            View All Activity (Coming Soon)
        </button>
        <?php else: ?>
        <a href="/activity/" class="btn btn--primary">
            View All Activity →
        </a>
        <?php endif; ?>
    </div>
    <?php endif; ?>
</section>
