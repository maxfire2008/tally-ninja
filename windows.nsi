!include "MUI.nsh"

!define MUI_ABORTWARNING # This will warn the user if they exit from the installer.

!insertmacro MUI_PAGE_WELCOME # Welcome to the installer page.
!insertmacro MUI_PAGE_DIRECTORY # In which folder install page.
!insertmacro MUI_PAGE_INSTFILES # Installing page.
!insertmacro MUI_PAGE_FINISH # Finished installation page.

!insertmacro MUI_LANGUAGE "English"

Name "Sport Scorer" # Name of the installer (usually the name of the application to install).
OutFile "SportScorerInstaller.exe" # Name of the installer's file.
InstallDir "$PROGRAMFILES\SportScorer" # Default installing folder ($PROGRAMFILES is Program Files folder).
ShowInstDetails show # This will always show the installation details.

Section "SportScorer" # In this section add your files or your folders.
    SetOutPath "$INSTDIR"

    File "build\editor.exe"

    # create a start menu shortcut if the user wants one
    CreateShortCut "$SMPROGRAMS\SportScorer.lnk" "$INSTDIR\editor.exe"
    # create a desktop shortcut if the user wants one
    CreateShortCut "$DESKTOP\SportScorer.lnk" "$INSTDIR\editor.exe"
SectionEnd