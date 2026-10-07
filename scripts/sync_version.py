from pathlib import Path
import re


ROOT = Path(__file__).resolve().parents[1]
version = (ROOT / "version.txt").read_text(encoding="utf-8").strip()
if not re.fullmatch(r"\d+\.\d+\.\d+", version):
    raise SystemExit(f"Invalid version: {version}")

site = ROOT / "site" / "index.html"
text = site.read_text(encoding="utf-8")
text = re.sub(r'GENIE Report Studio \d+\.\d+\.\d+', f'GENIE Report Studio {version}', text)
text = re.sub(r'Version \d+\.\d+\.\d+ ·', f'Version {version} ·', text)
site.write_text(text, encoding="utf-8")
