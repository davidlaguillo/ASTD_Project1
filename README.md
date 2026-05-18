# CO2 Dashboard

Dash dashboard for exploring total and per-capita fossil CO2 emissions by country, year, sector, ranking, map, and density GIFs.

## Project Structure

```text
app.py                    # Main Dash app
generate_density_gifs.py  # Optional GIF generator
data/CO2.xlsx             # Source dataset
assets/custom.css         # Dash auto-loaded CSS
assets/density_*.gif      # Pre-generated GIFs
```

## Setup

From the project root.

### Windows

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

If PowerShell blocks activation, run commands through the venv Python directly:

```powershell
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

### Linux/macOS

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

## Run the App

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python app.py
```

Linux/macOS:

```bash
source .venv/bin/activate
python app.py
```

Then open:

```text
http://127.0.0.1:8050
```

## GIFs

The dashboard uses the pre-generated GIFs in `assets/`, so regenerating them is not required:

```text
assets/density_per_capita.gif
assets/density_total.gif
```

To regenerate them:

Windows:

```powershell
.\.venv\Scripts\Activate.ps1
python generate_density_gifs.py
```

Without activating the venv:

```powershell
.\.venv\Scripts\python.exe generate_density_gifs.py
```

Linux/macOS:

```bash
source .venv/bin/activate
python generate_density_gifs.py
```

This creates intermediate files in `output/` and refreshes the GIFs in `assets/`.
