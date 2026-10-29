# Development

This is a personal project. These are the commands I use to run and test it on Windows.

## Set up

Install Python 3.12, then create an environment and install the dependencies:

```powershell
py -3.12 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
```

Run the app with `python source\main.py`. **It can move files in your real Downloads folder.** Use a test account or carefully review the sort preview before testing.

## Test

```powershell
python -m unittest discover -s tests -v
```

The tests use temporary directories and do not touch your Downloads folder.

## Build a release installer

Install Inno Setup 6, then run `.\build_windows.ps1 -Version A.B.C`. The installer is written to `Output\download-organizer-setup.exe`.
