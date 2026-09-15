#!/usr/bin/env python3
"""Generate helper batch files for an Unreal Engine project.

Paths and command-line flags verified against Unreal Engine 5.8.
See README.md for usage.
"""

import argparse
import glob
import json
import os
import sys

## Every project script sources vars.bat before doing anything else.
PREAMBLE = (
    "@echo off\n"
    "\n"
    "call \"%~dp0vars.bat\"\n"
    "\n"
)

## Appended to every project script so a failure is visible instead of
## scrolling past.
TRAILER = (
    "\n"
    "if %ERRORLEVEL% NEQ 0 (\n"
    "    echo.\n"
    "    echo ERROR: %~nx0 failed with exit code %ERRORLEVEL%.\n"
    "    pause\n"
    "    exit /b %ERRORLEVEL%\n"
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
        "call \"%UE5_EDITOR_EXE%\" \"%UPROJECT_PATH%\" -log\n",
    ),
    (
        "run_editor_standalone.bat",
        "call \"%UE5_EDITOR_EXE%\" \"%UPROJECT_PATH%\" -game -log -windowed -resx=1280 -resy=720\n",
    ),
    (
        "run_standalone.bat",
        "call \"%PROJECT_BIN_DIR%\\%PROJECT%.exe\" -log -windowed -resx=1280 -resy=720\n",
    ),
]

## Visual Studio project format, passed through to UnrealBuildTool by
## generate.bat. "auto" leaves the flag empty so UnrealBuildTool falls back to
## the source code editor chosen in the editor preferences.
VS_VERSION_FLAGS = {
    "auto": "",
    "2022": "-2022",
    "2026": "-2026",
}


def write_file(filename, contents):
    with open(filename, "w", newline="\r\n", encoding="utf-8") as handle:
        handle.write(contents)

    print("Written " + filename + " to disk")


def write_script(filename, body):
    write_file(filename, PREAMBLE + body + TRAILER)


def write_rootdir(filename, unreal_directory):
    template = (
        "@echo off\n"
        "\n"
        "set \"UE5_DIR=" + unreal_directory + "\"\n"
    )

    write_file(filename, template)


def write_vars(filename, project_name, vs_version_flag):
    template = (
        "@echo off\n"
        "\n"
        "call \"%~dp0rootdir.bat\"\n"
        "\n"
        "set \"ROOTDIR=%~dp0\"\n"
        "set \"ROOTDIR=%ROOTDIR:~0,-1%\"\n"
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
    )

    write_file(filename, template)


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

    for script_name, script_body in SCRIPTS:
        write_script(script_name, script_body)

    write_rootdir("rootdir.bat", ue5_directory)
    write_vars("vars.bat", directory_name, VS_VERSION_FLAGS[args.vs])
