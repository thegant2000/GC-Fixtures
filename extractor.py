from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    parts = []
    for page in reader.pages:
        parts.append(page.extract_text() or "")
    return "\n".join(parts)


def infer_year(text: str, default_year: Optional[int] = None) -> int:
    if default_year:
        return default_year

    match = re.search(r"\b(20\d{2})\b", text)
    if match:
        return int(match.group(1))

    return datetime.now().year


def normalise_time(value: str) -> str:
    value = value.strip().replace(" ", "").replace(".", ":")

    m = re.match(r"^(\d{1,2}):(\d{2})$", value)
    if not m:
        return value

    hour = int(m.group(1))
    minute = int(m.group(2))

    # Fixture sheet uses evening throw-ins like 5.45, so treat 1-11 as PM.
    if 1 <= hour <= 11:
        hour += 12

    return f"{hour:02d}:{minute:02d}"


def split_competition(competition: str) -> tuple[str, str]:
    competition = competition.strip()
    m = re.match(r"^(.*?),\s*(Division\s+\d+)$", competition, re.IGNORECASE)
    if m:
        return m.group(1).strip(), m.group(2).strip()
    return competition, ""


def clean_team_name(name: str) -> str:
    return re.sub(r"\s{2,}", " ", name).strip()


def remove_trailing_referee(text: str) -> tuple[str, str]:
    """
    Removes a referee name appended to the end of a fixture line, e.g.
    'Garrycastle  B. Pierce' -> ('Garrycastle', 'B. Pierce')
    'Esker Gaels   P . McCaughey' -> ('Esker Gaels', 'P. McCaughey')
    """
    text = clean_team_name(text)

    referee_pattern = re.compile(
        r"^(.*?)(?:\s{2,}|\s+)([A-Z]\s*\.?\s*[A-Za-z]+(?:\s+[A-Z][a-zA-Z]+)*)$"
    )

    m = referee_pattern.match(text)
    if not m:
        return text, ""

    team_part = clean_team_name(m.group(1))
    referee = re.sub(r"\s*\.\s*", ".", m.group(2))
    referee = re.sub(r"\s{2,}", " ", referee).strip()

    return team_part, referee


def fixtures_to_rows(text: str, team_name: str = "Garrycastle", year: Optional[int] = None) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    detected_year = infer_year(text, year)

    rows: List[Dict] = []

    current_date_iso = None
    current_date_display = None
    current_weekday = None
    current_throw_in = None
    current_competition = None

    date_pattern = re.compile(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+([A-Za-z]+)",
        re.IGNORECASE,
    )

    competition_pattern = re.compile(
        r"^(Under\s+\d+|Minor)\s*,\s*Division\s+\d+$",
        re.IGNORECASE,
    )

    throw_in_pattern = re.compile(
        r"throw[\s-]?in[:\s]*([0-9]{1,2}[.:][0-9]{2})",
        re.IGNORECASE,
    )

    fixture_pattern = re.compile(r"^(.*?)\s+v\s+(.*?)$", re.IGNORECASE)

    month_map = {
        "january": 1,
        "february": 2,
        "march": 3,
        "april": 4,
        "may": 5,
        "june": 6,
        "july": 7,
        "august": 8,
        "september": 9,
        "october": 10,
        "november": 11,
        "december": 12,
    }

    for line in lines:
        line = clean_team_name(line)

        # Date line
        date_match = date_pattern.match(line)
        if date_match:
            current_weekday = date_match.group(1).title()
            day = int(date_match.group(2))
            month_name = date_match.group(3).lower()
            month = month_map.get(month_name)
            if month:
                dt = datetime(detected_year, month, day)
                current_date_iso = dt.strftime("%Y-%m-%d")
                current_date_display = dt.strftime("%A %d %B %Y")
            continue

        # Throw-in line
        ti_match = throw_in_pattern.search(line)
        if ti_match:
            current_throw_in = normalise_time(ti_match.group(1))
            continue

        # Competition header
        if competition_pattern.match(line):
            current_competition = line
            continue

        # Fixture line
        fx_match = fixture_pattern.match(line)
        if fx_match and current_competition:
            home_team = clean_team_name(fx_match.group(1))
            away_raw = clean_team_name(fx_match.group(2))

            away_team, referee = remove_trailing_referee(away_raw)

            if team_name.lower() not in home_team.lower() and team_name.lower() not in away_team.lower():
                continue

            is_home = team_name.lower() in home_team.lower()
            opponent = away_team if is_home else home_team
            age_group, division = split_competition(current_competition)

            rows.append(
                {
                    "date_iso": current_date_iso,
                    "date_display": current_date_display,
                    "weekday": current_weekday,
                    "throw_in": current_throw_in,
                    "competition": current_competition,
                    "age_group": age_group,
                    "division": division,
                    "home_team": home_team,
                    "away_team": away_team,
                    "team": team_name,
                    "opponent": opponent,
                    "is_home": is_home,
                    "referee": referee,
                    "original_line": line,
                }
            )

    return rows
