<?php
/**
 * ATF (Assyriological Text Format) Parser
 * Parses raw ATF transliterations into structured data for interactive display
 */

class ATFParser {
    private string $raw = '';
    private array $result = [];

    // Surface name mappings
    private const SURFACE_LABELS = [
        'obverse' => 'Obverse',
        'reverse' => 'Reverse',
        'left' => 'Left Edge',
        'right' => 'Right Edge',
        'top' => 'Top',
        'bottom' => 'Bottom',
        'edge' => 'Edge',
        'face' => 'Face',
        'seal' => 'Seal'
    ];

    // Determinative types and their display
    private const DETERMINATIVES = [
        'd' => ['type' => 'divine', 'label' => 'divine name', 'display' => 'ᵈ'],
        'f' => ['type' => 'female', 'label' => 'female name', 'display' => 'ᶠ'],
        'm' => ['type' => 'male', 'label' => 'male name', 'display' => 'ᵐ'],
        'ki' => ['type' => 'place', 'label' => 'place name', 'display' => 'ᵏⁱ'],
        'disz' => ['type' => 'count', 'label' => 'count marker', 'display' => ''],
        'gesz' => ['type' => 'wood', 'label' => 'wooden object', 'display' => 'ᵍᵉˢᶻ'],
        'gi' => ['type' => 'reed', 'label' => 'reed object', 'display' => 'ᵍⁱ'],
        'kusz' => ['type' => 'leather', 'label' => 'leather object', 'display' => 'ᵏᵘˢᶻ'],
        'tug2' => ['type' => 'cloth', 'label' => 'textile', 'display' => 'ᵗᵘᵍ'],
        'urud' => ['type' => 'copper', 'label' => 'copper/bronze', 'display' => 'ᵘʳᵘᵈ'],
        'na4' => ['type' => 'stone', 'label' => 'stone object', 'display' => 'ⁿᵃ⁴'],
        'id2' => ['type' => 'water', 'label' => 'river/canal', 'display' => 'ⁱᵈ'],
        'u2' => ['type' => 'plant', 'label' => 'plant', 'display' => 'ᵘ²'],
        'iri' => ['type' => 'city', 'label' => 'city', 'display' => 'ⁱʳⁱ'],
        'kur' => ['type' => 'land', 'label' => 'land/mountain', 'display' => 'ᵏᵘʳ'],
    ];

    /**
     * Parse ATF text into structured array
     */
    public function parse(string $atf): array {
        $this->raw = $atf;
        $this->result = [
            'header' => [
                'p_number' => null,
                'designation' => null,
                'language' => null,
                'object_type' => 'tablet'
            ],
            'surfaces' => [],
            'composites' => [],
            'hasMultipleSurfaces' => false,
            'hasMultipleColumns' => false
        ];

        $lines = explode("\n", $atf);
        $currentSurface = null;
        $currentColumn = null;

        foreach ($lines as $lineText) {
            $lineText = trim($lineText);
            if (empty($lineText)) continue;

            $parsed = $this->parseLine($lineText);

            switch ($parsed['type']) {
                case 'header':
                    $this->result['header']['p_number'] = $parsed['p_number'];
                    $this->result['header']['designation'] = $parsed['designation'];
                    break;

                case 'language':
                    $this->result['header']['language'] = $parsed['language'];
                    break;

                case 'object':
                    $this->result['header']['object_type'] = $parsed['object_type'];
                    break;

                case 'surface':
                    // Check if we should reuse an auto-created obverse surface
                    // This happens when content/state lines appear before @obverse in the ATF
                    if ($parsed['name'] === 'obverse' && $parsed['modifier'] === null &&
                        count($this->result['surfaces']) === 1 &&
                        $this->result['surfaces'][0]['name'] === 'obverse' &&
                        $this->result['surfaces'][0]['modifier'] === null) {
                        // Reuse the existing auto-created obverse
                        $currentSurface = 0;
                    } else {
                        $currentSurface = $this->addSurface($parsed['name'], $parsed['modifier']);
                    }
                    $currentColumn = null;
                    break;

                case 'column':
                    $currentColumn = $this->addColumn($currentSurface, $parsed['number']);
                    break;

                case 'state':
                    // Auto-create obverse surface if no surface has been defined yet
                    if ($currentSurface === null) {
                        $currentSurface = $this->addSurface('obverse', null);
                    }
                    $this->addState($currentSurface, $currentColumn, $parsed['text']);
                    break;

                case 'content':
                    // Auto-create obverse surface if no surface has been defined yet
                    if ($currentSurface === null) {
                        $currentSurface = $this->addSurface('obverse', null);
                    }
                    $this->addContentLine($currentSurface, $currentColumn, $parsed);
                    break;

                case 'composite':
                    $this->addCompositeRef($currentSurface, $currentColumn, $parsed['ref']);
                    break;

                case 'translation':
                    $this->addInlineTranslation($currentSurface, $currentColumn, $parsed['language'], $parsed['text']);
                    break;

                case 'comment':
                case 'protocol':
                    // Skip for now
                    break;
            }
        }

        // Set flags for UI decisions
        $this->result['hasMultipleSurfaces'] = count($this->result['surfaces']) > 1;
        $this->result['hasMultipleColumns'] = $this->checkMultipleColumns();

        return $this->result;
    }

    /**
     * Parse a single line and determine its type
     */
    private function parseLine(string $line): array {
        // Header line: &P000001 = Designation
        if (preg_match('/^&(P\d+)\s*=\s*(.+)$/', $line, $m)) {
            return [
                'type' => 'header',
                'p_number' => $m[1],
                'designation' => trim($m[2])
            ];
        }

        // Protocol/language: #atf: lang akk
        if (preg_match('/^#atf:\s*lang\s+(\S+)/', $line, $m)) {
            return [
                'type' => 'language',
                'language' => $m[1]
            ];
        }

        // Inline translation: #tr.en: translation text
        if (preg_match('/^#tr\.(\w+):\s*(.+)$/', $line, $m)) {
            return [
                'type' => 'translation',
                'language' => $m[1],
                'text' => trim($m[2])
            ];
        }

        // Other ATF directives (comments)
        if (str_starts_with($line, '#')) {
            return ['type' => 'comment', 'text' => substr($line, 1)];
        }

        // Object type: @tablet, @bulla, @prism, etc.
        if (preg_match('/^@(tablet|bulla|envelope|prism|fragment|object)/', $line, $m)) {
            return [
                'type' => 'object',
                'object_type' => $m[1]
            ];
        }

        // Surface: @obverse, @reverse, @left, etc.
        if (preg_match('/^@(obverse|reverse|left|right|top|bottom|edge|face|seal)(?:\s+(\S+))?/', $line, $m)) {
            return [
                'type' => 'surface',
                'name' => $m[1],
                'modifier' => $m[2] ?? null
            ];
        }

        // Generic surface: @surface a1, @surface b2, etc. (used for prisms, cylinders)
        if (preg_match('/^@surface\s+(\S+)/', $line, $m)) {
            return [
                'type' => 'surface',
                'name' => 'surface',
                'modifier' => $m[1]
            ];
        }

        // Column: @column 1
        if (preg_match('/^@column\s+(\d+)/', $line, $m)) {
            return [
                'type' => 'column',
                'number' => (int)$m[1]
            ];
        }

        // State: $ beginning broken, $ rest broken, etc.
        if (str_starts_with($line, '$')) {
            return [
                'type' => 'state',
                'text' => trim(substr($line, 1))
            ];
        }

        // Composite reference: >>Q000002 045
        if (preg_match('/^>>(Q\d+)\s+(.+)$/', $line, $m)) {
            return [
                'type' => 'composite',
                'ref' => [
                    'q_number' => $m[1],
                    'line' => trim($m[2])
                ]
            ];
        }

        // Content line: 1. text or 1'. text
        if (preg_match('/^(\d+[\'"]?)\.?\s+(.*)$/', $line, $m)) {
            return [
                'type' => 'content',
                'number' => $m[1] . '.',
                'raw' => $m[2],
                'words' => $this->parseWords($m[2]),
                'isPrime' => str_contains($m[1], "'")
            ];
        }

        // Unnumbered content (rare)
        if (!str_starts_with($line, '&') && !str_starts_with($line, '@') &&
            !str_starts_with($line, '#') && !str_starts_with($line, '$') &&
            !str_starts_with($line, '>')) {
            return [
                'type' => 'content',
                'number' => '',
                'raw' => $line,
                'words' => $this->parseWords($line),
                'isPrime' => false
            ];
        }

        return ['type' => 'unknown', 'raw' => $line];
    }

    /**
     * Parse words from a content line
     */
    private function parseWords(string $text): array {
        $words = [];
        $pos = 0;
        $len = strlen($text);

        while ($pos < $len) {
            // Skip whitespace
            while ($pos < $len && ctype_space($text[$pos])) {
                $pos++;
            }
            if ($pos >= $len) break;

            $word = $this->extractNextWord($text, $pos);
            if ($word !== null) {
                $words[] = $word;
            }
        }

        return $words;
    }

    /**
     * Extract the next word/token from text
     */
    private function extractNextWord(string $text, int &$pos): ?array {
        $len = strlen($text);
        if ($pos >= $len) return null;

        $start = $pos;
        $char = $text[$pos];

        // Punctuation/separators
        if (in_array($char, [',', '.', ';', ':'])) {
            $pos++;
            return [
                'type' => 'punctuation',
                'text' => $char,
                'lookup' => null
            ];
        }

        // Broken text: [...]
        if ($char === '[') {
            $end = strpos($text, ']', $pos);
            if ($end !== false) {
                $content = substr($text, $pos, $end - $pos + 1);
                $pos = $end + 1;
                return [
                    'type' => 'broken',
                    'text' => $content,
                    'lookup' => null,
                    'inner' => trim($content, '[]')
                ];
            }
        }

        // Logogram: _text_
        if ($char === '_') {
            $end = strpos($text, '_', $pos + 1);
            if ($end !== false) {
                $content = substr($text, $pos + 1, $end - $pos - 1);
                $pos = $end + 1;
                return [
                    'type' => 'logogram',
                    'text' => $content,
                    'lookup' => $this->normalizeLookup($content),
                    'display' => $content
                ];
            }
        }

        // Determinative: {d}word or word{ki}
        if ($char === '{') {
            $end = strpos($text, '}', $pos);
            if ($end !== false) {
                $det = substr($text, $pos + 1, $end - $pos - 1);
                $pos = $end + 1;

                // Get following word if prefix determinative
                $following = $this->extractWordChars($text, $pos);

                $detInfo = self::DETERMINATIVES[$det] ?? [
                    'type' => 'other',
                    'label' => $det,
                    'display' => "($det)"
                ];

                return [
                    'type' => 'determinative',
                    'text' => $following,
                    'lookup' => $this->normalizeLookup($following),
                    'determinative' => $det,
                    'detType' => $detInfo['type'],
                    'detLabel' => $detInfo['label'],
                    'detDisplay' => $detInfo['display'],
                    'position' => 'prefix'
                ];
            }
        }

        // Regular word (may have damage markers at end)
        $word = $this->extractWordChars($text, $pos);
        if (empty($word)) {
            // Skip unknown character
            $pos++;
            return null;
        }

        // Check for trailing determinative: word{ki}
        if ($pos < $len && $text[$pos] === '{') {
            $end = strpos($text, '}', $pos);
            if ($end !== false) {
                $det = substr($text, $pos + 1, $end - $pos - 1);
                $pos = $end + 1;

                $detInfo = self::DETERMINATIVES[$det] ?? [
                    'type' => 'other',
                    'label' => $det,
                    'display' => "($det)"
                ];

                return [
                    'type' => 'determinative',
                    'text' => $word,
                    'lookup' => $this->normalizeLookup($word),
                    'determinative' => $det,
                    'detType' => $detInfo['type'],
                    'detLabel' => $detInfo['label'],
                    'detDisplay' => $detInfo['display'],
                    'position' => 'suffix'
                ];
            }
        }

        // Parse damage markers
        $damaged = false;
        $uncertain = false;
        $corrected = false;
        $cleanWord = $word;

        if (str_ends_with($word, '#')) {
            $damaged = true;
            $cleanWord = rtrim($word, '#');
        }
        if (str_ends_with($cleanWord, '?')) {
            $uncertain = true;
            $cleanWord = rtrim($cleanWord, '?');
        }
        if (str_ends_with($cleanWord, '!')) {
            $corrected = true;
            $cleanWord = rtrim($cleanWord, '!');
        }

        return [
            'type' => 'word',
            'text' => $word,
            'lookup' => $this->normalizeLookup($cleanWord),
            'damaged' => $damaged,
            'uncertain' => $uncertain,
            'corrected' => $corrected
        ];
    }

    /**
     * Extract word characters from position
     */
    private function extractWordChars(string $text, int &$pos): string {
        $len = strlen($text);
        $start = $pos;

        // Word pattern: letters, numbers, diacritics, hyphens, subscripts
        $wordChars = 'a-zA-Z0-9šṣṭāēīūâêîûŠṢṬĀĒĪŪÂÊÎÛ₀₁₂₃₄₅₆₇₈₉\-~@|#?!';

        while ($pos < $len) {
            $char = $text[$pos];
            // Check if character matches word pattern
            if (preg_match("/[$wordChars]/u", $char)) {
                $pos++;
            } else {
                break;
            }
        }

        return substr($text, $start, $pos - $start);
    }

    /**
     * Normalize a word for dictionary lookup
     */
    private function normalizeLookup(string $word): ?string {
        if (empty($word)) return null;

        // Remove damage markers
        $word = preg_replace('/[#?!*]/', '', $word);

        // Convert subscript numbers to regular
        $word = strtr($word, [
            '₀' => '', '₁' => '', '₂' => '', '₃' => '', '₄' => '',
            '₅' => '', '₆' => '', '₇' => '', '₈' => '', '₉' => ''
        ]);

        // Remove sign variants (~a, ~b, @g, etc.)
        $word = preg_replace('/[~@][a-z0-9]+/', '', $word);

        // Remove pipe notation for complex signs
        $word = str_replace(['|', 'x'], '', $word);

        // Lowercase
        $word = mb_strtolower($word);

        return empty($word) ? null : $word;
    }

    /**
     * Add a surface to the result
     */
    private function addSurface(string $name, ?string $modifier): int {
        $label = self::SURFACE_LABELS[$name] ?? ucfirst($name);
        if ($modifier) {
            $label .= ' ' . $modifier;
        }

        $this->result['surfaces'][] = [
            'name' => $name,
            'label' => $label,
            'modifier' => $modifier,
            'columns' => [],
            'states' => []
        ];

        return count($this->result['surfaces']) - 1;
    }

    /**
     * Add a column to a surface
     */
    private function addColumn(?int $surfaceIdx, int $number): int {
        // Ensure we have a surface
        if ($surfaceIdx === null) {
            $surfaceIdx = $this->addSurface('obverse', null);
        }

        $this->result['surfaces'][$surfaceIdx]['columns'][] = [
            'number' => $number,
            'lines' => [],
            'states' => []
        ];

        return count($this->result['surfaces'][$surfaceIdx]['columns']) - 1;
    }

    /**
     * Add a state marker
     */
    private function addState(?int $surfaceIdx, ?int $columnIdx, string $text): void {
        if ($surfaceIdx === null) {
            $surfaceIdx = $this->addSurface('obverse', null);
        }

        $state = [
            'type' => 'state',
            'text' => $text
        ];

        if ($columnIdx !== null && isset($this->result['surfaces'][$surfaceIdx]['columns'][$columnIdx])) {
            $this->result['surfaces'][$surfaceIdx]['columns'][$columnIdx]['lines'][] = $state;
        } else {
            $this->result['surfaces'][$surfaceIdx]['states'][] = $state;
        }
    }

    /**
     * Add a content line
     */
    private function addContentLine(?int $surfaceIdx, ?int $columnIdx, array $parsed): void {
        if ($surfaceIdx === null) {
            $surfaceIdx = $this->addSurface('obverse', null);
        }

        $line = [
            'type' => 'content',
            'number' => $parsed['number'],
            'raw' => $parsed['raw'],
            'words' => $parsed['words'],
            'isPrime' => $parsed['isPrime'],
            'composite' => null
        ];

        if ($columnIdx !== null && isset($this->result['surfaces'][$surfaceIdx]['columns'][$columnIdx])) {
            $this->result['surfaces'][$surfaceIdx]['columns'][$columnIdx]['lines'][] = $line;
        } else {
            // No column specified - add directly to surface or create default column
            if (empty($this->result['surfaces'][$surfaceIdx]['columns'])) {
                $this->result['surfaces'][$surfaceIdx]['columns'][] = [
                    'number' => 0,
                    'lines' => [],
                    'states' => []
                ];
            }
            $lastCol = count($this->result['surfaces'][$surfaceIdx]['columns']) - 1;
            $this->result['surfaces'][$surfaceIdx]['columns'][$lastCol]['lines'][] = $line;
        }
    }

    /**
     * Add composite reference to last content line
     */
    private function addCompositeRef(?int $surfaceIdx, ?int $columnIdx, array $ref): void {
        if ($surfaceIdx === null) return;

        // Add to global list
        $this->result['composites'][] = $ref;

        // Attach to last line
        $surface = &$this->result['surfaces'][$surfaceIdx];

        if ($columnIdx !== null && isset($surface['columns'][$columnIdx])) {
            $col = &$surface['columns'][$columnIdx];
            if (!empty($col['lines'])) {
                $lastIdx = count($col['lines']) - 1;
                if ($col['lines'][$lastIdx]['type'] === 'content') {
                    $col['lines'][$lastIdx]['composite'] = $ref;
                }
            }
        }
    }

    /**
     * Add inline translation to last content line
     */
    private function addInlineTranslation(?int $surfaceIdx, ?int $columnIdx, string $lang, string $text): void {
        if ($surfaceIdx === null) return;

        $surface = &$this->result['surfaces'][$surfaceIdx];

        // Find the last content line to attach translation to
        $col = null;
        if ($columnIdx !== null && isset($surface['columns'][$columnIdx])) {
            $col = &$surface['columns'][$columnIdx];
        } elseif (!empty($surface['columns'])) {
            $col = &$surface['columns'][count($surface['columns']) - 1];
        }

        if ($col && !empty($col['lines'])) {
            // Find last content line
            for ($i = count($col['lines']) - 1; $i >= 0; $i--) {
                if ($col['lines'][$i]['type'] === 'content') {
                    if (!isset($col['lines'][$i]['translations'])) {
                        $col['lines'][$i]['translations'] = [];
                    }
                    $col['lines'][$i]['translations'][$lang] = $text;
                    break;
                }
            }
        }
    }

    /**
     * Check if any surface has multiple columns
     */
    private function checkMultipleColumns(): bool {
        foreach ($this->result['surfaces'] as $surface) {
            if (count($surface['columns']) > 1) {
                return true;
            }
            // Also check if columns have explicit numbers > 1
            foreach ($surface['columns'] as $col) {
                if ($col['number'] > 1) {
                    return true;
                }
            }
        }
        return false;
    }

    /**
     * Get legend items based on what's in the parsed ATF
     */
    public function getLegendItems(): array {
        $legend = [];

        // Always include definition status
        $legend[] = ['class' => 'has-definition', 'label' => 'Has definition', 'symbol' => ''];
        $legend[] = ['class' => 'no-definition', 'label' => 'No definition', 'symbol' => ''];

        // Check for determinatives, damage, etc.
        $hasDamage = false;
        $hasUncertain = false;
        $hasBroken = false;
        $hasLogogram = false;
        $hasDivine = false;
        $hasPlace = false;
        $hasInlineTranslation = false;

        foreach ($this->result['surfaces'] as $surface) {
            foreach ($surface['columns'] as $col) {
                foreach ($col['lines'] as $line) {
                    if ($line['type'] !== 'content') continue;

                    // Check for inline translations
                    if (!empty($line['translations'])) {
                        $hasInlineTranslation = true;
                    }

                    foreach ($line['words'] as $word) {
                        if ($word['type'] === 'broken') $hasBroken = true;
                        if ($word['type'] === 'logogram') $hasLogogram = true;
                        if ($word['type'] === 'determinative') {
                            if ($word['detType'] === 'divine') $hasDivine = true;
                            if ($word['detType'] === 'place') $hasPlace = true;
                        }
                        if ($word['type'] === 'word') {
                            if ($word['damaged'] ?? false) $hasDamage = true;
                            if ($word['uncertain'] ?? false) $hasUncertain = true;
                        }
                    }
                }
            }
        }

        if ($hasDivine) {
            $legend[] = ['class' => 'det-divine', 'label' => 'Divine name', 'symbol' => 'ᵈ'];
        }
        if ($hasPlace) {
            $legend[] = ['class' => 'det-place', 'label' => 'Place name', 'symbol' => 'ᵏⁱ'];
        }
        if ($hasLogogram) {
            $legend[] = ['class' => 'logogram', 'label' => 'Logogram', 'symbol' => '_text_'];
        }
        if ($hasDamage) {
            $legend[] = ['class' => 'damaged', 'label' => 'Damaged', 'symbol' => '#'];
        }
        if ($hasUncertain) {
            $legend[] = ['class' => 'uncertain', 'label' => 'Uncertain', 'symbol' => '?'];
        }
        if ($hasBroken) {
            $legend[] = ['class' => 'broken', 'label' => 'Broken', 'symbol' => '[...]'];
        }
        if ($hasInlineTranslation) {
            $legend[] = ['class' => 'translation', 'label' => 'Line translation', 'symbol' => '│'];
        }

        return $legend;
    }
}
