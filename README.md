# zonemath

Answers one question: if it's this wall-clock time in one timezone, what
time is it in another?

That sounds trivial until you hit the two cases where "what time is it"
doesn't have an obvious answer:

- **The time never happened.** When clocks spring forward, the local
  wall clock skips a stretch of time entirely. `2:30 AM` on the day
  `America/New_York` starts DST is not a real moment - it never showed
  up on anyone's clock.
- **The time happened twice.** When clocks fall back, an hour repeats.
  `1:30 AM` on the day DST ends happened once before the clocks changed
  and once after, at two different UTC instants.

Most conversion code either ignores this (and silently picks whichever
answer the underlying library defaults to) or crashes in a way that's
hard to trace back to the actual cause. `zonemath` makes both cases
explicit: nonexistent times raise a specific error, and ambiguous times
require you to say which occurrence you mean (or default to the earlier
one and tell you it guessed).

It's a thin, careful wrapper around the standard library's `zoneinfo` -
no timezone database is bundled or vendored, no third-party packages
are involved.

## Usage

As a library:

```python
from datetime import datetime
from zonemath import convert, NonexistentTimeError

result = convert(datetime(2026, 6, 15, 9, 0), "America/New_York", "Asia/Tokyo")
print(result.target)          # 2026-06-15 22:00:00+09:00
print(result.is_ambiguous)    # False

try:
    convert(datetime(2026, 3, 8, 2, 30), "America/New_York", "UTC")
except NonexistentTimeError as exc:
    print(exc)  # 2026-03-08T02:30:00 does not exist in America/New_York
```

From the command line:

```
$ python -m zonemath "2026-06-15 09:00" America/New_York Asia/Tokyo
2026-06-15 22:00:00 JST (UTC+0900)

$ python -m zonemath "2026-11-01 01:30" America/New_York UTC
2026-11-01 05:30:00 UTC (UTC+0000)
note: 2026-11-01 01:30:00 occurs twice in America/New_York; used fold=0

$ python -m zonemath "2026-11-01 01:30" America/New_York UTC --fold 1
2026-11-01 06:30:00 UTC (UTC+0000)
```

Timezone names are IANA identifiers (`Europe/London`, `Australia/Sydney`,
`Pacific/Chatham`), the same names used by `zoneinfo`, not fixed UTC
offsets - offsets change with DST and with policy, zone names don't.

## Requirements

Python 3.9+, standard library only. On Linux you may need the `tzdata`
system package installed (or `pip install tzdata` if your distribution
doesn't ship one); macOS and Windows builds of Python bundle timezone
data through the OS or through `tzdata` automatically where needed.

## Running the tests

```
python -m unittest discover -s tests
```

The test suite is table-driven and deliberately spends most of its rows
on the awkward cases: spring-forward gaps, fall-back ambiguity in both
hemispheres (their DST calendars run in opposite months), fractional
UTC offsets (`Asia/Kolkata` at +5:30, `Pacific/Chatham` at +12:45), and
the day Samoa skipped entirely in December 2011 when it jumped across
the international date line.

## Status

Early. The core conversion logic and its test suite are the priority;
see the roadmap for what's still missing.
