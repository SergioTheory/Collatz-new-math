"""
spectral_gap_n8.py
Спектральная щель наклонённого 3-адического обратного оператора
при n=8 (4374 состояний) и сравнение с эталоном при n=7.

Что считает:
  1. Строит матрицу наклонённого обратного оператора
     P_n^{(s)}(x,y) = 1/(1-q^T) * sum_a q^a * 1[y = (2^a x - 1)/3 mod 3^n]
     где q = e^s / 2, T = 2*3^(n-1), суммирование по a с 2^a*x = 1 (mod 3).
  2. Вычисляет корень Перрона  rho  и второй по модулю собственный
     значение  lambda_2.
  3. Считает щель  gap = 1 - |lambda_2| / rho  и отношение max/min
     перроновской собственной функции.
  4. Повторяет для набора наклонов  s в [0, 0.5]  и сравнивает
     с эталоном при n=7 из статьи.

Запуск:  python spectral_gap_n8.py
Время:   ~2-5 мин на одном ядре (зависит от CPU).
"""

import numpy as np
import time
import sys
import os

# ──────────────────────────────────────────────────────────────────────
# Построение оператора
# ──────────────────────────────────────────────────────────────────────
def build_operator(n, s):
    """Строит плотную матрицу наклонённого обратного оператора."""
    q = np.exp(s) / 2.0
    T = 2 * 3 ** (n - 1)
    mod = 3 ** n

    # Состояния: x в [1, 3^n), x не делится на 3
    states = np.array([x for x in range(1, mod) if x % 3 != 0], dtype=np.int64)
    num = len(states)

    # Быстрый доступ:  x -> индекс в states
    idx_of = np.full(mod, -1, dtype=np.int64)
    for i, x in enumerate(states):
        idx_of[x] = i

    # Предвычисление степеней 2 по модулю 3^n  и весов q^a
    pow2 = np.empty(T + 1, dtype=np.int64)
    pow2[0] = 1
    for a in range(1, T + 1):
        pow2[a] = (pow2[a - 1] * 2) % mod
    qa = np.array([q ** a for a in range(T + 1)])

    norm = 1.0 / (1.0 - q ** T)
    P = np.zeros((num, num), dtype=np.float64)

    for i, x in enumerate(states):
        # чётность a определяется остатком x по модулю 3:
        #   2^a * x = 1 (mod 3)  =>  a чётно при x=1, нечётно при x=2
        if x % 3 == 1:
            a_iter = range(2, T + 1, 2)
        else:
            a_iter = range(1, T + 1, 2)

        # Векторизованно вычисляем образы для всех допустимых a
        a_arr = np.fromiter(a_iter, dtype=np.int64)
        y_arr = (pow2[a_arr] * x - 1) // 3 % mod

        # Фильтруем допустимые состояния (не 0, не кратно 3)
        valid = (y_arr > 0) & (y_arr % 3 != 0)
        y_v = y_arr[valid]
        a_v = a_arr[valid]

        j_idx = idx_of[y_v]
        ok = j_idx >= 0
        P[i, j_idx[ok]] += qa[a_v[ok]] * norm

    return P


# ──────────────────────────────────────────────────────────────────────
# Спектральный анализ
# ──────────────────────────────────────────────────────────────────────
def spectral_gap(P):
    """Возвращает  (rho, |lambda_2|, gap, max/min, спектр)."""
    from scipy.linalg import eig
    vals, vecs = eig(P)

    order = np.argsort(-np.abs(vals))
    vals = vals[order]
    vecs = vecs[:, order]

    rho = float(np.abs(vals[0]))
    lam2 = float(np.abs(vals[1]))
    gap = 1.0 - lam2 / rho

    # Перроновская собственная функция (должна быть вещественной и > 0)
    h = np.abs(np.real(vecs[:, 0]))
    max_min = float(np.max(h) / np.min(h))

    return rho, lam2, gap, max_min, vals


# ──────────────────────────────────────────────────────────────────────
# Эталон из статьи (n = 7, 1458 состояний)
# ──────────────────────────────────────────────────────────────────────
REFERENCE_N7 = {
    0.0: (0.3418, 0.0469, 1289.8),
    0.1: (0.4181, 0.0759, 207.5),
    0.2: (0.5264, 0.1291, 36.7),
    0.3: (0.6935, 0.2152, 9.2),
    0.4: (0.9790, 0.3269, 3.6),
    0.5: (1.5646, 0.4531, 2.0),
}


# ──────────────────────────────────────────────────────────────────────
# Основной расчёт
# ──────────────────────────────────────────────────────────────────────
def main():
    # Set number of threads for OpenBLAS / MKL / OMP to fully utilize CPU
    os.environ['OMP_NUM_THREADS'] = '35'
    os.environ['OPENBLAS_NUM_THREADS'] = '35'
    os.environ['MKL_NUM_THREADS'] = '35'

    n = 8
    num_states = 3 ** n - 3 ** (n - 1)
    s_values = [0.0, 0.1, 0.2, 0.3, 0.4, 0.5]

    print(f"Спектральная щель Леммы A3 при n={n}  ({num_states} состояний)")
    print("=" * 70)
    print(f"{'s':>5} | {'rho':>9} {'gap':>8} {'max/min':>10} | "
          f"{'rho_ref':>8} {'gap_ref':>8} {'m/m_ref':>9} | {'time':>6}")
    print("-" * 70)

    results = {}
    for s in s_values:
        t0 = time.time()
        P = build_operator(n, s)
        rho, lam2, gap, max_min, vals = spectral_gap(P)
        dt = time.time() - t0

        ref = REFERENCE_N7.get(s, (0, 0, 0))
        results[s] = (rho, gap, max_min)

        print(f"{s:>5.1f} | {rho:>9.4f} {gap:>8.4f} {max_min:>10.1f} | "
              f"{ref[0]:>8.4f} {ref[1]:>8.4f} {ref[2]:>9.1f} | {dt:>5.1f}s", flush=True)

    # ── Итог ──
    print("=" * 70)
    print("Интерпретация:")
    for s, (rho, gap, mm) in results.items():
        ref_gap = REFERENCE_N7[s][1]
        ref_mm = REFERENCE_N7[s][2]
        trend_gap = "растёт" if gap > ref_gap else "убывает"
        trend_mm = "растёт" if mm > ref_mm else "убывает"
        print(f"  s={s:.1f}:  щель {gap:.4f} ({trend_gap} к {ref_gap:.4f}), "
              f"max/min {mm:.1f} ({trend_mm} к {ref_mm:.1f})")

    print("\nКритерий Леммы A3: щель ограничена снизу на компакте,")
    print("max/min ограничена сверху. Если при переходе 7->8 щель")
    print("не падает к нулю, а отношение не взрывается — гипотеза")
    print("равномерной щели подтверждается на большем масштабе.")


if __name__ == "__main__":
    main()
