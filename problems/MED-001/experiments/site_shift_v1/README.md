# Reproduce the completely synthetic MED-001 baseline

No patients, disease predictions, clinical decisions or treatment recommendations.

Requirements used: Python 3.12.14, NumPy 2.3.5, SciPy 1.17.0, CPU only. No downloads or network are needed for execution once these packages are installed. No additional packages were installed for this round.

From repository root:

```sh
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python problems/MED-001/experiments/site_shift_v1/run_baseline.py --controls-only --output /tmp/med-unused
OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 python problems/MED-001/experiments/site_shift_v1/run_baseline.py --output /tmp/med-site-shift-replay
```

Use a new output directory; compare its raw files and results JSON with the committed SHA256 manifest. The source asserts the frozen specification hash. It first runs known metric fixtures and deliberate corruption controls, then completes all predeclared seeds/sites without tuning. `environment.json` runtime and `stdout.txt` timing vary; the raw CSVs/results should be byte-identical in the recorded environment. Cross-version floating-point differences are possible.

Recalibration is fitted only on calibration rows. Evaluation-set logistic calibration fits are descriptive diagnostics, never applied as predictive adjustments. AUPRC is average precision, with grouped ties. Subgroup row-level intervals condition on fitted calibration; repeated-seed intervals are rough t(4) Monte Carlo summaries. The simulation oracle is diagnostic only. Passing guards does not establish clinical validity or adversarial security.

The pinned governance checkout is external to this repository:

```sh
python /path/to/FrontierLab-Governance/tools/frontier.py validate .
python /path/to/FrontierLab-Governance/tools/frontier.py check-pins .
python /path/to/FrontierLab-Governance/tools/frontier.py check-diff . 3db7921a92f6ae95a1b7116c7b9e04d99db357ad HEAD
```

Use governance revision `9c3ae2dbaa1c814f3ef451c041dedfe3b77d926f` exactly. The problem card/evaluator/completion criterion are not altered. This branch is a draft research record, not a clinical approval or deployable model.
