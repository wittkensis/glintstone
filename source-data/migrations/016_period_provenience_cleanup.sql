-- Migration 016: Remap compound period_normalized values and malformed provenience_normalized values
-- These are ~55 artifacts with compound/variant period strings and ~50 with malformed provenience strings

-- ── Period remaps: compound/variant → primary period ──

UPDATE artifacts SET period_normalized = 'Parthian'
WHERE period_normalized IN (
    'Parthian (247 BC-224 AD)',
    'Parthian (247 BC - 224 AD)'
);

UPDATE artifacts SET period_normalized = 'Neo-Babylonian'
WHERE period_normalized IN (
    'Neo-Babylonian (ca. 626-539 BC) or Achaemenid',
    'Neo-Babylonian (ca. 626-539 BC).'
);

UPDATE artifacts SET period_normalized = 'ED I-II'
WHERE period_normalized = 'ED I-II (ca. 2900-2700 BC), Old Babylonian (ca. 1900-1600 BC)';

UPDATE artifacts SET period_normalized = 'Old Akkadian'
WHERE period_normalized IN (
    'Old Akkadian (ca. 2340-2200 BC); Ur III',
    'Old Akkadian (ca. 2340-2200 BC); Middle Elamite'
);

UPDATE artifacts SET period_normalized = 'Ur III'
WHERE period_normalized = 'Ur III (ca. 2100-2000 BC); Early Old Babylonian';

UPDATE artifacts SET period_normalized = 'ED IIIa'
WHERE period_normalized IN (
    'Early Dynastic IIIA (c. 2700-2500 BC)',
    'ED IIIa (ca. 2600-2500 BC); Old Babylonian'
);

UPDATE artifacts SET period_normalized = 'ED IIIb'
WHERE period_normalized IN (
    'ED IIIb (ca. 2500-2340 BC) or Old Babylonian',
    'ED IIIb (ca. 2500-2340 BC); Ur III',
    'ED IIIb (ca. 2500-2340 BC); Old Akkadian'
);

UPDATE artifacts SET period_normalized = 'Middle Babylonian'
WHERE period_normalized = 'Middle Babylonian (ca. 1400-1100 BC))';

UPDATE artifacts SET period_normalized = 'Uruk III'
WHERE period_normalized = 'Uruk III (ca. 3200-3000 BC) - Early Dynastic I-II';

-- ── Provenience remaps: malformed ancient_names ──

UPDATE artifacts SET provenience_normalized = 'Emar'
WHERE provenience_normalized = 'Emar?';

UPDATE artifacts SET provenience_normalized = 'Bābili'
WHERE provenience_normalized IN (
    'Bābili (mod. Babylon)/Borsippa',
    'Bābili (mod. Babylon)a'
);

UPDATE artifacts SET provenience_normalized = 'Nagar'
WHERE provenience_normalized = 'Nagar (mod. Tell Brak),';

UPDATE artifacts SET provenience_normalized = 'uncertain'
WHERE provenience_normalized = 'uncertain mod. uncertain)';
