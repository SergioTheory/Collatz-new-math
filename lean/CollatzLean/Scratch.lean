import Mathlib

lemma test_log (x : ℝ) (hx : 0 < x) : Real.log (1 + x) ≤ x := by
  have h1 : 0 < 1 + x := by positivity
  have h2 := Real.log_le_sub_one_of_pos h1
  linarith
