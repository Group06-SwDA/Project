const fs = require('fs');
const path = require('path');

const ROOT = './backstage';
const results = {};

function walk(dir) {
  const files = fs.readdirSync(dir);
  for (const file of files) {
    const full = path.join(dir, file);
    if (full.includes('node_modules')) continue;
    const stat = fs.statSync(full);
    if (stat.isDirectory()) {
      walk(full);
    } else if (file === 'package.json') {
      try {
        const pkg = JSON.parse(fs.readFileSync(full));
        if (pkg.dependencies && pkg.name) {
          results[pkg.name] = Object.keys(pkg.dependencies);
        }
      } catch(e) {}
    }
  }
}

walk(ROOT);
fs.writeFileSync('runtime-deps.json', JSON.stringify(results, null, 2));
console.log(`Done! Found ${Object.keys(results).length} packages with runtime dependencies.`);
