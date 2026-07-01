# V2-A generator pilot - development only

**Status:** development calibration artifact. Not confirmatory Tier 0 evidence.

**Development seeds:** `0..9` for width sweeps; `0..19` for latent parent.
These seeds are spent and must not be reused in the confirmatory run.

The local harness reproduced the relevant frozen V1 equations:

```text
profile = mean term counts per literature * background IDF
B = shared positive support passing max_df=0.5 and idf_min=1.0
mediated = sum(min(w_A, w_C) over B)
```

It was a historical development diagnostic, used because the workspace could not
clone the complete repository at the time. The real `LiteratureStore` + `propose_bridge`
grid has SINCE been run via `scripts/pilot_v2a_grid.py` (PR #8) and reproduced the same
rank-level outcomes — DEVELOPMENT, NOT CONFIRMATORY; rank-decision agreement is not
value fidelity and does not bless the reconstruction below.

## Development configuration

```text
n_peers = 24
endpoint documents = 20
background documents per topic = 20
background topics = 8
widths = every integer from 0 through 24
paired world and nested peer prefixes per seed
```

All rates below are development values, not frozen confirmatory values.

## Results

```text
cell                         reversals  symmetric width=0 A/C  symmetric full A/C
base M=.30, ratio=1, noise=1     0              .00/.00             .90/1.00
thin M=.15, ratio=1, noise=1     0              .10/.10            1.00/1.00
strong M=.50, ratio=1, noise=1   0              .00/.00             .90/1.00
thin M=.15, ratio=.5, noise=1    0              .00/.00             .90/.80
thin M=.15, ratio=2, noise=1     0              .00/.10            1.00/1.00
thin M=.15, ratio=1, noise=4     0              .30/.20            1.00/.90
thin M=.15, ratio=.5, noise=4    0              .00/.00             .40/.40
```

Additional boundary probes:

```text
M=.20, ratio=.5, noise=2: width=0 .00/.00; full .50/.50
M=.20, ratio=.5, noise=4: width=0 .00/.00; full .40/.40
M=.25, ratio=.5, noise=4: width=0 .00/.00; full .50/.40
M=.20, ratio=1,  noise=2: width=0 .00/.00; full 1.00/.90
```

Latent-parent development result with M absent:

```text
RISK_A = 1.00
RISK_C = 0.95
```

## Reading

1. No within-replicate monotonicity reversal occurred in any development cell.
   The paired-prefix invariant is working.
2. The base regime separates the selective and broad endpoints.
3. Thin M combined with half-sized peer corpora and medium noise does not reliably
   degrade even at full width. This is a real generator/method sensitivity boundary,
   not a value to hide by tuning.
4. The difficult `thin M x half-size peers x medium noise` interaction remains a
   **contract cell**, not a characterization-only escape hatch. V2-A currently has
   no pre-specified minimum document-count or noise exclusion, so reclassifying this
   cell after observing its 40% degradation rate would narrow the claim post hoc.
   If the frozen confirmatory criterion fails there, Tier 0 fails.

## Before freezing

- **[DONE]** rerun the pilot script against the complete repository's real V1
  implementation — done via `scripts/pilot_v2a_grid.py` on real V1 (PR #8);
  DEVELOPMENT, NOT CONFIRMATORY;
- keep the difficult interaction in the contract grid unless a new, independently
  justified scope rule is pre-registered before any confirmatory run;
- derive numeric endpoint criteria from the declared claim and pilot power;
- define untouched confirmatory seed derivation;
- never reuse the development seeds listed above.
