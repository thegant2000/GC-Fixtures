# Garrycastle Fixtures Extractor

A simple Streamlit app that lets a user upload a fixtures PDF, extracts only the selected club's games, shows them on screen, and allows download as CSV or JSON.

This project was designed so the exported file can be used later by a separate Python script to query weekend fixtures.

## Features

- Upload a fixtures PDF in the browser
- Filter by club name (defaults to `Garrycastle`)
- Extract fixtures into a table on screen
- Download CSV and JSON outputs
- Optional **This weekend only** filter in the app
- Stores script-friendly fields such as:
  - `date_iso` (`YYYY-MM-DD`)
  - `throw_in` (`HH:MM`)
  - `is_home`
  - `home_team`
  - `away_team`
  - `opponent`
  - `original_line`

## Project structure

```text
.
├── extractor.py
├── requirements.txt
├── streamlit_app.py
└── README.md
```

## Run locally

### 1. Clone the repo

```bash
git clone https://github.com/YOUR-USERNAME/garrycastle-fixtures-extractor.git
cd garrycastle-fixtures-extractor
```

### 2. Create and activate a virtual environment

#### Windows (PowerShell)

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

#### macOS / Linux

```bash
python3 -m venv .venv
source .venv/bin/activate
```

### 3. Install dependencies

```bash
pip install -r requirements.txt
```

### 4. Start the app

```bash
streamlit run streamlit_app.py
```

## Deploy to Streamlit Community Cloud

1. Create a new GitHub repository.
2. Upload these project files to the repository root.
3. Push the repo to GitHub.
4. Go to Streamlit Community Cloud.
5. Sign in with GitHub.
6. Create a new app and select:
   - **Repository**: your repo
   - **Branch**: `main`
   - **Main file path**: `streamlit_app.py`
7. Deploy.

## Notes on the output format

The app intentionally stores dates and times in a format that is easy to query later in Python:

- `date_iso` uses `YYYY-MM-DD`
- `throw_in` uses 24-hour `HH:MM`
- `is_home` is a boolean

That makes later filtering straightforward, for example querying all fixtures on a given weekend.

## Example later usage in Python

```python
import pandas as pd

fixtures = pd.read_csv("garrycastle_fixtures.csv")
fixtures["date_iso"] = pd.to_datetime(fixtures["date_iso"])

weekend_games = fixtures[fixtures["date_iso"].dt.weekday >= 5]
print(weekend_games[["date_iso", "home_team", "away_team", "throw_in"]])
```

## Requirements

- Python 3.10+
- Streamlit
- pandas
- pypdf

## Known limitation

This parser is based on the structure of the fixture PDF you provided. If future fixture PDFs use a very different layout, the parsing rules in `extractor.py` may need slight adjustment.
