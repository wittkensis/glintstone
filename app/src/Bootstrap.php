<?php
/**
 * Application Bootstrap
 * Initializes the application core and provides service container access
 */

declare(strict_types=1);

namespace Glintstone;

// Define base paths
define('APP_ROOT', dirname(__DIR__));
define('SRC_ROOT', __DIR__);
define('PUBLIC_ROOT', APP_ROOT . '/public_html');
define('CACHE_ROOT', APP_ROOT . '/cache');
define('DB_PATH', dirname(APP_ROOT) . '/database/glintstone.db');

// Autoloader for src/ classes
spl_autoload_register(function (string $class): void {
    // Only handle Glintstone namespace
    if (strpos($class, 'Glintstone\\') !== 0) {
        return;
    }

    // Convert namespace to path
    $relativePath = str_replace('Glintstone\\', '', $class);
    $relativePath = str_replace('\\', '/', $relativePath);
    $file = SRC_ROOT . '/' . $relativePath . '.php';

    if (file_exists($file)) {
        require_once $file;
    }
});

// Simple service container
class App
{
    private static ?App $instance = null;
    private array $services = [];
    private array $factories = [];

    private function __construct()
    {
        $this->registerDefaultServices();
    }

    public static function getInstance(): App
    {
        if (self::$instance === null) {
            self::$instance = new self();
        }
        return self::$instance;
    }

    /**
     * Register a service factory
     */
    public function register(string $name, callable $factory): void
    {
        $this->factories[$name] = $factory;
    }

    /**
     * Get a service instance (lazy-loaded singleton)
     */
    public function get(string $name): mixed
    {
        if (!isset($this->services[$name])) {
            if (!isset($this->factories[$name])) {
                throw new \RuntimeException("Service not found: {$name}");
            }
            $this->services[$name] = ($this->factories[$name])($this);
        }
        return $this->services[$name];
    }

    /**
     * Check if a service is registered
     */
    public function has(string $name): bool
    {
        return isset($this->factories[$name]) || isset($this->services[$name]);
    }

    private function registerDefaultServices(): void
    {
        // Cache service
        $this->register(Cache\FileCache::class, function () {
            return new Cache\FileCache(CACHE_ROOT);
        });

        // Repository services
        $this->register(Repository\ArtifactRepository::class, function () {
            return new Repository\ArtifactRepository();
        });

        $this->register(Repository\InscriptionRepository::class, function () {
            return new Repository\InscriptionRepository();
        });

        $this->register(Repository\GlossaryRepository::class, function () {
            return new Repository\GlossaryRepository();
        });

        $this->register(Repository\FilterStatsRepository::class, function () {
            return new Repository\FilterStatsRepository();
        });

        $this->register(Repository\CollectionRepository::class, function () {
            return new Repository\CollectionRepository();
        });

        // Service layer
        $this->register(Service\TabletService::class, function (App $app) {
            return new Service\TabletService(
                $app->get(Repository\ArtifactRepository::class),
                $app->get(Repository\InscriptionRepository::class),
                $app->get(Cache\FileCache::class)
            );
        });

        $this->register(Service\FilterService::class, function (App $app) {
            return new Service\FilterService(
                $app->get(Repository\FilterStatsRepository::class),
                $app->get(Cache\FileCache::class)
            );
        });

        $this->register(Service\DictionaryService::class, function (App $app) {
            return new Service\DictionaryService(
                $app->get(Repository\GlossaryRepository::class),
                $app->get(Cache\FileCache::class)
            );
        });
    }
}

// Global helper function
function app(): App
{
    return App::getInstance();
}
