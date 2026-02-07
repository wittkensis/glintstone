<?php
/**
 * Icon System
 * Provides reusable SVG icons with consistent styling
 * Usage: icon('expand', 'Optional CSS classes')
 */

function icon($name, $classes = '') {
    $icons = [
        'expand' => '<path d="M12.9998 6L11.5898 7.41L16.1698 12L11.5898 16.59L12.9998 18L18.9998 12L12.9998 6Z"/><path d="M6.41 6L5 7.41L9.58 12L5 16.59L6.41 18L12.41 12L6.41 6Z"/>',
        'collapse' => '<path d="M11 18L12.41 16.59L7.83 12L12.41 7.41L11 6L5 12L11 18Z"/><path d="M17.5898 18L18.9998 16.59L14.4198 12L18.9998 7.41L17.5898 6L11.5898 12L17.5898 18Z"/>',
        'layers' => '<path d="M4 6H2V22H18V20H4V6ZM22 2H6V18H22V2ZM20 12L17.5 10.5L15 12V4H20V12Z"/>',
    ];

    if (!isset($icons[$name])) {
        return '';
    }

    $class = $classes ? ' class="' . htmlspecialchars($classes) . '"' : '';

    return sprintf(
        '<svg%s viewBox="0 0 24 24" fill="currentColor" xmlns="http://www.w3.org/2000/svg" aria-hidden="true">%s</svg>',
        $class,
        $icons[$name]
    );
}

/**
 * Icon button helper
 * Creates a button with an icon and accessible label
 * Usage: icon_button('expand', 'Expand view', 'btn-icon')
 */
function icon_button($icon_name, $label, $classes = '', $attributes = '') {
    $class = 'icon-btn' . ($classes ? ' ' . $classes : '');
    $attrs = $attributes ? ' ' . $attributes : '';

    return sprintf(
        '<button type="button" class="%s" aria-label="%s"%s>%s<span class="sr-only">%s</span></button>',
        htmlspecialchars($class),
        htmlspecialchars($label),
        $attrs,
        icon($icon_name),
        htmlspecialchars($label)
    );
}
