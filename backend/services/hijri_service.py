"""
Hijri Calendar Cultural Context Layer
PRD Section 5.3, F12: When an official document references a Gregorian
  deadline, the system optionally displays the Hijri equivalent for Muslim users.
Uses hijri-converter Python library.
"""

from __future__ import annotations

import logging
import re
from datetime import datetime, date

from hijri_converter import Gregorian

logger = logging.getLogger(__name__)

# Common date patterns found in Malaysian government docs
DATE_PATTERNS = [
    r"(\d{1,2})\s+(Januari|Februari|Mac|April|Mei|Jun|Julai|Ogos|September|Oktober|November|Disember)\s+(\d{4})",
    r"(\d{1,2})\s+(January|February|March|April|May|June|July|August|September|October|November|December)\s+(\d{4})",
    r"(\d{1,2})/(\d{1,2})/(\d{4})",
    r"(\d{4})-(\d{2})-(\d{2})",
]

BM_MONTHS = {
    "Januari": 1, "Februari": 2, "Mac": 3, "April": 4,
    "Mei": 5, "Jun": 6, "Julai": 7, "Ogos": 8,
    "September": 9, "Oktober": 10, "November": 11, "Disember": 12,
}

EN_MONTHS = {
    "January": 1, "February": 2, "March": 3, "April": 4,
    "May": 5, "June": 6, "July": 7, "August": 8,
    "September": 9, "October": 10, "November": 11, "December": 12,
}

HIJRI_MONTHS = [
    "", "Muharram", "Safar", "Rabi'ul Awal", "Rabi'ul Akhir",
    "Jamadil Awal", "Jamadil Akhir", "Rejab", "Sya'ban",
    "Ramadan", "Syawal", "Zulkaedah", "Zulhijjah",
]


def gregorian_to_hijri(g_date: date) -> str:
    """Convert a Gregorian date to a Hijri date string."""
    try:
        hijri = Gregorian(g_date.year, g_date.month, g_date.day).to_hijri()
        month_name = HIJRI_MONTHS[hijri.month] if hijri.month <= 12 else str(hijri.month)
        return f"{hijri.day} {month_name} {hijri.year} H"
    except Exception as exc:
        logger.warning(f"Hijri conversion failed for {g_date}: {exc}")
        return ""


def _parse_date_from_match(match: re.Match, pattern_idx: int) -> date | None:
    """Parse a date from a regex match based on pattern index."""
    try:
        groups = match.groups()
        if pattern_idx == 0:  # BM month names
            day, month_name, year = int(groups[0]), BM_MONTHS.get(groups[1], 0), int(groups[2])
            if month_name:
                return date(year, month_name, day)
        elif pattern_idx == 1:  # EN month names
            day, month_name, year = int(groups[0]), EN_MONTHS.get(groups[1], 0), int(groups[2])
            if month_name:
                return date(year, month_name, day)
        elif pattern_idx == 2:  # DD/MM/YYYY
            return date(int(groups[2]), int(groups[1]), int(groups[0]))
        elif pattern_idx == 3:  # YYYY-MM-DD
            return date(int(groups[0]), int(groups[1]), int(groups[2]))
    except (ValueError, IndexError):
        return None
    return None


def enrich_text_with_hijri(text: str) -> str:
    """
    Scan text for Gregorian dates and append Hijri equivalents inline.
    PRD F12: When a Gregorian deadline is referenced, display Hijri equivalent.
    """
    enriched = text
    for idx, pattern in enumerate(DATE_PATTERNS):
        for match in re.finditer(pattern, text):
            g_date = _parse_date_from_match(match, idx)
            if g_date:
                hijri_str = gregorian_to_hijri(g_date)
                if hijri_str:
                    original = match.group(0)
                    replacement = f"{original} ({hijri_str})"
                    enriched = enriched.replace(original, replacement, 1)

    return enriched
