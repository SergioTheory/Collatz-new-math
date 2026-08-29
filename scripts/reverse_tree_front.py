"""
reverse_tree_front.py — Route 4: reverse-tree front coverage certificate (k=16).

Reverse Collatz tree from 1, exact big-integer arithmetic:
    x --(accelerated reverse)--> (2^s·x − 1)/3   for s with 2^s·x ≡ 1 (mod 3)

Every node is an odd integer whose orbit reaches 1.  "No holes" at finite
scale = every odd residue class mod 2^k contains a tree node.  We compute,
deterministically (no randomness), the depth at which the tree covers 100% of
the odd classes mod 2^16.

Nodes are deduplicated by (y mod 2^16, y mod 3^8) which is exact for the
depth reached here.
Certificate -> data/route4_front_certificate.json
"""
import json, os, time

K = 16
SMAX = K
D_3 = 8
P3 = 3 ** D_3
MOD2 = 1 << K


def get_children(y):
    ym3 = y % 3
    if ym3 == 0:
        return []
    start_s = 2 if ym3 == 1 else 1
    out = []
    for s in range(start_s, SMAX + 1, 2):
        x = ((y << s) - 1) // 3
        out.append(x)
    return out


def main():
    t0 = time.time()
    frontier = [1]
    seen_keys = {(1 % MOD2, 1 % P3)}
    cov = set()
    target = 1 << (K - 1)          # number of odd classes mod 2^16
    depth = 0

    print(f"Target odd classes mod 2^{K}: {target}")

    while len(cov) < target and depth < 50:
        for y in frontier:
            cov.add(y % MOD2)

        print(f"Depth {depth:>2}: frontier {len(frontier):>7} | "
              f"covered mod 2^{K}: {len(cov)}/{target}")

        if len(cov) == target:
            break

        next_frontier = []
        for y in frontier:
            for child in get_children(y):
                key = (child % MOD2, child % P3)
                if key not in seen_keys:
                    seen_keys.add(key)
                    next_frontier.append(child)

        frontier = next_frontier
        depth += 1

    out = {
        "K": K,
        "front_depth": depth,
        "covered_classes": len(cov),
        "target_classes": target,
        "fully_covered": len(cov) == target,
        "elapsed_sec": round(time.time() - t0, 2),
    }

    p = os.path.join("..", "data", "route4_front_certificate.json")
    os.makedirs(os.path.dirname(p), exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(out, f, indent=2)
    print(f"\nCertificate saved to {p} (Time: {out['elapsed_sec']}s)")


if __name__ == "__main__":
    main()