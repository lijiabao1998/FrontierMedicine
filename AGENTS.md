# FrontierMedicine agent 入口

先讀 README、STATUS、VALIDATION 與治理 9c3ae2dbaa1c814f3ef451c041dedfe3b77d926f。agent 用 <agent>/MED-xxx-<topic> 分支，不直接main、不自合。

每輪先重新查external validation/clinical trial/guideline版本，再凍結intended use、population、endpoint、data split、primary metric與decision context。只用公開或合規去識別資料；不能輸出個人診斷、用藥或治療方案，不能自行開prospective clinical study。
