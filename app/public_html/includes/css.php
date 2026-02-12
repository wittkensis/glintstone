<?php
/**
 * CSS Loading System
 *
 * WordPress-style enqueue system for CSS bundles with dependency resolution.
 *
 * Usage:
 *   // In page files before header.php
 *   require_once __DIR__ . '/includes/css.php';
 *   CSSLoader::enqueue('page-tablets');
 *
 *   // In header.php
 *   CSSLoader::render();
 */

class CSSLoader {
    /** @var array Registered CSS bundles */
    private static array $registered = [];

    /** @var array Enqueued bundle handles */
    private static array $enqueued = [];

    /** @var bool Whether bundles have been initialized */
    private static bool $initialized = false;

    /**
     * Register a CSS bundle
     *
     * @param string $handle Unique identifier for the bundle
     * @param string $path   Path to the CSS file (relative to web root)
     * @param array  $deps   Array of handles this bundle depends on
     */
    public static function register(string $handle, string $path, array $deps = []): void {
        self::$registered[$handle] = [
            'path' => $path,
            'deps' => $deps
        ];
    }

    /**
     * Enqueue a CSS bundle for output
     *
     * @param string $handle Bundle handle to enqueue
     */
    public static function enqueue(string $handle): void {
        self::init();

        if (!isset(self::$registered[$handle])) {
            error_log("CSSLoader: Unknown bundle '{$handle}'");
            return;
        }

        if (!in_array($handle, self::$enqueued)) {
            self::$enqueued[] = $handle;
        }
    }

    /**
     * Render all enqueued CSS as link tags
     * Called in header.php
     */
    public static function render(): void {
        self::init();

        // Always enqueue core bundles
        $required = ['fonts', 'core', 'components', 'layout'];
        foreach ($required as $handle) {
            if (!in_array($handle, self::$enqueued)) {
                array_unshift(self::$enqueued, $handle);
            }
        }

        $ordered = self::resolveDependencies();
        $rendered = [];

        foreach ($ordered as $handle) {
            if (in_array($handle, $rendered)) continue;
            if (!isset(self::$registered[$handle])) continue;

            $bundle = self::$registered[$handle];

            // Handle fonts specially (preconnect + font URL)
            if ($handle === 'fonts') {
                echo "    <link rel=\"preconnect\" href=\"https://fonts.googleapis.com\">\n";
                echo "    <link rel=\"preconnect\" href=\"https://fonts.gstatic.com\" crossorigin>\n";
                echo "    <link href=\"{$bundle['path']}\" rel=\"stylesheet\">\n";
            } else {
                echo "    <link rel=\"stylesheet\" href=\"{$bundle['path']}\">\n";
            }

            $rendered[] = $handle;
        }
    }

    /**
     * Get list of enqueued handles (for debugging)
     */
    public static function getEnqueued(): array {
        return self::$enqueued;
    }

    /**
     * Initialize and register all CSS bundles
     */
    private static function init(): void {
        if (self::$initialized) return;
        self::$initialized = true;

        // =================================================================
        // FONTS
        // =================================================================
        self::register('fonts',
            'https://fonts.googleapis.com/css2?family=Noto+Sans+Cuneiform&family=Playfair+Display:wght@400;500;600;700&display=swap'
        );

        // =================================================================
        // CORE (foundation styles)
        // =================================================================
        self::register('core', '/assets/css/core/index.css');

        // =================================================================
        // LAYOUT (structural)
        // =================================================================
        self::register('layout', '/assets/css/layout/index.css', ['core']);

        // =================================================================
        // COMPONENTS (reusable UI)
        // =================================================================
        self::register('components', '/assets/css/components/index.css', ['core']);

        // =================================================================
        // PAGE BUNDLES
        // =================================================================

        // Home page
        self::register('page-home', '/assets/css/page-home/index.css', ['components', 'layout']);

        // Tablets section
        self::register('page-tablets', '/assets/css/page-tablets/index.css', ['components', 'layout']);

        // Dictionary section
        self::register('page-dictionary', '/assets/css/page-dictionary/index.css', ['components', 'layout']);

        // Signs section
        self::register('page-signs', '/assets/css/page-signs/index.css', ['components', 'layout']);

        // Collections section
        self::register('page-collections', '/assets/css/page-collections/index.css', ['components', 'layout']);
    }

    /**
     * Resolve dependencies and return ordered list of handles
     */
    private static function resolveDependencies(): array {
        $resolved = [];
        $seen = [];

        foreach (self::$enqueued as $handle) {
            self::resolve($handle, $resolved, $seen);
        }

        return $resolved;
    }

    /**
     * Recursively resolve dependencies for a handle
     */
    private static function resolve(string $handle, array &$resolved, array &$seen): void {
        if (in_array($handle, $resolved)) return;
        if (in_array($handle, $seen)) {
            error_log("CSSLoader: Circular dependency detected for '{$handle}'");
            return;
        }

        $seen[] = $handle;

        if (isset(self::$registered[$handle])) {
            foreach (self::$registered[$handle]['deps'] as $dep) {
                self::resolve($dep, $resolved, $seen);
            }
        }

        $resolved[] = $handle;
    }
}
