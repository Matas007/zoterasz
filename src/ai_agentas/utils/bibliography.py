from __future__ import annotations

import re

from .text_norm import (
    BibliographySplit,
    looks_like_heading,
    looks_like_stop_heading,
    norm_ws,
    split_lines,
    join_lines,
)


_BIB_ITEM_BULLET_RE = re.compile(r"^\s*([\[\(]?\d+[\]\)]\.?|\-\s+|\u2022\s+)\s+")


def _is_bib_item_like(line: str) -> bool:
    """Heuristika: ar eilute panasi i bibliografijos irasa."""
    l = norm_ws(line)
    if not l:
        return False
    if _BIB_ITEM_BULLET_RE.match(line):
        return True
    # Autorius, metai...
    if re.search(r"\b(19|20)\d{2}\b", l) and ("," in l or "." in l):
        return True
    # DOI / URL
    if "doi:" in l.lower() or "http://" in l.lower() or "https://" in l.lower():
        return True
    return False


def _is_clearly_not_reference(entry: str) -> bool:
    """Atfiltruoja irasus, kurie tikrai nera bibliografijos saltiniai."""
    l = norm_ws(entry).lower()
    if not l:
        return True
    # Per trumpas
    if len(l) < 15:
        return True
    # Atrodo kaip antraste / priedas / klausimas
    if looks_like_stop_heading(entry):
        return True
    # Interviu / klausimyno turinys
    if l.startswith("sveiki") or l.startswith("ar galite") or l.startswith("ar j"):
        return True
    # DIDELES RAIDES be metu = greiciausiai antraste, ne saltinis
    upper_ratio = sum(1 for c in entry if c.isupper()) / max(1, sum(1 for c in entry if c.isalpha()))
    has_year = bool(re.search(r"\b(19|20)\d{2}\b", l))
    if upper_ratio > 0.6 and not has_year and len(l) < 100:
        return True
    # Nera nei metu, nei autoriaus su taskeliu/kableliu, nei DOI/URL
    has_punct = "." in l and "," in l
    has_doi_url = "doi" in l or "http" in l
    if not has_year and not has_punct and not has_doi_url and len(l) < 200:
        return True
    return False


def split_bibliography(text: str) -> BibliographySplit:
    """
    Atskiria dokumento pagrindini teksta nuo literaturos saraso.

    Strategija:
    1. Ieskome antrascuu (References/Literatura/...) nuo galo
    2. Po rastos antrastes imame eilutes IKI kitos stop-antrastes (Priedai, Santrauka...)
    3. Jei antrastes nera — heuristinis "bib-like" tankio paieska
    """
    lines = split_lines(text)
    if not lines:
        return BibliographySplit(body_text="", bibliography_text="", bibliography_start_line=None)

    # 1) Antraste nuo galo
    bib_heading_idx = None
    for i in range(len(lines) - 1, -1, -1):
        if looks_like_heading(lines[i]):
            bib_heading_idx = i
            break

    if bib_heading_idx is not None:
        # Nustatome bibliografijos pabaiga: iki kitos "stop" antrastes arba dokumento galo
        bib_start = bib_heading_idx + 1
        bib_end = len(lines)
        for j in range(bib_start, len(lines)):
            if looks_like_stop_heading(lines[j]):
                bib_end = j
                break

        bib = join_lines(lines[bib_start:bib_end]).strip()
        body = join_lines(lines[:bib_heading_idx]).rstrip()
        return BibliographySplit(body_text=body, bibliography_text=bib, bibliography_start_line=bib_start)

    # 2) Heuristika: surandame nuo galo ilgesni segmenta su bib-item eiluciu dauguma
    min_tail = min(80, len(lines))
    tail_start = len(lines) - min_tail

    best = None  # (score, start_idx_in_doc)
    for start in range(tail_start, len(lines)):
        seg = lines[start:]
        non_empty = [ln for ln in seg if norm_ws(ln)]
        if len(non_empty) < 5:
            continue
        bib_like = sum(1 for ln in non_empty if _is_bib_item_like(ln))
        score = bib_like / max(1, len(non_empty))
        if score >= 0.55:
            cand = (score, start)
            if best is None or cand[1] < best[1] or (cand[1] == best[1] and cand[0] > best[0]):
                best = cand

    if best is None:
        return BibliographySplit(body_text=text.rstrip(), bibliography_text="", bibliography_start_line=None)

    _, start = best
    body = join_lines(lines[:start]).rstrip()
    bib = join_lines(lines[start:]).strip()
    return BibliographySplit(body_text=body, bibliography_text=bib, bibliography_start_line=start)


def bibliography_to_entries(bibliography_text: str) -> list[str]:
    """
    Suskaldo bibliografijos teksta i atskirus irasus.
    Grupuoja pagal tuscias eilutes arba numeracija/bullet.
    Isfiltruoja aiksiai ne-saltininius irasus.
    """
    lines = split_lines(bibliography_text)
    entries: list[str] = []
    buf: list[str] = []

    def flush():
        nonlocal buf
        e = " ".join(norm_ws(x) for x in buf if norm_ws(x)).strip()
        if e:
            entries.append(e)
        buf = []

    for ln in lines:
        stripped = norm_ws(ln)
        if not stripped:
            flush()
            continue
        # Jei sutinkame stop-antraste — stabdom viska
        if looks_like_stop_heading(ln):
            flush()
            break
        if buf and _BIB_ITEM_BULLET_RE.match(ln):
            flush()
        buf.append(ln)

    flush()

    # Filtruojame: ismetame per trumpus ir aiksiai ne-saltininius
    return [e for e in entries if len(e) >= 15 and not _is_clearly_not_reference(e)]
