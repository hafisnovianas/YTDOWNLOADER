const ytdlp = require('yt-dlp-exec');
console.log('Type:', typeof ytdlp);
console.log('Keys:', Object.keys(ytdlp));

const fs = require('fs');
const path = require('path');

// Check for yt-dlp binary in node_modules
const ytdlpDir = path.join(__dirname, 'node_modules', 'yt-dlp-exec');
if (fs.existsSync(ytdlpDir)) {
  console.log('yt-dlp-exec contents:', fs.readdirSync(ytdlpDir));
}

// Check .bin
const binDir = path.join(__dirname, 'node_modules', '.bin');
if (fs.existsSync(binDir)) {
  const bins = fs.readdirSync(binDir).filter(f => f.toLowerCase().includes('yt'));
  console.log('.bin yt entries:', bins);
}

// Check for @distube/yt-dlp or yt-dlp-wrap
const nodeModules = path.join(__dirname, 'node_modules');
const allPackages = fs.readdirSync(nodeModules);
const ytPackages = allPackages.filter(p => p.toLowerCase().includes('yt') || p.toLowerCase().includes('dlp'));
console.log('YT related packages:', ytPackages);

// Try to use it as a function
console.log('\nTrying to extract binary path...');
try {
  // yt-dlp-exec@1.x exposes the path differently
  const result = ytdlp.toString();
  console.log('toString:', result.substring(0, 200));
} catch(e) {
  console.log('toString error:', e.message);
}

// Check if ytDlpPath exists as a property
for (const key of Object.keys(ytdlp)) {
  console.log(`ytdlp.${key}:`, typeof ytdlp[key], String(ytdlp[key]).substring(0, 100));
}
