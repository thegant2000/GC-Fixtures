from __future__ import annotations

import re
from datetime import datetime
from typing import Dict, List, Optional

from pypdf import PdfReader


def extract_text(pdf_path: str) -> str:
    reader = PdfReader(pdf_path)
    pages = []
    for page in reader.pages:
        pages.append(page.extract_text() or "")
    return "\n".join(pages)


def infer_year(text: str, default_year: Optional[int] = None) -> int:
    if default_year is not None:
        return default_year

    match = re.search(r"\b(20\d{2})\b", text)
    if match:
        return int(match.group(1))

    return datetime.now().year


def normalise_spaces(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def normalise_time(value: str) -> str:
    value = value.strip().replace(".", ":")
    m = re.match(r"^(\d{1,2}):(\d{2})$", value)
    if not m:
        return value

    hour = int(m.group(1))
    minute = int(m.group(2))

    if 1 <= hour <= 11:
        hour += 12

    return f"{hour:02d}:{minute:02d}"


def month_number(month_name: str) -> int:
    months = {
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
    return months[month_name.lower()]


def strip_referee(value: str) -> tuple[str, str]:
    """
    Split:
      'Garrycastle 2 V. Cox' -> ('Garrycastle 2', 'V. Cox')
      'Esker Gaels P. McCaughey' -> ('Esker Gaels', 'P. McCaughey')
      'Garrycastle R. Cornally' -> ('Garrycastle', 'R. Cornally')
    """
    value = normalise_spaces(value)

    patterns = [
        r"^(.*?)\s+([A-Z]\.\s*[A-Z][A-Za-z'/-]+)$",
        r"^(.*?)\s+([A-Z]\s*\.\s*[A-Z][A-Za-z'/-]+)$",
        r"^(.*?)\s+([A-Z][a-z]+\s+[A-Z][A-Za-z'/-]+)$",
        r"^(.*?)\s+([A-Z][a-z]+\s+[A-Z][A-Za-z'/-]+\s+[A-Z][A-Za-z'/-]+)$",
    ]

    for pattern in patterns:
        m = re.match(pattern, value)
        if m:
            team = normalise_spaces(m.group(1))
            referee = normalise_spaces(m.group(2))
            referee = re.sub(r"\s*\.\s*", ". ", referee).replace(".  ", ". ").strip()
            referee = re.sub(r"\s+", " ", referee)
            return team, referee

    return value, ""


def fixtures_to_rows(text: str, team_name: str = "Garrycastle", year: Optional[int] = None) -> List[Dict]:
    lines = [normalise_spaces(line) for line in text.splitlines() if line.strip()]
    detected_year = infer_year(text, year)

    rows: List[Dict] = []

    current_age_group = None
    current_date_iso = None
    current_date_display = None
    current_weekday = None
    current_division = None
    current_throw_in = None

    throw_in_re = re.compile(r"throw\s*in\s*([0-9]{1,2}[.:][0-9]{2})", re.IGNORECASE)
    section_re = re.compile(
        r"^(Under\s+\d+|Minor)\s+Football\s+Fixtures\s+"
        r"(Monday|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday)\s+"
        r"(\d{1,2})(?:st|nd|rd|th)?\s+([A-Za-z]+)$",
        re.IGNORECASE,
    )
    division_re = re.compile(r"^Division\s+(\d+)$", re.IGNORECASE)
    fixture_re = re.compile(r"^(.*?)\s+v\s+(.*?)$", re.IGNORECASE)

    for line in lines:
        ti_match = throw_in_re.search(line)
        if ti_match:
            current_throw_in = normalise_time(ti_match.group(1))
            continue

        section_match = section_re.match(line)
        if section_match:
            current_age_group = section_match.group(1).title()
            current_weekday = section_match.group(2).title()
            day = int(section_match.group(3))
            month = month_number(section_match.group(4))
            dt = datetime(detected_year, month, day)
            current_date_iso = dt.strftime("%Y-%m-%d")
            current_date_display = dt.strftime("%A %d %B %Y")
            current_division = None
            continue

        division_match = division_re.match(line)
        if division_match:
            current_division = f"Division {division_match.group(1)}"
            continue

        fixture_match = fixture_re.match(line)
        if fixture_match and current_age_group and current_division:
            home_team = normalise_spaces(fixture_match.group(1))
            away_with_ref = normalise_spaces(fixture_match.group(2))
            away_team, referee = strip_referee(away_with_ref)

            if team_name.lower() not in home_team.lower() and team_name.lower() not in away_team.lower():
                continue

            is_home = team_name.lower() in home_team.lower()
            opponent = away_team if is_home else home_team
            competition = f"{current_age_group}, {current_division}"

            rows.append(
                {

                    "date": current_date_display,
                    "weekday": current_weekday,
                    "start_time": current_throw_in,
                    "competition": competition,
                    "age_group": current_age_group,
                    "home_team": home_team,
                    "away_team": away_team,
                    "referee": referee,
                }
            )

    return rows
