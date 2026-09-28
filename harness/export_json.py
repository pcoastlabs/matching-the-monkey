"""Export the tournament and the frozen projections as JSON.

    python harness/export_json.py

Writes data/tournament.json (the mean table plus every
per-transition table) and data/projections.json (the frozen
2026-27 file, verbatim, as records). These are the artifacts the
pcoastlabs.com tournament page renders. The site never computes
anything; if a number is on the site, it came out of this
harness.

Requires the entrant CSVs (see make_entrants.py); without them
the export covers only the built-in rows.
"""
from __future__ import annotations

import csv
import json
from collections import defaultdict
from pathlib import Path

from run_tournament import (
    DATA, REPO, SEASONS, TRANSITIONS, _spearman, load_entrant,
    marcel, ours, ours_marcel,
)

OUT = DATA / "tournament.json"
PROJ_OUT = DATA / "projections.json"


def main() -> None:
    manifest = DATA / "entrants" / "entrants.json"
    entrants = []
    if manifest.is_file():
        spec = json.loads(manifest.read_text(encoding="utf-8-sig"))
        for e in spec.get("entrants", []):
            path = REPO / e["csv"]
            if path.is_file():
                entrants.append((e["name"], load_entrant(path),
                                 float(e.get("age_scale", 1.0))))

    pred_names = ["ours", "ours-marcel"]
    for name, _, _ in entrants:
        pred_names += [name, f"{name}-marcel"]
    judge_names = ["ours"] + [name for name, _, _ in entrants]

    season_of = {int(s[7:11]): s for s in SEASONS}
    season_of[2025] = "season_2025_26"
    acc = defaultdict(list)
    samples = []
    for n in TRANSITIONS:
        sname, sname1 = season_of[n], season_of[n + 1]
        i = SEASONS.index(sname)
        preds = {"ours": {k: v[0] for k, v in ours[sname].items()},
                 "ours-marcel": ours_marcel(i, sname)}
        judges = {"ours": {k: v[0] for k, v in ours[sname1].items()}}
        for name, series, ascale in entrants:
            preds[name] = {k: v[0] for k, v in series[n].items()}
            preds[f"{name}-marcel"] = marcel(series, n, ascale)
            judges[name] = {k: v[0] for k, v in series[n + 1].items()}
        common = None
        for d in list(preds.values()) + list(judges.values()):
            ks = set(d)
            common = ks if common is None else common & ks
        common = sorted(common)
        samples.append({"transition": f"{n}-{n + 1}",
                        "players": len(common)})
        for pn in pred_names:
            for jn in judge_names:
                acc[(pn, jn)].append(_spearman(
                    [preds[pn][k] for k in common],
                    [judges[jn][k] for k in common]))

    nt = len(TRANSITIONS)

    def table(idx):
        rows = []
        for pn in pred_names:
            cells = [round(acc[(pn, j)][idx], 3) if idx is not None
                     else round(sum(acc[(pn, j)]) / nt, 3)
                     for j in judge_names]
            rows.append({"predictor": pn, "cells": cells,
                         "row_mean": round(sum(cells) / len(cells), 3)})
        return rows

    out = {
        "judges": judge_names,
        "samples": samples,
        "mean": table(None),
        "transitions": {s["transition"]: table(i)
                        for i, s in enumerate(samples)},
    }
    OUT.write_text(json.dumps(out, indent=1), encoding="utf-8")
    print(f"wrote {OUT.relative_to(REPO)}")

    team_of = {}
    with open(DATA / "players.csv", encoding="utf-8-sig",
              newline="") as f:
        for r in csv.DictReader(f):
            team_of[r["pid"]] = r.get("team", "")
    proj = list(csv.DictReader(
        open(DATA / "projections_2026_27.csv", encoding="utf-8-sig")))
    for r in proj:
        r["team"] = team_of.get(r["pid"], "")
    PROJ_OUT.write_text(json.dumps(proj), encoding="utf-8")
    print(f"wrote {PROJ_OUT.relative_to(REPO)} ({len(proj)} skaters)")


if __name__ == "__main__":
    main()
