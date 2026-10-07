# Platinum-189

Project repository: https://github.com/AleTitoo/ExtractingGenie

Download website: https://platinum-189.vercel.app/

Platinum-189 is a local Windows application for importing selectable-text GENIE PDFs and extracting the interference-corrected weighted mean activity table. Reports stay on the computer.

Version 1.0.7 retains the approved two-shell Pt-189 icon and animation, the larger website icon, and the simplified app header. Its installer closes the existing app and private report service before replacing files. Extraction and evidence handling are unchanged.

**Known unfinished work:** the full in-app install-and-restart sequence has not passed verification. Automatic installation is paused in this release; update checks remain available and the update button opens the download website. Close Platinum-189 and run the downloaded installer manually. The independent updater handoff and visible automatic relaunch are deferred to the next development session.

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
