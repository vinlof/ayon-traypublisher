"""Resolve marketing metadata from a dropped filename.

The rules follow Gigaswitcher Cavalry names without importing that addon.
``products_9x16_story_SE`` yields region ``SE``, format ``story`` and aspect
``9:16``. ``de-youtube-kontoret-9x16`` yields region ``DE`` and aspect ``9:16``.
A language code or a ``story``, ``feed``, or ``reel`` token can sit anywhere
in the name when it is separated by ``_`` or ``-``.
"""

import math
import re


MARKETING_REGIONS = frozenset({
    "SE",
    "DK",
    "FI",
    "DE",
    "AT",
    "FR",
    "NL",
})

_FORMAT_SUFFIXES = frozenset({
    "mp4",
    "mov",
    "m4v",
    "avi",
    "mkv",
    "png",
    "jpg",
    "jpeg",
    "exr",
    "tiff",
    "tif",
    "tga",
    "bmp",
    "svg",
})

_REGION_TOKEN_RE = re.compile(
    r"(?:^|[_\-])({})(?=[_\-]|$)".format(
        "|".join(sorted(MARKETING_REGIONS))
    ),
    re.IGNORECASE,
)
_FORMAT_TOKEN_RE = re.compile(
    r"(?:^|[_\-])(story|feed|reel)(?=[_\-]|$)",
    re.IGNORECASE,
)
_PIXEL_SIZE_RE = re.compile(r"(\d+)px_(\d+)px", re.IGNORECASE)
_ASPECT_TOKEN_RE = re.compile(
    r"(?:^|[_\-.])(\d+)\s*[xX:]\s*(\d+)(?:[_\-.]|$)"
)


def canonical_aspect_ratio(width, height):
    """Return a GCD-reduced ``width:height`` label, or ``None``."""

    try:
        width = int(width)
        height = int(height)
    except (TypeError, ValueError):
        return None
    if width <= 0 or height <= 0:
        return None
    divisor = math.gcd(width, height)
    return "{}:{}".format(width // divisor, height // divisor)


def parse_marketing_filename(name):
    """Return marketing fields found in ``name``.

    Present keys are ``marketingRegion``, ``marketingFormat`` and
    ``aspectRatio``. A name that matches none of them returns an empty dict.
    """

    raw_name = str(name or "").strip()
    if not raw_name:
        return {}

    parsed = {}
    aspect_ratio = _aspect_ratio_from_name(raw_name)
    if aspect_ratio:
        parsed["aspectRatio"] = aspect_ratio

    sanitized = _strip_optional_suffixes(_sanitize_name(raw_name))
    if not sanitized:
        return parsed

    format_match = _FORMAT_TOKEN_RE.search(sanitized)
    if format_match:
        parsed["marketingFormat"] = format_match.group(1).lower()

    region_match = _REGION_TOKEN_RE.search(sanitized)
    if region_match:
        parsed["marketingRegion"] = region_match.group(1).upper()
    return parsed


def _aspect_ratio_from_name(raw_name):
    token_match = _ASPECT_TOKEN_RE.search(raw_name)
    if token_match:
        return canonical_aspect_ratio(
            token_match.group(1),
            token_match.group(2),
        )
    pixel_match = _PIXEL_SIZE_RE.search(raw_name)
    if pixel_match:
        return canonical_aspect_ratio(
            pixel_match.group(1),
            pixel_match.group(2),
        )
    return None


def _sanitize_name(name):
    sanitized = re.sub(r"[^\w\-]", "_", name).strip("_")
    return re.sub(r"_+", "_", sanitized).strip("_")


def _strip_optional_suffixes(sanitized_name):
    """Drop a trailing frame index and file-extension suffix."""

    current = sanitized_name
    changed = True
    while changed and current:
        changed = False
        if "_" not in current:
            break
        base, suffix = current.rsplit("_", 1)
        if not base:
            break
        if suffix.lower() in _FORMAT_SUFFIXES or suffix.isdigit():
            current = base
            changed = True
    return current
