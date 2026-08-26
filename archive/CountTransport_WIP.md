# WIP: endpoint_count_bounds (±1 counting transport law)

**Status:** proof skeleton complete; NOT yet compiled. Do not import into the
build until both "remaining fixes" below are applied and `lake build` is green.

**Target theorem.**

```lean
theorem endpoint_count_bounds (d M y : ℕ) (hM : 2 ≤ M) (hy : Odd y)
    : ∀ (b c R r : ℕ), R < 2 ^ (M - 1) →
        (((Finset.range (b * 2 ^ (M - 1) + R)).filter
            fun t => (y + 2 * 3 ^ d * (c * 2 ^ (M - 1) + t)) % 2 ^ M
              = r % 2 ^ M).card
          ≤ b + 1)
        ∧ (b ≤ ((Finset.range (b * 2 ^ (M - 1) + R)).filter
            fun t => (y + 2 * 3 ^ d * (c * 2 ^ (M - 1) + t)) % 2 ^ M
              = r % 2 ^ M).card)
```

For `K = b * π + R` this is exactly `count = K / π ± 1` (Proposition B3).

## Proof skeleton

Induction on `b`.

* **Zero case.** Window length `R < π`; any two distinct members would give two
  positions `< π` with equal endpoint class, contradicting
  `endpoint_window_inj`. Finish with `Finset.one_lt_card` contrapositive +
  `omega`.

* **Succ case.** Split
  `range ((b+1)*π + R) = range π ∪ map (+π) (range (b*π+R))`
  (`range_split_union`).
  - Disjointness: LHS ⊆ `range π`, RHS ⊆ `Ici π`
    (`Disjoint.mono` + `Finset.filter_subset`, `Finset.map_subset`-style bound;
    elements of the mapped piece are `π + j ≥ π`).
  - First period contributes exactly **1** per odd class
    (`endpoint_card_uniform`, after `shift_const d M y c`).
  - Shifted rest reduces to IH at offset `(c+1)` via
    `shift_const d M y 1`.
  - Bounds: `total = 1 + ih_card ∈ [b+1, b+2]` ⇒ `≤ b+1+... wait, target is
    `≤ (b+1)` for the upper? No: upper is `b+1` where `b` counts FULL periods
    of THIS window; careful: total = 1(first period) + ih_card, and
    ih_card ≤ b + 1 gives total ≤ b + 2 — WRONG.
    Correct accounting: window length here is `π + (b*π + R)`, i.e. this is
    the `(b+1)`-case and the bound to prove is `≤ (b+1)+1 = b+2`?? No — the
    theorem's bound is `b + 1` with `b` full periods; in the succ-case there
    are `b + 1` full periods (`π + b*π`), so the bound is `(b+1) + ...`: the
    first period contributes 1 and the shifted rest has `b` full periods,
    contributing between `b` and `b+1`. Hence total ∈ [b+1, b+2] and the
    stated bound for `b+1` periods is `(b+1) + 1 = b+2` on the upper side and
    `b+1` on the lower side — i.e. restate the theorem with the bound
    `≤ (b+1)` replaced by `≤ (b + 1)` where the `+1` accounts for the partial
    remainder only. **Fix before compiling:** carry the exact statement form
    used by `card_filter_range_add`:
    `total = first(=1) + ih_card`, `ih_card ∈ [b, b+1]` ⇒
    `total ∈ [b+1, b+2]`, matching the theorem's `≤ b + 2`?? — resolve by
    keeping the theorem statement exactly as written above (bound `b + 1`)
    and noting that the FIRST period is counted inside `ih`'s window when the
    split point is `π`: use `card_filter_range_add` with `K := π`,
    `R := b*π + R` so that the second piece is precisely the IH instance at
    offset `(c+1)`, giving
    `total = 1 + ih_card`, `ih_card ≤ b + 1` ⇒ `total ≤ b + 2`?? — see
    integration notes.

## Integration notes / remaining tactical fixes

1. `endpoint_window_inj` — orientation fix:
   `mul_le_mul_left (Nat.le_of_lt h) _` yields the RIGHT-multiplied form
   `t₁ * u ≤ t₂ * u`; rewrite `heq`'s products into that form first:
   ```lean
   have hmeRaw : (y + t₁ * ((2:ℕ) * 3 ^ d)) ≡ (y + t₂ * ((2:ℕ) * 3 ^ d))
       [MOD 2 ^ M] := by
     rw [Nat.mul_comm (2 * 3 ^ d) t₁, Nat.mul_comm (2 * 3 ^ d) t₂]
     exact heq
   ```
   then `Nat.ModEq.add_left_cancel' y hmeRaw`, `modEq_iff_dvd' hmR`
   (with `hmR : t₁ * u ≤ t₂ * u`), `← Nat.sub_mul`,
   `twoPow_dvd_mul_half (c := 2 * 3 ^ d)`?? — use instead the pair
   `sPi_dvd` directly on the LEFT-multiplied dvd:
   obtain the dvd from `modEq_iff_dvd' hmL` where
   `hmL : y + s*t₁ ≤ y + s*t₂` via `Nat.add_le_add (le_refl y) hmR`;
   numerator `(y + s*t₂) - (y + s*t₁)`: cancel `y` with
   `Nat.add_sub_add_left`-style rewriting or state a one-off helper
   ```lean
   lemma dvd_of_add_mod_eq {y s t₁ t₂ N : ℕ} (h : (y + s*t₁) % N = (y + s*t₂) % N)
       (hle : s*t₁ ≤ s*t₂) : N ∣ s*t₂ - s*t₁ := by
     rw [Nat.sub_mul]?? -- use Nat.ModEq.add_left_cancel' + modEq_iff_dvd' hle
   ```
2. Succ-case peel order (verified pattern):
   ```lean
   rw [hrw, Finset.range_add_one, Finset.filter_insert]
   rcases Classical.em (p (K + R)) with h | h
   · rw [if_pos h, Finset.card_insert_of_notMem hnm, ih, …]
   · rw [if_neg h, ih, …, Nat.add_zero]
   ```
   — `if_pos/if_neg` BEFORE `card_insert_of_notMem`; the neg branch needs no
   `card_insert` at all (else-branch drops the insert) and closes with
   `Nat.add_zero` + `simp`.
3. Statement bookkeeping: keep the theorem quantified over `b c R r` as in
   `CountTransport_WIP` history; the bound is `≤ b + 1` for the window
   `b*π + R` **including** the partial remainder, and the induction step adds
   one period at the FRONT (`π + (b*π + R)`), consuming `card_filter_range_add`
   with `K := π`, `R := b*π + R`; then `first = 1` and `rest = ih(c+1)`
   give exactly `≤ 1 + (b + 1)`?? — final check against the statement:
   the correct bound after substitution is `≤ (b+1) + 1`?? Resolve during
   compilation by comparing with the zero-case value (`b = 0` ⇒ bounds
   `0 ≤ card ≤ 1`) and adjusting once.
