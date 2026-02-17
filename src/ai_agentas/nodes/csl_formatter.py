from __future__ import annotations

from .parse_bibliography import ParsedReference


SUPPORTED_STYLES = ["APA 7", "IEEE", "ISO 690", "MLA 9"]


def _fmt_authors_apa(author: str | None) -> str:
    if not author:
        return "Anon."
    parts = [a.strip() for a in author.split(",") if a.strip()]
    if len(parts) == 1:
        return parts[0]
    if len(parts) == 2:
        return f"{parts[0]} & {parts[1]}"
    return ", ".join(parts[:-1]) + f", & {parts[-1]}"


def _fmt_authors_ieee(author: str | None) -> str:
    if not author:
        return "Anon"
    parts = [a.strip() for a in author.split(",") if a.strip()]
    if len(parts) <= 3:
        return ", ".join(parts)
    return f"{parts[0]} et al."


def _fmt_authors_mla(author: str | None) -> str:
    if not author:
        return "Anon."
    parts = [a.strip() for a in author.split(",") if a.strip()]
    if len(parts) == 1:
        return parts[0] + "."
    if len(parts) == 2:
        return f"{parts[0]}, and {parts[1]}."
    return f"{parts[0]}, et al."


def _fmt_authors_iso(author: str | None) -> str:
    if not author:
        return "ANON."
    parts = [a.strip().upper() for a in author.split(",") if a.strip()]
    return ", ".join(parts) + "."


def _safe(val: str | None, default: str = "") -> str:
    return val.strip() if val else default


def format_apa7(ref: ParsedReference) -> str:
    """APA 7th edition"""
    author = _fmt_authors_apa(ref.author)
    year = f"({_safe(ref.year, 'n.d.')})"
    title = _safe(ref.title, "Untitled")

    parts = [f"{author} {year}. {title}."]

    if ref.journal:
        journal_part = f"*{ref.journal}*"
        if ref.volume:
            journal_part += f", *{ref.volume}*"
            if ref.issue:
                journal_part += f"({ref.issue})"
        if ref.pages:
            journal_part += f", {ref.pages}"
        journal_part += "."
        parts.append(journal_part)

    if ref.doi:
        parts.append(f"https://doi.org/{ref.doi}")
    elif ref.url:
        parts.append(ref.url)

    return " ".join(parts)


def format_ieee(ref: ParsedReference, number: int) -> str:
    """IEEE style"""
    author = _fmt_authors_ieee(ref.author)
    title = _safe(ref.title, "Untitled")
    parts = [f"[{number}] {author},"]
    parts.append(f'"{title},"')

    if ref.journal:
        journal_part = f"*{ref.journal}*"
        if ref.volume:
            journal_part += f", vol. {ref.volume}"
        if ref.issue:
            journal_part += f", no. {ref.issue}"
        if ref.pages:
            journal_part += f", pp. {ref.pages}"
        if ref.year:
            journal_part += f", {ref.year}"
        journal_part += "."
        parts.append(journal_part)
    elif ref.year:
        parts.append(f"{ref.year}.")

    if ref.doi:
        parts.append(f"doi: {ref.doi}.")

    return " ".join(parts)


def format_iso690(ref: ParsedReference) -> str:
    """ISO 690"""
    author = _fmt_authors_iso(ref.author)
    year = _safe(ref.year, "n.d.")
    title = _safe(ref.title, "Untitled")

    parts = [f"{author} {title}."]

    if ref.journal:
        journal_part = f"*{ref.journal}*"
        if ref.year:
            journal_part += f", {year}"
        if ref.volume:
            journal_part += f", vol. {ref.volume}"
        if ref.issue:
            journal_part += f", no. {ref.issue}"
        if ref.pages:
            journal_part += f", p. {ref.pages}"
        journal_part += "."
        parts.append(journal_part)
    else:
        parts.append(f"{year}.")

    if ref.doi:
        parts.append(f"DOI: {ref.doi}.")
    elif ref.url:
        parts.append(f"Prieiga per: {ref.url}.")

    return " ".join(parts)


def format_mla9(ref: ParsedReference) -> str:
    """MLA 9th edition"""
    author = _fmt_authors_mla(ref.author)
    title = f'"{_safe(ref.title, "Untitled")}."'

    parts = [author, title]

    if ref.journal:
        journal_part = f"*{ref.journal}*"
        if ref.volume:
            journal_part += f", vol. {ref.volume}"
        if ref.issue:
            journal_part += f", no. {ref.issue}"
        if ref.year:
            journal_part += f", {ref.year}"
        if ref.pages:
            journal_part += f", pp. {ref.pages}"
        journal_part += "."
        parts.append(journal_part)

    if ref.doi:
        parts.append(f"https://doi.org/{ref.doi}.")
    elif ref.url:
        parts.append(f"{ref.url}.")

    return " ".join(parts)


def format_reference(ref: ParsedReference, style: str, number: int = 1) -> str:
    """Formatuoja viena saltini pagal pasirinkta stiliaus pavadinima."""
    style_lower = style.lower().strip()
    if "apa" in style_lower:
        return format_apa7(ref)
    if "ieee" in style_lower:
        return format_ieee(ref, number)
    if "iso" in style_lower:
        return format_iso690(ref)
    if "mla" in style_lower:
        return format_mla9(ref)
    return format_apa7(ref)


def format_bibliography(refs: list[ParsedReference], style: str) -> str:
    """Formatuoja visa bibliografijos sarasa pagal pasirinkta stilu."""
    lines = []
    for i, ref in enumerate(refs):
        lines.append(format_reference(ref, style, number=i + 1))
    return "\n\n".join(lines)
