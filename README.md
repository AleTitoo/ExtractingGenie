# GENIE Report Studio

Project repository: https://github.com/AleTitoo/ExtractingGenie

GENIE Report Studio is a local Windows application for importing selectable-text GENIE PDFs and extracting the interference-corrected weighted mean activity table. Reports stay on the computer.

Version 1.0.3 adds the approved application icon and a streamlined one-click installer and updater. Updates download with visible progress, are verified with SHA-256, preserve existing shortcuts, and relaunch the application after installation.

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

The installer contains its own runtime. It opens a dedicated local application window through Microsoft Edge, which is included with Windows 10 and 11. The local service stops when that window closes. No report data is uploaded. The application checks for updates after startup and every 30 minutes; downloads begin only when the user chooses **Download update**. The user can install immediately with **Restart and install** or postpone it with **Later**.
