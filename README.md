# Conference Deadlines

Countdowns to research-track paper deadlines across computer architecture and EDA
conferences: ICCAD, ASPLOS, MICRO, DATE, HPCA — plus DAC, ISCA and the 2027 cycles
that have not published dates yet.

**Live:** https://ahmetefe3423.github.io/conference-deadlines/

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
| `conferenceDates` | `["YYYY-MM-DD", "YYYY-MM-DD"]` — start and end |
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

### Not-yet-announced venues

`notAnnounced` lists venues with no published dates. They appear at the bottom with no
countdown. Move one up into `conferences` once its CFP appears.

Each may carry an optional `lastCycle` block — the previous cycle's **actual** dates,
shown as reference:

```json
{
  "name": "ISCA 2027",
  "note": "No official site; every 2027 URL 404s.",
  "watch": "https://iscaconf.org/isca2027/",
  "lastCycle": {
    "edition": "ISCA 2026 (53rd)",
    "dates": [
      { "label": "Full paper", "date": "2025-11-17", "note": "11:59 PM AoE" }
    ]
  }
}
```

These render as plain text with **no countdown attached**, and are labelled as what
last cycle *actually ran* — never as a prediction for this one.

That distinction is the entire point. While this repo was being built, an aggregator
was publishing a full ISCA 2027 schedule — abstract 10 Nov, paper 17 Nov, notification
27 Mar, plus a "second submission round" on 5 and 12 Dec. Every one of those is an
ISCA 2026 date shifted forward exactly one year, and the "second round" is really
ISCA's separate Industry Track. It looked authoritative and was entirely invented.
Last year's date is useful; last year's date wearing this year's label is not.

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
