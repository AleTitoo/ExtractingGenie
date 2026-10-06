Unicode true
Name "GENIE Report Studio"
OutFile "dist\GENIE-Report-Studio-Setup-1.0.2.exe"
InstallDir "$LOCALAPPDATA\Programs\GENIE Report Studio"
RequestExecutionLevel user
SetCompressor /SOLID lzma

Page directory
Page instfiles
UninstPage uninstConfirm
UninstPage instfiles

Section "Install"
  SetOutPath "$INSTDIR"
  File "backend-dist\GENIE-Report-Studio.exe"
  WriteUninstaller "$INSTDIR\Uninstall.exe"
  CreateDirectory "$SMPROGRAMS\GENIE Report Studio"
  IfFileExists "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" skipStartShortcut 0
  CreateShortcut "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe"
  skipStartShortcut:
  IfFileExists "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk" skipUninstallShortcut 0
  CreateShortcut "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk" "$INSTDIR\Uninstall.exe"
  skipUninstallShortcut:
  IfFileExists "$DESKTOP\GENIE Report Studio.lnk" skipDesktopShortcut 0
  CreateShortcut "$DESKTOP\GENIE Report Studio.lnk" "$INSTDIR\GENIE-Report-Studio.exe"
  skipDesktopShortcut:
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "DisplayName" "GENIE Report Studio"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "DisplayVersion" "1.0.2"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "Publisher" "Alexandre Pereira"
  WriteRegStr HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio" "UninstallString" '"$INSTDIR\Uninstall.exe"'
SectionEnd

Section "Uninstall"
  Delete "$DESKTOP\GENIE Report Studio.lnk"
  Delete "$SMPROGRAMS\GENIE Report Studio\GENIE Report Studio.lnk"
  Delete "$SMPROGRAMS\GENIE Report Studio\Uninstall.lnk"
  RMDir "$SMPROGRAMS\GENIE Report Studio"
  Delete "$INSTDIR\GENIE-Report-Studio.exe"
  Delete "$INSTDIR\Uninstall.exe"
  RMDir "$INSTDIR"
  DeleteRegKey HKCU "Software\Microsoft\Windows\CurrentVersion\Uninstall\GENIE Report Studio"
SectionEnd
