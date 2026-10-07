## Platinum-189 v1.0.8

Automatic installation and reopening are restored. Choose **Download update**, then **Restart and install**. The app closes only after its independent Windows update helper confirms startup; the helper installs the update and reopens a visible app window. If helper startup fails, the app stays open and reports the error.

- Rechecks installer SHA-256 before installation.
- Preserves saved reports and existing updated shortcuts.
- Keeps the approved icon, animation, and simplified header.
- Leaves PDF extraction and source evidence unchanged.

### Upgrading from v1.0.7
Automatic installation was paused in v1.0.7. Install v1.0.8 once using the downloadable installer. Future updates can install and reopen from inside the app.

### Validation
25 Python tests and 5 desktop tests passed. The packaged Windows app was checked for failed-helper recovery, real installation, visible reopening, report-file integrity, and shortcut preservation.
