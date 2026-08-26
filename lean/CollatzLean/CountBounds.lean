import Mathlib
import CollatzLean.UnitsHalf
import CollatzLean.EndpointUniform

/-!
# Step 3b: The ±1 counting transport law

`endpoint_count_bounds`: over a window consisting of `b` full periods plus a
partial remainder `R < π` (`π = 2^(M-1)`), started at an offset that is itself
a multiple of `π`, every odd class modulo `2^M` receives between `b` and
`b + 1` endpoints.  Since such windows have `K = b * π + R`, i.e. `K / π = b`,
this is exactly the `count = K / π ± 1` law of Proposition B3.
-/

open Nat

/-! ### Toolbox: cardinality over a split range -/

/-- Cardinality of a filtered range splits along the cut point `K`. -/
lemma card_filter_range_add {p : ℕ → Prop} [DecidablePred p] (K R : ℕ) :
    ((Finset.range (K + R)).filter p).card
      = ((Finset.range K).filter p).card
        + ((Finset.range R).filter (fun x => p (K + x))).card := by
  induction R with
  | zero => simp
  | succ R ih =>
    have hrw : K + (R + 1) = (K + R) + 1 := by omega
    have hnm : K + R ∉ (Finset.range (K + R)).filter p := by
      simp only [Finset.mem_filter, Finset.mem_range]
      omega
    have hnm2 : R ∉ (Finset.range R).filter (fun x => p (K + x)) := by
      simp only [Finset.mem_filter, Finset.mem_range]
      omega
    rw [hrw, Finset.range_add_one, Finset.filter_insert]
    rcases Classical.em (p (K + R)) with h | h
    · rw [if_pos h, Finset.card_insert_of_notMem hnm, ih,
        Finset.range_add_one, Finset.filter_insert, if_pos h,
        Finset.card_insert_of_notMem hnm2, Nat.add_assoc]
    · rw [if_neg h, ih, Finset.range_add_one, Finset.filter_insert, if_neg h]

/-! ### Toolbox: injectivity on windows shorter than one period -/

/-- Core step: a strictly ordered pair cannot share an endpoint class. -/
lemma endpoint_window_inj_aux {d M y t₁ t₂ : ℕ} (hM : 2 ≤ M)
    (hlt : t₁ < t₂) (hlt₂ : t₂ < 2 ^ (M - 1))
    (heq : (y + 2 * 3 ^ d * t₁) % 2 ^ M = (y + 2 * 3 ^ d * t₂) % 2 ^ M) :
    False := by
  have hmL : t₁ * ((2:ℕ) * 3 ^ d) ≤ t₂ * ((2:ℕ) * 3 ^ d) := by
    rw [← Nat.mul_comm ((2:ℕ) * 3 ^ d) t₁,
        ← Nat.mul_comm ((2:ℕ) * 3 ^ d) t₂]
    exact Nat.mul_le_mul_left _ (Nat.le_of_lt hlt)
  have hmeR : ((y:ℕ) + t₁ * ((2:ℕ) * 3 ^ d))
      ≡ ((y:ℕ) + t₂ * ((2:ℕ) * 3 ^ d)) [MOD 2 ^ M] := by
    rw [← Nat.mul_comm ((2:ℕ) * 3 ^ d) t₁,
        ← Nat.mul_comm ((2:ℕ) * 3 ^ d) t₂]
    exact heq
  have hst := Nat.ModEq.add_left_cancel' y hmeR
  -- hst : 2^M ∣ t₂ * u - t₁ * u, where u = 2 * 3^d
  rw [modEq_iff_dvd' hmL] at hst
  rw [← Nat.sub_mul] at hst
  -- hst : 2^M ∣ (t₂ - t₁) * u
  rw [Nat.mul_comm (t₂ - t₁) ((2:ℕ) * 3 ^ d)] at hst
  -- hst : 2^M ∣ (2 * 3^d) * (t₂ - t₁)
  have hhalf := twoPow_dvd_mul_half (c := 3 ^ d) (by omega) hst
  -- hhalf : 2^(M-1) ∣ 3^d * (t₂ - t₁)
  have hunit : (2 ^ (M - 1)) ∣ t₂ - t₁ :=
    dvd_of_unit_mul_dvd (pos_two_pow_pred hM) (isUnit_three_pow_cast _ _) hhalf
  have hpos : 0 < t₂ - t₁ := Nat.sub_pos_of_lt hlt
  have hlt' : t₂ - t₁ < 2 ^ (M - 1) := by omega
  have hle2 : 2 ^ (M - 1) ≤ t₂ - t₁ := Nat.le_of_dvd hpos hunit
  omega

/-- Injectivity of the endpoint map on windows shorter than one period. -/
lemma endpoint_window_inj (d M y : ℕ) (hM : 2 ≤ M)
    {t₁ t₂ : ℕ} (hlt₁ : t₁ < 2 ^ (M - 1)) (hlt₂ : t₂ < 2 ^ (M - 1))
    (heq : (y + 2 * 3 ^ d * t₁) % 2 ^ M = (y + 2 * 3 ^ d * t₂) % 2 ^ M) :
    t₁ = t₂ := by
  rcases Nat.lt_trichotomy t₁ t₂ with h | h | h
  · exact absurd heq (endpoint_window_inj_aux hM h hlt₂)
  · exact h
  · exact absurd heq.symm
      (endpoint_window_inj_aux hM (by omega) hlt₁)

/-! ### Main counting theorem -/

/-- **Counting transport (±1 law).**  Over a window of `b` full periods plus a
partial remainder `R < π` (`π = 2^(M-1)`), started at an offset that is itself
a multiple of `π`, every odd class modulo `2^M` receives between `b` and
`b + 1` endpoints.  For `K = b * π + R` this is precisely `count = K / π ± 1`
(the Proposition-B3 counting law). -/
theorem endpoint_count_bounds (d M y : ℕ) (hM : 2 ≤ M) (hy : Odd y)
    : ∀ (b c R r : ℕ), R < 2 ^ (M - 1) → Odd r →
        (((Finset.range (b * 2 ^ (M - 1) + R)).filter
            fun t => (y + 2 * 3 ^ d * (c * 2 ^ (M - 1) + t)) % 2 ^ M
              = r % 2 ^ M).card
          ≤ b + 1)
        ∧ (b ≤ ((Finset.range (b * 2 ^ (M - 1) + R)).filter
            fun t => (y + 2 * 3 ^ d * (c * 2 ^ (M - 1) + t)) % 2 ^ M
              = r % 2 ^ M).card) := by
  intro b
  induction b with
  | zero =>
    intro c R r hR hrOdd
    refine ⟨?_, Nat.zero_le _⟩
    refine le_of_not_gt fun hcard => ?_
    rw [Finset.one_lt_card] at hcard
    obtain ⟨t₁, ht₁m, t₂, ht₂m, hne⟩ := hcard
    simp only [Finset.mem_filter, Finset.mem_range] at ht₁m ht₂m
    have hb1 := shift_const d M y c t₁ hM
    have hb2 := shift_const d M y c t₂ hM
    have hcol : (y + 2 * 3 ^ d * t₁) % 2 ^ M = (y + 2 * 3 ^ d * t₂) % 2 ^ M := by
      rw [← hb1, ← hb2, ht₁m.2, ht₂m.2]
    have hlt₁' : t₁ < 2 ^ (M - 1) := by omega
    have hlt₂' : t₂ < 2 ^ (M - 1) := by omega
    have hinj := endpoint_window_inj d M y hM hlt₁' hlt₂' hcol
    omega
  | succ b ih =>
    intro c R r hR hrOdd
    set π := 2 ^ (M - 1) with hπdef
    -- split the window: first period, then the rest shifted by one more period
    rw [show (b + 1) * π + R = π + (b * π + R) from by ring,
      card_filter_range_add]
    -- first period: exactly one member of every odd class
    have hfirst : ((Finset.range π).filter
        fun t => (y + 2 * 3 ^ d * t) % 2 ^ M = r % 2 ^ M).card = 1 :=
      endpoint_card_uniform d M y hM hy (isUnit_three_pow (M - 1) d) r hrOdd
    -- the shifted rest reduces to the induction hypothesis at offset (c + 1)
    have hrest : ((Finset.range (b * π + R)).filter
        fun x => (y + 2 * 3 ^ d * (π + x)) % 2 ^ M = r % 2 ^ M).card
      = ((Finset.range (b * π + R)).filter
        fun t => (y + 2 * 3 ^ d * ((c + 1) * π + t)) % 2 ^ M = r % 2 ^ M).card := by
      congr 1
      ext t
      simp only [Finset.mem_filter]
      have h1 : (y + 2 * 3 ^ d * (π + t)) % 2 ^ M
          = (y + 2 * 3 ^ d * t) % 2 ^ M := by
        have hh := shift_const d M y 1 t hM
        rwa [Nat.one_mul] at hh
      rw [h1, shift_const d M y (c + 1) t hM]
    obtain ⟨hup, hlo⟩ := ih (c + 1) R r hR hrOdd
    -- normalize the two summands back to their canonical (offset-free / IH) forms
    have heq1 : ((Finset.range π).filter
        fun t => (y + 2 * 3 ^ d * (c * π + t)) % 2 ^ M = r % 2 ^ M).card
      = ((Finset.range π).filter
        fun t => (y + 2 * 3 ^ d * t) % 2 ^ M = r % 2 ^ M).card := by
      congr 1
      ext t
      rw [Finset.mem_filter, Finset.mem_filter, shift_const d M y c t hM]
    have heq2 : ((Finset.range (b * π + R)).filter
        fun x => (y + 2 * 3 ^ d * (c * π + (π + x))) % 2 ^ M = r % 2 ^ M).card
      = ((Finset.range (b * π + R)).filter
        fun t => (y + 2 * 3 ^ d * ((c + 1) * π + t)) % 2 ^ M = r % 2 ^ M).card := by
      congr 1
      ext t
      have hid : c * π + (π + t) = (c + 1) * π + t := by
        rw [Nat.succ_mul]
        ring
      rw [Finset.mem_filter, Finset.mem_filter, hid]
    refine ⟨by linarith [hfirst, heq1, hup, heq2], ?_⟩
    linarith [heq1, hfirst, heq2, hup, hlo]
