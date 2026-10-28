# Download Organizer

![MIT License](https://img.shields.io/badge/license-MIT-blue.svg)
![Python](https://img.shields.io/badge/python-3.12+-blue.svg)
![Platform](https://img.shields.io/badge/platform-Windows%20%7C%20macOS%20%7C%20Linux-lightgrey.svg)

A cross-platform desktop utility that automatically organizes your Downloads folder based on configurable rules. Features a system tray interface with an intuitive GUI for managing file sorting rules, drag-and-drop rule reordering, and customizable sorting intervals.

## Features

- **Automatic file organization**: Runs silently in the background and sorts files at customizable intervals
- **System tray integration**: Clean, unobtrusive interface with easy access to all features
- **Configurable rules**: Create custom rules based on file extensions and filename keywords
- **Modern GUI**: User-friendly interface built with ttkbootstrap for managing sorting rules
- **Drag-and-drop reordering**: Easily reorganize rule priority by dragging rule cards
- **Flexible destinations**: Sort files into Downloads subfolders or absolute paths
- **Smart file handling**: Automatically handles duplicate filenames with incremental numbering
- **Adjustable intervals**: Customize how frequently the organizer scans for new files
- **Quick actions**: Manual sort and default folder creation buttons
- **Sort preview**: Review planned file moves before running a manual sort
- **Comprehensive logging**: Detailed logs stored in system AppData directory

## Installation

### Option 1: Download Pre-built Installer (Recommended)

1. Visit the [**Releases Page**](https://github.com/Cervini/project_organizer/releases)
2. Download the latest `download-organizer-setup.exe` file
3. Run the installer and follow the setup wizard
4. The application will automatically start after installation

### Option 2: Build from Source

**Requirements:**
- [Python 3.12+](https://www.python.org/)
- [Inno Setup](https://jrsoftware.org/isinfo.php) (Windows only, for installer creation)

**Steps:**

1. **Clone the repository:**
   ```bash
   git clone https://github.com/Cervini/organizer.git
   cd organizer
   ```

2. **Install dependencies:**
   
   **Windows:**
   ```bash
   pip install -r requirements.txt
   ```
   
   **macOS/Linux:**
   ```bash
   # Remove Windows-specific dependencies
   sed '/pywin32-ctypes/d' requirements.txt | pip install -r /dev/stdin
   ```
   
   **Additional Linux dependencies:**
   - **Ubuntu/Debian:** `sudo apt-get install python3-gi gir1.2-gtk-3.0`
   - **Fedora:** `sudo dnf install python3-gobject gtk3`
   - **Arch Linux:** `sudo pacman -S python-gobject gtk3`

3. **Build the Windows installer:**

   Install Python 3.12 and [Inno Setup 6](https://jrsoftware.org/isinfo.php), then run:

   ```bash
   powershell -ExecutionPolicy Bypass -File .\build_windows.ps1
   ```

   The build script creates a temporary virtual environment, installs the pinned
   dependencies, runs the test suite, packages the app and compiles the installer.
   It then installs the package into a temporary directory, verifies first-run
   configuration migration and preservation of existing settings, uninstalls that
   test copy, and removes its temporary environment. Find the installer in `Output/`.
   To set the displayed installer version, pass `-Version`, for example
   `-Version 2.1.3`.

## Usage

### Getting Started

Once installed, Download Organizer runs automatically in the system tray. Look for the broom icon in your system tray area.

### System Tray Menu

**Right-click the tray icon** to access:
- **Configure Rules**: Open the main configuration window
- **Exit**: Close the application

### Main Configuration Window

The configuration window provides several tools:

**Top Toolbar:**
- **Add New Rule**: Create custom sorting rules
- **Sort Downloads folder**: Manually trigger organization
- **Preview sort**: Review planned moves without changing files
- **Create default folders**: Set up common file type folders
- **Interval setting**: Adjust scanning frequency (in minutes)

**Rule Management:**
- **Drag and drop**: Reorder rules by dragging rule cards (higher rules have priority)
- **Edit**: Modify existing rules
- **Delete**: Remove unwanted rules

### Creating Rules

Each rule can specify:

| Field | Description | Example |
|-------|-------------|---------|
| **Name** | Rule identifier | "PDF Documents" |
| **Extensions** | File types to match | `.pdf, .doc, .docx` |
| **Keywords** | Filename patterns | `invoice, receipt, contract` |
| **Destination** | Target folder | `Documents\PDFs\` |
| **Subfolder** | Create within Downloads | ✓ (recommended) |

**Rule Logic:**
- Files matching **either** extensions **or** keywords will be moved
- Rules are processed in order (top to bottom)
- First matching rule wins

### Examples

**Organize by file type:**
```yaml
Name: Images
Extensions: .jpg, .png, .gif, .webp
Destination: Images\
Subfolder: ✓
```

**Organize by content:**
```yaml
Name: Invoices
Keywords: invoice, bill, receipt
Destination: Documents\Invoices\
Subfolder: ✓
```

**Organize to absolute path:**
```yaml
Name: Work Documents
Extensions: .docx, .xlsx, .pptx
Destination: C:\Work\Documents\
Subfolder: ✗
```

## Project Structure

```
organizer/
├── source/                  # Application source code
│   ├── main.py             # Entry point and system tray logic
│   ├── gui.py              # User interface components
│   └── utils.py            # File operations and configuration
├── resources/              # Application resources
│   ├── config.yaml         # Default configuration and rules
│   ├── broom.ico           # Windows icon
│   └── broom.png           # Cross-platform icon
├── installer_script.iss    # Inno Setup script
├── requirements.txt        # Python dependencies
└── README.md
```

## Configuration

### Default Rules

The application ships with sensible defaults:

| Rule | Extensions | Destination |
|------|------------|-------------|
| **Documents** | `.pdf`, `.docx`, `.txt` | `Documents\` |
| **Images** | `.jpg`, `.png`, `.gif`, `.webp`, `.ico`, `.svg` | `Images\` |
| **Archives** | `.zip`, `.rar`, `.7z`, `.gz` | `Archives\` |
| **Installers** | `.msi`, `.exe` | `Installers\` |

### Configuration File

The default rules ship in `resources/config.yaml`. Your editable settings are stored
in a per-user configuration directory:

- **Windows:** `%APPDATA%\Organizer\config.yaml`
- **macOS/Linux:** `$XDG_CONFIG_HOME/organizer/config.yaml`, or `~/.config/organizer/config.yaml` when `XDG_CONFIG_HOME` is not set

On first launch, the app copies an existing configuration from the previous location
to the user configuration directory. The bundled default file is not modified.

```yaml
interval: 2  # Minutes between scans
rules:
  - name: Documents
    extensions: [.pdf, .docx, .txt]
    keywords: []
    destination: Documents\
    sub: true
```

### Logging

Logs are automatically created in:
- **Windows:** `%APPDATA%\Organizer\organizer.log`
- **macOS/Linux:** `~/.organizer/organizer.log`

Features rotating logs (5MB max, 5 backups) with detailed operation tracking.

## Technical Details

**Built with:**
- **Python 3.12+** - Core application logic
- **pystray** - System tray integration
- **ttkbootstrap** - Modern GUI framework
- **PyYAML** - Configuration management
- **Pillow** - Image processing
- **PyInstaller** - Executable creation

**Platform Support:**
- **Windows** - Full support with installer
- **macOS** - Compatible (build from source)
- **Linux** - Compatible (build from source)

## Contributing

Contributions are welcome!
See the [CONTRIBUTING](CONTRIBUTING.md) file for details.

## Future Enhancements

- [ ] Auto-updater functionality
- [ ] Advanced rule conditions (file size, date, etc.)
- [ ] Multiple folder monitoring
- [ ] Rule templates and sharing
- [ ] Statistics and usage analytics

## License

This project is licensed under the MIT License. See the [LICENSE](LICENSE) file for details.

## Support

- **Issues:** [GitHub Issues](https://github.com/Cervini/organizer/issues)
- **Discussions:** [GitHub Discussions](https://github.com/Cervini/organizer/discussions)
- **Email:** [Contact via GitHub](https://github.com/Cervini)

---

**Made with 🍬🍬🍬 by [Simone Cervini](https://github.com/Cervini)**
