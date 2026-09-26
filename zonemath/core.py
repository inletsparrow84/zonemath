"""Wall-clock time conversion between IANA timezones.

Answers one question: given a local time in one timezone, what is the
corresponding local time in another timezone? The interesting part is
telling the truth about times that don't exist (DST spring-forward gaps,
or the day Samoa skipped in 2011) and times that happen twice (DST
fall-back), rather than silently picking an answer.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timezone
from zoneinfo import ZoneInfo, available_timezones

__all__ = ["ConversionResult", "NonexistentTimeError", "convert", "search_zones"]


class NonexistentTimeError(ValueError):
    """The given local time never happened in the source zone."""


@dataclass(frozen=True)
class ConversionResult:
    source: datetime  # aware, in from_zone
    target: datetime  # aware, in to_zone
    is_ambiguous: bool  # True if the source wall-clock time occurs twice


def convert(
    local_dt: datetime,
    from_zone: str,
    to_zone: str,
    *,
    fold: int = 0,
) -> ConversionResult:
    """Convert a naive wall-clock time in from_zone to its equivalent in to_zone.

    fold picks which occurrence to use when local_dt is ambiguous (0 = the
    earlier UTC offset that day, 1 = the later one); it's ignored otherwise.
    Raises NonexistentTimeError if local_dt never occurred in from_zone.
    """
    if local_dt.tzinfo is not None:
        raise ValueError("local_dt must be naive (no tzinfo); it is interpreted in from_zone")

    src = ZoneInfo(from_zone)

    if _is_nonexistent(local_dt, src):
        raise NonexistentTimeError(f"{local_dt.isoformat()} does not exist in {from_zone}")

    aware_source = local_dt.replace(tzinfo=src, fold=fold)
    target = aware_source.astimezone(ZoneInfo(to_zone))

    return ConversionResult(
        source=aware_source,
        target=target,
        is_ambiguous=_is_ambiguous(local_dt, src),
    )


def search_zones(pattern: str = "") -> list[str]:
    """Return known IANA zone names containing pattern (case-insensitive), sorted.

    Matching is a plain substring test, not a glob or regex, so e.g. "chatham"
    finds "Pacific/Chatham" and an empty pattern lists every zone the local
    tzdata knows about.
    """
    needle = pattern.lower()
    return sorted(name for name in available_timezones() if needle in name.lower())


def _is_nonexistent(naive_dt: datetime, zone: ZoneInfo) -> bool:
    # If the wall clock never showed this value, the offset used to build it
    # was borrowed from before or after a gap, and converting to UTC and
    # back won't land back on naive_dt.
    aware = naive_dt.replace(tzinfo=zone)
    round_trip = aware.astimezone(timezone.utc).astimezone(zone)
    return round_trip.replace(tzinfo=None) != naive_dt


def _is_ambiguous(naive_dt: datetime, zone: ZoneInfo) -> bool:
    earlier = naive_dt.replace(tzinfo=zone, fold=0).utcoffset()
    later = naive_dt.replace(tzinfo=zone, fold=1).utcoffset()
    return earlier != later
