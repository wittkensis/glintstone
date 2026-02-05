/**
 * Glintstone - Main JavaScript
 */

document.addEventListener('DOMContentLoaded', function() {
    // Initialize sign popups
    initSignPopups();

    // Initialize dictionary lookups
    initDictionaryLookups();

    // Initialize ATF click handlers
    initATFInteraction();

    // Create popup container
    createPopupContainer();
});

/**
 * Create the popup container element
 */
function createPopupContainer() {
    if (document.getElementById('glintstone-popup')) return;

    const popup = document.createElement('div');
    popup.id = 'glintstone-popup';
    popup.className = 'popup hidden';
    popup.innerHTML = `
        <div class="popup-header">
            <span class="popup-title"></span>
            <button class="popup-close">&times;</button>
        </div>
        <div class="popup-content"></div>
    `;
    document.body.appendChild(popup);

    // Close button handler
    popup.querySelector('.popup-close').addEventListener('click', hidePopup);

    // Close on outside click
    document.addEventListener('click', function(e) {
        if (!popup.contains(e.target) && !e.target.closest('.cuneiform, .atf-word')) {
            hidePopup();
        }
    });

    // Close on escape key
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Escape') hidePopup();
    });
}

/**
 * Sign popup functionality
 */
function initSignPopups() {
    document.querySelectorAll('.cuneiform').forEach(function(el) {
        el.style.cursor = 'pointer';
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            const sign = e.target.textContent.trim();
            if (sign) {
                showSignPopup(sign, e.clientX, e.clientY);
            }
        });
    });
}

/**
 * Show sign popup
 */
async function showSignPopup(sign, x, y) {
    showPopup('Loading...', '', x, y);

    try {
        const response = await fetch('/api/sign.php?q=' + encodeURIComponent(sign));
        const data = await response.json();

        if (data.error) {
            showPopup('Sign Not Found', `<p class="popup-error">No data available for "${sign}"</p>`, x, y);
            return;
        }

        const content = `
            <div class="sign-info">
                <div class="sign-display">${data.utf8 || sign}</div>
                <dl class="sign-details">
                    <dt>Sign ID</dt>
                    <dd>${data.sign_id || 'Unknown'}</dd>
                    ${data.unicode_hex ? `<dt>Unicode</dt><dd>U+${data.unicode_hex.replace('x', '').toUpperCase()}</dd>` : ''}
                    ${data.uname ? `<dt>Name</dt><dd>${data.uname}</dd>` : ''}
                </dl>
                ${data.values && data.values.length > 0 ? `
                    <div class="sign-values">
                        <strong>Values:</strong>
                        <span class="value-list">${data.values.join(', ')}</span>
                    </div>
                ` : ''}
            </div>
        `;

        showPopup(data.sign_id || sign, content, x, y);
    } catch (err) {
        console.error('Sign lookup error:', err);
        showPopup('Error', '<p class="popup-error">Failed to load sign data</p>', x, y);
    }
}

/**
 * Dictionary lookup functionality
 */
function initDictionaryLookups() {
    // Enable dictionary lookups on marked elements
    document.querySelectorAll('.dict-lookup, [data-lookup]').forEach(function(el) {
        el.style.cursor = 'pointer';
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            const word = el.dataset.lookup || el.textContent.trim();
            if (word) {
                showDictionaryPopup(word, e.clientX, e.clientY);
            }
        });
    });
}

/**
 * Show dictionary popup
 */
async function showDictionaryPopup(word, x, y) {
    showPopup('Loading...', '', x, y);

    try {
        const response = await fetch('/api/glossary.php?q=' + encodeURIComponent(word));
        const data = await response.json();

        if (!data.entries || data.entries.length === 0) {
            showPopup('Not Found', `<p class="popup-error">No glossary entries found for "${word}"</p>`, x, y);
            return;
        }

        let content = '<div class="glossary-results">';
        data.entries.forEach(entry => {
            content += `
                <div class="glossary-entry">
                    <div class="entry-head">
                        <strong>${entry.headword || entry.citation_form}</strong>
                        ${entry.pos ? `<span class="pos">${entry.pos}</span>` : ''}
                        <span class="lang">${entry.language}</span>
                    </div>
                    ${entry.guide_word ? `<div class="guide-word">"${entry.guide_word}"</div>` : ''}
                    ${entry.icount ? `<div class="occurrence-count">${entry.icount} occurrences</div>` : ''}
                </div>
            `;
        });
        content += '</div>';

        showPopup(`Dictionary: ${word}`, content, x, y);
    } catch (err) {
        console.error('Dictionary lookup error:', err);
        showPopup('Error', '<p class="popup-error">Failed to load dictionary data</p>', x, y);
    }
}

/**
 * Initialize ATF interaction - make words clickable
 */
function initATFInteraction() {
    const atfDisplay = document.querySelector('.atf-display');
    if (!atfDisplay) return;

    // Process ATF content to wrap words in spans
    const lines = atfDisplay.innerHTML.split('\n');
    const processedLines = lines.map(line => {
        // Skip directive lines
        if (line.includes('class="directive"') || line.includes('class="composite-ref"')) {
            return line;
        }

        // Skip empty lines
        const trimmed = line.trim();
        if (!trimmed || /^[\d.]+\.?\s*$/.test(trimmed)) {
            return line;
        }

        // Extract line number if present (e.g., "1. ")
        const lineNumMatch = line.match(/^(\d+\.\s*)/);
        const lineNum = lineNumMatch ? lineNumMatch[1] : '';
        const content = lineNumMatch ? line.slice(lineNum.length) : line;

        // Split into words and wrap each
        const words = content.split(/(\s+)/);
        const wrappedWords = words.map(word => {
            // Skip whitespace and special chars
            if (/^\s*$/.test(word) || /^[,.\-\[\](){}#$@&]$/.test(word)) {
                return word;
            }
            // Skip if already wrapped
            if (word.includes('<span')) {
                return word;
            }
            // Wrap word for lookup
            const cleanWord = word.replace(/[#?\[\]<>()]/g, '');
            if (cleanWord.length > 0) {
                return `<span class="atf-word" data-lookup="${cleanWord}">${word}</span>`;
            }
            return word;
        });

        return lineNum + wrappedWords.join('');
    });

    atfDisplay.innerHTML = processedLines.join('\n');

    // Add click handlers to ATF words
    atfDisplay.querySelectorAll('.atf-word').forEach(el => {
        el.addEventListener('click', function(e) {
            e.stopPropagation();
            const word = el.dataset.lookup;
            if (word) {
                showDictionaryPopup(word, e.clientX, e.clientY);
            }
        });
    });
}

/**
 * Show popup at position
 */
function showPopup(title, content, x, y) {
    const popup = document.getElementById('glintstone-popup');
    if (!popup) return;

    popup.querySelector('.popup-title').textContent = title;
    popup.querySelector('.popup-content').innerHTML = content;

    // Position popup
    const padding = 20;
    const popupWidth = 320;
    const popupHeight = popup.offsetHeight || 200;

    let left = x + padding;
    let top = y + padding;

    // Keep on screen
    if (left + popupWidth > window.innerWidth) {
        left = x - popupWidth - padding;
    }
    if (top + popupHeight > window.innerHeight) {
        top = y - popupHeight - padding;
    }
    if (left < padding) left = padding;
    if (top < padding) top = padding;

    popup.style.left = left + 'px';
    popup.style.top = top + 'px';
    popup.classList.remove('hidden');
}

/**
 * Hide popup
 */
function hidePopup() {
    const popup = document.getElementById('glintstone-popup');
    if (popup) {
        popup.classList.add('hidden');
    }
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
