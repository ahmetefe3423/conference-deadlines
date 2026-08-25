# Conference Deadlines

Countdowns to research-track paper deadlines across computer architecture and
EDA conferences: ICCAD, ASPLOS, MICRO, DATE, HPCA — plus DAC, ISCA and the 2027
cycles that have not published dates yet.

Live at: https://USERNAME.github.io/conference-deadlines

## Editing

Everything lives in `index.html` — it is a single self-contained page with no
build step and no dependencies. Deadlines are the `ENTRIES` array near the top
of the `<script>` block:

```js
{ nm:"DATE", yr:"2027", cy:"", venue:"Dresden", conf:["2027-03-22","2027-03-24"],
  src:"https://www.date-conference.com/call-for-papers", ev:[
  {k:"Abstract",   d:"2026-09-13", tz:"AoE"},
  {k:"Full paper", d:"2026-09-20", tz:"AoE"}]}
```

- `d`  — the calendar date **exactly as the venue publishes it**, `YYYY-MM-DD`.
- `tz` — `"AoE"`, `"EDT"`, or `null` when the venue publishes no clock time.
  `null` makes the page count to end of day and label the row accordingly,
  rather than inventing a precision the CFP never stated.
- `cy` — cycle label, for venues running more than one round into the same
  conference (ASPLOS Spring / Fall).

Bands sort themselves by nearest deadline; closed cycles fall to the bottom.
Nothing else needs touching.

## Adding a timezone

`OFF` at the top of the script maps a label to a UTC offset. DAC publishes
5 PM US Pacific rather than AoE, so it will need an entry when its CFP appears.

## Deploying

Push to `main`. GitHub Pages redeploys automatically.

## Provenance

Every date was read from the venue's own call for papers or its HotCRP instance,
then independently re-checked against the same source. Aggregator sites are not
used: at time of writing at least one was publishing ISCA 2027 dates that were
simply ISCA 2026 shifted forward a year.
