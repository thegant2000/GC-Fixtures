from __future__ import annotations

import re
from datetime import datetime
from typing import List, Dict, Optional
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
    value = value.strip().lower().replace(" ", "")
    m = re.match(r"^(\d{1,2})[:.](\d{2})$", value)
    if not m:
        return value
    hour = int(m.group(1))
    minute = int(m.group(2))
    return f"{hour:02d}:{minute:02d}"


def parse_pdf(pdf_path: str) -> str:
    return extract_text(pdf_path)


def fixtures_to_rows(text: str, team_name: str = "Garrycastle", year: Optional[int] = None) -> List[Dict]:
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    detected_year = infer_year(text, year)

    rows: List[Dict] = []

    current_date = None
    current_weekday = None
    current_throw_in = None
    current_competition = None

    date_pattern = re.compile(
        r"^(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+(\d{1,2})\s+([A-Za-z]+)",
        re.IGNORECASE,
    )

    fixture_pattern = re.compile(r"^(.*?)\s+v\s+(.*?)$", re.IGNORECASE)
    throw_in_pattern = re.compile(r"throw[\s-]?in[:\s]*([0-9]{1,2}[:.][0-9]{2})", re.IGNORECASE)

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
        date_match = date_pattern.match(line)
        if date_match:
            current_weekday = date_match.group(1)
            day = int(date_match.group(2))
            month_name = date_match.group(3).lower()
            month = month_map.get(month_name)
            if month:
                current_date = f"{detected_year:04d}-{month:02d}-{day:02d}"
            continue

        ti_match = throw_in_pattern.search(line)
        if ti_match:
            current_throw_in = normalise_time(ti_match.group(1))
            continue

        if "division" in line.lower() or "minor" in line.lower() or "under" in line.lower():
            current_competition = line
            continue

        fx_match = fixture_pattern.match(line)
        if fx_match:
            home_team = fx_match.group(1).strip()
            away_team = fx_match.group(2).strip()

            if team_name.lower() not in home_team.lower() and team_name.lower() not in away_team.lower():
                continue

            is_home = team_name.lower() in home_team.lower()
            opponent = away_team if is_home else home_team

            rows.append(
                {
                    "date_iso": current_date,
                    "weekday": current_weekday,
                    "throw_in": current_throw_in,
                    "competition": current_competition,
                    "home_team": home_team,
                    "away_team": away_team,
                    "team": team_name,
                    "opponent": opponent,
                    "is_home": is_home,
                    "original_line": line,
                }
            )

    return rows
