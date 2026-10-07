Unicode true
!ifndef APP_VERSION
  !error "APP_VERSION must be supplied by scripts/build.ps1"
!endif

Name "Platinum-189"
OutFile "dist\Platinum-189-Setup-${APP_VERSION}.exe"
InstallDir "$LOCALAPPDATA\Programs\Platinum-189"
RequestExecutionLevel user
SetCompressor zlib
Icon "assets\platinum-189.ico"
UninstallIcon "assets\platinum-189.ico"
VIProductVersion "${APP_VERSION}.0"
VIAddVersionKey /LANG=1033 "ProductName" "Platinum-189"
VIAddVersionKey /LANG=1033 "ProductVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "FileVersion" "${APP_VERSION}"
VIAddVersionKey /LANG=1033 "CompanyName" "Alexandre Pereira"
VIAddVersionKey /LANG=1033 "FileDescription" "Platinum-189 installer"
VIAddVersionKey /LANG=1033 "LegalCopyright" "Copyright Alexandre Pereira"

SilentInstall normal
AutoCloseWindow true
ShowInstDetails nevershow
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  FileOpen $1 "$INSTDIR\.installing" w
  FileWrite $1 "Installation in progress"
  FileClose $1
  InitPluginsDir
  File /oname=$PLUGINSDIR\close-installed-app.ps1 "scripts\close-installed-app.ps1"
  nsExec::ExecToStack '"$SYSDIR\WindowsPowerShell\v1.0\powershell.exe" -NoProfile -ExecutionPolicy Bypass -File "$PLUGINSDIR\close-installed-app.ps1" -InstallDir "$INSTDIR"'
  Pop $0
  Pop $1
  StrCmp $0 "0" appClosed
  Delete "$INSTDIR\.installing"
  MessageBox MB_OK|MB_ICONSTOP "Platinum-189 could not close. Close the app and run the installer again."
  SetErrorLevel 1
  Abort
  appClosed:
  File /r "dist\win-unpacked\*.*"
  ; Older updater helpers relaunch this historical path after installation.
  IfFileExists "$LOCALAPPDATA\Programs\GENIE Report Studio\GENIE-Report-Studio.exe" 0 skipLegacyBridge
  SetOutPath "$LOCALAPPDATA\Programs\GENIE Report Studio"
  File /oname=GENIE-Report-Studio.exe "backend-dist\Legacy-GENIE-Launcher.exe"
  skipLegacyBridge:
  SetOutPath "$INSTDIR"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\Platinum-189"
  IfFileExists "$SMPROGRAMS\Platinum-189\Platinum-189.lnk" skipLegacyStartRename 0
  Rename "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" "$SMPROGRAMS\Platinum-189\Platinum-189.lnk"
  skipLegacyStartRename:
  IfFileExists "$DESKTOP\Platinum-189.lnk" skipLegacyDesktopRename 0
  Rename "$DESKTOP\GENIE Report Studio.lnk" "$DESKTOP\Platinum-189.lnk"
  skipLegacyDesktopRename:
  Delete "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk"
  RMDir "$SMPROGRAMS\GENIE Report Studio"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio"
  ReadRegDWORD $0 HKCU "Software\Platinum-189" "NativeShortcutVersion"
  IntCmp $0 2 preserveStart migrateStart preserveStart
  migrateStart:
  CreateShortcut "$SMPROGRAMS\Platinum-189\Platinum-189.lnk" "$INSTDIR\Platinum-189.exe" "" "$INSTDIR\resources\platinum-189-v2.ico" 0
  Goto skipStartShortcut
  preserveStart:
  IfFileExists "$SMPROGRAMS\Platinum-189\Platinum-189.lnk" skipStartShortcut 0
  CreateShortcut "$SMPROGRAMS\Platinum-189\Platinum-189.lnk" "$INSTDIR\Platinum-189.exe" "" "$INSTDIR\Platinum-189.exe" 0
  skipStartShortcut:
  IfFileExists "$SMPROGRAMS\Platinum-189\Uninstall.lnk" skipUninstallShortcut 0
  CreateShortcut "$SMPROGRAMS\Platinum-189\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  skipUninstallShortcut:
  IntCmp $0 2 preserveDesktop migrateDesktop preserveDesktop
  migrateDesktop:
  IfFileExists "$DESKTOP\Platinum-189.lnk" 0 preserveDesktop
  CreateShortcut "$DESKTOP\Platinum-189.lnk" "$INSTDIR\Platinum-189.exe" "" "$INSTDIR\resources\platinum-189-v2.ico" 0
  Goto skipDesktopShortcut
  preserveDesktop:
  IfFileExists "$DESKTOP\Platinum-189.lnk" skipDesktopShortcut 0
  CreateShortcut "$DESKTOP\Platinum-189.lnk" "$INSTDIR\Platinum-189.exe" "" "$INSTDIR\Platinum-189.exe" 0
  skipDesktopShortcut:
  WriteRegDWORD HKCU "Software\Platinum-189" "NativeShortcutVersion" 2
  System::Call 'shell32::SHChangeNotify(i 0x08000000, i 0, p 0, p 0)'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "DisplayName" "Platinum-189"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "DisplayVersion" "${APP_VERSION}"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "Publisher" "Alexandre Pereira"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "InstallLocation" "$INSTDIR"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "DisplayIcon" "$INSTDIR\Platinum-189.exe"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "UninstallString" '"$INSTDIR\Uninstall.exe"'
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "QuietUninstallString" '"$INSTDIR\Uninstall.exe" /S'
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "NoModify" 1
  WriteRegDWORD HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189" "NoRepair" 1
  Delete "$INSTDIR\.installing"
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\Platinum-189.lnk"
  Delete "$SMPROGRAMS\Platinum-189\Platinum-189.lnk"
  Delete "$SMPROGRAMS\Platinum-189\Uninstall.lnk"
  RMDir "$SMPROGRAMS\Platinum-189"
  Delete "$INSTDIR\Platinum-189.exe"
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
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\Platinum-189"
  DeleteRegKey HKCU "Software\Platinum-189"
  Delete "$LOCALAPPDATA\Programs\GENIE Report Studio\GENIE-Report-Studio.exe"
SectionEnd
