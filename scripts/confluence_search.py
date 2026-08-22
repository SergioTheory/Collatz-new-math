"""
confluence_search.py — Поиск точек слияния траекторий Zone 2 чисел

Для всех чисел с peak=140 из records_data.py:
1. Вычисляет промежуточные x_k по ускоренной динамике (odd steps only)
2. Берёт x_k mod 2^20 для каждого шага
3. Ищет совпадения между парами чисел — точки слияния
4. Проверяет, является ли слияние полным (все последующие шаги тоже совпадают)

Использование:
  python confluence_search.py
"""

from __future__ import annotations

import sys
from pathlib import Path
from collections import defaultdict

sys.path.insert(0, str(Path(__file__).parent))
sys.path.insert(0, str(Path(__file__).parent.parent))

from crt_solver import analyze_to_peak, collatz_peak


# ── Все числа с peak=140 из records_data.py ─────────────────────────────────

ZONE2_BINARY = [
    # 71 бит — первое (Barina #1)
    "10111111011101000101101010111101101011101101000001010000111010011101111",
    # 71 бит — второе (Barina #2 = Z2_CORE extended)
    "11111111110000001110010011001110000101010001101110011110011100110111111",
    # 72 бит
    "111111111100000011100100110011100001010100011011100111100111001101111110",
    # 73 бит
    "1111111111000000111001001100111000010101000110111001111001110011011111101",
    # 74 бит
    "11111111110000001110010011001110000101010001101110011110011100110111111010",
    # 75 бит
    "111111111100000011100100110011100001010100011011100111100111001101111110101",
    # 76 бит
    "1111111111000000111001001100111000010101000110111001111001110011011111101000",
    # 77 бит
    "11111111110000001110010011001110000101010001101110011110011100110111111100011",
    # 78 бит
    "111111111100000011100100110011100001010100011011100111100111001101111111100011",
    # 79 бит
    "1111111111000000111001001100111000010101000110111001111001110011011111111001011",
    # 80 бит
    "11111111110000001110010011001110000101010001101110011110011100110111111110110011",
    # 81 бит
    "111111111100000011100100110011100001010100011011100111100111001101111111101110011",
    # 82 бит
    "1111111111000000111001001100111000010101000110111001111001110011011111111101001001",
]


EXTRA_NUMBERS = [
    # (n, bits, label)
    (9662093721059247840295139,  83, "Z2-83b"),
    (19324187442118495680593175, 84, "Z2-84b"),
    (38648374884236991361186739, 85, "Z2-85b"),
    (77296749768473982722370787, 86, "Z2-86b"),
    (154593499536947965444748439, 87, "Z2-87b"),
    (309485009821345068724781055, 88, "FA-88b"),  # Family A, peak=141, контроль
]

# Метки новых чисел (83–88) для фильтрации пар в Части 3
NEW_LABELS = {item[2] for item in EXTRA_NUMBERS}

MOD_BITS = 20
MOD = 1 << MOD_BITS  # 2^20 = 1048576


def accelerated_trajectory(n: int, max_odd_steps: int = 500) -> list[int]:
    """
    Вычисляет последовательность x_0, x_1, ..., x_d по ускоренной динамике:
    x_{k+1} = (3·x_k + 1) >> v2(3·x_k + 1)
    Каждый x_k — нечётное число (результат после всех делений на 2).
    Возвращает список [x_0, x_1, ..., x_d].
    """
    trajectory = []
    cur = n

    # Если n чётное, сначала убираем все двойки
    while cur > 1 and cur % 2 == 0:
        cur >>= 1

    for _ in range(max_odd_steps + 1):
        trajectory.append(cur)
        if cur <= 1:
            break
        val = 3 * cur + 1
        # v2: считаем сколько раз делится на 2
        while val % 2 == 0:
            val >>= 1
        cur = val

    return trajectory


def extract_shifts_from_traj(n: int, max_odd_steps: int = 500) -> list[int]:
    """Извлекает shift-вектор (число делений на 2 после каждого 3x+1)."""
    cur = n
    while cur > 1 and cur % 2 == 0:
        cur >>= 1

    shifts = []
    for _ in range(max_odd_steps):
        if cur <= 1:
            break
        val = 3 * cur + 1
        count = 0
        while val % 2 == 0:
            val >>= 1
            count += 1
        shifts.append(count)
        cur = val

    return shifts


def main():
    print(f"{'=' * 78}")
    print(f"  Confluence Search — точки слияния траекторий Zone 2")
    print(f"{'=' * 78}")
    print(f"  Модуль: 2^{MOD_BITS} = {MOD}")
    print()

    # ── ЧАСТЬ 1: Базовая информация о числах ─────────────────────────────────
    print(f"  ЧАСТЬ 1: Информация о числах с peak=140")
    print(f"  {'-' * 70}")

    numbers = []  # (label, n, bits, d, S, peak)

    # 71–82 бит из ZONE2_BINARY
    seen_labels = set()
    for bstr in ZONE2_BINARY:
        n = int(bstr, 2)
        bits = n.bit_length()
        info = analyze_to_peak(n, max_steps=500_000)
        d = info['total_o']
        S = info['total_e']
        peak = info['peak']
        # Различаем два 71-битных числа по d
        base_label = f"Z2-{bits}b"
        label = base_label
        suffix = 2
        while label in seen_labels:
            label = f"{base_label}#{suffix}"
            suffix += 1
        seen_labels.add(label)
        numbers.append((label, n, bits, d, S, peak))

    # 83–88 бит (hardcoded)
    for n_val, bits_expected, label in EXTRA_NUMBERS:
        info = analyze_to_peak(n_val, max_steps=500_000)
        d = info['total_o']
        S = info['total_e']
        peak = info['peak']
        numbers.append((label, n_val, n_val.bit_length(), d, S, peak))

    print(f"  {'label':<12} {'bits':>4} {'peak':>4} {'d':>4} {'S':>4}  {'S/d':>6}  {'ratio':>6}")
    print(f"  {'-' * 55}")
    for label, n, bits, d, S, peak in numbers:
        ratio = peak / bits
        sd = S / d if d > 0 else 0
        print(f"  {label:<12} {bits:>4} {peak:>4} {d:>4} {S:>4}  {sd:>6.4f}  {ratio:>6.4f}")

    # Группировка: d=213 vs d=258 (или другие)
    d_groups = defaultdict(list)
    for label, n, bits, d, S, peak in numbers:
        d_groups[d].append((label, n, bits, S))

    print(f"\n  Группы по d:")
    for d_val in sorted(d_groups.keys()):
        members = d_groups[d_val]
        labels = [m[0] for m in members]
        print(f"    d={d_val}: {', '.join(labels)}")

    # ── ЧАСТЬ 2: Вычисляем траектории ──────────────────────────────────────────
    print(f"\n  ЧАСТЬ 2: Вычисляем ускоренные траектории")
    print(f"  {'-' * 70}")

    trajectories = {}  # label -> list of x_k
    residues = {}      # label -> list of x_k mod 2^20
    max_d = max(d for _, _, _, d, _, _ in numbers)

    for label, n, bits, d, S, peak in numbers:
        traj = accelerated_trajectory(n, max_odd_steps=max_d + 10)
        trajectories[label] = traj
        residues[label] = [x % MOD for x in traj]
        print(f"  {label}: {len(traj)} шагов, "
              f"x_0={n}, x_0 mod 2^20 = {n % MOD}")

    # ── ЧАСТЬ 3: Поиск совпадений x_k mod 2^20 ─────────────────────────────────
    print(f"\n  ЧАСТЬ 3: Поиск точек слияния (x_ki mod 2^{MOD_BITS} == x_kj mod 2^{MOD_BITS})")
    print(f"  {'-' * 70}")

    labels = [item[0] for item in numbers]
    d_map = {item[0]: item[3] for item in numbers}

    # Для пар с хотя бы одним НОВЫМ числом (83–88) ищем совпадения
    # Для старых пар (71–82) — уже известно из прошлого запуска
    confluences = []  # (label_i, label_j, k_i, k_j, residue, is_full, ...)

    for i in range(len(labels)):
        for j in range(i + 1, len(labels)):
            li, lj = labels[i], labels[j]

            # Только пары, где хотя бы одно число новое (83–88)
            if li not in NEW_LABELS and lj not in NEW_LABELS:
                continue

            ri, rj = residues[li], residues[lj]

            # Строим индекс: residue -> list of steps для числа j
            rj_index = defaultdict(list)
            for kj, val in enumerate(rj):
                rj_index[val].append(kj)

            # Ищем совпадения
            pair_matches = []
            for ki, val_i in enumerate(ri):
                if val_i in rj_index:
                    for kj in rj_index[val_i]:
                        pair_matches.append((ki, kj, val_i))

            if pair_matches:
                # Только первое слияние (минимальное ki + kj)
                pair_matches.sort(key=lambda x: x[0] + x[1])
                ki, kj, residue = pair_matches[0]

                # Проверяем, полное ли слияние
                ti, tj = trajectories[li], trajectories[lj]
                remaining_i = len(ti) - ki
                remaining_j = len(tj) - kj
                check_len = min(remaining_i, remaining_j)

                is_full = True
                diverge_at = -1
                for step in range(check_len):
                    if ti[ki + step] % MOD != tj[kj + step] % MOD:
                        is_full = False
                        diverge_at = step
                        break

                confluences.append((li, lj, ki, kj, residue, is_full,
                                   check_len, diverge_at))

    # Выводим результаты
    if not confluences:
        print("  Совпадений не найдено!")
    else:
        print(f"\n  Найдено {len(confluences)} точек слияния:")
        print(f"  {'num_i':<12} {'num_j':<12} {'k_i':>4} {'k_j':>4}  "
              f"{'residue':>10}  {'full?':>5}  {'note'}")
        print(f"  {'-' * 70}")

        for li, lj, ki, kj, residue, is_full, check_len, div_at in confluences:
            full_str = "YES" if is_full else "NO"
            if is_full:
                note = f"полное слияние, проверено {check_len} шагов"
            else:
                note = f"расходятся через {div_at} шаг(ов)"

            print(f"  {li:<12} {lj:<12} {ki:>4} {kj:>4}  "
                  f"{residue:>10}  {full_str:>5}  {note}")

    # ── ЧАСТЬ 4: Особый фокус — d=213 vs d=258 ────────────────────────────────
    print(f"\n  ЧАСТЬ 4: Слияния между разными группами d")
    print(f"  {'-' * 70}")

    cross_group = []
    for li, lj, ki, kj, residue, is_full, check_len, div_at in confluences:
        if d_map[li] != d_map[lj]:
            cross_group.append((li, lj, ki, kj, residue, is_full, check_len, div_at))

    if not cross_group:
        print("  Нет слияний между числами с разным d.")
        # Проверим что d все одинаковые
        unique_d = set(d_map.values())
        if len(unique_d) == 1:
            print(f"  (Все числа имеют d={unique_d.pop()} — разных групп нет)")
    else:
        print(f"  Найдено {len(cross_group)} cross-group слияний:")
        for li, lj, ki, kj, residue, is_full, check_len, div_at in cross_group:
            full_str = "YES" if is_full else "NO"
            print(f"  {li} (d={d_map[li]}) × {lj} (d={d_map[lj]}): "
                  f"k_i={ki}, k_j={kj}, res={residue}, full={full_str}")

    # ── ЧАСТЬ 5: Полные слияния — детальный анализ ─────────────────────────────
    print(f"\n  ЧАСТЬ 5: Детальный анализ полных слияний")
    print(f"  {'-' * 70}")

    full_merges = [(li, lj, ki, kj, r, cl)
                   for li, lj, ki, kj, r, is_full, cl, _ in confluences
                   if is_full]

    if not full_merges:
        print("  Нет полных слияний.")
    else:
        # Группируем: для каждого полного слияния показываем
        # реальные значения x_ki и x_kj (не только mod 2^20)
        shown = set()
        for li, lj, ki, kj, residue, check_len in full_merges:
            key = (li, lj, ki, kj)
            if key in shown:
                continue
            shown.add(key)

            xi = trajectories[li][ki]
            xj = trajectories[lj][kj]

            exact_match = (xi == xj)

            print(f"\n  {li}[k={ki}] ↔ {lj}[k={kj}]:")
            print(f"    x_i = {xi}")
            print(f"    x_j = {xj}")
            print(f"    x_i mod 2^20 = {xi % MOD}")
            print(f"    x_j mod 2^20 = {xj % MOD}")
            print(f"    Точное совпадение: {'ДА' if exact_match else 'НЕТ'}")
            if exact_match:
                print(f"    → Траектории ИДЕНТИЧНЫ начиная с этой точки!")
            else:
                print(f"    x_i bits = {xi.bit_length()}, x_j bits = {xj.bit_length()}")
                # Проверяем совпадение по более крупным модулям
                for mb in [32, 40, 48, 56, 64]:
                    m = 1 << mb
                    if xi % m == xj % m:
                        print(f"    Совпадают mod 2^{mb}: ДА")
                    else:
                        print(f"    Совпадают mod 2^{mb}: НЕТ")
                        break

    # ── ЧАСТЬ 5b: Целевая проверка — сливаются ли 83–88 к x* ? ────────────────
    X_STAR = 20152090995747160937051
    print(f"\n  ЧАСТЬ 5b: Проверка слияния к x* = {X_STAR}")
    print(f"  {'-' * 70}")
    print(f"  x* bits = {X_STAR.bit_length()}, x* mod 2^20 = {X_STAR % MOD}")

    for label, n, bits, d, S, peak in numbers:
        traj = trajectories[label]
        found = False
        for k, x_k in enumerate(traj):
            if x_k == X_STAR:
                print(f"  {label:>12}: x_{k} == x*  ТОЧНОЕ СОВПАДЕНИЕ на шаге {k}")
                found = True
                break
        if not found:
            # Проверяем mod 2^20
            x_star_mod = X_STAR % MOD
            for k, x_k in enumerate(traj):
                if x_k % MOD == x_star_mod:
                    exact = "EXACT" if x_k == X_STAR else f"mod only (x_k={x_k})"
                    print(f"  {label:>12}: x_{k} mod 2^20 == x* mod 2^20 "
                          f"на шаге {k}  [{exact}]")
                    found = True
                    break
            if not found:
                print(f"  {label:>12}: НЕТ совпадения с x* (ни exact, ни mod 2^20)")

    # ── ЧАСТЬ 6: Статистика совпадений по шагам ────────────────────────────────
    print(f"\n  ЧАСТЬ 6: Когда происходит слияние (распределение по шагам)")
    print(f"  {'-' * 70}")

    # Для пар из одной d-группы: на каком шаге начинается полное совпадение?
    for d_val in sorted(d_groups.keys()):
        members = d_groups[d_val]
        if len(members) < 2:
            continue
        print(f"\n  Группа d={d_val} ({len(members)} чисел):")

        for i in range(len(members)):
            for j in range(i + 1, len(members)):
                li, lj = members[i][0], members[j][0]
                ti, tj = trajectories[li], trajectories[lj]
                min_len = min(len(ti), len(tj))

                # Ищем первый шаг полного совпадения (с конца)
                # Идём с конца траектории и находим, где расходятся
                first_match = None
                for k in range(min_len - 1, -1, -1):
                    if ti[k] == tj[k]:
                        first_match = k
                    else:
                        break

                if first_match is not None:
                    print(f"    {li} ↔ {lj}: полное совпадение с шага "
                          f"k={first_match} (из {min_len}), "
                          f"расхождение в первых {first_match} шагах = адаптер")
                else:
                    # Нет точного совпадения — ищем mod 2^20
                    first_mod_match = None
                    for k in range(min_len - 1, -1, -1):
                        if ti[k] % MOD == tj[k] % MOD:
                            first_mod_match = k
                        else:
                            break
                    if first_mod_match is not None:
                        print(f"    {li} ↔ {lj}: mod 2^{MOD_BITS} совпадение "
                              f"с шага k={first_mod_match}")
                    else:
                        print(f"    {li} ↔ {lj}: нет совпадений")

    print(f"\n{'=' * 78}")
    print(f"  Готово.")
    print(f"{'=' * 78}")


if __name__ == '__main__':
    main()
