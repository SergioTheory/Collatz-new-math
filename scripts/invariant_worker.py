from __future__ import annotations

import argparse
from pathlib import Path

from automaton_invariants import compute_automaton_invariants, save_invariants
from preimage_automaton import build_preimage_automaton


def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(description="Worker: build automaton invariants for one depth")
    p.add_argument("--root", required=True, help="xstar | 27 | barina | integer")
    p.add_argument("--depth", required=True, type=int)
    p.add_argument("--a-max", required=True, type=int)
    p.add_argument("--max-bits", type=int, default=None)
    p.add_argument("--output", required=True, help="target invariants json path")
    p.add_argument("--minimize", dest="minimize", action="store_true", default=True)
    p.add_argument("--no-minimize", dest="minimize", action="store_false")
    return p


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    bundle = build_preimage_automaton(
        root=args.root,
        max_depth=int(args.depth),
        max_bits=args.max_bits,
        a_max=int(args.a_max),
        minimize=bool(args.minimize),
        include_forward_summary=False,
    )
    inv = compute_automaton_invariants(bundle)
    save_invariants(inv, Path(args.output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
