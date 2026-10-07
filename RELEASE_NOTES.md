## Platinum-189 v1.0.9

Adds the approved native Excel export. Choose **Export Excel (.xlsx)** to save the selected reports and current confidence filter as a formatted workbook.

- Results sheet with readable widths, numeric activities and uncertainties, scientific notation, filters, frozen headers, and an editable uncertainty-review threshold.
- Source records preserve exact original values, timestamps, flags, source pages and hashes, including records excluded by the confidence filter.
- Energy lines retain line-by-line activities and GENIE use/exclusion decisions.
- Rejected or missing measurements remain blank. Mixed activity units require separate exports.
- Existing lab-layout CSV, detailed CSV, approved branding and automatic installation/reopening remain available.

PDF extraction is unchanged. Filling an uploaded Excel template remains a proposed future feature.

### Validation
29 Python tests and 5 desktop tests passed. The native export was checked with both archived E2 reports, including source-value preservation, filtering, dates, formula safety, and the workbook download endpoint.
