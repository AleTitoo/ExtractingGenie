const fs = require('fs');
const path = require('path');
const crypto = require('crypto');

const hash = file => crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');

function migrateLibrary(legacyRoot, newRoot) {
  const marker = path.join(newRoot, 'library-migration-v1.json');
  if (fs.existsSync(marker)) return;
  const source = path.join(legacyRoot, 'library');
  if (!fs.existsSync(source) || path.resolve(legacyRoot) === path.resolve(newRoot)) return;
  const target = path.join(newRoot, 'library');
  fs.mkdirSync(target, { recursive: true });
  for (const entry of fs.readdirSync(source, { withFileTypes: true })) {
    if (!entry.isFile()) continue;
    const from = path.join(source, entry.name), to = path.join(target, entry.name);
    if (fs.existsSync(to)) {
      if (hash(from) !== hash(to)) throw Error(`Library migration found conflicting files: ${entry.name}. Both copies have been retained.`);
    } else {
      fs.copyFileSync(from, to, fs.constants.COPYFILE_EXCL);
      if (hash(from) !== hash(to)) throw Error(`Library migration verification failed: ${entry.name}`);
    }
  }
  fs.writeFileSync(marker, JSON.stringify({ source: legacyRoot, completed: new Date().toISOString() }));
}

module.exports = { migrateLibrary };
