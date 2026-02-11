<?php
/**
 * File-based Cache
 * Simple caching using JSON files with TTL support
 */

declare(strict_types=1);

namespace Glintstone\Cache;

final class FileCache
{
    private string $cacheDir;

    public function __construct(string $cacheDir)
    {
        $this->cacheDir = rtrim($cacheDir, '/');
    }

    /**
     * Get a cached value
     */
    public function get(string $key, mixed $default = null): mixed
    {
        $path = $this->getPath($key);

        if (!file_exists($path)) {
            return $default;
        }

        $content = file_get_contents($path);
        if ($content === false) {
            return $default;
        }

        $data = json_decode($content, true);
        if ($data === null) {
            return $default;
        }

        // Check expiration
        if (isset($data['expires_at']) && $data['expires_at'] !== null) {
            if (time() > $data['expires_at']) {
                $this->delete($key);
                return $default;
            }
        }

        return $data['value'] ?? $default;
    }

    /**
     * Set a cached value
     *
     * @param string $key Cache key
     * @param mixed $value Value to cache
     * @param int|null $ttl Time to live in seconds (null = forever)
     */
    public function set(string $key, mixed $value, ?int $ttl = null): bool
    {
        $path = $this->getPath($key);
        $dir = dirname($path);

        if (!is_dir($dir)) {
            mkdir($dir, 0755, true);
        }

        $data = [
            'value' => $value,
            'created_at' => time(),
            'expires_at' => $ttl !== null ? time() + $ttl : null,
        ];

        $result = file_put_contents($path, json_encode($data, JSON_PRETTY_PRINT));

        return $result !== false;
    }

    /**
     * Delete a cached value
     */
    public function delete(string $key): bool
    {
        $path = $this->getPath($key);

        if (file_exists($path)) {
            return unlink($path);
        }

        return true;
    }

    /**
     * Check if a key exists and is not expired
     */
    public function has(string $key): bool
    {
        return $this->get($key, $this) !== $this;
    }

    /**
     * Get or compute a value (cache-aside pattern)
     *
     * @param string $key Cache key
     * @param int $ttl Time to live in seconds
     * @param callable $callback Function to compute value if not cached
     */
    public function remember(string $key, int $ttl, callable $callback): mixed
    {
        $cached = $this->get($key);

        if ($cached !== null) {
            return $cached;
        }

        $value = $callback();
        $this->set($key, $value, $ttl);

        return $value;
    }

    /**
     * Clear all cache files matching a pattern
     *
     * @param string $pattern Glob pattern (e.g., "filter_stats:*")
     */
    public function clear(string $pattern = '*'): int
    {
        $count = 0;
        $searchPattern = $this->cacheDir . '/' . str_replace(':', '/', $pattern);

        // Handle both exact matches and glob patterns
        if (strpos($pattern, '*') !== false) {
            $files = glob($searchPattern . '.json');
        } else {
            $files = ["{$searchPattern}.json"];
        }

        foreach ($files as $file) {
            if (file_exists($file) && unlink($file)) {
                $count++;
            }
        }

        return $count;
    }

    /**
     * Clear all expired cache entries
     */
    public function clearExpired(): int
    {
        $count = 0;
        $iterator = new \RecursiveIteratorIterator(
            new \RecursiveDirectoryIterator($this->cacheDir),
            \RecursiveIteratorIterator::LEAVES_ONLY
        );

        foreach ($iterator as $file) {
            if ($file->getExtension() !== 'json') {
                continue;
            }

            $content = file_get_contents($file->getPathname());
            $data = json_decode($content, true);

            if (isset($data['expires_at']) && $data['expires_at'] !== null && time() > $data['expires_at']) {
                unlink($file->getPathname());
                $count++;
            }
        }

        return $count;
    }

    /**
     * Get cache file path for a key
     * Keys can use : as namespace separator (converted to directories)
     */
    private function getPath(string $key): string
    {
        // Sanitize key - replace : with / for subdirectories, remove unsafe chars
        $safePath = preg_replace('/[^a-zA-Z0-9_\-:\/]/', '_', $key);
        $safePath = str_replace(':', '/', $safePath);

        return $this->cacheDir . '/' . $safePath . '.json';
    }
}
