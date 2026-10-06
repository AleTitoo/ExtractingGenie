"""One measurement per row, using the supplied lab CSV's column order.

No decay correction or unit conversion is performed. The original first
experiment's measurement rows, EOB timestamp, and constants are not reused.
"""
import csv
import io
import re
from pathlib import Path
from core import selected, atomic_write, relative_uncertainty, review_threshold

NUCLIDES = ['Pt-189','Re-181','Os-183','Ir-184','Ir-185','Ir-186','Ir-187',
            'Ir-188','Ir-194','Pt-188','Pt-191','Au-191','Au-192','Au-198','Au-200']
METADATA = ['Foil no.','Time of counting','File name','Distance (cm)','Time (s)',
            'Geometry file','Deadtime(%)','time elapsed (s)']
AUDIT = ['Activity units','Uncertainty sigma','Selection rule','GENIE flags / excluded results',
         'Metadata notes','Efficiency ID (as reported)','Source PDF','PDF summary page(s)',
         'Report generated','SHA256']

def safe_text(value):
    value = str(value or '')
    return "'"+value if value.startswith(('=','+','-','@')) else value

def build_lab_rows(reports, threshold='0.7', include_below=False, uncertainty_threshold='10'):
    if not reports:
        raise ValueError('Select at least one report.')
    # Validate the filter even when the report contains no qualifying rows.
    selected([],threshold,include_below)
    uncertainty_cutoff = review_threshold(uncertainty_threshold)
    units = {r['units'] for r in reports}
    if len(units) != 1:
        raise ValueError('Reports have different activity units. Export each unit group separately.')
    extras = sorted({r['nuclide'] for p in reports for r in p['rows']} - set(NUCLIDES))
    isotopes = NUCLIDES + extras
    width = 8 + 5*len(isotopes) - 1
    note = ['']*(width+len(AUDIT)+1)
    note[1] = 'End of beam: not supplied'
    note[8] = f'Activity and error: {next(iter(units))}; copied unchanged from GENIE'
    note[13] = 'EOB A, EOB error and elapsed time intentionally blank; no decay correction'
    group = ['']*len(note)
    header = METADATA[:]
    for i, isotope in enumerate(isotopes):
        group[8+5*i] = isotope
        header.extend(['A','error','EOB A','error'])
        if i < len(isotopes)-1:
            header.append('')
    header += ['']+AUDIT
    result = [note,group,header]
    for report in sorted(reports,key=lambda r:(r['sample_label'],r['sha256'])):
        row = ['']*len(note)
        label = report['sample_label']
        foil = re.search(r'(?:^|_)([A-Za-z]+) Foil\s+(\d+)(?:_|$)',label)
        distance = re.search(r'_(\d+(?:\.\d+)?)cm_',label)
        row[0] = f'{foil[1]}-{foil[2]}' if foil else ''
        row[1] = safe_text(report['acquired'])
        row[2] = safe_text(label)
        row[3] = distance[1] if distance else ''
        row[4] = report.get('live_time','')
        # Efficiency ID is a calibration identifier, not necessarily a geometry filename.
        row[6] = report.get('dead_time','')
        chosen = {r['nuclide'] for r in selected(report['rows'],threshold,include_below)}
        flags=[]
        for r in report['rows']:
            if r['nuclide'] not in chosen:
                flags.append(f"{r['nuclide']}: below/equal cutoff ({r['confidence']})")
                continue
            if r['status'] != 'Reported':
                flags.append(f"{r['nuclide']}: {r['status']} ({r['flags']}); activity left blank")
                continue
            index = 8+5*isotopes.index(r['nuclide'])
            row[index:index+2] = [r['activity'],r['uncertainty']]
            relative = relative_uncertainty(r.get('activity'),r.get('uncertainty'))
            if relative is None:
                flags.append(f"{r['nuclide']}: relative uncertainty cannot be assessed")
            elif relative > uncertainty_cutoff:
                flags.append(f"{r['nuclide']}: relative uncertainty {format(relative,'.3f')}% > {uncertainty_threshold}%")
            if r['flags']:
                flags.append(f"{r['nuclide']}: {r['flags']}")
        notes = ['Time of counting = acquisition start; Time (s) = live time',
                 'Geometry filename unavailable; EOB inputs not supplied']
        if foil or distance:
            notes.append('Foil/distance inferred from report filename; verify')
        if not foil:
            notes.append('Foil number unavailable')
        if not distance:
            notes.append('Distance unavailable')
        metadata = [report['units'],report['sigma'],
                    'All confidence values' if include_below else f'ID confidence > {threshold}',
                    '; '.join(flags),'; '.join(notes),report.get('efficiency_id',''),
                    report['source_name'],', '.join(map(str,sorted({r['page'] for r in report['rows']}))),
                    report['generated'],report['sha256']]
        row[width+1:] = [safe_text(v) for v in metadata]
        result.append(row)
    return result

def export_lab_csv(reports,target,threshold='0.7',include_below=False,uncertainty_threshold='10'):
    stream = io.StringIO(newline='')
    csv.writer(stream).writerows(build_lab_rows(reports,threshold,include_below,uncertainty_threshold))
    atomic_write(target,stream.getvalue().encode('utf-8-sig'))
    return len(reports)
