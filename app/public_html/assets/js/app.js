/**
 * Glintstone - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sign popups
    initSignPopups();

    // Initialize dictionary lookups
    initDictionaryLookups();
});

/**
 * Sign popup functionality
 */
function initSignPopups() {
    // TODO: Implement click-to-show sign details
    document.querySelectorAll('.cuneiform').forEach(function(el) {
        el.addEventListener('click', function(e) {
            const sign = e.target.textContent;
            showSignPopup(sign, e.clientX, e.clientY);
        });
    });
}

/**
 * Show sign popup
 */
function showSignPopup(sign, x, y) {
    // TODO: Fetch sign data from API and display popup
    console.log('Sign clicked:', sign);
}

/**
 * Dictionary lookup functionality
 */
function initDictionaryLookups() {
    // TODO: Implement word click-to-lookup
}

/**
 * API helper
 */
async function fetchAPI(endpoint) {
    const response = await fetch('/api/' + endpoint);
    if (!response.ok) {
        throw new Error('API error: ' + response.status);
    }
    return response.json();
}
