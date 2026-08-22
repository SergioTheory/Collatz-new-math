# CollatzLean: Formal Verification of the Exact Conditional Transport

This directory contains the Lean 4 formalization for the **Collatz Crystal Hunter Project**. 
The formalization provides machine-checked proofs for the core large-deviation theory mechanics of the Collatz space, specifically focusing on the 2-adic transport and the CRT dimensionality obstruction.

## Verified Theorems

The formalization rigorously verifies **Theorem 2.1 (Exact Conditional Transport)**, ensuring that there are no "leaks" in the modular arithmetic and that the conditional mapping holds across all $2$-adic scales.

The main proof components are located in `CollatzLean/`:
* `Basic.lean`: Core definitions for Collatz maps, $p$-adic valuations, and modular conditions.
* `LemmaT1_step1_pure.lean` & `LemmaT1_step2.lean`: The rigorous derivation of the survival conditions and exact within-word transport.
* `DirectViaB3.lean`: The bridging proofs connecting the finite-scale dynamics to the macroscopic architecture.

*(Note: Early historical sketches and unverified drafts from the initial stages of the project can be found in the root `archive/` folder).*

## Prerequisites

To verify the proofs on your own machine, you need to install **Lean 4**. We strongly recommend using `elan` (the Lean version manager).

1. Install `elan` by following the instructions at: [leanprover/elan](https://github.com/leanprover/elan)
2. Ensure you have `lake` (Lean's package manager) installed (it comes bundled with `elan`).

## How to Build and Verify

To compile the project, download the Mathlib dependencies, and verify all proofs, run the following commands in this directory:

```bash
# 1. Download the required version of Mathlib
lake exe cache get

# 2. Build the project and verify all proofs
lake build
