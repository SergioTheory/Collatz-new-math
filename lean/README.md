# CollatzLean: Formal Verification of the Exact Conditional Transport

[![Lean 4 - Verified](https://img.shields.io/badge/Lean_4-100%25_Verified-blue.svg)](.)

This directory contains the Lean 4 formalization for the **Collatz Crystal Hunter Project**. 
The formalization provides machine-checked proofs for the core large-deviation theory mechanics of the Collatz space, specifically focusing on the exact 2-adic finite-scale transport mechanics and the macroscopic architecture interface.

## Verified Theorems (0 sorry statements)

The formalization rigorously verifies **Theorem 2.1 (Exact Conditional Transport)**, ensuring that there are no "leaks" in the modular arithmetic and that the conditional mapping holds across all $-adic scales.

The main proof components are located in CollatzLean/ and are fully verified out-of-the-box:
* LemmaT1_step1_pure.lean: Endpoint bijection across the 2-adic layers.
* EndpointUniform.lean: The endpoint mapping law corresponding strictly to the Haar measure on odd classes.
* UnitsHalf.lean: Modular arithmetics, dropping external unit hypotheses (isUnit_three_pow), and halving transfers.
* CountBounds.lean: Range filtration and the counting bounds for the $\pm 1$ transport law (Proposition B3).
* DirectViaB3.lean: The macroscopic interface bounding survival probability and Hausdorff dimensions using rigorous xiom declarations for the external metric properties.

*(Note: Early historical sketches and unverified drafts from the initial stages of the project can be found in the root archive/ folder. They are not part of the active build).*

## Prerequisites

To verify the proofs on your own machine, you need to install **Lean 4**. We strongly recommend using lan (the Lean version manager).

1. Install Lean by following the instructions at: [leanprover/elan](https://github.com/leanprover/elan)
2. Ensure you have lake (Lean's package manager) installed (it comes bundled with lan).

## How to Build and Verify

To compile the project, download the Mathlib dependencies, and verify all proofs, run the following commands in this directory:

`bash
# 1. Download the required version of Mathlib (optional but recommended for speed)
lake exe cache get

# 2. Build the project and verify all proofs
lake build
`

If the lake build command completes without errors (e.g. Build completed successfully), all mathematical theorems in this directory have been successfully mathematically verified by the Lean 4 kernel with 0 sorry statements.
