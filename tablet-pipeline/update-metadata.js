#!/usr/bin/env node

/**
 * Glintstone Tablet Metadata Editor
 *
 * Interactive tool to update tablet metadata with period, genre, collection info, etc.
 */

const fs = require('fs').promises;
const path = require('path');
const readline = require('readline');

const METADATA_DIR = path.join(__dirname, '..', 'data', 'tablets');

// Standard categorization values
const PERIODS = [
  'Uruk IV-III (ca. 3400-3000 BC)',
  'Early Dynastic I-II (ca. 2900-2700 BC)',
  'Early Dynastic IIIa (ca. 2600-2500 BC)',
  'Early Dynastic IIIb (ca. 2500-2340 BC)',
  'Old Akkadian (ca. 2340-2200 BC)',
  'Lagash II (ca. 2200-2100 BC)',
  'Ur III (ca. 2100-2000 BC)',
  'Old Babylonian (ca. 1900-1600 BC)',
  'Middle Babylonian (ca. 1400-1100 BC)',
  'Neo-Assyrian (ca. 911-612 BC)',
  'Neo-Babylonian (ca. 626-539 BC)',
  'Achaemenid (547-331 BC)',
  'Hellenistic (323-63 BC)'
];

const GENRES = [
  'Administrative',
  'Legal',
  'Letter',
  'Literary',
  'Lexical',
  'Mathematical',
  'Astronomical',
  'Medical',
  'Omen',
  'Ritual',
  'Royal/Monumental',
  'School',
  'Unknown'
];

const LANGUAGES = [
  'Sumerian',
  'Akkadian',
  'Sumerian & Akkadian',
  'Elamite',
  'Hittite',
  'Hurrian',
  'Unknown'
];

// Create readline interface
const rl = readline.createInterface({
  input: process.stdin,
  output: process.stdout
});

// Promisify question
function question(prompt) {
  return new Promise(resolve => {
    rl.question(prompt, resolve);
  });
}

// Load metadata
async function loadMetadata(pNumber) {
  const filePath = path.join(METADATA_DIR, `${pNumber}.json`);
  try {
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Error loading metadata for ${pNumber}: ${error.message}`);
    return null;
  }
}

// Save metadata
async function saveMetadata(pNumber, metadata) {
  const filePath = path.join(METADATA_DIR, `${pNumber}.json`);
  await fs.writeFile(filePath, JSON.stringify(metadata, null, 2));
  console.log(`✓ Metadata saved for ${pNumber}`);
}

// List all tablets with metadata
async function listTablets() {
  try {
    const files = await fs.readdir(METADATA_DIR);
    const jsonFiles = files.filter(f => f.endsWith('.json') && f.startsWith('P'));
    return jsonFiles.map(f => f.replace('.json', ''));
  } catch (error) {
    return [];
  }
}

// Display current metadata
function displayMetadata(metadata) {
  console.log('\nCurrent Metadata:');
  console.log('─'.repeat(60));
  console.log(`ID: ${metadata.id}`);
  console.log(`CDLI URL: ${metadata.cdliUrl}`);
  console.log(`Period: ${metadata.period || '(not set)'}`);
  console.log(`Genre: ${metadata.genre || '(not set)'}`);
  console.log(`Language: ${metadata.language || '(not set)'}`);
  console.log(`Collection: ${metadata.collection || '(not set)'}`);
  console.log(`Museum: ${metadata.museum || '(not set)'}`);
  console.log(`Accession #: ${metadata.accessionNumber || '(not set)'}`);
  console.log(`Provenience: ${metadata.provenience || '(not set)'}`);
  console.log(`Material: ${metadata.material || '(not set)'}`);
  console.log(`Dimensions: ${metadata.dimensions || '(not set)'}`);
  console.log(`Description: ${metadata.description || '(not set)'}`);
  console.log(`Tags: ${metadata.tags.length > 0 ? metadata.tags.join(', ') : '(none)'}`);
  console.log(`Notes: ${metadata.notes || '(none)'}`);
  console.log('─'.repeat(60));
}

// Select from list
async function selectFromList(prompt, options) {
  console.log(`\n${prompt}`);
  options.forEach((opt, idx) => {
    console.log(`  ${idx + 1}. ${opt}`);
  });
  console.log(`  ${options.length + 1}. (Other - enter manually)`);
  console.log(`  0. Skip`);

  while (true) {
    const answer = await question('\nEnter number: ');
    const num = parseInt(answer);

    if (num === 0) return null;
    if (num > 0 && num <= options.length) return options[num - 1];
    if (num === options.length + 1) {
      return await question('Enter value: ');
    }
    console.log('Invalid selection, try again.');
  }
}

// Interactive metadata editor
async function editMetadata(pNumber) {
  console.log(`\n=== Editing Metadata for ${pNumber} ===`);

  const metadata = await loadMetadata(pNumber);
  if (!metadata) {
    console.log('Metadata file not found. Please download the tablet first.');
    return;
  }

  displayMetadata(metadata);

  console.log('\nWhat would you like to update?');
  console.log('  1. Period');
  console.log('  2. Genre');
  console.log('  3. Language');
  console.log('  4. Collection/Museum info');
  console.log('  5. Physical details (material, dimensions)');
  console.log('  6. Description');
  console.log('  7. Tags');
  console.log('  8. Notes');
  console.log('  9. Update all fields');
  console.log('  0. Done');

  const choice = await question('\nSelect option: ');

  switch (choice) {
    case '1':
      const period = await selectFromList('Select Period:', PERIODS);
      if (period) metadata.period = period;
      break;

    case '2':
      const genre = await selectFromList('Select Genre:', GENRES);
      if (genre) metadata.genre = genre;
      break;

    case '3':
      const language = await selectFromList('Select Language:', LANGUAGES);
      if (language) metadata.language = language;
      break;

    case '4':
      const collection = await question('Collection name: ');
      if (collection) metadata.collection = collection;

      const museum = await question('Museum/Institution: ');
      if (museum) metadata.museum = museum;

      const accession = await question('Accession/Catalogue number: ');
      if (accession) metadata.accessionNumber = accession;

      const provenience = await question('Provenience (findspot): ');
      if (provenience) metadata.provenience = provenience;

      const excavation = await question('Excavation number: ');
      if (excavation) metadata.excavationNumber = excavation;
      break;

    case '5':
      const material = await question('Material (e.g., "clay"): ');
      if (material) metadata.material = material;

      const dimensions = await question('Dimensions (e.g., "5.2 x 3.8 x 1.9 cm"): ');
      if (dimensions) metadata.dimensions = dimensions;
      break;

    case '6':
      const description = await question('Description: ');
      if (description) metadata.description = description;
      break;

    case '7':
      const tags = await question('Tags (comma-separated): ');
      if (tags) metadata.tags = tags.split(',').map(t => t.trim()).filter(t => t);
      break;

    case '8':
      const notes = await question('Notes: ');
      if (notes) metadata.notes = notes;
      break;

    case '9':
      // Update all fields
      const allPeriod = await selectFromList('Select Period:', PERIODS);
      if (allPeriod) metadata.period = allPeriod;

      const allGenre = await selectFromList('Select Genre:', GENRES);
      if (allGenre) metadata.genre = allGenre;

      const allLanguage = await selectFromList('Select Language:', LANGUAGES);
      if (allLanguage) metadata.language = allLanguage;

      const allCollection = await question('Collection name: ');
      if (allCollection) metadata.collection = allCollection;

      const allMuseum = await question('Museum/Institution: ');
      if (allMuseum) metadata.museum = allMuseum;

      const allAccession = await question('Accession/Catalogue number: ');
      if (allAccession) metadata.accessionNumber = allAccession;

      const allProvenience = await question('Provenience (findspot): ');
      if (allProvenience) metadata.provenience = allProvenience;

      const allMaterial = await question('Material: ');
      if (allMaterial) metadata.material = allMaterial;

      const allDimensions = await question('Dimensions: ');
      if (allDimensions) metadata.dimensions = allDimensions;

      const allDescription = await question('Description: ');
      if (allDescription) metadata.description = allDescription;

      const allTags = await question('Tags (comma-separated): ');
      if (allTags) metadata.tags = allTags.split(',').map(t => t.trim()).filter(t => t);

      const allNotes = await question('Notes: ');
      if (allNotes) metadata.notes = allNotes;
      break;

    case '0':
      await saveMetadata(pNumber, metadata);
      return;

    default:
      console.log('Invalid option');
      break;
  }

  metadata.updatedAt = new Date().toISOString();
  await saveMetadata(pNumber, metadata);

  // Ask if they want to continue editing
  const continueEdit = await question('\nContinue editing? (y/n): ');
  if (continueEdit.toLowerCase() === 'y') {
    await editMetadata(pNumber);
  }
}

// Bulk update from CSV
async function bulkUpdateFromCSV(csvPath) {
  console.log(`Loading bulk updates from ${csvPath}...`);

  try {
    const content = await fs.readFile(csvPath, 'utf8');
    const lines = content.split('\n');
    const headers = lines[0].split(',').map(h => h.trim());

    console.log(`Found ${lines.length - 1} tablets to update`);

    for (let i = 1; i < lines.length; i++) {
      const line = lines[i].trim();
      if (!line) continue;

      const values = line.split(',').map(v => v.trim());
      const pNumber = values[0];

      if (!pNumber || !pNumber.match(/^P\d+$/)) {
        console.log(`Skipping invalid P-number: ${pNumber}`);
        continue;
      }

      const metadata = await loadMetadata(pNumber);
      if (!metadata) {
        console.log(`Metadata not found for ${pNumber}, skipping`);
        continue;
      }

      // Update fields based on CSV columns
      for (let j = 1; j < headers.length; j++) {
        const header = headers[j].toLowerCase();
        const value = values[j];

        if (!value) continue;

        switch (header) {
          case 'period': metadata.period = value; break;
          case 'genre': metadata.genre = value; break;
          case 'language': metadata.language = value; break;
          case 'collection': metadata.collection = value; break;
          case 'museum': metadata.museum = value; break;
          case 'accession': metadata.accessionNumber = value; break;
          case 'provenience': metadata.provenience = value; break;
          case 'material': metadata.material = value; break;
          case 'dimensions': metadata.dimensions = value; break;
          case 'description': metadata.description = value; break;
          case 'tags': metadata.tags = value.split(';').map(t => t.trim()); break;
        }
      }

      metadata.updatedAt = new Date().toISOString();
      await saveMetadata(pNumber, metadata);
      console.log(`✓ Updated ${pNumber}`);
    }

    console.log('\nBulk update complete!');

  } catch (error) {
    console.error(`Error processing CSV: ${error.message}`);
  }
}

// Main menu
async function main() {
  const args = process.argv.slice(2);

  // Handle CSV bulk import
  if (args[0] === '--csv' && args[1]) {
    await bulkUpdateFromCSV(args[1]);
    rl.close();
    return;
  }

  // Handle single tablet update
  if (args[0] && args[0].match(/^P\d+$/i)) {
    await editMetadata(args[0]);
    rl.close();
    return;
  }

  // Interactive mode
  console.log('\n=== Glintstone Tablet Metadata Editor ===\n');

  const tablets = await listTablets();
  if (tablets.length === 0) {
    console.log('No tablets found. Download some tablets first using download-tablets.js');
    rl.close();
    return;
  }

  console.log(`Found ${tablets.length} tablets:\n`);
  tablets.forEach((t, idx) => {
    console.log(`  ${idx + 1}. ${t}`);
  });

  const selection = await question('\nEnter tablet number or P-number to edit (or "q" to quit): ');

  if (selection.toLowerCase() === 'q') {
    rl.close();
    return;
  }

  const num = parseInt(selection);
  let pNumber;

  if (num > 0 && num <= tablets.length) {
    pNumber = tablets[num - 1];
  } else if (selection.match(/^P\d+$/i)) {
    pNumber = selection;
  } else {
    console.log('Invalid selection');
    rl.close();
    return;
  }

  await editMetadata(pNumber);
  rl.close();
}

if (require.main === module) {
  main().catch(error => {
    console.error('Error:', error);
    rl.close();
    process.exit(1);
  });
}
