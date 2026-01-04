#!/usr/bin/env node

/**
 * Glintstone Tablet Image Downloader
 *
 * Downloads cuneiform tablet images from CDLI (Cuneiform Digital Library Initiative)
 * with validation, retry logic, and metadata extraction.
 */

const https = require('https');
const http = require('http');
const fs = require('fs').promises;
const fsSync = require('fs');
const path = require('path');

// Configuration
const CONFIG = {
  cdliPhotoBaseUrl: 'https://cdli.earth/dl/photo',
  cdliApiBaseUrl: 'https://cdli.earth/api',
  outputDir: path.join(__dirname, '..', 'public', 'images', 'tablets', 'authentic'),
  metadataDir: path.join(__dirname, '..', 'data', 'tablets'),
  minImageSize: 1024, // 1KB minimum - anything smaller is likely an error page
  maxRetries: 3,
  retryDelay: 2000, // 2 seconds
  requestTimeout: 30000, // 30 seconds
  userAgent: 'Glintstone-Tablet-Downloader/1.0'
};

// Utility: Sleep function for retry delays
const sleep = (ms) => new Promise(resolve => setTimeout(resolve, ms));

// Utility: Check if a buffer is a valid image
function isValidImage(buffer) {
  if (buffer.length < CONFIG.minImageSize) {
    return false;
  }

  // Check for common image file signatures (magic numbers)
  const signatures = {
    jpg: [0xFF, 0xD8, 0xFF],
    png: [0x89, 0x50, 0x4E, 0x47],
    gif: [0x47, 0x49, 0x46],
    tiff: [0x49, 0x49, 0x2A, 0x00], // Little-endian TIFF
    tiff2: [0x4D, 0x4D, 0x00, 0x2A], // Big-endian TIFF
  };

  // Check JPG signature
  if (buffer[0] === 0xFF && buffer[1] === 0xD8 && buffer[2] === 0xFF) {
    return true;
  }

  // Check PNG signature
  if (buffer[0] === 0x89 && buffer[1] === 0x50 && buffer[2] === 0x4E && buffer[3] === 0x47) {
    return true;
  }

  // Check for HTML error pages
  const text = buffer.toString('utf8', 0, Math.min(200, buffer.length));
  if (text.includes('<html>') || text.includes('404') || text.includes('nginx')) {
    return false;
  }

  return true;
}

// Download file with retry logic
async function downloadFile(url, retryCount = 0) {
  return new Promise((resolve, reject) => {
    const protocol = url.startsWith('https') ? https : http;

    const options = {
      headers: {
        'User-Agent': CONFIG.userAgent
      },
      timeout: CONFIG.requestTimeout
    };

    const request = protocol.get(url, options, (response) => {
      // Handle redirects
      if (response.statusCode === 301 || response.statusCode === 302) {
        const redirectUrl = response.headers.location;
        console.log(`    Redirecting to: ${redirectUrl}`);
        return downloadFile(redirectUrl, retryCount).then(resolve).catch(reject);
      }

      if (response.statusCode !== 200) {
        return reject(new Error(`HTTP ${response.statusCode}: ${response.statusMessage}`));
      }

      const chunks = [];

      response.on('data', (chunk) => {
        chunks.push(chunk);
      });

      response.on('end', () => {
        const buffer = Buffer.concat(chunks);
        resolve(buffer);
      });

      response.on('error', reject);
    });

    request.on('error', reject);
    request.on('timeout', () => {
      request.destroy();
      reject(new Error('Request timeout'));
    });
  });
}

// Download tablet image with validation and retry
async function downloadTabletImage(pNumber, retryCount = 0) {
  const imageUrl = `${CONFIG.cdliPhotoBaseUrl}/${pNumber}.jpg`;

  try {
    console.log(`  Downloading ${pNumber} from ${imageUrl}...`);
    const buffer = await downloadFile(imageUrl);

    // Validate the downloaded content
    if (!isValidImage(buffer)) {
      throw new Error('Downloaded file is not a valid image (likely an error page)');
    }

    console.log(`    ✓ Valid image received (${(buffer.length / 1024).toFixed(1)} KB)`);
    return buffer;

  } catch (error) {
    if (retryCount < CONFIG.maxRetries) {
      console.log(`    ✗ Failed: ${error.message}. Retrying (${retryCount + 1}/${CONFIG.maxRetries})...`);
      await sleep(CONFIG.retryDelay);
      return downloadTabletImage(pNumber, retryCount + 1);
    } else {
      throw new Error(`Failed after ${CONFIG.maxRetries} retries: ${error.message}`);
    }
  }
}

// Fetch tablet metadata from CDLI
async function fetchTabletMetadata(pNumber) {
  // CDLI doesn't have a public REST API, so we'll create a basic metadata structure
  // that can be manually populated or scraped from the website
  return {
    id: pNumber,
    cdliUrl: `https://cdli.earth/${pNumber}`,
    downloadedAt: new Date().toISOString(),
    period: null,
    genre: null,
    collection: null,
    museum: null,
    accessionNumber: null,
    dimensions: null,
    material: null,
    language: null,
    provenience: null,
    excavationNumber: null,
    description: null,
    translations: [],
    transcriptions: [],
    tags: [],
    notes: ''
  };
}

// Save image to disk
async function saveImage(pNumber, buffer) {
  await fs.mkdir(CONFIG.outputDir, { recursive: true });
  const filePath = path.join(CONFIG.outputDir, `${pNumber}.jpg`);
  await fs.writeFile(filePath, buffer);
  console.log(`    ✓ Saved to ${filePath}`);
  return filePath;
}

// Save metadata to JSON
async function saveMetadata(pNumber, metadata) {
  await fs.mkdir(CONFIG.metadataDir, { recursive: true });
  const filePath = path.join(CONFIG.metadataDir, `${pNumber}.json`);
  await fs.writeFile(filePath, JSON.stringify(metadata, null, 2));
  console.log(`    ✓ Metadata saved to ${filePath}`);
  return filePath;
}

// Load existing metadata or create new
async function loadOrCreateMetadata(pNumber) {
  const filePath = path.join(CONFIG.metadataDir, `${pNumber}.json`);
  try {
    const data = await fs.readFile(filePath, 'utf8');
    return JSON.parse(data);
  } catch (error) {
    // File doesn't exist, create new metadata
    return await fetchTabletMetadata(pNumber);
  }
}

// Process a single tablet
async function processTablet(pNumber) {
  console.log(`\nProcessing ${pNumber}...`);

  try {
    // Check if image already exists and is valid
    const existingPath = path.join(CONFIG.outputDir, `${pNumber}.jpg`);
    try {
      const stats = await fs.stat(existingPath);
      if (stats.size >= CONFIG.minImageSize) {
        const buffer = await fs.readFile(existingPath);
        if (isValidImage(buffer)) {
          console.log(`  ✓ Valid image already exists (${(stats.size / 1024).toFixed(1)} KB)`);

          // Still update metadata
          const metadata = await loadOrCreateMetadata(pNumber);
          await saveMetadata(pNumber, metadata);

          return { pNumber, status: 'already_exists', size: stats.size };
        } else {
          console.log(`  ! Existing file is invalid, re-downloading...`);
        }
      }
    } catch (error) {
      // File doesn't exist, continue with download
    }

    // Download image
    const imageBuffer = await downloadTabletImage(pNumber);

    // Save image
    await saveImage(pNumber, imageBuffer);

    // Create/update metadata
    const metadata = await loadOrCreateMetadata(pNumber);
    metadata.downloadedAt = new Date().toISOString();
    metadata.fileSize = imageBuffer.length;
    await saveMetadata(pNumber, metadata);

    return {
      pNumber,
      status: 'success',
      size: imageBuffer.length
    };

  } catch (error) {
    console.error(`  ✗ Error processing ${pNumber}: ${error.message}`);
    return {
      pNumber,
      status: 'failed',
      error: error.message
    };
  }
}

// Main function
async function main() {
  const args = process.argv.slice(2);

  if (args.length === 0) {
    console.error('Usage: node download-tablets.js <P-number> [P-number2] [P-number3] ...');
    console.error('   or: node download-tablets.js --file <path-to-list.txt>');
    console.error('\nExample:');
    console.error('  node download-tablets.js P005377 P010012 P001251');
    console.error('  node download-tablets.js --file tablet-list.txt');
    process.exit(1);
  }

  let pNumbers = [];

  // Load from file if --file option
  if (args[0] === '--file' && args[1]) {
    const fileContent = await fs.readFile(args[1], 'utf8');
    pNumbers = fileContent
      .split('\n')
      .map(line => line.trim())
      .filter(line => line && !line.startsWith('#') && line.match(/^P\d+$/i));
  } else {
    pNumbers = args.filter(arg => arg.match(/^P\d+$/i));
  }

  if (pNumbers.length === 0) {
    console.error('No valid P-numbers found. P-numbers must be in format: P123456');
    process.exit(1);
  }

  console.log(`\n=== Glintstone Tablet Downloader ===`);
  console.log(`Downloading ${pNumbers.length} tablets from CDLI\n`);

  const results = [];

  for (const pNumber of pNumbers) {
    const result = await processTablet(pNumber);
    results.push(result);
  }

  // Summary
  console.log('\n=== Summary ===');
  const successful = results.filter(r => r.status === 'success' || r.status === 'already_exists');
  const failed = results.filter(r => r.status === 'failed');

  console.log(`Total: ${results.length}`);
  console.log(`Successful: ${successful.length}`);
  console.log(`Failed: ${failed.length}`);

  if (failed.length > 0) {
    console.log('\nFailed downloads:');
    failed.forEach(r => {
      console.log(`  - ${r.pNumber}: ${r.error}`);
    });
  }

  // Save summary report
  const reportPath = path.join(CONFIG.metadataDir, `download-report-${Date.now()}.json`);
  await fs.mkdir(CONFIG.metadataDir, { recursive: true });
  await fs.writeFile(reportPath, JSON.stringify({
    timestamp: new Date().toISOString(),
    total: results.length,
    successful: successful.length,
    failed: failed.length,
    results
  }, null, 2));

  console.log(`\nDetailed report saved to: ${reportPath}`);
}

// Run if executed directly
if (require.main === module) {
  main().catch(error => {
    console.error('Fatal error:', error);
    process.exit(1);
  });
}

module.exports = {
  downloadTabletImage,
  processTablet,
  isValidImage,
  CONFIG
};
