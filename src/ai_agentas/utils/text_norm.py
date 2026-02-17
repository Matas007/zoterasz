from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass


_WS_RE = re.compile(r"\s+")


def norm_ws(s: str) -> str:
    """Normalizuoja whitespace (naudinga palyginimui)."""
    return _WS_RE.sub(" ", (s or "").strip())


_BIB_HEADINGS = {
    "literatura",
    "literaturos sarasas",
    "saltiniai",
    "references",
    "bibliography",
    "literature",
    "works cited",
    "naudota literatura",
    "naudoti saltiniai",
    "informacijos saltiniai",
}

# Lietuviskos raidziu formos (su ir be diakritiku)
_BIB_HEADINGS_WITH_DIACRITICS = {
    "literat\u016bra",
    "literat\u016bros s\u0105ra\u0161as",
    "\u0161altiniai",
}

_ALL_BIB_HEADINGS = _BIB_HEADINGS | _BIB_HEADINGS_WITH_DIACRITICS


def _ascii_fold(s: str) -> str:
    s = unicodedata.normalize("NFKD", s)
    s = "".join(ch for ch in s if not unicodedata.combining(ch))
    return s


def looks_like_heading(line: str) -> bool:
    """Ar eilute atrodo kaip bibliografijos skyriaus antraste."""
    l = norm_ws(line).lower()
    # Pasaliname numeracija priekyje (pvz. "5. Literatura")
    l = re.sub(r"^\d+[\.\)]\s*", "", l).strip()
    # Pasaliname gale esancius skyrybos zenklus (pvz. "LITERATURA:")
    l = re.sub(r"[:;\-–—\.\s]+$", "", l).strip()
    # PDF atveju kartais buna isskaidyta raidemis: "L I T E R A T U R A"
    compact = re.sub(r"\s+", "", l)
    folded = _ascii_fold(compact)
    normalized_set = {_ascii_fold(x.replace(" ", "")) for x in _ALL_BIB_HEADINGS}
    return compact in {x.replace(" ", "") for x in _ALL_BIB_HEADINGS} or folded in normalized_set


# Antrasciau, kuriu atsiradimas reiskia, kad bibliografija baigesi
_STOP_HEADINGS_RE = re.compile(
    r"^\s*(?:\d+[\.\)]\s*)?"
    r"(pried(?:as|ai)|appendix|appendices|priedai"
    r"|santrauka|summary|abstract"
    r"|interviu|interview"
    r"|klausimynas|questionnaire"
    r"|\.?\s*priedas\b)",
    re.IGNORECASE,
)


def looks_like_stop_heading(line: str) -> bool:
    """Ar eilute atrodo kaip skyriaus antraste, kuri eina PO bibliografijos
    (pvz. Priedai, Santrauka, Appendix)."""
    l = norm_ws(line)
    if not l:
        return False
    # Per ilga eilute greiciausiai nera antraste
    if len(l) > 120:
        return False
    return bool(_STOP_HEADINGS_RE.match(l))


def split_lines(text: str) -> list[str]:
    return [ln.rstrip("\n") for ln in (text or "").splitlines()]


def join_lines(lines: list[str]) -> str:
    return "\n".join(lines)


@dataclass(frozen=True)
class BibliographySplit:
    body_text: str
    bibliography_text: str
    bibliography_start_line: int | None
