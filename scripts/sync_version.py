from pathlib import Path
import re
import json


ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"Invalid version: {version}")

site = ROOT / "site" / "index.html"
text = site.read_text(encoding="utf-8")
text = re.sub(r'Platinum-189 \d+\.\d+\.\d+', f'Platinum-189 {version}', text)
text = re.sub(r'Version \d+\.\d+\.\d+ ·', f'Version {version} ·', text)
site.write_text(text, encoding="utf-8")
package = ROOT / 'package.json'
data = json.loads(package.read_text(encoding='utf-8'))
data['version'] = version
package.write_text(json.dumps(data, indent=2) + '\n', encoding='utf-8')
