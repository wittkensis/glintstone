/**
 * Glintstone v2 - Shared behaviors
 */

// TODO: @wittkensis note: Should this be part of the Python framework instead of frontend?

document.addEventListener('DOMContentLoaded', function() {
    // Active nav link highlighting (supplement CSS-based approach)
    const currentPath = window.location.pathname;
    document.querySelectorAll('.nav-link').forEach(link => {
        const href = link.getAttribute('href');
        if (href && currentPath.startsWith(href) && href !== '/') {
            link.classList.add('active');
        }
    });
});
