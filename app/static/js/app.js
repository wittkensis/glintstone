/**
 * Glintstone v2 - Shared behaviors
 */

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
