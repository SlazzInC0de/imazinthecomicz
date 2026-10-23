"""Small text helpers shared by the fetchers and the dataset builder."""
import html
import re

_TAG = re.compile(r"<[^>]+>")
_SOURCE = re.compile(r"\((?:source|sources|from)\s*:[^)]*\)", re.IGNORECASE)
_NOTE = re.compile(r"\n\s*(?:note|notes)\s*:.*$", re.IGNORECASE | re.DOTALL)
_MD = re.compile(r"(~!|!~|__|\*\*|~~~)")
_SPACE = re.compile(r"[ \t\r\f\v]+")
_BLANKS = re.compile(r"\n{3,}")


def clean_description(raw: str | None) -> str:
    """Turn an AniList / Comic Vine description into plain readable text."""
    if not raw:
        return ""
    text = re.sub(r"<br\s*/?>", "\n", raw, flags=re.IGNORECASE)
    text = re.sub(r"</p>\s*<p[^>]*>", "\n\n", text, flags=re.IGNORECASE)
    text = _TAG.sub("", text)
    text = html.unescape(text)
    text = _MD.sub("", text)
    text = _SOURCE.sub("", text)
    text = _NOTE.sub("", text)
    text = _SPACE.sub(" ", text)
    text = "\n".join(line.strip() for line in text.split("\n"))
    text = _BLANKS.sub("\n\n", text)
    return text.strip()


def first_paragraphs(text: str, limit: int = 1400) -> str:
    """Trim long wiki-style descriptions at a paragraph or sentence boundary."""
    if len(text) <= limit:
        return text
    cut = text[:limit]
    for sep in ("\n\n", ". ", "\n"):
        idx = cut.rfind(sep)
        if idx > limit * 0.5:
            return cut[: idx + (1 if sep == ". " else 0)].strip()
    return cut.strip()
