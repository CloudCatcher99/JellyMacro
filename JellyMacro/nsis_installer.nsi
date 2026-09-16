# NSIS Installer script for JellyMacro
# This creates a Windows installer for JellyMacro

!define APP_NAME "JellyMacro"
!define APP_VERSION "1.0.0"
!define COMPANY_NAME "Xeu"
!define INSTALL_DIR "$LOCALAPPDATA\JellyMacro"

RequestExecutionLevel user

!include "LogicLib.nsh"
!include "MUI2.nsh"

Name "${APP_NAME} ${APP_VERSION}"
OutFile "JellyMacro-Setup.exe"
InstallDir "${INSTALL_DIR}"
InstallDirRegKey HKLM "Software\${COMPANY_NAME}\${APP_NAME}" "InstallDir"
ShowInstColors >

!define MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_WELCOME_SHOW

!define MUI_PAGE_DIRECTORY
!insertmacro MUI_PAGE_DIRECTORY

!define MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_INSTFILES

!define MUI_PAGE_FINISH
!insertmacro MUI_PAGE_FINISH

!define MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_CONFIRM

!define MUI_UNPAGE_INSTFILES
!insertmacro MUI_UNPAGE_INSTFILES

!define MUI_UNPAGE_DONE
!insertmacro MUI_UNPAGE_DONE

Section "MainSection" SEC01
    SetOutPath "$INSTDIR"
    
    File /oname=jellymacro.exe "dist\JellyMacro.exe"
    
    WriteRegStr HKLM "Software\${COMPANY_NAME}\${APP_NAME}" "InstallDir" "$INSTDIR"
    WriteRegStr HKLM "Software\${COMPANY_NAME}\${APP_NAME}" "Version" "${APP_VERSION}"
    
    CreateDirectory "$SMPROGRAMS\${APP_NAME}"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\${APP_NAME}.lnk" "$INSTDIR\jellymacro.exe"
    CreateShortCut "$SMPROGRAMS\${APP_NAME}\Uninstall ${APP_NAME}.lnk" "$INSTDIR\Uninstall.exe"
    
    CreateShortCut "$DESKTOP\${APP_NAME}.lnk" "$INSTDIR\jellymacro.exe"
SectionEnd

Section "Uninstall"
    Delete "$INSTDIR\jellymacro.exe"
    Delete "$INSTDIR\Uninstall.exe"
    RMDir /r "$INSTDIR"
    
    Delete "$DESKTOP\${APP_NAME}.lnk"
    RMDir "$SMPROGRAMS\${APP_NAME}"
    
    DeleteRegKey HKLM "Software\${COMPANY_NAME}\${APP_NAME}"
SectionEnd