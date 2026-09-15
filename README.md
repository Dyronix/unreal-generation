# unreal generation script

Generates a set of helper `.bat` files into an Unreal Engine project folder, so
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

## Generated scripts

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

To retarget an existing project at a different engine version, edit `UE5_DIR`
in `rootdir.bat` — there is no need to re-run `setup.py`.

Every generated script reports a non-zero exit code and pauses on failure, so a
broken build does not scroll past unnoticed.

## Notes

`generate.bat` goes through the engine's `Engine\Build\BatchFiles\Build.bat`
rather than calling `UnrealBuildTool.exe` directly. `Build.bat` resolves the
.NET SDK bundled with the engine (UE 5.8 ships .NET 10), so the scripts work on
machines that do not have a matching .NET runtime installed system-wide.
