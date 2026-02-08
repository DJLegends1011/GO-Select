# GO-Select

A modern, graphical tool for managing character select screens in **Ikemen GO** and **MUGEN** engines. Built with Python and CustomTkinter, it provides a sleek dark-mode interface for editing your roster, stage lists, and advanced configuration parameters.

## Features

- **Visual Grid Editor**: View and edit your character select grid with ease.
- **Advanced Parameter Support**: Full support for standard MUGEN parameters (`order`, `music`, `stage`, `ai`) and Ikemen GO specific features (`hidden`, `unlock`, `arcadepath`, `ratiopath`, `exclude`).
- **Music Management**: Easily assign music tracks for specific rounds, victory screens, and low-life situations.
- **Stage Management**: Manage your "Extra Stages" list alongside your characters.
- **2D Scrolling & Zoom**: Handles large rosters with scrollable grid support.
- **Configuration Persistence**: Remembers your game paths. Supports both global configuration (AppData) and portable mode (local INI file).
- **Auto-Backups**: Option to automatically backup `select.def` before saving.

## Requirements

- Python 3.8 or higher
- `customtkinter` library

## Installation

1. Clone or download this repository.
2. Install the required dependencies:
   ```bash
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:
   ```bash
   python GO_Select.py
   ```
2. On first launch, you will be prompted to locate your `system.def` file (usually found in the `data` folder of your Ikemen GO/MUGEN installation).
3. **Left Panel**: Shows available characters scanned from your `chars` directory. Click a character to select it.
4. **Center Panel**: Represents your select screen grid.
   - Click a slot to select it.
   - Click a character from the left panel to assign it to the selected slot.
   - Right-click a slot for context menu options (Properties, Set Random, Clear).
5. **Right Panel**: Shows available stages.
   - Click "Add Selected" to add stages to your Extra Stages list.
   - Use the gear icon next to a stage to edit its specific parameters (music, order, unlock).
6. **Properties**: Click "Update" or right-click a slot to open the full Parameter Editor for characters.

## Configuration

Click the **Options** button in the toolbar to access settings:
- **Use local options file**: Check this to save `go_select.ini` in the application folder (useful for portable installations or managing multiple screenpacks).
- **Make a backup before every save**: Ensures you never lose your configuration by creating timestamped backups in `data/GoSelect_Backups`.

## Building Standalone Executable

You can build a standalone Windows executable (no Python installation required):

### Quick Build
Simply run the included build script:
```batch
build.bat
```

### Manual Build
1. Install build dependencies:
   ```bash
   pip install pyinstaller customtkinter
   ```

2. Run PyInstaller with the spec file:
   ```bash
   python -m PyInstaller GO_Select.spec --clean
   ```

3. The executable will be created at `dist/GO-Select.exe` (~13 MB)

### Distribution
The standalone `GO-Select.exe` can be distributed without Python. Users just need to:
1. Place the EXE in their Ikemen GO/MUGEN game folder (or anywhere)
2. Run it and point to their `system.def` when prompted

## License

This project is open source. Feel free to modify and distribute.
