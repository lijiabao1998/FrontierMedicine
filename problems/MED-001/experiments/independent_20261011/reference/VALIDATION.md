# 醫學驗證契約

每題先凍結 intended use、target population、index time、predictors、outcome、reference standard、clinical decision point、primary metric與 harms。
- train/internal test/external validation/prospective/shadow/RCT/real-world 分層，不混成一個“驗證”。
- AUROC之外至少看calibration、decision curve/clinical utility、missingness、subgroup與workflow failures。
- site/patient/time split避免資料洩漏；prevalence shift與device/protocol shift單列。
- diagnostic/prognostic prediction不能自動升格treatment recommendation；causal treatment效應需相應設計。
- clinical AI結果只作研究，不對個人提供診療結論；任何intervention需合資格機構及倫理/監管程序。
