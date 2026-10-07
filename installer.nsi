Unicode true
!ifndef APP_VERSION
  !error "APP_VERSION must be supplied by scripts/build.ps1"
!endif

Name "GENIE Report Studio"
OutFile "dist\GENIE-Report-Studio-Setup-${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\GENIE Report Studio"
RequestExecutionLevel user
SetCompressor /SOLID lzma
Icon "assets\genie-report-studio.ico"
UninstallIcon "assets\genie-report-studio.ico"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "GENIE Report Studio"
VIAddVersionKey /LANG=1033 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "Alexandre Pereira"
VIAddVersionKey /LANG=1033 "FileDescription" "GENIE Report Studio installer"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright Alexandre Pereira"

SilentInstall normal
AutoCloseWindow true
ShowInstDetails nevershow
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File /r "dist\win-unpacked\*.*"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\GENIE Report Studio"
  ReadRegDWORD $0 HKCU "Software\GENIE Report Studio" "NativeShortcutVersion"
  IntCmp $0 1 preserveStart migrateStart preserveStart
  migrateStart:
  CreateShortcut "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe" "" "$INSTDIR\resources\genie-report-studio.ico" 0
  Goto skipStartShortcut
  preserveStart:
  IfFileExists "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" skipStartShortcut 0
  CreateShortcut "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe" "" "$INSTDIR\GENIE-Report-Studio.exe" 0
  skipStartShortcut:
  IfFileExists "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk" skipUninstallShortcut 0
  CreateShortcut "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  skipUninstallShortcut:
  IntCmp $0 1 preserveDesktop migrateDesktop preserveDesktop
  migrateDesktop:
  IfFileExists "$DESKTOP\GENIE Report Studio.lnk" 0 preserveDesktop
  CreateShortcut "$DESKTOP\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe" "" "$INSTDIR\resources\genie-report-studio.ico" 0
  Goto skipDesktopShortcut
  preserveDesktop:
  IfFileExists "$DESKTOP\GENIE Report Studio.lnk" skipDesktopShortcut 0
  CreateShortcut "$DESKTOP\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe" "" "$INSTDIR\GENIE-Report-Studio.exe" 0
  skipDesktopShortcut:
  WriteRegDWORD HKCU "Software\GENIE Report Studio" "NativeShortcutVersion" 1
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "DisplayName" "GENIE Report Studio"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "Publisher" "Alexandre Pereira"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "DisplayIcon" "$INSTDIR\GENIE-Report-Studio.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "NoRepair" 1
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\GENIE Report Studio.lnk"
  Delete "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk"
  Delete "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk"
  RMDir "$SMPROGRAMS\GENIE Report Studio"
  Delete "$INSTDIR\GENIE-Report-Studio.exe"
  Delete "$INSTDIR\*.dll"
  Delete "$INSTDIR\*.pak"
  Delete "$INSTDIR\*.bin"
  Delete "$INSTDIR\*.dat"
  Delete "$INSTDIR\*.json"
  Delete "$INSTDIR\LICENSE.electron.txt"
  Delete "$INSTDIR\LICENSES.chromium.html"
  RMDir /r "$INSTDIR\resources"
  RMDir /r "$INSTDIR\locales"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio"
  DeleteRegKey HKCU "Software\GENIE Report Studio"
SectionEnd
