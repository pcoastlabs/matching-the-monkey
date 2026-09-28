"""Generate the frozen 2026-27 projections.

    python harness/freeze_2026_27.py

Writes data/projections_2026_27.csv: our projected 2026-27 value
(WAR-style, per-82) for every skater with 30+ GP in 2025-26.

The recipe is the tournament's own Marcel, the same one every
entrant faces, launched from the final shipped season:

    5/4/3 GP-weighted average over 2025-26 / 2024-25 / 2023-24,
    K=40 ballast toward the 2025-26 positional mean,
    plus the smoothed positional age delta at Oct 1, 2026.

REVISED Sept 28, 2026, before opening night: the age deltas are
fit on the full published history (every consecutive-season pair
in data/ours_values.csv, 2010-11 on) instead of the original five
seasons. Our own post-publication review found thin-cell artifacts
in the short curve — (D,19) was empty, so teenage defensemen
received no age term, and (F,21) was overstated by small-sample
noise. The original freeze remains in git history under the
freeze-2026-27 tag; this file, tagged freeze-2026-27r2, is the
projection the scoring grades. The tournament tables in the
article are untouched — their recipe still uses the five-season
curve they were computed and published with.

Every input ships in this repo. The script is deterministic:
rerun it and diff against the committed file to verify the freeze
was produced by the stated recipe and nothing else.
"""
from __future__ import annotations

import csv
from collections import defaultdict
from pathlib import Path

import csv as _csv
from collections import defaultdict as _dd

from run_tournament import (DATA, K, MIN_GP, _norm_name, age_at, ch,
                            ours)


def _full_history_age_deltas():
    """Positional age deltas from EVERY consecutive-season pair in
    the published values file (2010-11 on), same construction the
    tournament uses on its five seasons: gp-weighted mean delta per
    (group, age-at-next-season), smoothed +-1 year, 30-GP floor."""
    rates = _dd(dict)
    with open(DATA / "ours_values.csv", encoding="utf-8-sig",
              newline="") as f:
        for r in _csv.DictReader(f):
            if r["position"] == "G" or int(r["gp"]) < MIN_GP:
                continue
            pid = int(r["pid"])
            h = ch.get(pid) or {}
            full = f"{h.get('first_name', '')} {h.get('last_name', '')}"
            key = (_norm_name(full),
                   "D" if r["position"] == "D" else "F")
            if not key[0]:
                continue
            gp = int(r["gp"])
            rates[int(r["season"])][key] = (
                float(r["war_indiv"]) / gp * 82, gp, key[1], pid)
    deltas = _dd(list)
    for y in sorted(rates):
        if y + 1 not in rates:
            continue
        for k, (v1, g1, grp, pid) in rates[y].items():
            nxt = rates[y + 1].get(k)
            if not nxt:
                continue
            a = age_at(pid, y + 1)
            if a is None:
                continue
            deltas[(grp, round(a))].append((nxt[0] - v1,
                                            min(g1, nxt[1])))
    ad = {kk: sum(d * g for d, g in v) / sum(g for _, g in v)
          for kk, v in deltas.items()}
    out = {}
    for grp in ("F", "D"):
        for a in range(18, 46):
            vals = [ad[(grp, b)] for b in (a - 1, a, a + 1)
                    if (grp, b) in ad]
            out[(grp, a)] = sum(vals) / len(vals) if vals else 0.0
    return out


sm = _full_history_age_deltas()

LAUNCH = "season_2025_26"                  # history anchor
HISTORY = [(5, "season_2025_26"), (4, "season_2024_25"),
           (3, "season_2023_24")]
PROJECT_YEAR = 2026                        # the 2026-27 season
OUT = DATA / "projections_2026_27.csv"


def main() -> None:
    cur = ours[LAUNCH]
    pm = defaultdict(list)
    for _k, (rate, _gp, grp, _pid) in cur.items():
        pm[grp].append(rate)
    pm = {g: sum(v) / len(v) for g, v in pm.items()}

    rows = []
    for k, (rate25, gp25, grp, pid) in cur.items():
        num = den = 0.0
        for w, sname in HISTORY:
            prev = ours[sname].get(k)
            if prev:
                num += w * prev[1] * prev[0]
                den += w * prev[1]
        shrunk = (num + K * pm[grp]) / (den + K)
        a = age_at(pid, PROJECT_YEAR)
        proj = shrunk + (sm.get((grp, round(a)), 0.0) if a else 0.0)
        h = ch.get(pid) or {}
        name = f"{h.get('first_name', '')} {h.get('last_name', '')}".strip()
        rows.append([pid, name, grp, gp25, round(rate25, 3),
                     round(proj, 3)])

    rows.sort(key=lambda r: (-r[5], r[0]))
    with open(OUT, "w", encoding="utf-8", newline="") as f:
        w = csv.writer(f)
        w.writerow(["pid", "player", "position_group", "gp_2025_26",
                    "war82_2025_26", "projected_war82_2026_27"])
        w.writerows(rows)
    print(f"wrote {OUT.relative_to(Path(__file__).resolve().parent.parent)}"
          f" ({len(rows)} skaters)")
    print("top of the projection:")
    for r in rows[:8]:
        print(f"  {r[1]:24s} {r[2]}  {r[5]:+.3f}")


if __name__ == "__main__":
    main()
