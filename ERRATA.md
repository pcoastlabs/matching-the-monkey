# Errata

Issues found in the shipped data after the freeze. The frozen
files do not change; the point of a freeze is that it stays
frozen. Anything that affects the April grading is recorded
here before the season starts.

## Three corrupted games-played fields (found 2026-09-27)

Auditing `data/ours_values.csv` against the NHL's public
season summaries turned up three skater-season rows whose `gp`
field reads 1 while the value column carries a normal
full-season number:

| player | season | our gp | actual reg-season gp |
| --- | --- | --- | --- |
| Karson Kuhlman | 2022-23 | 1 | 47 |
| Colin Miller | 2023-24 | 1 | 46 |
| Michael Bunting | 2025-26 | 1 | 74 |

Every other skater-season row in the file (about 4,700) checks
out against the league counts, in both directions.

Consequences:

- The harness drops rows under 30 games played, so these three
  player-seasons were excluded from their seasons. For Kuhlman
  and Miller that trims the affected common samples by at most
  one skater and nothing else.
- Bunting played 74 games in 2025-26 and should be in the
  frozen 2026-27 projections. He is not, because the corrupted
  row fell under the games-played floor. The freeze predates
  the discovery and stays as committed, so the projection
  covers 661 of the 662 skaters the stated rule should cover.
  Scoring intersects each entrant's own list, so his absence
  costs us one player of sample in April and affects no other
  entrant.

The population rule itself verified cleanly: taking playoff
games into account, our 661 skaters match the league's 30-plus
games list one for one apart from Bunting.

## Pre-season freeze revision (Sept 28, 2026)

Reviewing the projections against the newly published full history
exposed two small-sample artifacts in the age curve used by the
original freeze: the (D,19) cell was empty — teenage defensemen
received no age adjustment at all — and (F,21) was overstated
(+0.55 on three transitions vs +0.32 on fifteen). The freeze was
regenerated with age deltas fit on the full published history,
before opening night; 655 of 661 projections moved, most by under
0.1 wins. The original stays in git history (tag freeze-2026-27);
the graded file is freeze-2026-27r2. The same refit curve became the tournament
recipe as well: 18 of the 50 mean-table cells move, by at most
0.005, with three row means shifting 0.001-0.002 — all inside the
table's bootstrap-measured resolution (95% band ±0.012 on row-mean
differences). The article's table was updated to match; the code
reproduces it. This is the last change: after opening night the
frozen file is immutable, whatever we find.
