"""Command-line entry point: python -m zonemath TIME FROM_ZONE TO_ZONE"""

from __future__ import annotations

import argparse
import sys
from datetime import datetime
from zoneinfo import ZoneInfoNotFoundError

from .core import ConversionResult, NonexistentTimeError, convert

TIME_FORMATS = (
    "%Y-%m-%d %H:%M:%S",
    "%Y-%m-%d %H:%M",
    "%Y-%m-%dT%H:%M:%S",
    "%Y-%m-%dT%H:%M",
)


def _parse_time(value: str) -> datetime:
    for fmt in TIME_FORMATS:
        try:
            return datetime.strptime(value, fmt)
        except ValueError:
            continue
    raise argparse.ArgumentTypeError(
        f"could not parse {value!r}; expected e.g. '2026-03-08 02:30'"
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="zonemath",
        description="Convert a wall-clock time from one IANA timezone to another.",
    )
    parser.add_argument("time", type=_parse_time, help="local time, e.g. '2026-03-08 02:30'")
    parser.add_argument("from_zone", help="source IANA zone, e.g. America/New_York")
    parser.add_argument("to_zone", help="target IANA zone, e.g. Europe/London")
    parser.add_argument(
        "--fold",
        type=int,
        choices=(0, 1),
        default=0,
        help="which occurrence to use if the time is ambiguous (default: 0, the earlier one)",
    )
    return parser


def main(argv: "list[str] | None" = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        result: ConversionResult = convert(args.time, args.from_zone, args.to_zone, fold=args.fold)
    except NonexistentTimeError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1
    except ZoneInfoNotFoundError as exc:
        print(f"error: unknown timezone: {exc}", file=sys.stderr)
        return 1

    print(result.target.strftime("%Y-%m-%d %H:%M:%S %Z (UTC%z)"))
    if result.is_ambiguous:
        print(
            f"note: {args.time.isoformat(sep=' ')} occurs twice in {args.from_zone}; "
            f"used fold={args.fold}",
            file=sys.stderr,
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
