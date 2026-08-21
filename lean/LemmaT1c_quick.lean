import Mathlib

lemma count_le_step (X r n : ℕ) (hn : 0 < n) (hr : r < n) :
    (X + 1 + n - r) / n = (X + n - r) / n + if (X + 1) % n = r then 1 else 0 := by
  set A := X + n - r
  have hA : X + 1 + n - r = A + 1 := by omega
  rw [hA, Nat.succ_div]
  have hmod : n ∣ A + 1 ↔ (X + 1) % n = r := by
    constructor
    · rintro ⟨k, hk⟩
      have hk1 : 1 ≤ k := by omega
      have hY : X + 1 = (k - 1) * n + r := by omega
      rw [hY, add_comm, Nat.add_mul_mod_self_left, Nat.mod_eq_of_lt hr]
    · intro h
      refine ⟨(X + 1) / n + 1, ?_⟩
      have hY : X + 1 = ((X + 1) / n) * n + r := by omega
      omega
  by_cases h_dvd : n ∣ A + 1
  · rw [if_pos h_dvd, if_pos (hmod.mp h_dvd)]
  · rw [if_neg h_dvd, if_neg (mt hmod.mpr h_dvd)]
