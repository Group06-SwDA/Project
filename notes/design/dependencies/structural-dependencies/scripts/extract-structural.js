const fs = require('fs');
const path = require('path');

const ROOT = './'; // run from repo root

const edges = {};

function walk(dir) {
  const files = fs.readdirSync(dir);

  for (const file of files) {
    const full = path.join(dir, file);

    if (full.includes('node_modules')) continue;

    const stat = fs.statSync(full);

    if (stat.isDirectory()) {
      walk(full);
    } else if (full.endsWith('.ts') || full.endsWith('.tsx')) {
      processFile(full);
    }
  }
}

function getCurrentPlugin(filePath) {
  // normalize slashes (important on Windows)
  const normalized = filePath.replace(/\\/g, '/');

  let match = normalized.match(/plugins\/([^/]+)/);
  if (match) return match[1];

  match = normalized.match(/packages\/([^/]+)/);
  if (match) return match[1];

  return null;
}

function extractImports(content) {
  const regex = /from\s+['"](@backstage\/plugin-[^'"]+)['"]/g;
  const results = [];

  let match;
  while ((match = regex.exec(content))) {
    results.push(match[1]);
  }

  return results;
}

function normalizePlugin(pkg) {
  return pkg
    .replace('@backstage/plugin-', '')
    .replace(/-react$/, '')
    .replace(/-node$/, '');
}

function processFile(file) {
  const plugin = getCurrentPlugin(file);
  if (!plugin) return;

  const content = fs.readFileSync(file, 'utf-8');
  const imports = extractImports(content);

  for (const imp of imports) {
    const target = normalizePlugin(imp);

    if (plugin === target) continue;

    const key = `${plugin}-->${target}`;
    edges[key] = (edges[key] || 0) + 1;
  }
}

walk(ROOT);

// save result
fs.writeFileSync('structural-deps.json', JSON.stringify(edges, null, 2));

console.log('Done. Output: structural-deps.json');
