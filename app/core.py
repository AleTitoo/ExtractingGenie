"""Local, conservative extraction of GENIE interference-corrected summaries."""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import json
import re
import tempfile
import os

VERSION = 3
NUM = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?'
ROW = re.compile(rf'^([X&?@# ]*)([A-Z][a-z]?-[0-9]+(?:m[0-9]*)?)\s*([&?@# ]*)\s+({NUM})(?:\s+({NUM})\s+({NUM}))?$')

def parse_pages(pages, filename):
    text = '\n'.join(pages)
    rows, active, complete, units, sigma = [], False, False, None, None
    sections = 0
    for page_no, page in enumerate(pages, 1):
        for line in page.splitlines():
            line = line.strip()
            compact = re.sub(r'\s+', '', line).strip('*')
            if compact == 'INTERFERENCECORRECTEDREPORT':
                sections += 1
                if sections > 1:
                    raise ValueError('Multiple weighted-mean summaries: split the report before import.')
                active = True
                continue
            if not active:
                continue
            if 'Confidence' in line and 'Uncertainty' in line:
                match = re.search(r'\(([^)]+)\)', line)
                if match:
                    units = match[1]
            if line.startswith('Errors quoted at'):
                match = re.fullmatch(rf'Errors quoted at\s+({NUM})\s+sigma', line)
                if not match:
                    raise ValueError('Unrecognized uncertainty convention.')
                sigma = match[1]
                complete, active = True, False
                continue
            match = ROW.fullmatch(line)
            if match:
                before, nuclide, after, confidence, activity, uncertainty = match.groups()
                flags = ''.join(dict.fromkeys((before + after).replace(' ', '')))
                if not Decimal(0) <= Decimal(confidence) <= Decimal(1):
                    raise ValueError(f'Invalid confidence for {nuclide}.')
                if uncertainty is not None and Decimal(uncertainty) < 0:
                    raise ValueError(f'Negative uncertainty for {nuclide}.')
                status = ('Rejected by interference analysis' if 'X' in flags else
                          'Undetermined solution' if '?' in flags else
                          'Missing weighted activity' if activity is None else 'Reported')
                rows.append(dict(nuclide=nuclide, confidence=confidence, activity=activity,
                                 uncertainty=uncertainty, flags=flags, status=status,
                                 page=page_no, raw_line=line))
            elif re.search(r'[A-Z][a-z]?-[0-9]', line):
                raise ValueError(f'Unrecognized summary row on page {page_no}: {line}')
    if not complete or not rows or not units or not sigma:
        raise ValueError('Complete weighted-mean summary, units, or sigma not found. No results imported.')
    if len({r['nuclide'] for r in rows}) != len(rows):
        raise ValueError('Duplicate nuclides in summary; manual review required.')
    def field(label):
        m = re.search(r'^' + re.escape(label) + r'[ \t]*:[ \t]*([^\n]*)', text, re.M)
        return m[1].strip() if m else ''
    def numeric_field(label, suffix):
        value = field(label)
        match = re.fullmatch(rf'({NUM})\s*{re.escape(suffix)}', value)
        return match[1] if match else ''
    return dict(parser_version=VERSION, source_name=filename, sample_label=Path(filename).stem,
                sample_id=field('Sample Identification'), sample_title=field('Sample Title'),
                generated=field('Report Generated On'), acquired=field('Acquisition Started'),
                live_time=numeric_field('Live Time', 'seconds'),
                real_time=numeric_field('Real Time', 'seconds'),
                dead_time=numeric_field('Dead Time', '%'),
                efficiency_id=field('Efficiency ID'),
                units=units, sigma=sigma, rows=rows)

def parse_pdf(path):
    import pdfplumber
    with pdfplumber.open(path) as pdf:
        return parse_pages([p.extract_text() or '' for p in pdf.pages], Path(path).name)

def atomic_write(path, data):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    fd, temp = tempfile.mkstemp(dir=path.parent, suffix='.tmp')
    try:
        with os.fdopen(fd, 'wb') as f:
            f.write(data)
        os.replace(temp, path)
    finally:
        if os.path.exists(temp):
            os.unlink(temp)

def import_report(path, library):
    library = Path(library)
    data = Path(path).read_bytes()
    digest = hashlib.sha256(data).hexdigest()
    record_path = library / (digest + '.json')
    existed = record_path.exists()
    if existed:
        saved = json.loads(record_path.read_text(encoding='utf-8'))
        if saved.get('parser_version') == VERSION:
            return saved, False
    # Parse the exact bytes being archived, even if the original is later changed.
    import io
    import pdfplumber
    with pdfplumber.open(io.BytesIO(data)) as pdf:
        report = parse_pages([p.extract_text() or '' for p in pdf.pages], Path(path).name)
    report['sha256'] = digest
    atomic_write(library / (digest + '.pdf'), data)
    atomic_write(record_path, json.dumps(report, indent=2).encode('utf-8'))
    return report, not existed

def load_library(library):
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(Path(library).glob('*.json'))]

def selected(rows, threshold='0.7', include_below=False):
    cutoff = Decimal(str(threshold))
    if not cutoff.is_finite() or not 0 <= cutoff <= 1:
        raise ValueError('Confidence threshold must be between 0 and 1.')
    return [r for r in rows if include_below or Decimal(r['confidence']) > cutoff]

HEADERS = ['Report / sample label', 'Sample identification', 'Nuclide', 'ID confidence',
           'Weighted mean activity', 'Activity uncertainty', 'Units', 'Sigma', 'Status',
           'GENIE flags', 'PDF page', 'Report generated', 'Acquisition started',
           'Source PDF', 'SHA256', 'Selection rule']

def export_csv(reports, target, library, threshold='0.7', include_below=False):
    import io
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(HEADERS)
    count = 0
    for report in reports:
        for r in selected(report['rows'], threshold, include_below):
            values = [report['sample_label'], report['sample_id'], r['nuclide'], r['confidence'],
                      r['activity'], r['uncertainty'], report['units'], report['sigma'],
                      r['status'], r['flags'], r['page'], report['generated'], report['acquired'],
                      str((Path(library) / (report['sha256'] + '.pdf')).resolve()), report['sha256'],
                      'All rows' if include_below else f'ID confidence > {threshold}']
            # Protect text fields from spreadsheet formula interpretation.
            for i in [0,1,2,6,8,9,11,12,13,14,15]:
                if isinstance(values[i], str) and values[i].startswith(('=', '+', '-', '@')):
                    values[i] = "'" + values[i]
            writer.writerow(values)
            count += 1
    atomic_write(target, stream.getvalue().encode('utf-8-sig'))
    return count
