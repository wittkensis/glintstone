<?php
/**
 * Collection Card Component
 * Reusable card for displaying collection metadata with 2x2 thumbnail grid
 *
 * Required variables:
 * @var array $collection - Collection data with metadata and preview_tablets
 *   - collection_id (int)
 *   - name (string)
 *   - description (string|null)
 *   - tablet_count (int)
 *   - preview_tablets (array) - Array of up to 4 tablet objects
 *
 * Optional variables:
 * @var bool $selectable - Show checkbox for multi-select (default: false)
 */

// Set defaults
$selectable = $selectable ?? false;

// Set up card properties
$collectionId = $collection['collection_id'];
$href = "/collections/detail.php?id=" . $collectionId;
$cardClass = "card collection-card";

// Add selectable class if needed
if ($selectable) {
    $cardClass .= " selectable";
}
?>
<a href="<?= $href ?>" class="<?= $cardClass ?>" data-collection-id="<?= $collectionId ?>">

    <?php if ($selectable): ?>
    <label class="card-checkbox-wrapper" onclick="event.preventDefault(); event.stopPropagation();">
        <input type="checkbox"
               class="card-checkbox"
               name="collection_ids[]"
               value="<?= htmlspecialchars($collectionId) ?>"
               data-collection-id="<?= htmlspecialchars($collectionId) ?>">
    </label>
    <?php endif; ?>

    <!-- Collection Cover: Image or 2x2 Preview Grid -->
    <?php if (!empty($collection['image_path'])): ?>
        <!-- Single Collection Image -->
        <div class="collection-cover-image">
            <img src="<?= htmlspecialchars($collection['image_path']) ?>"
                 alt="<?= htmlspecialchars($collection['name']) ?>"
                 loading="lazy">
        </div>
    <?php else: ?>
        <!-- 2x2 Preview Grid -->
        <div class="card-image-grid collection-cover">
            <?php if (!empty($collection['preview_tablets'])): ?>
                <?php foreach ($collection['preview_tablets'] as $tablet): ?>
                    <div class="cover-thumb">
                        <img src="/api/thumbnail.php?p=<?= urlencode($tablet['p_number']) ?>&size=100"
                             alt="<?= htmlspecialchars($tablet['designation'] ?? $tablet['p_number']) ?>"
                             loading="lazy"
                             onerror="this.style.display='none'; this.nextElementSibling.style.display='flex';">
                        <div class="cover-thumb__fallback" style="display:none;">
                            <span class="cuneiform-icon">𒀭</span>
                        </div>
                    </div>
                <?php endforeach; ?>
                <?php
                // Fill empty slots if less than 4 tablets
                $emptySlots = 4 - count($collection['preview_tablets']);
                for ($i = 0; $i < $emptySlots; $i++):
                ?>
                    <div class="cover-thumb empty">
                        <span class="cuneiform-icon">𒀭</span>
                    </div>
                <?php endfor; ?>
            <?php else: ?>
                <!-- All empty if no tablets -->
                <?php for ($i = 0; $i < 4; $i++): ?>
                    <div class="cover-thumb empty">
                        <span class="cuneiform-icon">𒀭</span>
                    </div>
                <?php endfor; ?>
            <?php endif; ?>
        </div>
    <?php endif; ?>

    <!-- Collection Metadata -->
    <div class="card-details collection-meta">
        <h3 class="card-primary collection-name">
            <?= htmlspecialchars($collection['name']) ?>
        </h3>
        <?php if (!empty($collection['description'])): ?>
            <p class="card-meta collection-description">
                <?= htmlspecialchars(mb_substr($collection['description'], 0, 120)) ?>
                <?= mb_strlen($collection['description']) > 120 ? '...' : '' ?>
            </p>
        <?php endif; ?>
        <div class="card-meta collection-stats">
            <span class="stat">
                <?= number_format($collection['tablet_count']) ?>
                <?= $collection['tablet_count'] === 1 ? 'tablet' : 'tablets' ?>
            </span>
        </div>
    </div>
</a>
