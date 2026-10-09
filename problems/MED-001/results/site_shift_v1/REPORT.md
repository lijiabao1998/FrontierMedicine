# MED-001: synthetic site-shift calibration baseline

## Scope and conclusion

This is a methods/pipeline replication with **COMPLETELY SYNTHETIC DATA**. It is not a validation of a medical AI, disease model, hospital, patient population or treatment. All generating parameters are invented. No patient-derived parameters or records are used. MED-001 remains **OPEN**; its clinical completion criterion was not tested.

Across the five predeclared repetitions, local logistic recalibration lowered held-out Brier score for the two invented shift scenarios, but worsened it in **all five unshifted reference repetitions**. Monotone recalibration left rankings unchanged. In the measurement-shift scenario, the observed-score AUROC remained below the full-information simulation oracle. These are finite simulation observations, not new methods or clinical results.

## Primary results

The primary estimand is the equal-seed mean of held-out Brier(recalibrated) − Brier(fixed). Negative means lower Brier. Intervals are t(4) Monte Carlo summaries from only five repetitions, not clinical uncertainty or multiplicity-adjusted inference.

| Invented scenario | Fixed Brier mean | Recalibrated Brier mean | Paired difference | Rough 95% interval |
|---|---:|---:|---:|---:|
| A: reference | 0.19201657 | 0.19343281 | +0.00141624 | [−0.00090493, +0.00373741] |
| B: outcome-intercept shift | 0.25471713 | 0.18662843 | −0.06808870 | [−0.07687344, −0.05930396] |
| C: measurement scale + MCAR missingness | 0.21551717 | 0.20266011 | −0.01285706 | [−0.01833756, −0.00737657] |

The reference's worse recalibrated Brier results are retained. No improvement threshold or inferential declaration was used for acceptance. A passing pipeline is not scientific confirmation.

## Design, estimands and separation

- Five seeds: 101, 202, 303, 404, 505. Three sites, each with 256 calibration and 512 independent evaluation rows. Total: 15 scheduled cells and 11,520 synthetic rows.
- Independent standard normal x1 and x2. Truth probability is sigmoid(site intercept + x1 − 0.5 x2). Binary labels are Bernoulli draws.
- Fixed score: −0.5 + observed_x1 − 0.5 observed_x2. No model training or tuning is performed.
- A: intercept −0.5; unaltered measurements. B: intercept +0.8; unaltered measurements. C: intercept −0.5; x1 measurement multiplied by 2; x2 independently missing 10% and zero-imputed by a fixed rule.
- Separate local recalibration fits two logistic parameters on each cell's calibration rows only. The original coefficients never change. Updated-model performance is labelled separately from fixed-model performance.
- Diagnostic calibration intercept/slope is fit on evaluation outcomes solely to describe calibration; it is never applied back to evaluation predictions. This is not the fitted local recalibrator.
- Separate seed/site/split random streams and unique row IDs prevent intended overlap. The simulation sites are artificial scenarios. They do not establish true clinical site-held-out external validity.
- Primary paired comparisons and two synthetic subgroups are predeclared in the frozen specification. The subgroup is x1<0 versus x1≥0, not a protected demographic attribute. Row-level subgroup intervals condition on the fitted calibrator; seed-level intervals approximately include its sampling variation.

## Secondary diagnostics and limitations

Fixed and recalibrated AUROCs are identical within every repetition because all fitted recalibration slopes were positive. Mean AUROC is 0.75985078 (A), 0.75522900 (B) and 0.73592985 (C). The C oracle has mean AUROC 0.74785845 and mean Brier 0.19634723. The oracle is a full-information simulation comparator, not a trainable model or a guaranteed finite-sample optimum.

The average joint calibration slope in C is 0.48100147 for the fixed score and 0.89523323 after local recalibration. Reporting these fitted evaluation-set diagnostics is not proof of calibration. Average precision is the non-interpolated, equal-score-group definition, not trapezoidal PR area. Reliability-bin counts, missingness, calibration fits, raw seed results and toy net-benefit arithmetic are in `results.json`.

At thresholds 0.2, 0.5 and 0.8 the net-benefit formula is evaluated only as a synthetic arithmetic check against select-all/select-none. There is no disease, patient preference, treatment, consequence model, intervention cost or clinically justified threshold. **No clinical utility is demonstrated.**

Five repetitions and the small calibration sample are intentionally limited. MCAR missingness is an artificial simplification. No population/device/workflow realism is asserted. AUROC/AP/calibration-coefficient intervals, large Monte Carlo coverage, true protected-group fairness, outcome misclassification, temporal shift, prospective/shadow/RCT studies, clinical utility and deployment are **NOT_RUN**.

## Source provenance and novelty

Fresh queries, timestamps, access limits and source scope are recorded in the round preflight. This is a conceptual methods replication, not a numerical reproduction of any source paper.

- [Eertink et al., 2022, original simulation study](https://pmc.ncbi.nlm.nih.gov/articles/PMC9464671/): full methods read. Informs separation of discrimination/calibration and sensitivity to validation populations. Their clinically based simulation distributions and data were not reused.
- [Guo et al., ICML 2017, primary calibration study](https://proceedings.mlr.press/v70/guo17a/guo17a.pdf): full calibration methods read, including hold-out fitting of logistic postprocessing. Neural-network benchmark findings do not establish medical cross-site validity.
- [Vickers and Elkin, 2006, primary decision-curve method](https://pmc.ncbi.nlm.nih.gov/articles/PMC2577036/): methods/formula read. Only mathematical net-benefit arithmetic is borrowed; none of the clinical data or decisions is used.
- [Li et al., Nature Medicine 2026](https://www.nature.com/articles/s41591-025-04184-7): perspective, abstract-only/paywalled. It motivates context evaluation and is not primary validation evidence.
- [TRIPOD+AI, 2024](https://www.bmj.com/content/385/bmj-2023-078378): identified through fresh search; direct HTML and PDF retrieval failed. Not counted as a fully read source.

Broad and targeted correction searches did not surface a specific retraction of the primary method sources; this bounded search does not establish absence. No full copyrighted articles were copied into the repository. The synthetic dataset is newly generated for this work; the repository has no general LICENSE, and no blanket downstream license grant is implied.

## Verification and reproducibility

Before experiments: public scope claim [issue #3](https://github.com/lijiabao1998/FrontierMedicine/issues/3), governance start/admit, frozen specification SHA256 `cb8e12aad804940aac4f4db855b1a62302f6abc372a9210f9baaf25939e5dfdd`; remote preregistration commit `fb801447522047016b9c849a254a0917019a21e5`. The author evaluator was committed locally before any synthetic experiment at `8be6971`.

Author controls passed before data generation: known Brier/AUROC/AP/net-benefit fixture, tied-score metrics, deliberately flipped-label metrics, and explicit rejection of duplicate split IDs, sealed-label modification and fixed-model modification. All 15 runs completed without numerical fit failures. Byte-identical replay of all 15 raw CSVs and results JSON passed. The replay uses the same scheduled cells, not extra scientific trials. Runtime-only environment/stdout fields are excluded from determinism comparison.

Independent coordinator verification is in `independent/`: 1,996 checks passed across all raw rows and primary/secondary metrics within a maximum numeric discrepancy of 7.771561172376096e-16. The separate least-squares score-equation solver, pairwise AUROC and grouped-threshold AP import no author code. This review was after results were visible, uses the same RNG/libraries, and does not verify subgroup/conditional intervals or clinical validity. Its own deliberate primary-mean and raw-label corruptions both failed. Author tests alone do not constitute independent confirmation. Governance checks only inspect records and paths, not scientific truth.

Raw CSV files contain both calibration and evaluation rows, their split labels, latent and observed invented covariates, labels, oracle probabilities and both prediction variants. `manifest.json` seals raw CSV/result bytes; `environment.json` identifies actual versions and source hash; `stdout.txt` retains raw execution output; `determinism.json` records exact replay checks.
