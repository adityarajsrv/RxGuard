import re

_STRENGTH_RE = re.compile(
    r"^(?P<name>.+?)\s+(?P<num>\d+(?:\.\d+)?)\s*(?:mg)?$", re.IGNORECASE
)


def split_name_and_strength(text: str) -> tuple[str, float | None]:
    cleaned = " ".join(text.strip().split())
    match = _STRENGTH_RE.match(cleaned)
    if not match:
        return cleaned, None
    value = float(match.group("num"))
    if not (0 < value <= 5000):
        return cleaned, None
    return match.group("name").strip(), value