"""
reverse_tree.py — Обратное дерево Коллатца.

Для хорошего числа n строит его "предков" — числа m,
такие что forward(m) = n (через обратные шаги).

Обратные шаги:
  - Если n чётное: m = n * 2  (обратный шаг /2)
  - Если (n - 1) делится на 3 и ((n-1)//3) нечётно: m = (n-1) // 3

BFS с обрезкой по ширине: не более max_width узлов на уровень.
При превышении оставляем узлы с наилучшей плотностью единиц.
"""
from __future__ import annotations

from collections import deque
from typing import Generator

from logger import get_logger

log = get_logger("reverse_tree")


class ReverseTreeSearcher:
    """
    Обратный обход дерева Коллатца.
    """

    def __init__(self, cfg: dict) -> None:
        rt_cfg = cfg.get("reverse_tree", {})
        self.enabled:       bool  = rt_cfg.get("enabled", True)
        self.depth:         int   = rt_cfg.get("depth", 40)
        self.max_width:     int   = rt_cfg.get("max_width", 1000)
        self.max_overhead:  int   = rt_cfg.get("max_bits_overhead", 2)

        gen_cfg = cfg.get("generator", {})
        self.density_k: float = gen_cfg.get("density_k", 10.0)

        log.info(
            f"ReverseTreeSearcher: depth={self.depth}, "
            f"max_width={self.max_width}, enabled={self.enabled}"
        )

    def _density_range(self, bits: int) -> tuple[float, float]:
        k = self.density_k
        mn = max(0.50, 0.50 + k / bits)
        mx = min(0.72, 0.70 - k / bits)
        if mn >= mx:
            mn, mx = 0.54, 0.64
        return mn, mx

    def _passes_density(self, m: int, max_bits: int) -> bool:
        """Проверяет, что предок не нарушает ограничения плотности и размера."""
        mb = m.bit_length()
        if mb > max_bits + self.max_overhead:
            return False
        mn_d, mx_d = self._density_range(mb)
        density = bin(m).count("1") / mb
        return mn_d <= density <= mx_d

    def _score(self, m: int) -> float:
        """Оценка для приоритизации при обрезке (выше = лучше)."""
        mb = m.bit_length()
        if mb == 0:
            return 0.0
        mn_d, mx_d = self._density_range(mb)
        density = bin(m).count("1") / mb
        mid = (mn_d + mx_d) / 2.0
        return 1.0 - abs(density - mid)  # чем ближе к середине диапазона — тем лучше

    def expand(self, n: int) -> Generator[int, None, None]:
        """
        BFS по обратному дереву от числа n.
        Генерирует предков-кандидатов.

        Args:
            n: исходное число (найденный рекорд)

        Yields:
            Числа-предки, прошедшие фильтр плотности
        """
        if not self.enabled:
            return

        orig_bits = n.bit_length()
        max_bits  = orig_bits + self.max_overhead

        # BFS: очередь хранит (число, глубина)
        queue: deque[tuple[int, int]] = deque()
        queue.append((n, 0))
        visited: set[int] = {n}
        found_count = 0

        while queue:
            # Собираем весь текущий уровень
            level_nodes = []
            current_depth = queue[0][1] if queue else 0
            while queue and queue[0][1] == current_depth:
                level_nodes.append(queue.popleft())

            if current_depth >= self.depth:
                break

            next_level: list[tuple[int, int]] = []

            for node, depth in level_nodes:
                # Обратный шаг 1: m = node * 2 (всегда чётное → /2 → node)
                m1 = node * 2
                if m1 not in visited and m1.bit_length() <= max_bits:
                    visited.add(m1)
                    if self._passes_density(m1, max_bits):
                        next_level.append((m1, depth + 1))
                        yield m1
                        found_count += 1

                # Обратный шаг 2: m = (node - 1) // 3, если node нечётное
                # Условие: (node - 1) % 3 == 0 и m нечётное
                if node > 1 and (node - 1) % 3 == 0:
                    m2 = (node - 1) // 3
                    if m2 > 0 and m2 & 1 and m2 not in visited:
                        if m2.bit_length() <= max_bits:
                            visited.add(m2)
                            if self._passes_density(m2, max_bits):
                                next_level.append((m2, depth + 1))
                                yield m2
                                found_count += 1

            # Обрезка по ширине
            if len(next_level) > self.max_width:
                next_level.sort(key=lambda x: self._score(x[0]), reverse=True)
                pruned = len(next_level) - self.max_width
                next_level = next_level[:self.max_width]
                log.debug(
                    f"ReverseTree depth={current_depth+1}: "
                    f"pruned {pruned} nodes, kept {self.max_width}"
                )

            queue.extend(next_level)

        log.debug(f"ReverseTree from n={n.bit_length()}bit: found {found_count} ancestors")
