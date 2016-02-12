# LPy NSIS installer script.
#
# This file is part of LPy.
# 
# This copy of LPy is free software; you can redistribute it and/or modify it
# under the terms of the GNU General Public License as published by the Free
# Software Foundation; either version 2, or (at your option) any later
# version.
# 
# LPy is supplied in the hope that it will be useful, but WITHOUT ANY
# WARRANTY; without even the implied warranty of MERCHANTABILITY or FITNESS
# FOR A PARTICULAR PURPOSE.  See the GNU General Public License for more
# details.
# 
# You should have received a copy of the GNU General Public License along with
# LPy; see the file LICENSE.  If not, write to the Free Software Foundation,
# Inc., 59 Temple Place - Suite 330, Boston, MA 02111-1307, USA.


# These will change with different releases.
!define PSC_VERSION        "0.2.0"
!define PSC_VERSION_EXTRA  "Alpha"
!define PSC_VERSION_MEXTRA "a"
!define PSC_LICENSE        "GPL"
!define PSC_LICENSE_LC     "gpl"

# These are all derived from the above.
!define PSC_BASE_NAME      "PlantScan3D"
!define PSC_SHORT_NAME     "${PSC_BASE_NAME} ${PSC_LICENSE} v${PSC_VERSION}${PSC_VERSION_MEXTRA}"
!define PSC_LONG_NAME      "${PSC_BASE_NAME} ${PSC_LICENSE} v${PSC_VERSION} ${PSC_VERSION_EXTRA}"

# Tweak some of the standard pages.
!define MUI_WELCOMEPAGE_TEXT \
"This wizard will guide you through the installation of ${PSC_LONG_NAME}.\r\n\
\r\n\
Any code you write must be released under a license that is compatible with \
the GPL.\r\n\
\r\n\
Click Next to continue."

!define MUI_FINISHPAGE_RUN "$PSC_INSTDIR\bin\lpy.exe"
#!define MUI_FINISHPAGE_RUN_TEXT "Run L-Py"
!define MUI_FINISHPAGE_LINK "Get the latest news of PlantScan3D here"
!define MUI_FINISHPAGE_LINK_LOCATION "http://openalea.gforge.inria.fr/"


# Include the tools we use.
!include MUI.nsh
!include LogicLib.nsh


# Define the product name and installer executable.
Name "PlantScan3D"
Caption "${PSC_LONG_NAME} Setup"
OutFile "PlantScan3D-${PSC_VERSION}${PSC_VERSION_MEXTRA}-win32-Bundle.exe"


# Set the install directory, from the registry if possible.
#InstallDir "${PSC_INSTALLDIR}"

# The different installation types.  "Full" is everything.  "Minimal" is the
# runtime environment.
InstType "Full"
InstType "Minimal"


# Maximum compression.
SetCompressor /SOLID lzma


# We want the user to confirm they want to cancel.
!define MUI_ABORTWARNING

Var PSC_INSTDIR

Function .onInit
   
    StrCpy $PSC_INSTDIR "$PROGRAMFILES\OpenAlea\PlantScan3D"
    
FunctionEnd


# Define the different pages.
!insertmacro MUI_PAGE_WELCOME
!insertmacro MUI_PAGE_LICENSE "doc/LICENSE.txt"
!insertmacro MUI_PAGE_COMPONENTS

!define MUI_DIRECTORYPAGE_TEXT_DESTINATION "PlantScan3D repository"
!define MUI_DIRECTORYPAGE_VARIABLE $PSC_INSTDIR
!insertmacro MUI_PAGE_DIRECTORY

!insertmacro MUI_PAGE_INSTFILES
!insertmacro MUI_PAGE_FINISH
  
!insertmacro MUI_UNPAGE_CONFIRM
!insertmacro MUI_UNPAGE_INSTFILES

  
# Other settings.
!insertmacro MUI_LANGUAGE "English"


# Installer sections.

Section "Binaries" SecModules
    SectionIn 1 2 RO

    # Make sure this is clean and tidy.
    RMDir /r $PSC_INSTDIR
    CreateDirectory $PSC_INSTDIR

    SetOverwrite on

    # We have to take the SIP files from where they should have been installed.
    SetOutPath $PSC_INSTDIR\bin
    File /r .\dist\*
    
SectionEnd

Section "Documentation" SecDocumentation
    SectionIn 1

    SetOverwrite on

    SetOutPath $PSC_INSTDIR\doc
    File .\doc\*
SectionEnd

Section "Examples and tutorial" SecExamples
    SectionIn 1

    SetOverwrite on

    IfFileExists "$PSC_INSTDIR\share" 0 +2
        CreateDirectory $PSC_INSTDIR\share

    SetOutPath $PSC_INSTDIR\examples
    File /r .\data\*
SectionEnd

Section "Start Menu shortcuts" SecShortcuts
    SectionIn 1

    # Make sure this is clean and tidy.
    RMDir /r "$SMPROGRAMS\${PSC_BASE_NAME}"
    CreateDirectory "$SMPROGRAMS\${PSC_BASE_NAME}"
    
    CreateShortCut "$SMPROGRAMS\${PSC_BASE_NAME}\PlantScan3D.lnk" "$PSC_INSTDIR\bin\mtgeditor.exe"

    IfFileExists "$PSC_INSTDIR\doc" 0 +2
        CreateShortCut "$SMPROGRAMS\${PSC_BASE_NAME}\Web Site.lnk" "http://openalea.gforge.inria.fr/"

    IfFileExists "$PSC_INSTDIR\examples" 0 +2
        CreateShortCut "$SMPROGRAMS\${PSC_BASE_NAME}\Examples Source.lnk" "$PSC_INSTDIR\share"

    CreateShortCut "$SMPROGRAMS\${PSC_BASE_NAME}\Uninstall PlantScan3D.lnk" "$PSC_INSTDIR\Uninstall.exe"
SectionEnd

Section -post
    # Tell Windows about the package.
    WriteRegExpandStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D" "UninstallString" '"$PSC_INSTDIR\Uninstall.exe"'
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D" "DisplayName" "${PSC_BASE_NAME}"
    WriteRegStr HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D" "DisplayVersion" "${PSC_VERSION} ${PSC_VERSION_MEXTRA}"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D" "NoModify" "1"
    WriteRegDWORD HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D" "NoRepair" "1"

    # Save the installation directory for the uninstaller.
    WriteRegStr HKLM "Software\PlantScan3D" "Install Path" $PSC_INSTDIR
    
    # Create the uninstaller.
    WriteUninstaller "$PSC_INSTDIR\Uninstall.exe"
SectionEnd


# Section description text.
!insertmacro MUI_FUNCTION_DESCRIPTION_BEGIN
!insertmacro MUI_DESCRIPTION_TEXT ${SecModules} \
"The PlantScan3D binaries."
!insertmacro MUI_DESCRIPTION_TEXT ${SecDocumentation} \
"The PlantScan3D documentation."
!insertmacro MUI_DESCRIPTION_TEXT ${SecExamples} \
"The PlantScan3D data."
!insertmacro MUI_DESCRIPTION_TEXT ${SecShortcuts} \
"This adds shortcuts to your Start Menu."
!insertmacro MUI_FUNCTION_DESCRIPTION_END


Section "Uninstall"
    # Get the install directory.
    ReadRegStr $PSC_INSTDIR HKLM "Software\PlantScan3D" "Install Path"

    # The shortcuts section.
    RMDir /r "$SMPROGRAMS\${PSC_BASE_NAME}"

    # The examples section and the installer itself.
    RMDir /r "$PSC_INSTDIR"

    # Clean the registry.
    DeleteRegKey HKLM "Software\Microsoft\Windows\CurrentVersion\Uninstall\PlantScan3D"
    DeleteRegKey HKLM "Software\PlantScan3D"
SectionEnd
