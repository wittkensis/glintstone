/**
 * Composites Table
 * Sortable, filterable table with row navigation
 */

class CompositesTable {
    constructor(tableElement) {
        this.table = tableElement;
        if (!this.table) return;

        this.tbody = this.table.querySelector('tbody');
        this.rows = Array.from(this.tbody.querySelectorAll('.composite-row'));
        this.searchInput = document.getElementById('composite-search');
        this.countDisplay = document.querySelector('.table-count');

        this.currentSort = {
            column: 'q_number',
            direction: 'asc'
        };

        this.init();
    }

    init() {
        this.bindSortHeaders();
        this.bindSearch();
        this.bindRowClicks();
        this.updateCount();
    }

    /**
     * Bind click handlers to sortable column headers
     */
    bindSortHeaders() {
        const sortableHeaders = this.table.querySelectorAll('th.sortable');

        sortableHeaders.forEach(header => {
            header.addEventListener('click', () => {
                const column = header.dataset.sort;
                this.sortBy(column);
            });
        });
    }

    /**
     * Sort table by column
     * @param {string} column - Column identifier to sort by
     */
    sortBy(column) {
        // Toggle direction if same column, otherwise default to ascending
        if (this.currentSort.column === column) {
            this.currentSort.direction = this.currentSort.direction === 'asc' ? 'desc' : 'asc';
        } else {
            this.currentSort.column = column;
            this.currentSort.direction = 'asc';
        }

        // Update header indicators
        this.updateSortIndicators();

        // Sort rows
        this.rows.sort((a, b) => {
            const aValue = this.getCellValue(a, column);
            const bValue = this.getCellValue(b, column);

            // Handle numeric sorting for exemplar_count
            if (column === 'exemplar_count') {
                const aNum = parseInt(aValue) || 0;
                const bNum = parseInt(bValue) || 0;
                return this.currentSort.direction === 'asc' ? aNum - bNum : bNum - aNum;
            }

            // String sorting (case-insensitive)
            const comparison = aValue.localeCompare(bValue, undefined, { numeric: true });
            return this.currentSort.direction === 'asc' ? comparison : -comparison;
        });

        // Re-render rows
        this.rows.forEach(row => this.tbody.appendChild(row));
    }

    /**
     * Get cell value for sorting
     * @param {HTMLElement} row - Table row element
     * @param {string} column - Column identifier
     * @returns {string} Cell text content
     */
    getCellValue(row, column) {
        const cell = row.querySelector(`.${column}`);
        return cell ? cell.textContent.trim() : '';
    }

    /**
     * Update visual sort indicators on headers
     */
    updateSortIndicators() {
        // Remove all sort classes
        this.table.querySelectorAll('th.sortable').forEach(header => {
            header.classList.remove('sorted-asc', 'sorted-desc');
        });

        // Add class to current sort column
        const currentHeader = this.table.querySelector(`th[data-sort="${this.currentSort.column}"]`);
        if (currentHeader) {
            currentHeader.classList.add(`sorted-${this.currentSort.direction}`);
        }
    }

    /**
     * Bind search input for live filtering
     */
    bindSearch() {
        if (!this.searchInput) return;

        let debounceTimer;

        this.searchInput.addEventListener('input', (e) => {
            clearTimeout(debounceTimer);

            debounceTimer = setTimeout(() => {
                this.filter(e.target.value);
            }, 150); // Debounce delay in ms
        });
    }

    /**
     * Filter table rows by search term
     * @param {string} searchTerm - Search query
     */
    filter(searchTerm) {
        const term = searchTerm.toLowerCase().trim();

        let visibleCount = 0;

        this.rows.forEach(row => {
            // Search in Q-number and Designation
            const qNumber = row.querySelector('.q-number')?.textContent.toLowerCase() || '';
            const designation = row.querySelector('.designation')?.textContent.toLowerCase() || '';

            const matches = qNumber.includes(term) || designation.includes(term);

            if (matches || term === '') {
                row.classList.remove('hidden');
                visibleCount++;
            } else {
                row.classList.add('hidden');
            }
        });

        this.updateCount(visibleCount);
    }

    /**
     * Update count display
     * @param {number|null} visibleCount - Number of visible rows (null = all rows)
     */
    updateCount(visibleCount = null) {
        if (!this.countDisplay) return;

        const count = visibleCount !== null ? visibleCount : this.rows.length;
        this.countDisplay.textContent = `Showing ${count} composite${count !== 1 ? 's' : ''}`;
    }

    /**
     * Bind click handlers to table rows for navigation
     */
    bindRowClicks() {
        this.rows.forEach(row => {
            const href = row.dataset.href;
            if (!href) return;

            row.addEventListener('click', (e) => {
                // Allow middle-click to open in new tab
                if (e.button === 1 || e.ctrlKey || e.metaKey) {
                    window.open(href, '_blank');
                } else {
                    window.location.href = href;
                }
            });

            // Change cursor to indicate clickability
            row.style.cursor = 'pointer';
        });
    }
}

// Initialize when DOM is ready
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        const table = document.querySelector('.composites-table');
        if (table) {
            new CompositesTable(table);
        }
    });
} else {
    const table = document.querySelector('.composites-table');
    if (table) {
        new CompositesTable(table);
    }
}
