# GENIE Report Studio

GENIE Report Studio is a local Windows application for importing selectable-text GENIE PDFs and extracting the interference-corrected weighted mean activity table. Reports stay on the computer.

## Accuracy boundaries

- The parser accepts only a complete recognized `INTERFERENCE CORRECTED REPORT` table with units and a sigma footer.
- It stops instead of returning a partial result when it sees malformed rows, duplicate summary nuclides, multiple summaries, or an unfamiliar uncertainty convention.
- Weighted activity, uncertainty, confidence, units, flags, page number, timestamps, and the source PDF hash are preserved.
- Missing, rejected, and undetermined activities remain blank; they are never changed to zero.
- The default filter is strictly `ID confidence > 0.7` and can be changed in the application.

This initial release has been regression-tested against the existing E2 fixtures. Other GENIE layouts require validation before experimental use. Always review exported values against the source report.

## Development

Run the parser tests from the repository root:

```powershell
python -m unittest discover -s tests
```

The installer contains its own runtime. It opens a dedicated local application window through Microsoft Edge, which is included with Windows 10 and 11. The local service stops when that window closes. No report data is uploaded.
