import Mathlib

lemma count_le_step (X r n : ℕ) (hn : 0 < n) (hr : r < n) :
    (X + 1 + n - r) / n = (X + n - r) / n + if (X + 1) % n = r then 1 else 0 := by
  split_ifs with h
  · omega
  · omega
