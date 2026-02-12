/**
 * Filter sidebar interactions for tablet list page
 */

document.addEventListener('DOMContentLoaded', () => {
    initFilterSections();
    initFilterGroups();
    initCheckboxNavigation();
    initShowMoreButtons();
    initPipelineRadios();
    initChevronFilter();
    initStageFilter();
});

/**
 * Initialize expand/collapse for main filter sections
 */
function initFilterSections() {
    const sectionHeaders = document.querySelectorAll('.filter-section-header');

    sectionHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const section = header.closest('.filter-section');
            const content = section.querySelector('.filter-content');
            const toggle = header.querySelector('.filter-toggle');
            const isExpanded = header.getAttribute('aria-expanded') === 'true';

            header.setAttribute('aria-expanded', !isExpanded);
            toggle.textContent = isExpanded ? '+' : '−';

            if (isExpanded) {
                content.setAttribute('hidden', '');
            } else {
                content.removeAttribute('hidden');
            }
        });
    });
}

/**
 * Initialize expand/collapse for filter groups within sections
 */
function initFilterGroups() {
    const groupHeaders = document.querySelectorAll('.filter-group-header');

    groupHeaders.forEach(header => {
        header.addEventListener('click', () => {
            const group = header.closest('.filter-group');
            const isExpanded = group.getAttribute('data-expanded') === 'true';

            // Toggle this group
            group.setAttribute('data-expanded', !isExpanded);

            // Update toggle indicator
            const toggle = header.querySelector('.group-toggle');
            toggle.textContent = isExpanded ? '+' : '−';

            header.setAttribute('aria-expanded', !isExpanded);
        });
    });

    // Auto-expand groups that have selected items
    document.querySelectorAll('.filter-group').forEach(group => {
        const hasChecked = group.querySelector('input:checked');
        if (hasChecked) {
            group.setAttribute('data-expanded', 'true');
            const toggle = group.querySelector('.group-toggle');
            if (toggle) toggle.textContent = '−';
            const header = group.querySelector('.filter-group-header');
            if (header) header.setAttribute('aria-expanded', 'true');

            // Also expand the parent section
            const section = group.closest('.filter-section');
            if (section) {
                const sectionHeader = section.querySelector('.filter-section-header');
                const sectionContent = section.querySelector('.filter-content');
                const sectionToggle = sectionHeader?.querySelector('.filter-toggle');

                if (sectionHeader && sectionContent) {
                    sectionHeader.setAttribute('aria-expanded', 'true');
                    sectionContent.removeAttribute('hidden');
                    if (sectionToggle) sectionToggle.textContent = '−';
                }
            }
        }
    });
}

/**
 * Handle checkbox changes to navigate with URL
 */
function initCheckboxNavigation() {
    const checkboxes = document.querySelectorAll('.filter-option input[type="checkbox"]');

    checkboxes.forEach(checkbox => {
        checkbox.addEventListener('change', () => {
            const url = checkbox.checked
                ? checkbox.dataset.urlAdd
                : checkbox.dataset.urlRemove;

            if (url) {
                window.location.href = url;
            }
        });
    });
}

/**
 * Initialize "Show more" buttons for long lists
 */
function initShowMoreButtons() {
    const showMoreButtons = document.querySelectorAll('.show-more');

    showMoreButtons.forEach(button => {
        button.addEventListener('click', () => {
            const moreItems = button.nextElementSibling;
            if (moreItems && moreItems.classList.contains('more-items')) {
                moreItems.removeAttribute('hidden');
                button.style.display = 'none';
            }
        });
    });
}

/**
 * Handle pipeline radio buttons
 */
function initPipelineRadios() {
    const radios = document.querySelectorAll('input[name="pipeline"]');

    radios.forEach(radio => {
        radio.addEventListener('change', () => {
            // Build URL with current filters, replacing pipeline value
            const params = new URLSearchParams(window.location.search);
            params.delete('page'); // Reset to page 1

            if (radio.value) {
                params.set('pipeline', radio.value);
            } else {
                params.delete('pipeline');
            }

            window.location.href = '?' + params.toString();
        });
    });
}

/**
 * Initialize stage filter pill interactions
 */
function initStageFilter() {
    const pills = document.querySelectorAll('.stage-filter__pill');
    if (pills.length === 0) return;

    pills.forEach(pill => {
        pill.addEventListener('keydown', (e) => {
            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                e.preventDefault();
                const all = Array.from(pills);
                const i = all.indexOf(pill);
                const next = e.key === 'ArrowRight'
                    ? (i + 1) % all.length
                    : (i - 1 + all.length) % all.length;
                all[next].focus();
            }
        });
    });
}

/**
 * Initialize chevron filter interactions
 * Generic function for horizontal chevron-style filters
 * Works with chevron-filter.php component
 */
function initChevronFilter() {
    const filterSteps = document.querySelectorAll('.chevron-filter__step');

    if (filterSteps.length === 0) {
        return; // No chevron filter on this page
    }

    filterSteps.forEach(step => {
        // Add keyboard navigation support
        step.addEventListener('keydown', (e) => {
            if (e.key === 'Enter' || e.key === ' ') {
                e.preventDefault();
                window.location.href = step.href;
            }

            // Arrow key navigation
            if (e.key === 'ArrowRight' || e.key === 'ArrowLeft') {
                e.preventDefault();
                const steps = Array.from(filterSteps);
                const currentIndex = steps.indexOf(step);

                let nextIndex;
                if (e.key === 'ArrowRight') {
                    nextIndex = (currentIndex + 1) % steps.length;
                } else {
                    nextIndex = (currentIndex - 1 + steps.length) % steps.length;
                }

                steps[nextIndex].focus();
            }
        });

        // Add visual feedback on click
        step.addEventListener('click', (e) => {
            step.style.transform = 'scale(0.98)';
            setTimeout(() => {
                step.style.transform = '';
            }, 150);
        });
    });
}
