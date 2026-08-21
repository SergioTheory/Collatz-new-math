import Mathlib.Data.Real.Basic
import Mathlib.MeasureTheory.Measure.Haar.Basic
import Mathlib.MeasureTheory.Measure.MeasureSpace

open MeasureTheory

local notation "ℤ_2" => ℤ_[2]

noncomputable def syr_gen (b N : ℕ) : ℕ :=
  let val := b * N + 1
  let a := padicValNat 2 val
  val / (2^a)

noncomputable def delta (b : ℕ) : ℝ :=
  Real.log 4 / Real.log b

axiom dichotomy_subcritical (b : ℕ) (hb_odd : Odd b) (hb_val : b = 3) :
  delta b > 1

axiom dichotomy_supercritical (b : ℕ) (hb_odd : Odd b) (hb_val : b ≥ 5) :
  delta b < 1
