#!/usr/bin/env python3
"""Generate helper batch files for an Unreal Engine project.

Writes a single "Unreal Tools.bat" menu into the project root and the scripts it
drives into a Scripts/ subfolder, so the project root has one obvious thing to
click.

Paths and command-line flags verified against Unreal Engine 5.8.
See README.md for usage.
"""

import argparse
import glob
import json
import os
import sys

MENU_FILENAME = "Unreal Tools.bat"
SCRIPTS_DIRNAME = "Scripts"

## Every project script sources vars.bat before doing anything else.
PREAMBLE = (
    "@echo off\n"
    "\n"
    "call \"%~dp0vars.bat\"\n"
    "\n"
)

## Appended to every project script. Reports the outcome either way -- a script
## that closes its own window on success is indistinguishable from a crash to
## anyone who got here by double-clicking. The menu sets UE_TOOLS_NOPAUSE so it
## can do the pausing itself instead of pausing twice.
TRAILER = (
    "\n"
    "set \"_EXITCODE=%ERRORLEVEL%\"\n"
    "echo.\n"
    "if \"%_EXITCODE%\"==\"0\" (\n"
    "    echo [ OK ] %~n0 finished successfully.\n"
    ") else (\n"
    "    echo [FAIL] %~n0 stopped with exit code %_EXITCODE%.\n"
    ")\n"
    "if not \"%UE_TOOLS_NOPAUSE%\"==\"1\" pause\n"
    "exit /b %_EXITCODE%\n"
)

## Emitted by the scripts that launch an executable. Checking first lets us name
## the file to edit instead of leaving a raw "system cannot find the path"
## behind, and `start` means the console does not sit around for the whole
## session holding the app open.
def launch_body(exe_variable, arguments, what):
    return (
        "if exist \"" + exe_variable + "\" (\n"
        "    echo Starting " + what + "...\n"
        "    start \"\" \"" + exe_variable + "\" " + arguments + "\n"
        ") else (\n"
        "    echo ERROR: " + what + " was not found at:\n"
        "    echo     " + exe_variable + "\n"
        "    echo.\n"
        "    echo Fix the engine path in " + SCRIPTS_DIRNAME + "\\rootdir.bat\n"
        "    cmd /c exit 1\n"
        ")\n"
    )


## Project scripts, as (filename, body). The body is sandwiched between
## PREAMBLE and TRAILER by write_script().
##
## Flag notes, all checked against Engine/Source/Programs/UnrealBuildTool in
## a 5.8 install:
##   -projectfiles  GlobalOptions.cs, equivalent to -Mode=GenerateProjectFiles
##   -progress      GlobalOptions.cs
##   -waitmutex     GlobalOptions.cs
##   -NoHotReload   Configuration/Descriptors/TargetDescriptor.cs
## Project files are generated through Build.bat rather than by invoking
## UnrealBuildTool.exe directly: Build.bat calls GetDotnetPath.bat first, which
## points at the .NET SDK bundled with the engine. Calling the executable
## directly requires a matching .NET runtime installed system-wide.
SCRIPTS = [
    (
        "generate.bat",
        "call \"%BUILD_BAT%\" -projectfiles -project=\"%UPROJECT_PATH%\" -progress %VS_VERSION_FLAG%\n",
    ),
    (
        "build_editor.bat",
        "call \"%BUILD_BAT%\" %PROJECT%Editor Win64 Development \"%UPROJECT_PATH%\" -waitmutex -NoHotReload\n",
    ),
    (
        "build_standalone.bat",
        "call \"%BUILD_BAT%\" %PROJECT% Win64 Development \"%UPROJECT_PATH%\" -waitmutex -NoHotReload\n",
    ),
    (
        ## Clean.bat takes the same <Target> <Platform> <Config> arguments as
        ## Build.bat and forwards them to it with -Clean appended.
        "clean.bat",
        "call \"%CLEAN_BAT%\" %PROJECT%Editor Win64 Development \"%UPROJECT_PATH%\" -waitmutex\n",
    ),
    (
        "cook_content.bat",
        "call \"%UE5_EDITOR_CMD_EXE%\" \"%UPROJECT_PATH%\" -run=cook -targetplatform=Windows\n",
    ),
    (
        "package.bat",
        "call \"%RUNUAT_BAT%\" BuildCookRun -project=\"%UPROJECT_PATH%\" -noP4 -platform=Win64 ^\n"
        "     -clientconfig=Development -cook -build -stage -pak -archive ^\n"
        "     -archivedirectory=\"%ROOTDIR%\\Packaged\"\n",
    ),
    (
        "run_editor.bat",
        launch_body("%UE5_EDITOR_EXE%", "\"%UPROJECT_PATH%\" -log", "the editor"),
    ),
    (
        "run_editor_standalone.bat",
        launch_body(
            "%UE5_EDITOR_EXE%",
            "\"%UPROJECT_PATH%\" -game -log -windowed -resx=1280 -resy=720",
            "the game",
        ),
    ),
    (
        "run_standalone.bat",
        launch_body(
            "%PROJECT_BIN_DIR%\\%PROJECT%.exe",
            "-log -windowed -resx=1280 -resy=720",
            "the packaged game",
        ),
    ),
]

## Batch files the old flat layout wrote into the project root. Reported, never
## deleted -- removing files from someone's project is their call, not ours.
LEGACY_ROOT_SCRIPTS = [name for name, _ in SCRIPTS] + ["rootdir.bat", "vars.bat"]

## Visual Studio project format, passed through to UnrealBuildTool by
## generate.bat. "auto" leaves the flag empty so UnrealBuildTool falls back to
## the source code editor chosen in the editor preferences.
VS_VERSION_FLAGS = {
    "auto": "",
    "2022": "-2022",
    "2026": "-2026",
}


def write_file(path, contents):
    with open(path, "w", newline="\r\n", encoding="utf-8") as handle:
        handle.write(contents)

    print("Written " + os.path.relpath(path) + " to disk")


def write_script(directory, filename, body):
    write_file(os.path.join(directory, filename), PREAMBLE + body + TRAILER)


def write_rootdir(path, unreal_directory):
    template = (
        "@echo off\n"
        "\n"
        ":: The engine this project builds against. Edit this line to point at a\n"
        ":: different engine version -- there is no need to re-run setup.py.\n"
        "set \"UE5_DIR=" + unreal_directory + "\"\n"
    )

    write_file(path, template)


def write_vars(path, project_name, vs_version_flag):
    ## ROOTDIR is the project, which is now the parent of Scripts/. The for loop
    ## is how batch resolves a relative path to a full one.
    template = (
        "@echo off\n"
        "\n"
        "call \"%~dp0rootdir.bat\"\n"
        "\n"
        "set \"SCRIPTDIR=%~dp0\"\n"
        "set \"SCRIPTDIR=%SCRIPTDIR:~0,-1%\"\n"
        "for %%I in (\"%SCRIPTDIR%\\..\") do set \"ROOTDIR=%%~fI\"\n"
        "\n"
        "set \"PROJECT=" + project_name + "\"\n"
        "set \"PROJECT_DIR=%ROOTDIR%\"\n"
        "set \"PROJECT_BIN_DIR=%ROOTDIR%\\Binaries\\Win64\"\n"
        "set \"UPROJECT_PATH=%PROJECT_DIR%\\%PROJECT%.uproject\"\n"
        "\n"
        "set \"VS_VERSION_FLAG=" + vs_version_flag + "\"\n"
        "\n"
        "set \"UE5_EDITOR_EXE=%UE5_DIR%\\Engine\\Binaries\\Win64\\UnrealEditor.exe\"\n"
        "set \"UE5_EDITOR_CMD_EXE=%UE5_DIR%\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe\"\n"
        "set \"UE5_BUILDTOOL_EXE=%UE5_DIR%\\Engine\\Binaries\\DotNET\\UnrealBuildTool\\UnrealBuildTool.exe\"\n"
        "\n"
        "set \"BUILD_BAT=%UE5_DIR%\\Engine\\Build\\BatchFiles\\Build.bat\"\n"
        "set \"CLEAN_BAT=%UE5_DIR%\\Engine\\Build\\BatchFiles\\Clean.bat\"\n"
        "set \"RUNUAT_BAT=%UE5_DIR%\\Engine\\Build\\BatchFiles\\RunUAT.bat\"\n"
        "\n"
        ":: One clear message here beats every script failing in its own way.\n"
        "if not exist \"%UE5_DIR%\\Engine\" (\n"
        "    echo.\n"
        "    echo ERROR: No Unreal Engine found at:\n"
        "    echo     %UE5_DIR%\n"
        "    echo.\n"
        "    echo Fix the engine path in %~dp0rootdir.bat\n"
        "    echo.\n"
        ")\n"
    )

    write_file(path, template)


def write_menu(path, scripts_dirname):
    """The single entry point in the project root.

    Ordered by who needs what: the two things an artist or designer ever needs
    are first, and the tool-language commands live behind "More".
    """
    template = (
        "@echo off\n"
        "setlocal\n"
        "\n"
        "call \"%~dp0" + scripts_dirname + "\\vars.bat\"\n"
        "\n"
        ":: The menu pauses after each action, so the scripts should not.\n"
        "set \"UE_TOOLS_NOPAUSE=1\"\n"
        "title %PROJECT% - Unreal Tools\n"
        "\n"
        ":menu\n"
        "cls\n"
        "echo ============================================================\n"
        "echo   %PROJECT%  -  Unreal Tools\n"
        "echo ============================================================\n"
        "echo   Engine: %UE5_DIR%\n"
        "echo.\n"
        "echo   EVERYDAY\n"
        "echo     1.  Open the editor\n"
        "echo     2.  Fix the project after pulling   (rebuilds C++ code)\n"
        "echo.\n"
        "echo   TRYING THE GAME\n"
        "echo     3.  Play the game in a window\n"
        "echo     4.  Make a packaged build           (into Packaged\\)\n"
        "echo.\n"
        "echo   PROGRAMMERS\n"
        "echo     5.  Update the Visual Studio solution\n"
        "echo     6.  More...\n"
        "echo.\n"
        "echo     0.  Exit\n"
        "echo.\n"
        ":: choice takes a single keypress, so there is no Enter to forget. It\n"
        ":: also fails rather than blocking when there is no console to read.\n"
        "choice /c 1234560 /n /m \"Press a number: \"\n"
        "set \"pick=%ERRORLEVEL%\"\n"
        "\n"
        "set \"action=\"\n"
        "if \"%pick%\"==\"1\" set \"action=run_editor.bat\"\n"
        "if \"%pick%\"==\"2\" set \"action=build_editor.bat\"\n"
        "if \"%pick%\"==\"3\" set \"action=run_editor_standalone.bat\"\n"
        "if \"%pick%\"==\"4\" set \"action=package.bat\"\n"
        "if \"%pick%\"==\"5\" set \"action=generate.bat\"\n"
        "if \"%pick%\"==\"6\" goto advanced\n"
        "if \"%pick%\"==\"7\" goto :eof\n"
        ":: Anything else means choice could not read a key -- leave, do not spin.\n"
        "if not defined action goto :eof\n"
        "call :run %action%\n"
        "goto menu\n"
        "\n"
        ":advanced\n"
        "cls\n"
        "echo ============================================================\n"
        "echo   %PROJECT%  -  More\n"
        "echo ============================================================\n"
        "echo.\n"
        "echo     1.  Build the standalone game executable\n"
        "echo     2.  Cook content for Windows\n"
        "echo     3.  Run the compiled standalone executable\n"
        "echo     4.  Clean build products\n"
        "echo.\n"
        "echo     0.  Back\n"
        "echo.\n"
        "choice /c 12340 /n /m \"Press a number: \"\n"
        "set \"pick=%ERRORLEVEL%\"\n"
        "\n"
        "set \"action=\"\n"
        "if \"%pick%\"==\"1\" set \"action=build_standalone.bat\"\n"
        "if \"%pick%\"==\"2\" set \"action=cook_content.bat\"\n"
        "if \"%pick%\"==\"3\" set \"action=run_standalone.bat\"\n"
        "if \"%pick%\"==\"4\" set \"action=clean.bat\"\n"
        "if \"%pick%\"==\"5\" goto menu\n"
        "if not defined action goto :eof\n"
        "call :run %action%\n"
        "goto advanced\n"
        "\n"
        ":run\n"
        "cls\n"
        "call \"%~dp0" + scripts_dirname + "\\%~1\"\n"
        "echo.\n"
        "pause\n"
        "exit /b\n"
    )

    write_file(path, template)


def read_engine_version(engine_directory):
    """Return the parsed Engine/Build/Build.version, or None if it is absent."""
    version_path = os.path.join(engine_directory, "Engine", "Build", "Build.version")

    if not os.path.isfile(version_path):
        return None

    with open(version_path, encoding="utf-8") as handle:
        return json.load(handle)


def format_engine_version(version):
    parts = [version.get("MajorVersion"), version.get("MinorVersion"), version.get("PatchVersion")]
    return ".".join(str(part) for part in parts if part is not None)


def detect_project_name(directory):
    """Find the project name from its .uproject file.

    Falls back to the directory name when the project has not been created yet.
    Returns (name, found_uproject).
    """
    uprojects = sorted(glob.glob(os.path.join(directory, "*.uproject")))

    if len(uprojects) > 1:
        names = ", ".join(os.path.basename(path) for path in uprojects)
        raise Exception("Found more than one .uproject in \"" + directory + "\": " + names)

    if uprojects:
        return os.path.splitext(os.path.basename(uprojects[0]))[0], True

    fallback = os.path.basename(directory).replace("_", " ").title().replace(" ", "")
    return fallback, False


def report_legacy_scripts(directory):
    """Point out leftovers from the old flat layout, without touching them."""
    leftovers = [name for name in LEGACY_ROOT_SCRIPTS
                 if os.path.isfile(os.path.join(directory, name))]

    if leftovers:
        print("")
        print("NOTE: these files are left over from the old layout and are no longer used.")
        print("      They are safe to delete: " + ", ".join(leftovers))


##-------------------------------------------------------------------------------
## ENTRY POINT

##-------------------------------------------------------------------------------
## Main function of this program
if __name__ == "__main__":
    print("\n")
    print("#--------------------- System information ------------------")
    print("System version: " + sys.version)

    print("#--------------------- Batch file generation ---------------")
    parser = argparse.ArgumentParser()
    parser.add_argument("-p", "--path", help="Root directory of the Unreal Engine installation or source tree")
    parser.add_argument(
        "--vs",
        choices=sorted(VS_VERSION_FLAGS),
        default="auto",
        help="Visual Studio version to generate project files for (default: auto)",
    )

    ## Check parse args
    args, unknown = parser.parse_known_args()

    if not args.path:
        raise Exception("Please give the \"path (-p, --path)\" of the Unreal Engine installation to use.")

    ue5_directory = os.path.abspath(args.path)

    if not os.path.isdir(ue5_directory):
        raise Exception("\"" + ue5_directory + "\" directory was not found.")

    engine_version = read_engine_version(ue5_directory)

    if engine_version is None:
        raise Exception(
            "\"" + ue5_directory + "\" does not look like an Unreal Engine root: "
            "Engine/Build/Build.version was not found."
        )

    if engine_version.get("MajorVersion") != 5:
        print("WARNING: these scripts target Unreal Engine 5, found version "
              + format_engine_version(engine_version) + ".")

    current_directory = os.getcwd()
    directory_name, found_uproject = detect_project_name(current_directory)

    if not found_uproject:
        print("WARNING: no .uproject found in \"" + current_directory
              + "\", guessing the project name from the directory name.")

    print("Unreal Engine " + format_engine_version(engine_version) + " directory: " + ue5_directory)
    print("Current working directory: " + current_directory)
    print("Project Name: " + directory_name)
    print("Visual Studio: " + args.vs)
    print("")

    scripts_directory = os.path.join(current_directory, SCRIPTS_DIRNAME)
    os.makedirs(scripts_directory, exist_ok=True)

    for script_name, script_body in SCRIPTS:
        write_script(scripts_directory, script_name, script_body)

    write_rootdir(os.path.join(scripts_directory, "rootdir.bat"), ue5_directory)
    write_vars(os.path.join(scripts_directory, "vars.bat"), directory_name, VS_VERSION_FLAGS[args.vs])
    write_menu(os.path.join(current_directory, MENU_FILENAME), SCRIPTS_DIRNAME)

    report_legacy_scripts(current_directory)

    print("")
    print("Done. Double-click \"" + MENU_FILENAME + "\" to get started.")
