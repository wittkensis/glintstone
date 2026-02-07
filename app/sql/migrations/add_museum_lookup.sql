-- Migration: Add museum and excavation site lookup tables
-- Provides human-readable names for museum codes and excavation site codes

-- Museums lookup table
CREATE TABLE IF NOT EXISTS museums (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    city TEXT,
    country TEXT,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Excavation sites lookup table
CREATE TABLE IF NOT EXISTS excavation_sites (
    code TEXT PRIMARY KEY,
    name TEXT NOT NULL,
    ancient_name TEXT,
    modern_country TEXT,
    updated_at INTEGER NOT NULL DEFAULT (strftime('%s', 'now'))
);

-- Populate museums with known mappings (top institutions by frequency in corpus)
INSERT OR REPLACE INTO museums (code, name, city, country) VALUES
('BM', 'British Museum', 'London', 'United Kingdom'),
('IM', 'Iraq Museum', 'Baghdad', 'Iraq'),
('Ist', 'Istanbul Archaeological Museums', 'Istanbul', 'Turkey'),
('YBC', 'Yale Babylonian Collection', 'New Haven', 'United States'),
('CBS', 'Penn Museum (Babylonian Section)', 'Philadelphia', 'United States'),
('NBC', 'Nies Babylonian Collection', 'New Haven', 'United States'),
('VAT', 'Vorderasiatisches Museum', 'Berlin', 'Germany'),
('CUNES', 'Cornell University', 'Ithaca', 'United States'),
('AO', 'Louvre (Antiquites Orientales)', 'Paris', 'France'),
('OIM', 'Oriental Institute Museum', 'Chicago', 'United States'),
('N', 'Nippur Collection (Penn)', 'Philadelphia', 'United States'),
('Ash', 'Ashmolean Museum', 'Oxford', 'United Kingdom'),
('Bo', 'Bogazkoy Collection', 'Ankara', 'Turkey'),
('UM', 'University Museum (Penn)', 'Philadelphia', 'United States'),
('SM', 'Sulaymaniyah Museum', 'Sulaymaniyah', 'Iraq'),
('MS', 'Schoyen Collection', 'Oslo', 'Norway'),
('AUAM', 'Andrews University Museum', 'Berrien Springs', 'United States'),
('PTS', 'Princeton Theological Seminary', 'Princeton', 'United States'),
('FLP', 'Free Library of Philadelphia', 'Philadelphia', 'United States'),
('Sb', 'Louvre (Susa Collection)', 'Paris', 'France'),
('MLC', 'Morgan Library Collection', 'New York', 'United States'),
('LB', 'Liagre Bohl Collection', 'Leiden', 'Netherlands'),
('NCBT', 'Newell Collection', 'New Haven', 'United States'),
('VA', 'Vorderasiatische Abteilung', 'Berlin', 'Germany'),
('KM', 'Kelsey Museum', 'Ann Arbor', 'United States'),
('TCL', 'Textes Cuneiformes du Louvre', 'Paris', 'France'),
('HS', 'Hilprecht Sammlung', 'Jena', 'Germany'),
('Rm', 'Rassam Collection (BM)', 'London', 'United Kingdom'),
('K', 'Kouyunjik Collection (BM)', 'London', 'United Kingdom'),
('DT', 'Daily Telegraph Collection (BM)', 'London', 'United Kingdom'),
('Sp', 'Spartali Collection (BM)', 'London', 'United Kingdom'),
('Bu', 'Budge Collection (BM)', 'London', 'United Kingdom'),
('NMS', 'National Museum of Scotland', 'Edinburgh', 'United Kingdom');

-- Populate excavation sites with known mappings
INSERT OR REPLACE INTO excavation_sites (code, name, ancient_name, modern_country) VALUES
('U', 'Ur', 'Ur', 'Iraq'),
('W', 'Warka', 'Uruk', 'Iraq'),
('Ass', 'Qalat Sherqat', 'Assur', 'Iraq'),
('RS', 'Ras Shamra', 'Ugarit', 'Syria'),
('kt', 'Kultepe', 'Kanesh', 'Turkey'),
('ND', 'Nimrud', 'Kalhu', 'Iraq'),
('Msk', 'Meskene', 'Emar', 'Syria'),
('IB', 'Isin-Bahriyat', 'Isin', 'Iraq'),
('TA', 'Tell Asmar', 'Eshnunna', 'Iraq'),
('AbS', 'Abu Salabikh', 'Abu Salabikh', 'Iraq'),
('SH', 'Shemshara', 'Shemshara', 'Iraq'),
('TR', 'Tell al-Rimah', 'Karana', 'Iraq'),
('SU', 'Susa', 'Susa', 'Iran'),
('Di', 'Dilbat', 'Dilbat', 'Iraq'),
('T', 'Tello', 'Girsu', 'Iraq'),
('BE', 'Bismaya', 'Adab', 'Iraq'),
('Ish', 'Ishchali', 'Nerebtum', 'Iraq'),
('S', 'Sippar', 'Sippar', 'Iraq'),
('Kh', 'Khafajah', 'Tutub', 'Iraq'),
('ME', 'Tell Hariri', 'Mari', 'Syria'),
('Haddad', 'Tell Haddad', 'Me-Turan', 'Iraq'),
('Um', 'Jokha', 'Umma', 'Iraq'),
('RIH', 'Ras Ibn Hani', NULL, 'Syria'),
('Bo', 'Bogazkoy', 'Hattusa', 'Turkey'),
('Ni', 'Nuffar', 'Nippur', 'Iraq'),
('Bab', 'Babylon', 'Babylon', 'Iraq'),
('K', 'Kuyunjik', 'Nineveh', 'Iraq'),
('DG', 'Drehem', 'Puzrish-Dagan', 'Iraq'),
('L', 'Senkereh', 'Larsa', 'Iraq'),
('Sip', 'Abu Habbah', 'Sippar', 'Iraq');

-- Create indexes for faster lookups
CREATE INDEX IF NOT EXISTS idx_museums_code ON museums(code);
CREATE INDEX IF NOT EXISTS idx_excavation_sites_code ON excavation_sites(code);
