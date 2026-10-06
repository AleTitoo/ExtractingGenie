import unittest
from lab_export import build_lab_rows, NUCLIDES
from core import parse_pages
from test_core import HEADER,BODY,FOOTER

class LabLayoutTests(unittest.TestCase):
    def report(self):
        report=parse_pages(['Acquisition Started : 6/30/2026 11:18:06 AM\nLive Time : 300.0 seconds\nDead Time : 7.81 %\nEfficiency ID : L_IN_PLASTIC_BAG\n'+HEADER+BODY+FOOTER],
                           '189Pt_E2_Al Foil 6_300cm_300s.PDF')
        report['sha256']='test'
        return report

    def test_mapping_and_precision(self):
        rows=build_lab_rows([self.report()])
        self.assertEqual(len({len(r) for r in rows}),1)
        row=rows[3]
        self.assertEqual(row[:8],['Al-6','6/30/2026 11:18:06 AM','189Pt_E2_Al Foil 6_300cm_300s','300','300.0','','7.81',''])
        self.assertEqual(row[8:12],['2.0022751E+03','2.1220114E+02','',''])
        for i in range(len(NUCLIDES)):
            self.assertEqual(row[8+5*i+2:8+5*i+4],['',''])
        extra=rows[1].index('Pt-197m1')
        self.assertEqual(row[extra],'1.2932844E+03')

    def test_rejected_and_filtered_not_zero(self):
        rows=build_lab_rows([self.report()])
        for name in ['Os-183','Ir-185','Re-181']:
            pos=rows[1].index(name)
            self.assertEqual(rows[3][pos:pos+2],['',''])
        self.assertIn('Rejected by interference analysis',' '.join(rows[3]))

    def test_filter_equality_and_repeat_measurements(self):
        report=self.report()
        rows=build_lab_rows([report,report],threshold='0.977')
        self.assertEqual(len(rows),5)
        self.assertEqual(rows[3][8],'')

    def test_mixed_units_rejected(self):
        a,b=self.report(),self.report()
        b['units']='Bq'
        with self.assertRaises(ValueError):build_lab_rows([a,b])

    def test_unknown_filename_and_missing_metadata(self):
        report=self.report()
        report['sample_label']='unknown'
        report.pop('live_time')
        row=build_lab_rows([report])[3]
        self.assertEqual((row[0],row[3],row[4]),('','',''))

if __name__=='__main__': unittest.main()
