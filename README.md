# Download Organizer

A Windows desktop app that sorts files in your Downloads folder using rules you configure. It runs in the background and can be managed from the system tray.

## Install

Download `download-organizer-setup.exe` from the [GitHub Releases](https://github.com/Cervini/organizer/releases) page and run it.

## Use

When the app is running, it checks Downloads at the configured interval and moves matching files. The configuration window lets you add, edit, and delete rules. Use the up and down buttons on a rule to change its priority.

Rules match a file by extension or by a keyword in its name. The first matching rule wins. Destinations can be folders inside Downloads or absolute paths. Use **Preview sort** to see planned moves before starting a manual sort.

## Settings

Your editable configuration is stored at `%APPDATA%\Organizer\config.yaml`. On first launch, an existing configuration is copied there if one is available. The app does not modify the bundled default configuration.

The log file is `%APPDATA%\Organizer\organizer.log`.

## Run from source

Python 3.12 is required. On Windows:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
python source\main.py
```

Run the tests with:

```powershell
python -m unittest discover -s tests -v
```

## Build the Windows installer

Install Python 3.12 and [Inno Setup 6](https://jrsoftware.org/isinfo.php), then run:

```powershell
.\build_windows.ps1 -Version 2.1.4
```

The script runs the tests, builds the app and installer, and checks configuration migration in a temporary installation. The installer is written to `Output\download-organizer-setup.exe`.

For development notes, see [CONTRIBUTING.md](CONTRIBUTING.md).

## License

[MIT](LICENSE)
