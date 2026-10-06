import unittest
import tempfile
import csv
from pathlib import Path
from core import parse_pages, selected, export_csv, relative_uncertainty, review_threshold

HEADER = '''***** I N T E R F E R E N C E C O R R E C T E D R E P O R T *****
Nuclide Wt mean Wt mean
Nuclide Id Activity Activity
Name Confidence (uCi/Unit) Uncertainty
'''
BODY = '''X Os-183 0.931
Ir-184 @ 0.854 2.0746073E+01 1.3946176E+00
Ir-185 @ 0.696 3.0041904E+02 8.5411697E+01
Pt-189 @ 0.977 2.0022751E+03 2.1220114E+02
Pt-197m1 @ 0.926 1.2932844E+03 3.4136603E+02
'''
FOOTER = 'Errors quoted at 1.000 sigma'

class ParserTests(unittest.TestCase):
    def test_uncertainty_threshold_rejects_non_finite_or_negative_values(self):
        for value in ('NaN', 'Infinity', '-0.1'):
            with self.assertRaises(ValueError):
                review_threshold(value)

    def test_blank_metadata_does_not_capture_next_line(self):
        report = parse_pages(['Sample Identification :\nSample Type :\n'+HEADER+BODY+FOOTER], 'sample.pdf')
        self.assertEqual(report['sample_id'], '')

    def parse(self, body=BODY):
        return parse_pages([HEADER+body+FOOTER], 'sample.pdf')

    def test_precision_flags_and_missing(self):
        report = self.parse()
        self.assertEqual(report['units'], 'uCi/Unit')
        self.assertEqual(report['sigma'], '1.000')
        pt = report['rows'][3]
        self.assertEqual((pt['activity'],pt['uncertainty']), ('2.0022751E+03','2.1220114E+02'))
        self.assertEqual(report['rows'][4]['nuclide'],'Pt-197m1')
        self.assertIsNone(report['rows'][0]['activity'])
        self.assertEqual(report['rows'][0]['status'],'Rejected by interference analysis')

    def test_threshold_strict(self):
        rows = self.parse('Pt-189 0.700 1.0E+03 2.0E+01\n')['rows']
        self.assertEqual(selected(rows), [])
        self.assertEqual(len(selected(rows, include_below=True)), 1)
        for value in ('NaN','Infinity','-0.1','1.1'):
            with self.assertRaises(ValueError):
                selected(rows,value)

    def test_truncated_or_unknown_rejected(self):
        with self.assertRaises(ValueError):
            parse_pages([HEADER+BODY], 'truncated.pdf')
        with self.assertRaises(ValueError):
            self.parse('Pt-189 0.977 BROKEN 2.1220114E+02\n')
        with self.assertRaises(ValueError):
            self.parse(BODY+BODY)

    def test_pagination_and_other_tables(self):
        report = parse_pages(['Pt-189 0.977 9E+99 1E+99\n'+HEADER,
                              BODY+FOOTER], 'sample.pdf')
        self.assertEqual(report['rows'][3]['activity'],'2.0022751E+03')
        self.assertEqual(report['rows'][3]['page'],2)

    def test_csv_roundtrip(self):
        report = self.parse()
        report['sha256'] = 'abc'
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp)/'test.csv'
            self.assertEqual(export_csv([report],path,tmp),4)
            with path.open(encoding='utf-8-sig',newline='') as stream:
                rows = list(csv.DictReader(stream))
            self.assertEqual(rows[0]['Weighted mean activity'],'')
            self.assertEqual(rows[2]['Weighted mean activity'],'2.0022751E+03')

    def test_relative_uncertainty(self):
        self.assertEqual(relative_uncertainty('100','10'),10)
        self.assertIsNone(relative_uncertainty('0','1'))
        self.assertIsNone(relative_uncertainty(None,'1'))

    def test_interference_corrected_line_rows(self):
        page='''Interference Corrected Activity Report\n***** N U C L I D E I D E N T I F I C A T I O N R E P O R T *****\nPt-189 0.977 94.34* 6.50 1.868354E+03 5.502715E+02\n113.82* @ 2.50 2.350085E+03 6.993337E+02\n130.00 @ 0.11\n* = Energy line found in the spectrum.\n'''+HEADER+BODY+FOOTER
        report=parse_pages([page],'sample.pdf')
        self.assertEqual(len(report['line_rows']),3)
        self.assertEqual(report['line_rows'][0]['status'],'Used in weighted mean')
        self.assertEqual(report['line_rows'][1]['status'],'Not used in weighted mean')
        self.assertEqual(report['line_rows'][2]['status'],'Not found in spectrum')

if __name__ == '__main__':
    unittest.main()
