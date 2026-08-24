# Lemma Ledger

| Date | Script Name | Status | Key Number | Interpretation |
|---|---|---|---|---|
| 2026-08-24 | 1.1 cycle_fixedpoint_census.py | численно | 0 | 0 нетривиальных решений на всех достижимых d; эвристический ряд < 1; скелет теоремы подтверждён. |
| 2026-08-24 | 1.2 cycle_highmean_admissibility.py | численно | D1 < 1 | Коллапс размерности (D1 ~ 0.76 при n=8); цикловые слова имеют меру нуль по 3-адической голове; второй запрет. |
| 2026-08-24 | 2.1 restart_discrepancy_decay.py | численно | p < 0 | [GATE-2] TV-Fourier restart -> FALSIFIED (signed/abs ~ 0.5-0.9, no decay). |
| 2026-08-24 | 2.2 timeout_renewal_closure.py | численно | c_* нестабилен | [GATE-2] Renewal closure -> FALSIFIED (c*(B): 0.90->0.13 @ a=1.05; gamma<0). |
| 2026-08-24 | 2.3 wasserstein_multiblock.py | численно | rho > 1 | [GATE-2] W1 multiblock contract. -> FALSIFIED (rho>1, memory in low 2-adic bits persists). |
| 2026-08-24 | VERDICT | итог | - | [GATE-2] VERDICT: pointwise martingale/transport route CLOSED. Archimedean-2adic wall stands. |
| 2026-08-24 | 3.1 cycle_baker_exclude.py | аналитически | > 10^6 | Все циклы длины d <= 1,000,000 исключены благодаря фронту Барины 2^68 (так как N_ub ~ d / ln 2 << 2^68). |
