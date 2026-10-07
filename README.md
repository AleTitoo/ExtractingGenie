# Platinum-189

Project repository: https://github.com/AleTitoo/ExtractingGenie

Download website: https://platinum-189.vercel.app/

Platinum-189 is a local Windows application for importing selectable-text GENIE PDFs and extracting the interference-corrected weighted mean activity table. Reports stay on the computer.

Version 1.0.9 adds **Export Excel (.xlsx)** with the approved Results, Source records, and Energy lines sheets. It uses the current report selection and confidence filter, preserves exact original values in Source records, and includes fitted widths, native dates, filters, frozen headers, scientific notation, and an editable uncertainty-review threshold. Rejected or missing activities stay blank. Mixed-unit reports must be exported separately. Both CSV exports remain available.

Version 1.0.8 restores in-app update installation and visible reopening. The native shell starts an independent Windows helper, waits for its startup acknowledgement, and only then closes the app and its private report service. The helper installs the verified update and reopens Platinum-189. If the helper cannot start, the app remains open and reports the error. The installer checksum is rechecked before handoff and installation. Saved report files and existing updated shortcuts are preserved.

Version 1.0.7 was a stopping-point release with automatic installation paused. Computers still running 1.0.7 need to install 1.0.8 or newer once from the download website; subsequent updates can use **Download update**, then **Restart and install** inside the app.

The approved two-shell Pt-189 icon and animation, larger website icon, and simplified app header are retained. Extraction and evidence handling are unchanged.

Version 1.0.5 renamed the application to Platinum-189 in honor of the experiment that inspired it. The library migrates with byte-for-byte verification; the previous copy remains available as a backup. Compatibility downloads and a small launcher bridge keep older installations and their update paths working.

## Accuracy boundaries

- The parser accepts only a complete recognized `INTERFERENCE CORRECTED REPORT` table with units and a sigma footer.
- It stops instead of returning a partial result when it sees malformed rows, duplicate summary nuclides, multiple summaries, or an unfamiliar uncertainty convention.
- Weighted activity, uncertainty, confidence, units, flags, page number, timestamps, and the source PDF hash are preserved.
- Missing, rejected, and undetermined activities remain blank; they are never changed to zero.
- The default filter is strictly `ID confidence > 0.7` and can be changed in the application.
- High relative uncertainty is flagged for review without rejecting or changing the reported value.
- Every summary result links to a PNG crop rendered from the archived source PDF. Individual energy lines retain GENIE's `@` and `#` decisions.
- Updates are downloaded only when both the installer and matching `.sha256` asset are present and the digest matches.

The parser and evidence workflow are regression-tested against both archived E2 reports. Other GENIE layouts require validation before experimental use. Always review exported values against the source report.

## Development

Run the parser tests from the repository root:

```powershell
python -m unittest discover -s tests
```

The installer contains its own Electron and Python runtimes. The local service stops when the native application window closes. Reports remain in `%LOCALAPPDATA%\Platinum-189\library`. No report data is uploaded. The application checks for updates after startup and every 30 minutes; downloads begin only when the user chooses **Download update**. The user can install immediately with **Restart and install** or postpone it with **Later**.
