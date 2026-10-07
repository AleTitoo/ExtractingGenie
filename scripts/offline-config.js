const fs = require('fs');
const config = JSON.parse(fs.readFileSync('package.json', 'utf8')).build;
config.appId = 'com.aletitoo.platinum189.offline';
config.productName = 'Platinum-189 Lab';
config.win.icon = 'assets/platinum-189-offline.ico';
config.directories.output = 'dist-offline';
config.extraResources = [
  { from: 'backend-offline/Platinum-189.exe', to: 'backend/Platinum-189.exe' },
  { from: 'assets/platinum-189-offline.ico', to: 'platinum-189-offline-v3.ico' },
  { from: 'build/offline-edition.json', to: 'offline-edition.json' }
];
fs.writeFileSync('build/offline-package.json', JSON.stringify(config, null, 2));
