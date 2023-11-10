# Define the name and version of the program
!define PROGRAM_NAME "Sport Scorer"
!define PROGRAM_VERSION "1.0"

# Define the output directory for the installation
InstallDir "$ProgramFiles\${PROGRAM_NAME}"

# Set the default section
Section

# Output path for the installed files
SetOutPath $InstDir

# Install editor.exe
File "build\editor.exe"

# Install simple_tally_server.exe
; File "build\simple_tally_server.exe"

# Create shortcuts in the Start Menu
CreateDirectory "$SMPROGRAMS\${PROGRAM_NAME}"
CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\Editor.lnk" "$InstDir\editor.exe" "" "" 0
CreateShortCut "$SMPROGRAMS\${PROGRAM_NAME}\Tally Server.lnk" "$InstDir\simple_tally_server.exe" "" "" 0

# Create a desktop shortcut
CreateShortCut "$DESKTOP\${PROGRAM_NAME} Editor.lnk" "$InstDir\editor.exe" "" "" 0
CreateShortCut "$DESKTOP\${PROGRAM_NAME} Tally Server.lnk" "$InstDir\simple_tally_server.exe" "" "" 0

SectionEnd
