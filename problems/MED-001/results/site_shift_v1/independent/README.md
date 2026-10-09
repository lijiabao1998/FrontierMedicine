# Independent coordinator verification

Separate coordinator session, distinct evaluator implementation, after author results were visible (not blind). It imports no author code. Python 3.12.14, NumPy 2.3.5 and SciPy 1.17.0; CPU only.

From repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python problems/MED-001/results/site_shift_v1/independent/verify_medicine.py problems/MED-001/results/site_shift_v1 > /tmp/medicine-independent-review.json
```

`review.json`: 1,996 checks passed; maximum numeric discrepancy 7.771561172376096e-16. Independently regenerates all 11,520 rows in 15 cells using the same documented NumPy RNG. Uses a separate SciPy least-squares score-equation solver instead of the author's Newton iterations; evaluates AUROC through positive/negative pair comparisons and AP through grouped thresholds. Verifies held-out predictions and primary Brier summaries/seed t intervals.

`negative_controls.json`: the coordinator deliberately changed one reported primary mean by +0.1 and flipped one raw label, separately; both modifications were rejected with exit 1. Only absolute traceback source paths were normalized to repository-relative paths for publication; the error contents were retained. `checksums.json` seals verifier source and reports.

NOT_VERIFIED: clinical validity/utility, prospective evidence, the author's corruption-control implementation, conditional row confidence intervals, subgroup summaries. Same RNG implementation and same runtime libraries are shared, so this is not an independent data source or clinical replication. This review does not approve merging/deployment.
