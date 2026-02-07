/**
 * Tablet Browser Selection JavaScript
 * Handles multi-select functionality for adding tablets to collections
 */

(function() {
    'use strict';

    // Track selected tablets
    let selectedTablets = new Set();

    // Initialize on page load
    document.addEventListener('DOMContentLoaded', function() {
        initCheckboxHandlers();
        initSelectAllButton();
        initClearSelectionButton();
        initCardClickHandlers();
        updateUI();
    });

    /**
     * Initialize checkbox change handlers
     */
    function initCheckboxHandlers() {
        const checkboxes = document.querySelectorAll('.card-checkbox');

        checkboxes.forEach(checkbox => {
            checkbox.addEventListener('change', function(e) {
                e.stopPropagation();
                handleCheckboxChange(this);
            });
        });
    }

    /**
     * Initialize card click handlers (clicking card selects it)
     */
    function initCardClickHandlers() {
        const cards = document.querySelectorAll('.tablet-card.selectable');

        cards.forEach(card => {
            card.addEventListener('click', function(e) {
                // Don't toggle if clicking the checkbox wrapper or link behavior
                if (e.target.closest('.card-checkbox-wrapper') || e.target.tagName === 'A') {
                    e.preventDefault();
                    return;
                }

                // Prevent navigation
                e.preventDefault();

                // Toggle the checkbox
                const checkbox = this.querySelector('.card-checkbox');
                if (checkbox) {
                    checkbox.checked = !checkbox.checked;
                    handleCheckboxChange(checkbox);
                }
            });
        });
    }

    /**
     * Handle checkbox state change
     */
    function handleCheckboxChange(checkbox) {
        const pNumber = checkbox.value;
        const card = checkbox.closest('.tablet-card');

        if (checkbox.checked) {
            selectedTablets.add(pNumber);
            card.classList.add('selected');
        } else {
            selectedTablets.delete(pNumber);
            card.classList.remove('selected');
        }

        updateUI();
    }

    /**
     * Initialize "Select All" button
     */
    function initSelectAllButton() {
        const selectAllBtn = document.getElementById('select-all');

        if (selectAllBtn) {
            selectAllBtn.addEventListener('click', function() {
                const checkboxes = document.querySelectorAll('.card-checkbox');

                checkboxes.forEach(checkbox => {
                    if (!checkbox.checked) {
                        checkbox.checked = true;
                        handleCheckboxChange(checkbox);
                    }
                });
            });
        }
    }

    /**
     * Initialize "Clear Selection" button
     */
    function initClearSelectionButton() {
        const clearBtn = document.getElementById('clear-selection');

        if (clearBtn) {
            clearBtn.addEventListener('click', function() {
                const checkboxes = document.querySelectorAll('.card-checkbox');

                checkboxes.forEach(checkbox => {
                    if (checkbox.checked) {
                        checkbox.checked = false;
                        handleCheckboxChange(checkbox);
                    }
                });
            });
        }
    }

    /**
     * Update UI elements based on selection
     */
    function updateUI() {
        const count = selectedTablets.size;

        // Update selection count displays
        const selectionCount = document.querySelector('.selection-count');
        if (selectionCount) {
            selectionCount.textContent = `${count} selected`;
        }

        const bulkCount = document.getElementById('bulk-count');
        if (bulkCount) {
            bulkCount.textContent = count;
        }

        // Enable/disable submit button
        const submitBtn = document.getElementById('add-to-collection-btn');
        if (submitBtn) {
            submitBtn.disabled = count === 0;
        }
    }

    /**
     * Form submission handling
     * The form already has hidden inputs for checked checkboxes (name="p_numbers[]")
     * so we just need to ensure the form submits correctly
     */
    const form = document.getElementById('add-tablets-form');
    if (form) {
        form.addEventListener('submit', function(e) {
            if (selectedTablets.size === 0) {
                e.preventDefault();
                alert('Please select at least one tablet to add.');
                return false;
            }
            // Form will submit normally with all checked checkboxes
            return true;
        });
    }

})();
