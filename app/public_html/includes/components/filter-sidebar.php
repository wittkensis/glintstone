<?php
/**
 * Filter Sidebar Component
 * Reusable hierarchical filter sidebar
 *
 * Required variables:
 * @var array $languageStats - Language filter statistics
 * @var array $periodStats - Period filter statistics
 * @var array $provenienceStats - Provenience filter statistics
 * @var array $genreStats - Genre filter statistics
 * @var array $activeFilters - Current active filters
 * @var string|null $pipeline - Current pipeline filter value
 *
 * Optional variables:
 * @var string $clearAllUrl - URL for "Clear all" link (default: current page without query params)
 */

// Set defaults
$clearAllUrl = $clearAllUrl ?? $_SERVER['PHP_SELF'];
?>
<aside class="filter-sidebar">
    <div class="filter-header">
        <h2>Filters</h2>
        <?php if (!empty($activeFilters)): ?>
        <a href="<?= htmlspecialchars($clearAllUrl) ?>" class="clear-all">Clear all</a>
        <?php endif; ?>
    </div>

    <!-- Language Filter -->
    <div class="filter-section" data-filter="language">
        <button class="filter-section-header" aria-expanded="true">
            <span class="filter-title">Language</span>
            <span class="filter-toggle">−</span>
        </button>
        <div class="filter-content">
            <?php foreach ($languageStats as $group): ?>
            <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                <button class="filter-group-header" aria-expanded="false">
                    <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                    <span class="group-count"><?= number_format($group['total']) ?></span>
                    <span class="group-toggle">+</span>
                </button>
                <div class="filter-group-content">
                    <?php foreach ($group['items'] as $item): ?>
                    <label class="filter-option">
                        <input type="checkbox"
                               name="lang[]"
                               value="<?= htmlspecialchars($item['value']) ?>"
                               <?= isFilterActive('lang', $item['value']) ? 'checked' : '' ?>
                               data-url-add="<?= htmlspecialchars(buildFilterUrl(['lang' => $item['value']])) ?>"
                               data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['lang' => $item['value']])) ?>">
                        <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                        <span class="option-count"><?= number_format($item['count']) ?></span>
                    </label>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Period Filter -->
    <div class="filter-section" data-filter="period">
        <button class="filter-section-header" aria-expanded="false">
            <span class="filter-title">Period</span>
            <span class="filter-toggle">+</span>
        </button>
        <div class="filter-content" hidden>
            <?php foreach ($periodStats as $group): ?>
            <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                <button class="filter-group-header" aria-expanded="false">
                    <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                    <span class="group-count"><?= number_format($group['total']) ?></span>
                    <span class="group-toggle">+</span>
                </button>
                <div class="filter-group-content">
                    <?php foreach ($group['items'] as $item): ?>
                    <label class="filter-option">
                        <input type="checkbox"
                               name="period[]"
                               value="<?= htmlspecialchars($item['value']) ?>"
                               <?= isFilterActive('period', $item['value']) ? 'checked' : '' ?>
                               data-url-add="<?= htmlspecialchars(buildFilterUrl(['period' => $item['value']])) ?>"
                               data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['period' => $item['value']])) ?>">
                        <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                        <span class="option-count"><?= number_format($item['count']) ?></span>
                    </label>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Provenience/Site Filter -->
    <div class="filter-section" data-filter="site">
        <button class="filter-section-header" aria-expanded="false">
            <span class="filter-title">Discovery Site</span>
            <span class="filter-toggle">+</span>
        </button>
        <div class="filter-content" hidden>
            <?php foreach ($provenienceStats as $group): ?>
            <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                <button class="filter-group-header" aria-expanded="false">
                    <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                    <span class="group-count"><?= number_format($group['total']) ?></span>
                    <span class="group-toggle">+</span>
                </button>
                <div class="filter-group-content">
                    <?php foreach (array_slice($group['items'], 0, 20) as $item): ?>
                    <label class="filter-option">
                        <input type="checkbox"
                               name="site[]"
                               value="<?= htmlspecialchars($item['value']) ?>"
                               <?= isFilterActive('site', $item['value']) ? 'checked' : '' ?>
                               data-url-add="<?= htmlspecialchars(buildFilterUrl(['site' => $item['value']])) ?>"
                               data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['site' => $item['value']])) ?>">
                        <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                        <span class="option-count"><?= number_format($item['count']) ?></span>
                    </label>
                    <?php endforeach; ?>
                    <?php if (count($group['items']) > 20): ?>
                    <button class="show-more" data-group="<?= htmlspecialchars($group['group']) ?>">
                        Show <?= count($group['items']) - 20 ?> more...
                    </button>
                    <div class="more-items" hidden>
                        <?php foreach (array_slice($group['items'], 20) as $item): ?>
                        <label class="filter-option">
                            <input type="checkbox"
                                   name="site[]"
                                   value="<?= htmlspecialchars($item['value']) ?>"
                                   <?= isFilterActive('site', $item['value']) ? 'checked' : '' ?>
                                   data-url-add="<?= htmlspecialchars(buildFilterUrl(['site' => $item['value']])) ?>"
                                   data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['site' => $item['value']])) ?>">
                            <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                            <span class="option-count"><?= number_format($item['count']) ?></span>
                        </label>
                        <?php endforeach; ?>
                    </div>
                    <?php endif; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Genre Filter -->
    <div class="filter-section" data-filter="genre">
        <button class="filter-section-header" aria-expanded="false">
            <span class="filter-title">Genre</span>
            <span class="filter-toggle">+</span>
        </button>
        <div class="filter-content" hidden>
            <?php foreach ($genreStats as $group): ?>
            <div class="filter-group" data-group="<?= htmlspecialchars($group['group']) ?>">
                <button class="filter-group-header" aria-expanded="false">
                    <span class="group-name"><?= htmlspecialchars($group['group']) ?></span>
                    <span class="group-count"><?= number_format($group['total']) ?></span>
                    <span class="group-toggle">+</span>
                </button>
                <div class="filter-group-content">
                    <?php foreach ($group['items'] as $item): ?>
                    <label class="filter-option">
                        <input type="checkbox"
                               name="genre[]"
                               value="<?= htmlspecialchars($item['value']) ?>"
                               <?= isFilterActive('genre', $item['value']) ? 'checked' : '' ?>
                               data-url-add="<?= htmlspecialchars(buildFilterUrl(['genre' => $item['value']])) ?>"
                               data-url-remove="<?= htmlspecialchars(buildFilterUrl([], ['genre' => $item['value']])) ?>">
                        <span class="option-label"><?= htmlspecialchars($item['value']) ?></span>
                        <span class="option-count"><?= number_format($item['count']) ?></span>
                    </label>
                    <?php endforeach; ?>
                </div>
            </div>
            <?php endforeach; ?>
        </div>
    </div>

    <!-- Pipeline Status Filter -->
    <div class="filter-section" data-filter="pipeline">
        <button class="filter-section-header" aria-expanded="false">
            <span class="filter-title">Data Status</span>
            <span class="filter-toggle">+</span>
        </button>
        <div class="filter-content" hidden>
            <div class="filter-group-content" style="display: block;">
                <label class="filter-option">
                    <input type="radio" name="pipeline" value="" <?= !$pipeline ? 'checked' : '' ?>>
                    <span class="option-label">All</span>
                </label>
                <label class="filter-option">
                    <input type="radio" name="pipeline" value="complete" <?= $pipeline === 'complete' ? 'checked' : '' ?>>
                    <span class="option-label">Complete (all data)</span>
                </label>
                <label class="filter-option">
                    <input type="radio" name="pipeline" value="has_image" <?= $pipeline === 'has_image' ? 'checked' : '' ?>>
                    <span class="option-label">Has Image</span>
                </label>
                <label class="filter-option">
                    <input type="radio" name="pipeline" value="has_translation" <?= $pipeline === 'has_translation' ? 'checked' : '' ?>>
                    <span class="option-label">Has Translation</span>
                </label>

                <div class="filter-subsection">
                    <span class="subsection-label">Text Digitization</span>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="any_digitization" <?= $pipeline === 'any_digitization' ? 'checked' : '' ?>>
                        <span class="option-label">Any Digitization</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="human_transcription" <?= $pipeline === 'human_transcription' ? 'checked' : '' ?>>
                        <span class="option-label">Human Transcription (ATF)</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="machine_ocr" <?= $pipeline === 'machine_ocr' ? 'checked' : '' ?>>
                        <span class="option-label">Machine OCR (Sign Detection)</span>
                    </label>
                    <label class="filter-option">
                        <input type="radio" name="pipeline" value="no_digitization" <?= $pipeline === 'no_digitization' ? 'checked' : '' ?>>
                        <span class="option-label">No Digitization</span>
                    </label>
                </div>
            </div>
        </div>
    </div>
</aside>
