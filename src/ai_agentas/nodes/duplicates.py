from __future__ import annotations

from dataclasses import dataclass

from rapidfuzz import fuzz

from .parse_bibliography import ParsedReference


@dataclass(frozen=True)
class DuplicatePair:
    index_a: int
    index_b: int
    ref_a: ParsedReference
    ref_b: ParsedReference
    score: float  # 0-100, kur 100 = identiskas
    reason: str


def _normalize(s: str | None) -> str:
    return (s or "").strip().lower()


def _title_similarity(a: ParsedReference, b: ParsedReference) -> float:
    ta = _normalize(a.title)
    tb = _normalize(b.title)
    if not ta or not tb:
        return 0.0
    return fuzz.token_sort_ratio(ta, tb)


def _author_similarity(a: ParsedReference, b: ParsedReference) -> float:
    aa = _normalize(a.author)
    ab = _normalize(b.author)
    if not aa or not ab:
        return 0.0
    return fuzz.token_sort_ratio(aa, ab)


def _doi_match(a: ParsedReference, b: ParsedReference) -> bool:
    da = _normalize(a.doi)
    db = _normalize(b.doi)
    return bool(da and db and da == db)


def find_duplicates(
    refs: list[ParsedReference],
    title_threshold: float = 80.0,
    author_threshold: float = 70.0,
) -> list[DuplicatePair]:
    """
    Suranda galimus dublikatus tarp saltintu saraso.
    Lygina: DOI (tikslus), pavadinima (fuzzy), autoriu + metus.
    """
    duplicates: list[DuplicatePair] = []
    n = len(refs)

    for i in range(n):
        for j in range(i + 1, n):
            a, b = refs[i], refs[j]

            # 1) DOI sutapimas - tikslus dublikatas
            if _doi_match(a, b):
                duplicates.append(DuplicatePair(
                    index_a=i, index_b=j, ref_a=a, ref_b=b,
                    score=100.0, reason="DOI sutampa",
                ))
                continue

            # 2) Pavadinimo panasumas
            title_sim = _title_similarity(a, b)
            if title_sim < title_threshold:
                continue

            # 3) Papildomi signalai
            author_sim = _author_similarity(a, b)
            same_year = (a.year and b.year and a.year == b.year)

            combined = title_sim * 0.6 + author_sim * 0.3 + (10.0 if same_year else 0.0)

            if combined >= 70.0:
                reasons = []
                reasons.append(f"Pavadinimai panasus ({title_sim:.0f}%)")
                if author_sim > 50:
                    reasons.append(f"autoriai panasus ({author_sim:.0f}%)")
                if same_year:
                    reasons.append(f"tie patys metai ({a.year})")
                duplicates.append(DuplicatePair(
                    index_a=i, index_b=j, ref_a=a, ref_b=b,
                    score=combined, reason="; ".join(reasons),
                ))

    duplicates.sort(key=lambda d: d.score, reverse=True)
    return duplicates
