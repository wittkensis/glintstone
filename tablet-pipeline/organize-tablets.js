#!/usr/bin/env node

/**
 * Glintstone Tablet Organizer
 *
 * Organizes tablet images into categorized directories based on metadata
 * (by period, genre, or other criteria)
 */

const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

const CONFIG = {
  sourceDir: path.join(__dirname, '..', 'public', 'images', 'tablets', 'authentic'),
  metadataDir: path.join(__dirname, '..', 'data', 'tablets'),
  outputBaseDir: path.join(__dirname, '..', 'public', 'images', 'tablets', 'organized')
};

// Load metadata for a tablet
async function loadMetadata(pNumber) {
  const filePath = path.join(CONFIG.metadataDir, `${pNumber}.json`);
  try {
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    console.error(`Warning: No metadata found for ${pNumber}`);
    return null;
  }
}

// Sanitize directory name
function sanitizeDirName(name) {
  if (!name) return 'unknown';
  return name
    .toLowerCase()
    .replace(/[^a-z0-9-_\s]/g, '')
    .replace(/\s+/g, '-')
    .replace(/-+/g, '-')
    .substring(0, 50);
}

// Copy or symlink file
async function copyOrLink(source, destination, useSymlinks = false) {
  await fs.mkdir(path.dirname(destination), { recursive: true });

  if (useSymlinks) {
    try {
      await fs.unlink(destination);
    } catch (error) {
      // File doesn't exist, that's fine
    }
    await fs.symlink(source, destination);
  } else {
    await fs.copyFile(source, destination);
  }
}

// Organize by period
async function organizeByPeriod(useSymlinks = false) {
  console.log('\nOrganizing tablets by historical period...\n');

  const files = await fs.readdir(CONFIG.sourceDir);
  const tablets = files.filter(f => f.match(/^P\d+\.jpg$/i));

  for (const file of tablets) {
    const pNumber = file.replace('.jpg', '');
    const metadata = await loadMetadata(pNumber);

    if (!metadata) continue;

    const period = metadata.period || 'unknown-period';
    const periodDir = sanitizeDirName(period);

    const source = path.join(CONFIG.sourceDir, file);
    const destination = path.join(CONFIG.outputBaseDir, 'by-period', periodDir, file);

    await copyOrLink(source, destination, useSymlinks);
    console.log(`  ${pNumber} → by-period/${periodDir}/`);
  }

  console.log('\n✓ Organization by period complete');
}

// Organize by genre
async function organizeByGenre(useSymlinks = false) {
  console.log('\nOrganizing tablets by genre...\n');

  const files = await fs.readdir(CONFIG.sourceDir);
  const tablets = files.filter(f => f.match(/^P\d+\.jpg$/i));

  for (const file of tablets) {
    const pNumber = file.replace('.jpg', '');
    const metadata = await loadMetadata(pNumber);

    if (!metadata) continue;

    const genre = metadata.genre || 'unknown-genre';
    const genreDir = sanitizeDirName(genre);

    const source = path.join(CONFIG.sourceDir, file);
    const destination = path.join(CONFIG.outputBaseDir, 'by-genre', genreDir, file);

    await copyOrLink(source, destination, useSymlinks);
    console.log(`  ${pNumber} → by-genre/${genreDir}/`);
  }

  console.log('\n✓ Organization by genre complete');
}

// Organize by collection
async function organizeByCollection(useSymlinks = false) {
  console.log('\nOrganizing tablets by collection...\n');

  const files = await fs.readdir(CONFIG.sourceDir);
  const tablets = files.filter(f => f.match(/^P\d+\.jpg$/i));

  for (const file of tablets) {
    const pNumber = file.replace('.jpg', '');
    const metadata = await loadMetadata(pNumber);

    if (!metadata) continue;

    const collection = metadata.collection || metadata.museum || 'unknown-collection';
    const collectionDir = sanitizeDirName(collection);

    const source = path.join(CONFIG.sourceDir, file);
    const destination = path.join(CONFIG.outputBaseDir, 'by-collection', collectionDir, file);

    await copyOrLink(source, destination, useSymlinks);
    console.log(`  ${pNumber} → by-collection/${collectionDir}/`);
  }

  console.log('\n✓ Organization by collection complete');
}

// Organize by language
async function organizeByLanguage(useSymlinks = false) {
  console.log('\nOrganizing tablets by language...\n');

  const files = await fs.readdir(CONFIG.sourceDir);
  const tablets = files.filter(f => f.match(/^P\d+\.jpg$/i));

  for (const file of tablets) {
    const pNumber = file.replace('.jpg', '');
    const metadata = await loadMetadata(pNumber);

    if (!metadata) continue;

    const language = metadata.language || 'unknown-language';
    const languageDir = sanitizeDirName(language);

    const source = path.join(CONFIG.sourceDir, file);
    const destination = path.join(CONFIG.outputBaseDir, 'by-language', languageDir, file);

    await copyOrLink(source, destination, useSymlinks);
    console.log(`  ${pNumber} → by-language/${languageDir}/`);
  }

  console.log('\n✓ Organization by language complete');
}

// Generate organization index
async function generateIndex() {
  console.log('\nGenerating organization index...\n');

  const index = {
    generatedAt: new Date().toISOString(),
    byPeriod: {},
    byGenre: {},
    byCollection: {},
    byLanguage: {}
  };

  const files = await fs.readdir(CONFIG.sourceDir);
  const tablets = files.filter(f => f.match(/^P\d+\.jpg$/i));

  for (const file of tablets) {
    const pNumber = file.replace('.jpg', '');
    const metadata = await loadMetadata(pNumber);

    if (!metadata) continue;

    // By period
    const period = metadata.period || 'Unknown';
    if (!index.byPeriod[period]) index.byPeriod[period] = [];
    index.byPeriod[period].push(pNumber);

    // By genre
    const genre = metadata.genre || 'Unknown';
    if (!index.byGenre[genre]) index.byGenre[genre] = [];
    index.byGenre[genre].push(pNumber);

    // By collection
    const collection = metadata.collection || metadata.museum || 'Unknown';
    if (!index.byCollection[collection]) index.byCollection[collection] = [];
    index.byCollection[collection].push(pNumber);

    // By language
    const language = metadata.language || 'Unknown';
    if (!index.byLanguage[language]) index.byLanguage[language] = [];
    index.byLanguage[language].push(pNumber);
  }

  const indexPath = path.join(CONFIG.metadataDir, 'organization-index.json');
  await fs.writeFile(indexPath, JSON.stringify(index, null, 2));

  console.log(`✓ Index saved to ${indexPath}\n`);
  console.log('Summary:');
  console.log(`  Periods: ${Object.keys(index.byPeriod).length}`);
  console.log(`  Genres: ${Object.keys(index.byGenre).length}`);
  console.log(`  Collections: ${Object.keys(index.byCollection).length}`);
  console.log(`  Languages: ${Object.keys(index.byLanguage).length}`);
}

// Main function
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('\nUsage: node organize-tablets.js <command> [options]\n');
    console.error('Commands:');
    console.error('  period       Organize by historical period');
    console.error('  genre        Organize by document genre');
    console.error('  collection   Organize by collection/museum');
    console.error('  language     Organize by language');
    console.error('  all          Organize using all methods');
    console.error('  index        Generate organization index JSON\n');
    console.error('Options:');
    console.error('  --symlink    Use symbolic links instead of copying files\n');
    console.error('Examples:');
    console.error('  node organize-tablets.js period');
    console.error('  node organize-tablets.js all --symlink');
    console.error('  node organize-tablets.js index');
    process.exit(1);
  }

  const command = args[0];
  const useSymlinks = args.includes('--symlink');

  console.log('\n=== Glintstone Tablet Organizer ===');
  if (useSymlinks) {
    console.log('Mode: Symbolic links (no duplication)');
  } else {
    console.log('Mode: Copy files');
  }

  try {
    switch (command) {
      case 'period':
        await organizeByPeriod(useSymlinks);
        break;

      case 'genre':
        await organizeByGenre(useSymlinks);
        break;

      case 'collection':
        await organizeByCollection(useSymlinks);
        break;

      case 'language':
        await organizeByLanguage(useSymlinks);
        break;

      case 'all':
        await organizeByPeriod(useSymlinks);
        await organizeByGenre(useSymlinks);
        await organizeByCollection(useSymlinks);
        await organizeByLanguage(useSymlinks);
        await generateIndex();
        break;

      case 'index':
        await generateIndex();
        break;

      default:
        console.error(`Unknown command: ${command}`);
        process.exit(1);
    }

    console.log('\n✓ Done!\n');

  } catch (error) {
    console.error(`\nError: ${error.message}`);
    console.error(error.stack);
    process.exit(1);
  }
}

if (require.main === module) {
  main();
}

module.exports = {
  organizeByPeriod,
  organizeByGenre,
  organizeByCollection,
  organizeByLanguage,
  generateIndex
};
