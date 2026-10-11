# MED-001: bounded independent verification

Plan and baseline: see frozen PROTOCOL.json and byte-pinned SOURCE_MANIFEST.json in experiments/independent_20261011. Historical outputs and prior independent findings are inherited, not new numerical results.

Actual launch: 2026-10-11T19:47:53.047469+00:00; finished: 2026-10-11T19:47:53.439005+00:00; wall seconds 0.2341776999819558; child exit 0; verdict INDEPENDENT_SYNTHETIC_SUBGROUP_ARITHMETIC_PASS; all criteria True. Exactly one admitted execution, OS CPU affinity1, $0. See attempt-1/launch.json for exact start/command/cwd/environment and execution.json for exit/timeout. Raw stdout and stderr retained, including the Python runtime-location warning.

Pure synthetic arithmetic only. Conditional row intervals ignore calibration-set variability; five-seed t4 intervals are rough Monte Carlo summaries. No model/DGP regeneration, calibration refit, clinical or real-population fairness evidence; no causal inference or new medical discovery. Nature primary direct open returned Internal Error and PubMed direct open one-line unavailable content; author-hosted abstract and primary scoping-review abstract were read instead. No full-proof/clinical guideline adjudication; noisy searches cannot establish absence of retraction.

Independent implementation calculates the requested previously unverified report fields from archived raw data. Final independent review inspects code/artifacts and raw logs; it is not a second numerical replay or external peer review. New evidence is bounded report-field verification and semantic negative-control rejection only.

Original command (now FINISHED and one-attempt guard deliberately refuses replay):

```powershell
python -X utf8 problems/MED-001/experiments/independent_20261011/run_bounded.py --repo . --round 20261011T192958557438Z-gpt-MED-001
```

To reproduce, create a fresh isolated branch/round from the same pinned source, perform fresh preflight and public scope/budget registration, freeze the same source hashes, definitions and control list, obtain independent static review and official admission, then invoke the same runner with the NEW round id. Never delete attempt-1 or reset this finished round. No third-party libraries, samples or fitting are needed.
