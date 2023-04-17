import os
import sys
import argparse

def write_generate(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%UE5_BUILDTOOL_EXE%\" -projectfiles -project=\"%UPROJECT_PATH%\" -game -rocket -progress -log=\"%ROOTDIR%/Saved/Logs/UnrealVersionSelector-2022.07.24-13.51.06.log\""

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_build_editor(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%BUILD_BAT%\" %PROJECT%Editor Win64 Development \"%UPROJECT_PATH%\" -waitmutex -NoHotReload \n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_build_standalone(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%BUILD_BAT%\" %PROJECT% Win64 Development \"%UPROJECT_PATH%\" -waitmutex -NoHotReload \n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_cook_content(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%UE5_EDITOR_CMD_EXE%\" \"%UPROJECT_PATH%\" -run=cook -targetplatform=Windows\n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_run_editor_standalone(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%UE5_EDITOR_EXE%\" \"%UPROJECT_PATH%\" -game -log -windowed -resx=1280 -resy=720 "

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_run_editor(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%UE5_EDITOR_EXE%\" \"%UPROJECT_PATH%\" -log\n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_run_standalone(filename):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0\\vars.bat\"\n"
    template +=     "call \"%PROJECT_BIN_DIR%\"\\%PROJECT%.exe -log -windowed -resx=1280 -resy=720 \n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_rootdir(filename, unrealDirectory):
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "set UE5_DIR=" + unrealDirectory

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")

def write_vars(filename, projectName):   
    template =      ""

    template +=     "@echo off\n"
    template +=     "\n"
    template +=     "call \"%~dp0rootdir.bat\"\n"
    template +=     "\n"
    template +=     "set ROOTDIR=%~dp0\n"
    template +=     "set ROOTDIR=%ROOTDIR:~0,-1%\n"
    template +=     "\n"
    template +=     "set PROJECT=" + projectName + "\n"
    template +=     "set PROJECT_DIR=%ROOTDIR%\n"
    template +=     "set PROJECT_BIN_DIR=%ROOTDIR%\\Binaries\\Win64\n"
    template +=     "set UPROJECT_PATH=%PROJECT_DIR%\\%PROJECT%.uproject\n"
    template +=     "\n"
    template +=     "set UE5_EDITOR_EXE=%UE5_DIR%\\Engine\\Binaries\\Win64\\UnrealEditor.exe\n"
    template +=     "set UE5_EDITOR_CMD_EXE=%UE5_DIR%\\Engine\\Binaries\\Win64\\UnrealEditor-Cmd.exe\n"
    template +=     "set UE5_BUILDTOOL_EXE=%UE5_DIR%\\Engine\\Binaries\DotNET\\UnrealBuildTool\\UnrealBuildTool.exe\n"
    template +=     "\n"
    template +=     "set BUILD_BAT=%UE5_DIR%\\Engine\\Build\\BatchFiles\\Build.bat\n"

    build_editor = open(filename, "w+")
    build_editor.write(template)

    print("Written " + filename + " to disk")


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
    parser.add_argument("-p", "--path", help="Root directory of UE5 engine")

    ## Check parse args
    args, unknown = parser.parse_known_args()

    if not args.path:
        raise Exception("Please give the \"path (-p, --path)\" for the project you'd like to generate.")

    ue5_directory = args.path

    if not os.path.exists(ue5_directory):
        raise Exception("\"" + ue5_directory + "\" directory was not found.")

    current_directory = os.getcwd()
    
    directory_name = os.path.basename(current_directory )
    directory_name = directory_name.replace("_", " ").title().replace(" ", "")

    print("Unreal Engine 5.0 directory: " + ue5_directory)
    print("Current woring directory: " + current_directory)
    print("Project Name: " + directory_name)

    write_generate("generate.bat")
    write_build_editor("build_editor.bat")
    write_build_standalone("build_standalone.bat")
    write_cook_content("cook_content.bat")
    write_rootdir("rootdir.bat", ue5_directory)
    write_run_editor("run_editor.bat")
    write_run_editor_standalone("run_editor_standalone.bat")
    write_run_standalone("run_standalone.bat")
    write_vars("vars.bat", directory_name)    
