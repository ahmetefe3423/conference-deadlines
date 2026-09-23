# Conference Deadlines

**[ahmetefe3423.github.io/conference-deadlines](https://ahmetefe3423.github.io/conference-deadlines/)**

[![Check deadlines](https://github.com/ahmetefe3423/conference-deadlines/actions/workflows/check-deadlines.yml/badge.svg)](https://github.com/ahmetefe3423/conference-deadlines/actions/workflows/check-deadlines.yml)
[![License: MIT](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

Live countdowns to research-track paper deadlines across computer architecture and EDA
conferences — ICCAD, ASPLOS, MICRO, DATE, HPCA, DAC and ISCA — with the cycles that have
not published dates yet shown as clearly-labelled estimates rather than quietly omitted.

One static page, no build step, no dependencies. Every date is read from the venue's own
call for papers by hand, and a weekly job checks whether any of them has moved.

| | |
|---|---|
| [`index.html`](index.html) | The whole page: markup, styling and the countdown engine |
| [`data.json`](data.json) | Every deadline. The only file you edit to change a date |
| [`tools/check_deadlines.py`](tools/check_deadlines.py) | Weekly drift check against the live CFP pages |
| [`.claude/commands/update-deadlines.md`](.claude/commands/update-deadlines.md) | The agent prompt that re-verifies dates |
| [`icons/`](icons/), [`site.webmanifest`](site.webmanifest) | Name and icon when the page is installed as an app |

**Contents** · [Disclaimer](#disclaimer) · [Editing](#editing) ·
[Local preview](#local-preview) · [Automatic checking](#checking-the-dates-automatically) ·
[Installing as an app](#installing-it-as-an-app) · [License](#license)

## Disclaimer

**Unofficial, and no guarantee.** This is one person's page, not a service. Every date
was copied by hand from the venue's own call for papers or its HotCRP instance, and
then re-checked against the same source — but venues move deadlines, sometimes without
announcing it, and a date here can be stale or simply wrong. **The call for papers is
the authority.** Check it before you rely on anything here. The page is provided as is,
without warranty of any kind; missing a deadline is your risk, not the author's.

If you find a wrong date, please open an issue — that is the fastest way to fix it for
everyone.

## Editing

All deadlines live in **`data.json`**. You never need to touch `index.html` to add,
change or remove one. If the JSON is malformed or a field is wrong, the page prints
exactly what is wrong — including the line and column for a syntax error — instead of
rendering a wrong date.

### Adding a conference

```json
{
  "name": "DAC",
  "year": "2027",
  "cycle": "",
  "venue": "San Jose",
  "conferenceDates": ["2027-07-11", "2027-07-14"],
  "callForPapers": "https://dac.com/2027/authors/call-for-contributions",
  "deadlines": [
    { "label": "Abstract",   "date": "2026-11-10", "timezone": "PDT", "time": "17:00" },
    { "label": "Full paper", "date": "2026-11-17", "timezone": "PDT", "time": "17:00" }
  ]
}
```

### Fields

| Field | Meaning |
|---|---|
| `name` | Short name shown inside the circle, e.g. `"DATE"` |
| `year` | Shown under the name |
| `cycle` | Label for venues running more than one round into the same conference (ASPLOS Spring / Fall). Use `""` for a single round. |
| `venue` | City, shown under the circle |
| `conferenceDates` | `["YYYY-MM-DD", "YYYY-MM-DD"]` — start and end. Also the cycle's last event: see [Past cycles](#past-cycles). |
| `callForPapers` | URL of the official CFP |
| `deadlines` | The dates. Any order — the page sorts them. |

Each deadline:

| Field | Meaning |
|---|---|
| `label` | Shown on the page, e.g. `"Full paper"` |
| `date` | The date **exactly as the venue publishes it**, `YYYY-MM-DD` |
| `timezone` | A name from the `timezones` map, or `null` when the venue publishes no clock time at all |
| `time` | *Optional.* `"HH:MM"`, 24-hour. Defaults to `"23:59"`. |

### Timezones

`timezones` at the top of `data.json` maps a name to its offset from UTC in hours.
Add a line if a venue uses one that is missing.

Two things this exists to get right:

- **AoE is UTC−12**, the last timezone on Earth, so an AoE deadline lands on the
  *following* calendar day almost everywhere. The page shows dates as published by
  default so they match the CFP; the selector switches to your local time.
- **Not every venue uses AoE.** MICRO publishes EDT. DAC publishes 5 PM US Pacific,
  which needs both `"timezone": "PDT"` and `"time": "17:00"`. Assuming AoE for DAC
  would hand you about 19 hours that do not exist.

Use `"timezone": null` when a venue states only a calendar date. The page then counts
in whole days and labels the row, rather than inventing a precision the CFP never gave.

### Venues that have not announced yet

A venue whose call for papers is not out yet stays in `conferences` with two extra
fields, so it still appears in the ordering rather than being exiled to a footnote:

```json
{
  "name": "ISCA", "year": "2027",
  "estimated": true,
  "estimatedFrom": "ISCA 2026 abstract deadline, 10 Nov 2025",
  "watch": "https://iscaconf.org/isca2027/",
  "venue": "TBA",
  "conferenceDates": null,
  "callForPapers": "https://iscaconf.org/",
  "deadlines": [
    { "label": "Abstract", "date": "2026-11-10", "timezone": "AoE" }
  ]
}
```

The date is last cycle's equivalent shifted forward one year. The page labels the
counter **Estimated**, prints `not announced - based on <estimatedFrom>` beneath it,
draws the circle with a dashed border, and shows **TBA** on the right instead of a
schedule. `estimatedFrom` is required — an estimate that cannot say what it is based
on does not go on the page.

Why it is framed that way: while this repo was being built, an aggregator was
publishing a full ISCA 2027 schedule that was ISCA 2026 shifted a year, presented as
fact, including a "second submission round" that was really ISCA's Industry Track.
The arithmetic here is identical; the difference is entirely in the labelling. Never
let an estimate render as a confirmed date.

`conferenceDates` may be `null` when the conference dates are unknown. DAC is the case
where they are known well before the CFP, so it keeps them.

When the real call for papers appears, drop `estimated`, `estimatedFrom` and `watch`,
and replace the single estimated deadline with the published schedule.

### Past cycles

An edition whose deadlines have all elapsed moves into the **Past cycles** section at
the foot of the page. Nothing marks it as past — the page works it out.

**A closed cycle keeps counting if its conference has not happened yet.** Submissions
being over does not mean there is nothing left to wait for, so those editions lead the
section with a live counter to the meeting itself, showing the date range and the city
on the left. The label reads `Conference`; once the first day arrives it becomes
`Under way`; once the last day ends the counter switches off and the edition joins the
genuinely finished ones, most recently ended first. They are the only entries in the
section that are not dimmed.

This is what `conferenceDates` buys beyond display. Without it, ICCAD 2026 and MICRO
2026 both read as finished business while their conferences were still six weeks out.
An entry with `"conferenceDates": null` has no meeting to track, so it simply closes
when its last deadline passes.

No venue publishes an opening clock time, so the counter runs to the **start** of the
opening day and stops at the **end** of the last day, both in UTC. Neither boundary is
precise to the hour in any particular city, and the note under the counter says so
rather than implying otherwise. Keeping one finished cycle per venue is what makes the estimates
meaningful, and lets you eyeball how a venue's timing moves year to year.

## Local preview

`index.html` reads `data.json` over `fetch`, which browsers block for pages opened
directly from disk. To preview locally:

```
python3 -m http.server 8000
```

then open `http://localhost:8000`. The page says so itself if you forget.

## Checking the dates automatically

```
python3 tools/check_deadlines.py
```

Fetches every venue's call for papers, extracts the dates it finds, and compares them
against `data.json`. Also polls the venues that have not announced yet and reports the
moment their page stops returning 404/401. No dependencies — Python 3 standard library.

```
  [OK     ] DATE 2027     all 4 dates still present on the CFP page
  [DRIFT  ] MICRO 2026    configured date(s) no longer appear on the CFP page — Camera-ready (2026-09-11)
  [WAITING] DAC 2027      still HTTP 401 — not published yet
  [LIVE   ] ISCA 2027     page is now HTTP 200 — the call for papers may be out
```

Exit code is `0` when nothing needs attention and `1` when something does, so it works
in CI. `--json` for machine-readable output, `--quiet` to print only when action is
needed, `--verbose` for advisory findings.

**It never edits `data.json`.** That is deliberate, not laziness. Conference pages are
not machine-readable and the traps are specific and real: `iccad.com` embeds a DATE
promotional block containing a full AoE deadline table, which any proximity-based
extractor files under ICCAD. The IEEE CASS PDF for ICCAD 2026 served superseded dates
for months. DAC publishes 5 PM US Pacific while everything around it says AoE. A wrong
date carrying a live countdown is worse than a stale one, so the tool raises a hand and
a human decides.

`DRIFT` means *look*, not *it is broken*. A venue reformatting its page can trigger it.

### Resolving a change with an agent

The script detects that something moved; it cannot tell you what it moved to, because
regex cannot distinguish DATE's promotional block on `iccad.com` from ICCAD's own dates.
That part needs reading comprehension.

`.claude/commands/update-deadlines.md` is a prompt that does it. In Claude Code:

```
/update-deadlines
/update-deadlines DAC ISCA
```

It carries the verification procedure — HotCRP first, official CFP second, aggregators
never — plus every trap this project has actually hit, and it verifies its own
extraction adversarially before writing. It edits `data.json`, runs the checker, and
leaves the working tree dirty with a diff and a verbatim source quote per changed date.
**It does not commit or push.** A person reads the diff before it reaches the site.

It is a plain Markdown prompt, so it works with any agent that can browse and edit
files, not only Claude Code.

The division of labour: the script is cheap and runs weekly to notice *that* something
changed; the agent is expensive and runs on demand to determine *what it changed to*.

### Weekly, on GitHub

`.github/workflows/check-deadlines.yml` runs the check every Monday and opens an issue
if anything needs review. It also validates `data.json` on every push that touches it,
so a malformed config fails before it reaches the site. Nothing is ever auto-committed.

## Deploying

Push to `main`. GitHub Pages redeploys automatically.

## Provenance

Every date was read from the venue's own call for papers or its HotCRP instance, then
independently re-checked against the same source. Aggregator sites are deliberately not
used: at time of writing at least one was publishing ISCA 2027 dates that were simply
ISCA 2026 shifted forward a year, including a phantom "second round" that was really
the Industry Track.

## Installing it as an app

`site.webmanifest` and `icons/` give the page a name and an icon when it is installed
from the browser. Without them a shortcut inherits the browser's own icon, which is
what it looks like before the manifest exists.

The icon is `icons/icon.svg`, a countdown dial on a rule line — the page's own motif,
reduced to three shapes so it still reads at 16px. The PNGs are rendered from it:

```
inkscape icons/icon.svg -w 512 -h 512 -o icons/icon-512.png
```

`icons/icon-maskable.svg` is the same drawing pulled into the central safe zone, for
Android, which crops an app icon to a circle.

**If you installed the app before this existed,** the old icon is cached with the
installed shortcut. Remove it and install again to pick up the new one.

## License

[MIT](LICENSE) © 2026 Ahmet Efe. The code and the page are yours to reuse; the dates
themselves are facts and belong to nobody. Attribution is welcome, not required.
