---
description: Re-verify conference deadlines against official sources and update data.json
---

Re-verify the conference deadlines in `data.json` against their official sources and
update the file. $ARGUMENTS

If arguments name specific venues, check only those. Otherwise check every entry in
both `conferences` and `notAnnounced`.

## The one rule that matters

**Never write a date you did not read on a live official page.** Do not extrapolate
from last year. Do not reconstruct from memory — your training data is stale and these
dates change every cycle. If a date is not published, it stays unpublished.

A missing date is a small problem. A wrong date carrying a live countdown is the
failure this whole repository is built to prevent.

## Sources, in order of authority

1. **The venue's HotCRP instance** — `https://<conf><year>.hotcrp.com/deadlines`.
   This is the only machine-readable source and the only one that reliably states an
   exact clock time and timezone. Check it first. It has been right when the CFP page
   was silent: ICCAD 2026's camera-ready timezone appears *only* here.
2. **The official call-for-papers page**, linked as `callForPapers` in `data.json`.
3. **Nothing else.** Aggregators may be used to *locate* an official URL, never as the
   source of a date.

## Known traps — every one of these has actually occurred

- **`iccad.com` embeds a DATE promotional block** whose text contains a complete AoE
  deadline table ("Abstract Sunday, 13 September 2026 AoE", "Final paper Sunday,
  20 September 2026 AoE"). Those are DATE's dates on ICCAD's page. Any extraction that
  trusts proximity files them under ICCAD.
- **`mpc-deadlines` publishes fabricated ISCA 2027 dates** that are ISCA 2026 shifted
  forward exactly one year, including a "second submission round" that is really the
  separate Industry Track. It looks authoritative. It is invented.
- **ISCA's "rounds" are review rounds, not submission rounds.** ISCA 2026 had one main
  submission deadline and two reviewing rounds, plus a separate Industry Track.
- **The IEEE CASS PDF for ICCAD 2026 carried superseded dates for months** — rebuttal
  17 Jun and camera-ready 24 Aug, when the live site said 20 Jun and 4 Sep. Prefer the
  live site over any PDF, always.
- **DAC does not use AoE.** DAC 2026 published "November 11, 2025 (5 PM PST)". Assuming
  AoE hands authors ~19 hours that do not exist. DAC entries need both
  `"timezone": "PDT"` (or `PST`) and `"time": "17:00"`.
- **MICRO does not use AoE either** — it publishes EDT, roughly 16 hours earlier on the
  same calendar date.
- **DATE's site-wide "all times are CET" statement governs programme times, not
  deadlines.** Its deadlines are AoE. Rendering them at CET costs ~12 hours.
- **These sites keep prior years live at similar URLs.** Confirm the edition on every
  page you read. A date from the wrong year is the error that makes this pointless.

## Method

Work through each venue in turn:

1. Fetch the HotCRP deadlines page and the official CFP.
2. Extract every date: abstract, full paper, rebuttal window (start **and** end),
   notification, camera-ready. **Copy a verbatim quote for each one.** If you cannot
   quote it, you may not record it.
3. Capture the clock time and timezone **exactly as written**. Do not normalise
   "5:00pm US Pacific Time" into "23:59 AoE". If no time is published, that is the
   finding — record `"timezone": null` rather than assuming end-of-day AoE.
4. **Then verify your own work adversarially.** Re-read each page and try to *refute*
   what you just extracted. Is the quote really on that page? Is it the right edition?
   Is a rebuttal "period" start being recorded as its end? Treat anything you cannot
   personally re-confirm as unverified, and leave it alone rather than writing it.

Main-conference research tracks only. Workshops, tutorials, panels, PhD forums, student
competitions and artifact evaluation are deliberately out of scope.

## Updating the file

- Edit only `data.json`. The engine in `index.html` needs no changes.
- Add a new timezone to the `timezones` map if a venue uses one that is missing.
- When a venue in `notAnnounced` publishes its CFP, move it into `conferences` with its
  real dates and drop it from `notAnnounced`.
- Keep `watch` URLs current for anything still unannounced.

Then:

```
python3 tools/check_deadlines.py
```

It must exit 0 before you are done.

## Reporting back

Show a clear diff of what changed and, for every changed date, the verbatim quote and
the URL it came from. State plainly what you could **not** verify.

**Do not push, and do not commit without being asked.** Leave the working tree dirty
for a human to review. The whole point of using an agent here rather than a scraper is
that a person still reads the diff before it reaches the site.
