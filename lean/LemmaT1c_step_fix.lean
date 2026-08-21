import Mathlib

lemma count_le_step (X r n : ℕ) (hn : 0 < n) (hr : r < n) :
    (X + 1 + n - r) / n = (X + n - r) / n + if (X + 1) % n = r then 1 else 0 := by
  have h_div := Nat.div_add_mod (X + 1) n
  set q := (X + 1) / n
  set m := (X + 1) % n
  split_ifs with h
  · have hX : X + 1 = n * q + r := by omega
    omega
  · have hX : X + 1 = n * q + m := by omega
    have hm : m < n := Nat.mod_lt (X + 1) hn
    omega
