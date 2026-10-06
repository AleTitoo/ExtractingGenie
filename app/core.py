"""Local, conservative extraction of GENIE interference-corrected summaries."""
from pathlib import Path
from decimal import Decimal
import csv
import hashlib
import json
import re
import tempfile
import os

VERSION = 4
NUM = r'[+-]?(?:\d+(?:\.\d*)?|\.\d+)(?:[Ee][+-]?\d+)?'
ROW = re.compile(rf'^([X&?@# ]*)([A-Z][a-z]?-[0-9]+(?:m[0-9]*)?)\s*([&?@# ]*)\s+({NUM})(?:\s+({NUM})\s+({NUM}))?$')
LINE = re.compile(rf'^({NUM})(\*)?\s*([@# ]*)\s+({NUM})(?:\s+({NUM})\s+({NUM}))?$')
LINE_START = re.compile(rf'^([A-Z][a-z]?-[0-9]+(?:m[0-9]*)?)\s+({NUM})\s+(.+)$')

def relative_uncertainty(activity, uncertainty):
    if activity in (None, '') or uncertainty in (None, ''):
        return None
    activity_value = Decimal(str(activity))
    if not activity_value.is_finite() or activity_value == 0:
        return None
    uncertainty_value = Decimal(str(uncertainty))
    if not uncertainty_value.is_finite() or uncertainty_value < 0:
        return None
    return abs(uncertainty_value / activity_value) * Decimal(100)

def _line_row(text, page_no, nuclide, confidence, raw_line=None):
    match = LINE.fullmatch(text.strip())
    if not match:
        return None
    energy, found, flags, yield_percent, activity, uncertainty = match.groups()
    flags = ''.join(dict.fromkeys(flags.replace(' ', '')))
    status = ('Not found in spectrum' if not found else
              'Excluded from weighted mean' if '#' in flags else
              'Not used in weighted mean' if '@' in flags else
              'Used in weighted mean')
    return dict(nuclide=nuclide, confidence=confidence, energy=energy,
                found=bool(found), yield_percent=yield_percent,
                activity=activity, uncertainty=uncertainty, flags=flags,
                status=status, page=page_no, raw_line=(raw_line or text).strip())

def parse_pages(pages, filename):
    text = '\n'.join(pages)
    rows, active, complete, units, sigma = [], False, False, None, None
    line_rows, line_active, current_nuclide, current_confidence = [], False, None, None
    sections = 0
    for page_no, page in enumerate(pages, 1):
        page_lines = page.splitlines()
        interference_page = any(value.startswith('Interference Corrected Activity Report') for value in page_lines[:3])
        if interference_page and any(re.sub(r'\s+', '', value).strip('*') == 'NUCLIDEIDENTIFICATIONREPORT' for value in page_lines):
            line_active = True
        for line in page_lines:
            line = line.strip()
            compact = re.sub(r'\s+', '', line).strip('*')
            if line_active:
                if line.startswith('* = Energy line found'):
                    line_active = False
                else:
                    start = LINE_START.fullmatch(line)
                    detail_text = line
                    if start:
                        current_nuclide, current_confidence, detail_text = start.groups()
                    if current_nuclide:
                        detail = _line_row(detail_text, page_no, current_nuclide, current_confidence, line)
                        if detail:
                            line_rows.append(detail)
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
                relative = relative_uncertainty(activity, uncertainty)
                rows.append(dict(nuclide=nuclide, confidence=confidence, activity=activity,
                                 uncertainty=uncertainty, flags=flags, status=status,
                                 relative_uncertainty=(format(relative, 'f') if relative is not None else None),
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
                units=units, sigma=sigma, rows=rows, line_rows=line_rows)

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
        targets = report['rows'] + report.get('line_rows', [])
        for target in targets:
            try:
                lines = pdf.pages[target['page'] - 1].extract_text_lines(return_chars=False)
                wanted = re.sub(r'\s+', ' ', target['raw_line']).strip()
                match = next((line for line in lines
                              if re.sub(r'\s+', ' ', line.get('text', '')).strip() == wanted), None)
                if match:
                    target['bbox'] = [match['x0'], match['top'], match['x1'], match['bottom']]
            except Exception:
                pass
    report['sha256'] = digest
    atomic_write(library / (digest + '.pdf'), data)
    atomic_write(record_path, json.dumps(report, indent=2).encode('utf-8'))
    return report, not existed

def load_library(library):
    return [json.loads(p.read_text(encoding='utf-8')) for p in sorted(Path(library).glob('*.json'))]

def upgrade_library(library):
    """Reparse archived PDFs when extraction logic changes, without risking old records."""
    errors = []
    library = Path(library)
    for record_path in sorted(library.glob('*.json')):
        try:
            saved = json.loads(record_path.read_text(encoding='utf-8'))
            if saved.get('parser_version') == VERSION:
                continue
            pdf_path = library / (record_path.stem + '.pdf')
            if not pdf_path.exists():
                raise FileNotFoundError('archived source PDF is missing')
            import_report(pdf_path, library)
        except Exception as exc:
            errors.append(f'{record_path.stem}: {exc}')
    return errors

def selected(rows, threshold='0.7', include_below=False):
    cutoff = Decimal(str(threshold))
    if not cutoff.is_finite() or not 0 <= cutoff <= 1:
        raise ValueError('Confidence threshold must be between 0 and 1.')
    return [r for r in rows if include_below or Decimal(r['confidence']) > cutoff]

def review_threshold(value='10'):
    threshold = Decimal(str(value))
    if not threshold.is_finite() or threshold < 0:
        raise ValueError('Uncertainty review threshold must be zero or greater.')
    return threshold

HEADERS = ['Report / sample label', 'Sample identification', 'Nuclide', 'ID confidence',
           'Weighted mean activity', 'Activity uncertainty', 'Relative uncertainty (%)',
           'Review flag', 'Units', 'Sigma', 'Status',
           'GENIE flags', 'PDF page', 'Report generated', 'Acquisition started',
           'Source PDF', 'SHA256', 'Selection rule']

def export_csv(reports, target, library, threshold='0.7', include_below=False, uncertainty_threshold='10'):
    import io
    stream = io.StringIO(newline='')
    writer = csv.writer(stream)
    writer.writerow(HEADERS)
    count = 0
    uncertainty_cutoff = review_threshold(uncertainty_threshold)
    for report in reports:
        for r in selected(report['rows'], threshold, include_below):
            relative = relative_uncertainty(r.get('activity'), r.get('uncertainty'))
            review = ('Cannot assess relative uncertainty' if relative is None else
                      f'Review: relative uncertainty > {uncertainty_threshold}%' if relative > uncertainty_cutoff else '')
            values = [report['sample_label'], report['sample_id'], r['nuclide'], r['confidence'],
                      r['activity'], r['uncertainty'], format(relative, 'f') if relative is not None else '',
                      review, report['units'], report['sigma'],
                      r['status'], r['flags'], r['page'], report['generated'], report['acquired'],
                      str((Path(library) / (report['sha256'] + '.pdf')).resolve()), report['sha256'],
                      'All rows' if include_below else f'ID confidence > {threshold}']
            # Protect text fields from spreadsheet formula interpretation.
            for i in [0,1,2,7,8,9,10,11,13,14,15,16,17]:
                if isinstance(values[i], str) and values[i].startswith(('=', '+', '-', '@')):
                    values[i] = "'" + values[i]
            writer.writerow(values)
            count += 1
    atomic_write(target, stream.getvalue().encode('utf-8-sig'))
    return count
