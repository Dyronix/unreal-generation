# unreal generation script

Generates a set of helper scripts into an Unreal Engine project folder, so
building, cooking, packaging and running the project are all one double-click.

Verified against **Unreal Engine 5.8**. Expected to work on 5.3+.

## How to use

- Download or clone the repository on your machine
- Copy the contents of the repository (except the `.git` folder if cloned)
- Go to your/project/directory
- Paste the contents of the repository within that folder
- Run `python setup.py -p path/to/unreal/engine`
- Happy coding

The path given to `-p` must be an Unreal Engine root — the folder that contains
`Engine/Build/Build.version`. That is either an Epic Games Launcher install
(e.g. `C:\Program Files\Epic Games\UE_5.8`) or a source tree. The script reads
that file and reports the engine version it found.

The project name is taken from the `.uproject` in the current directory. If the
project does not exist yet, the script falls back to guessing the name from the
directory name and warns that it did so.

### Options

| Option | Description |
| --- | --- |
| `-p`, `--path` | Root directory of the Unreal Engine installation. Required. |
| `--vs` | Visual Studio version to generate project files for: `auto` (default), `2022` or `2026`. `auto` lets Unreal Build Tool use the source code editor set in the editor preferences. |

## What you get

```
YourProject/
    YourProject.uproject
    Unreal Tools.bat        <- the only thing anyone needs to click
    Scripts/
        ... the scripts the menu runs
```

**`Unreal Tools.bat`** is a menu. Press a number, it does the thing, it tells
you whether it worked. Designers and artists never need to go into `Scripts/`.

```
  EVERYDAY
    1.  Open the editor
    2.  Fix the project after pulling   (rebuilds C++ code)

  TRYING THE GAME
    3.  Play the game in a window
    4.  Make a packaged build           (into Packaged\)

  PROGRAMMERS
    5.  Update the Visual Studio solution
    6.  More...
```

"More" holds the standalone build, the content cook, the compiled-executable
run, and clean.

### For artists and designers

You open the project by double-clicking `YourProject.uproject`, same as always.
You only need `Unreal Tools.bat` in one situation: **you pulled, and now the
editor refuses to open** and complains that modules are out of date. That is
option **2**. Let it finish, then open the project normally.

### Scripts

Everything in `Scripts/` can also be run on its own if you prefer.

| Script | What it does |
| --- | --- |
| `generate.bat` | Generates the Visual Studio solution and project files |
| `build_editor.bat` | Builds the editor target (`<Project>Editor`, Win64 Development) |
| `build_standalone.bat` | Builds the game target (`<Project>`, Win64 Development) |
| `clean.bat` | Cleans the editor target's build products |
| `cook_content.bat` | Cooks content for Windows |
| `package.bat` | Cooks, stages, packages and archives a build into `Packaged/` |
| `run_editor.bat` | Launches the editor on the project |
| `run_editor_standalone.bat` | Launches the project in game mode, windowed at 1280x720 |
| `run_standalone.bat` | Runs the compiled standalone executable |
| `rootdir.bat` | Holds the engine path. Edit this to point at a different engine. |
| `vars.bat` | Derives every other path. Sourced by all of the above. |

Every script reports `[ OK ]` or `[FAIL]` when it finishes and waits for a
keypress, so nothing disappears before you can read it. The menu sets
`UE_TOOLS_NOPAUSE=1` to suppress that second pause when it is driving them.

To retarget an existing project at a different engine version, edit `UE5_DIR`
in `Scripts/rootdir.bat` — there is no need to re-run `setup.py`.

## Notes

`generate.bat` goes through the engine's `Engine\Build\BatchFiles\Build.bat`
rather than calling `UnrealBuildTool.exe` directly. `Build.bat` resolves the
.NET SDK bundled with the engine (UE 5.8 ships .NET 10), so the scripts work on
machines that do not have a matching .NET runtime installed system-wide.

Earlier versions wrote all the scripts loose in the project root. If you have
those leftovers, `setup.py` lists them at the end of its run so you can delete
them; it never deletes anything itself.
