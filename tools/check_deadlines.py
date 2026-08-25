#!/usr/bin/env python3
"""
Deadline monitor for data.json.

WHAT THIS DOES
    Fetches each venue's call for papers, extracts every date it can find, and
    compares that against what data.json claims. Reports anything that looks
    like drift. Also polls the venues that have not announced yet and tells you
    the moment their page stops returning 404/401.

WHAT THIS DELIBERATELY DOES NOT DO
    It never edits data.json. Conference pages are not machine-readable and the
    failure modes are nasty: iccad.com embeds a DATE promotional block whose
    text contains a full AoE deadline table, and any extractor that trusts
    proximity will file those under ICCAD. The IEEE CASS PDF for ICCAD 2026
    carried superseded dates for months. DAC publishes 5 PM US Pacific while
    everything around it uses AoE.

    A wrong date with a countdown attached is worse than a stale one, so this
    tool raises a hand and a human decides. That is the whole design.

USAGE
    python3 tools/check_deadlines.py                 # human-readable report
    python3 tools/check_deadlines.py --json          # machine-readable
    python3 tools/check_deadlines.py --quiet         # only print if action needed

EXIT CODES
    0  nothing needs attention
    1  something needs a human: possible drift, a CFP appeared, a page broke
    2  the tool itself failed (bad config, no network)
"""

import argparse
import datetime as dt
import json
import os
import re
import ssl
import sys
import urllib.error
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CONFIG = os.path.join(ROOT, "data.json")
UA = "conference-deadlines-monitor/1.0 (+https://github.com/ahmetefe3423/conference-deadlines)"
TIMEOUT = 30

MONTHS = {m.lower(): i for i, m in enumerate(
    ["January", "February", "March", "April", "May", "June", "July",
     "August", "September", "October", "November", "December"], 1)}
MONTHS.update({m.lower()[:3]: i for m, i in list(MONTHS.items())})

# "September 4, 2026" / "Sep 4 2026" / "4 September 2026" / "2026-09-04"
PATTERNS = [
    re.compile(r"\b([A-Z][a-z]{2,8})\.?\s+(\d{1,2})(?:st|nd|rd|th)?,?\s+(\d{4})\b"),
    re.compile(r"\b(\d{1,2})(?:st|nd|rd|th)?\s+([A-Z][a-z]{2,8})\.?,?\s+(\d{4})\b"),
    re.compile(r"\b(\d{4})-(\d{2})-(\d{2})\b"),
]

TZ_HINTS = re.compile(
    r"\b(AoE|Anywhere on Earth|UTC[+-]?\d*|GMT[+-]?\d*|PST|PDT|EST|EDT|CET|CEST|JST|"
    r"US Pacific(?: Time)?|Pacific Time|\d{1,2}:\d{2}\s*(?:am|pm)?|\d{1,2}\s*(?:AM|PM))\b",
    re.I)

TAG = re.compile(r"<(script|style)[^>]*>.*?</\1>|<[^>]+>", re.S | re.I)

DASH = r"\s*[-\u2010\u2011\u2012\u2013\u2014]\s*"
MON = r"[A-Z][a-z]{2,8}"

def expand_ranges(text):
    """Rewrite date ranges into two complete dates.

    Venues write rebuttal windows as ranges, and in every common form only the
    LAST date carries a year:

        MICRO   "Rebuttal/Revision: June 3-17, 2026"
        ASPLOS  "Author response - December 1 - December 4, 2026"

    Parsing those naively finds only the closing date, and the opening date then
    looks like it vanished from the page. That produced a false drift alert for
    every rebuttal window on the first run of this tool.
    """
    # "December 1 - December 4, 2026"  ->  "December 1, 2026  December 4, 2026"
    text = re.sub(rf"\b({MON})\.?\s+(\d{{1,2}}){DASH}({MON})\.?\s+(\d{{1,2}})"
                  rf"(?:st|nd|rd|th)?,?\s+(\d{{4}})\b",
                  r"\1 \2, \5 \3 \4, \5", text)
    # "June 3-17, 2026"               ->  "June 3, 2026  June 17, 2026"
    text = re.sub(rf"\b({MON})\.?\s+(\d{{1,2}}){DASH}(\d{{1,2}})"
                  rf"(?:st|nd|rd|th)?,?\s+(\d{{4}})\b",
                  r"\1 \2, \4 \1 \3, \4", text)
    # "3-17 June 2026"                ->  "3 June 2026  17 June 2026"
    text = re.sub(rf"\b(\d{{1,2}}){DASH}(\d{{1,2}})\s+({MON})\.?,?\s+(\d{{4}})\b",
                  r"\1 \3 \4 \2 \3 \4", text)
    return text


def fetch(url):
    """Return (status, text, error). Never raises."""
    ctx = ssl.create_default_context()
    req = urllib.request.Request(url, headers={"User-Agent": UA,
                                               "Accept": "text/html,application/json,*/*"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT, context=ctx) as r:
            raw = r.read(3_000_000)
            enc = r.headers.get_content_charset() or "utf-8"
            return r.status, raw.decode(enc, "replace"), None
    except urllib.error.HTTPError as e:
        return e.code, "", None
    except Exception as e:                                  # DNS, TLS, timeout
        return None, "", f"{type(e).__name__}: {e}"


def text_of(html):
    return expand_ranges(re.sub(r"\s+", " ", TAG.sub(" ", html)))


def dates_in(text):
    """Every parseable date in the page, as a set of YYYY-MM-DD."""
    out = set()
    for pat in PATTERNS:
        for m in pat.finditer(text):
            a, b, c = m.groups()
            try:
                if pat is PATTERNS[0]:
                    mo, d, y = MONTHS.get(a.lower()), int(b), int(c)
                elif pat is PATTERNS[1]:
                    d, mo, y = int(a), MONTHS.get(b.lower()), int(c)
                else:
                    y, mo, d = int(a), int(b), int(c)
                if not mo or not (2020 <= y <= 2035):
                    continue
                out.add(dt.date(y, mo, d).isoformat())
            except (ValueError, TypeError):
                continue
    return out


def check_conference(conf, verbose):
    """Compare configured dates against what the CFP page actually shows."""
    name = f"{conf['name']} {conf['year']}" + (f" {conf['cycle']}" if conf.get("cycle") else "")
    url = conf["callForPapers"]
    findings = []

    status, html, err = fetch(url)
    if err:
        return [("ERROR", name, f"could not reach {url} — {err}")]
    if status != 200:
        return [("ERROR", name, f"call for papers returned HTTP {status}: {url}")]

    text = text_of(html)
    found = dates_in(text)
    configured = {d["date"]: d["label"] for d in conf["deadlines"]}

    missing = [f"{lbl} ({d})" for d, lbl in sorted(configured.items()) if d not in found]
    if missing:
        findings.append(("DRIFT", name,
                         "configured date(s) no longer appear on the CFP page — "
                         + ", ".join(missing)
                         + f"  [{url}]"))

    # Dates on the page, in the future, that we do not track. Often a new
    # deadline; often also an unrelated date in site chrome. Advisory only.
    today = dt.date.today().isoformat()
    untracked = sorted(d for d in found if d > today and d not in configured)
    if untracked and verbose:
        findings.append(("INFO", name,
                         f"{len(untracked)} future date(s) on the page not in data.json: "
                         + ", ".join(untracked[:8])
                         + (" …" if len(untracked) > 8 else "")))

    # Timezone sanity: if we recorded null but the page does state a time.
    has_tz = bool(TZ_HINTS.search(text))
    null_tz = [d["label"] for d in conf["deadlines"] if d["timezone"] is None]
    if null_tz and has_tz:
        findings.append(("INFO", name,
                         "page mentions a clock time or timezone, but these are recorded as "
                         '"timezone": null — worth a look: ' + ", ".join(null_tz)))

    # A venue whose only findings are advisory must still report a status line,
    # or filtering INFO makes it disappear from the report entirely.
    if not any(f[0] in ("DRIFT", "ERROR") for f in findings):
        findings.insert(0, ("OK", name,
                            f"all {len(configured)} dates still present on the CFP page"))
    return findings


def check_unannounced(entry):
    """Poll a venue that has not published dates. The win is catching go-live."""
    name = entry["name"]
    url = entry.get("watch")
    if not url:
        return [("SKIP", name, 'no "watch" URL in data.json — nothing to poll')]

    status, html, err = fetch(url)
    if err:
        return [("INFO", name, f"{url} unreachable — {err}")]
    if status in (404, 401, 403):
        return [("WAITING", name, f"still HTTP {status} — not published yet ({url})")]
    if status == 200:
        found = sorted(d for d in dates_in(text_of(html)) if d >= dt.date.today().isoformat())
        detail = ("dates visible: " + ", ".join(found[:10])) if found else "no dates parsed yet"
        return [("LIVE", name,
                 f"page is now HTTP 200 — the call for papers may be out. {detail}  [{url}]")]
    return [("INFO", name, f"unexpected HTTP {status} — {url}")]


def main():
    ap = argparse.ArgumentParser(description="Check data.json against live conference pages.")
    ap.add_argument("--json", action="store_true", help="machine-readable output")
    ap.add_argument("--quiet", action="store_true", help="print only if action is needed")
    ap.add_argument("--verbose", action="store_true", help="include advisory INFO findings")
    args = ap.parse_args()

    try:
        with open(CONFIG, encoding="utf-8") as f:
            cfg = json.load(f)
    except Exception as e:
        print(f"could not read {CONFIG}: {e}", file=sys.stderr)
        return 2

    results = []
    for conf in cfg.get("conferences", []):
        results += check_conference(conf, args.verbose)
    for entry in cfg.get("notAnnounced", []):
        results += check_unannounced(entry)

    needs_attention = [r for r in results if r[0] in ("DRIFT", "ERROR", "LIVE")]

    if args.json:
        print(json.dumps({
            "checkedAt": dt.datetime.now(dt.timezone.utc).isoformat(),
            "needsAttention": len(needs_attention),
            "findings": [{"level": a, "venue": b, "detail": c} for a, b, c in results],
        }, indent=2))
        return 1 if needs_attention else 0

    if args.quiet and not needs_attention:
        return 0

    width = max((len(r[1]) for r in results), default=10)
    print(f"Deadline check — {dt.datetime.now(dt.timezone.utc):%Y-%m-%d %H:%M} UTC\n")
    for level, venue, detail in results:
        if level == "INFO" and not args.verbose:
            continue
        print(f"  [{level:<7}] {venue:<{width}}  {detail}")

    print()
    if needs_attention:
        print(f"{len(needs_attention)} item(s) need a human. "
              "Nothing was changed — verify against the official page, then edit data.json by hand.")
        return 1
    print("Nothing needs attention.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
