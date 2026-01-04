#!/usr/bin/env node

/**
 * Validate existing tablet images
 * Checks all images in the authentic directory and identifies invalid ones
 */

const fs = require('fs').promises;
const path = require('path');

const IMAGES_DIR = path.join(__dirname, '..', 'public', 'images', 'tablets', 'authentic');
const MIN_SIZE = 1024; // 1KB minimum

function isValidImage(buffer) {
  if (buffer.length < MIN_SIZE) {
    return { valid: false, reason: 'File too small (likely error page)' };
  }

  // Check for JPG signature
  if (buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF) {
    return { valid: true };
  }

  // Check for PNG signature
  if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
    return { valid: true };
  }

  // Check for HTML error pages
  const text = buffer.toString('utf8', 0, Math.min(200, buffer.length));
  if (text.includes('<html>') || text.includes('404') || text.includes('nginx')) {
    return { valid: false, reason: 'HTML error page instead of image' };
  }

  return { valid: false, reason: 'Unknown file format' };
}

async function validateImages() {
  console.log('\n=== Glintstone Image Validator ===\n');

  try {
    const files = await fs.readdir(IMAGES_DIR);
    const imageFiles = files.filter(f => f.match(/\.(jpg|jpeg|png|gif)$/i));

    if (imageFiles.length === 0) {
      console.log('No image files found in', IMAGES_DIR);
      return;
    }

    console.log(`Found ${imageFiles.length} image files to validate\n`);

    const results = {
      valid: [],
      invalid: []
    };

    for (const file of imageFiles) {
      const filePath = path.join(IMAGES_DIR, file);
      const stats = await fs.stat(filePath);
      const buffer = await fs.readFile(filePath);

      const validation = isValidImage(buffer);
      const sizeKB = (stats.size / 1024).toFixed(1);

      if (validation.valid) {
        console.log(`✓ ${file.padEnd(20)} ${sizeKB.padStart(8)} KB - Valid`);
        results.valid.push({ file, size: stats.size });
      } else {
        console.log(`✗ ${file.padEnd(20)} ${sizeKB.padStart(8)} KB - ${validation.reason}`);
        results.invalid.push({ file, size: stats.size, reason: validation.reason });
      }
    }

    // Summary
    console.log('\n=== Summary ===');
    console.log(`Total files: ${imageFiles.length}`);
    console.log(`Valid images: ${results.valid.length}`);
    console.log(`Invalid files: ${results.invalid.length}`);

    if (results.invalid.length > 0) {
      console.log('\n=== Invalid Files ===');
      console.log('These files should be re-downloaded:\n');
      results.invalid.forEach(item => {
        const pNumber = item.file.replace(/\.(jpg|jpeg|png|gif)$/i, '');
        console.log(`  ${pNumber}`);
      });

      console.log('\nTo re-download these tablets, run:');
      const pNumbers = results.invalid.map(item =>
        item.file.replace(/\.(jpg|jpeg|png|gif)$/i, '')
      ).join(' ');
      console.log(`  node scripts/download-tablets.js ${pNumbers}`);
    }

    console.log('');

  } catch (error) {
    console.error('Error:', error.message);
    process.exit(1);
  }
}

if (require.main === module) {
  validateImages();
}

module.exports = { validateImages, isValidImage };
