# GENIE Report Studio

Project repository: https://github.com/AleTitoo/ExtractingGenie

GENIE Report Studio is a local Windows application for importing selectable-text GENIE PDFs and extracting the interference-corrected weighted mean activity table. Reports stay on the computer.

Version 1.0.4 gives the visible application its own native Windows window, GENIE icon, and stable taskbar identity. Existing Start-menu and desktop shortcuts are migrated once and preserved on subsequent upgrades. The Python extraction service runs privately behind the window and retains the existing report-library location.

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

The installer contains its own Electron and Python runtimes. The local service stops when the native application window closes. Reports remain in `%LOCALAPPDATA%\GENIE Report Studio\library`. No report data is uploaded. The application checks for updates after startup and every 30 minutes; downloads begin only when the user chooses **Download update**. The user can install immediately with **Restart and install** or postpone it with **Later**.
