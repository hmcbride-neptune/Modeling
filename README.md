# Propagation Modeling Workflow

This repository contains code for the propagation modeling workflow. The scripts in this project automatically generate all the necessary files and configurations required to perform propagation modeling analysis.

## Overview

The propagation modeling workflow is designed to:
- Prepare input data for propagation analysis
- Generate required configuration files
- Execute propagation models
- Produce modeling outputs and reports

## Getting Started

1. Clone this repository
2. Install required dependencies
3. Run the modeling scripts to generate all necessary files 
    .\venv\Scripts\Activate.ps1 
    python run.py

## Building a one-dir executable (Windows)

This project can be packaged into a one-directory executable using PyInstaller. The repository includes a helper PowerShell script `build_onedir.ps1` and a PyInstaller spec `pyinstaller_modeling.spec`.

Steps:

1. Activate your virtual environment:

```powershell
& "venv\Scripts\Activate.ps1"
```

2. (Optional) Install PyInstaller if it's not present:

```powershell
pip install pyinstaller
```

3. Build using the provided script (this will install PyInstaller into the venv if missing):

```powershell
.\build_onedir.ps1
```

Or run PyInstaller directly with the spec:

```powershell
pyinstaller pyinstaller_modeling.spec
```

The one-dir output will be in the `dist\run` (or `dist\Modeling` when using the spec) folder. The GUI requires a graphical environment to run.

## Output

The code will create all files needed to complete the propagation modeling workflow in the designated output directories.
