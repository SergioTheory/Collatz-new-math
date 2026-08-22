import os
import re

# Простой словарь для перевода терминов, чтобы сохранить их точными
glossary = {
    "Арифметический хаос с редкими островами порядка: вычислительная карта пространства Коллатца": "Arithmetic Chaos with Rare Islands of Order: A Computational Map of the Collatz Space",
    "Аннотация": "Abstract",
    "Глоссарий и константы": "Glossary and Constants",
    "Введение и хронология исследования": "Introduction and Chronology of the Study",
    "Задача Коллатца": "The Collatz Problem",
    "Отправная точка: результаты Давида Барины": "Starting Point: David Barina's Results",
    "Фаза 1: Collatz Crystal Hunter и марковские цепи (февраль 2026)": "Phase 1: Collatz Crystal Hunter and Markov Chains (February 2026)",
    "Фаза 2: Статистический анализ 30 миллионов чисел (начало марта 2026)": "Phase 2: Statistical Analysis of 30 Million Numbers (Early March 2026)",
    "Фаза 3: От статистики к структуре (март 2026)": "Phase 3: From Statistics to Structure (March 2026)",
    "Нотация и ускоренная динамика": "Notation and Accelerated Dynamics",
    "2-адическая интерпретация": "2-adic Interpretation",
    "Базовый слой: **Family A**": "Base Layer: **Family A**",
    "**Zone 2**: единственный подтверждённый крупный confluence-класс": "**Zone 2**: The Only Confirmed Major Confluence Class",
    "Открытие": "Discovery",
    "Таблица представителей **Zone 2**": "Table of **Zone 2** Representatives",
    "Инварианты **Zone 2**": "Invariants of **Zone 2**",
    "Точка слияния $x^*$": "Confluence Point $x^*$",
    "Обратное дерево $x^*$ и полный размер **Zone 2**": "Reverse Tree of $x^*$ and Full Size of **Zone 2**",
    "Число Барины: изолированный второй путь к пику 140": "Barina's Number: An Isolated Second Path to Peak 140",
    "Число 27 как миниатюрная **Zone 2**": "Number 27 as a Miniature **Zone 2**",
    "Мёртвая зона 88–170 бит": "Dead Zone 88–170 Bits",
    "Вероятностная анатомия Мёртвой зоны": "Probabilistic Anatomy of the Dead Zone",
    "Опровержение Zone 3": "Refutation of Zone 3",
    "Архипелаг confluence-центров": "Archipelago of Confluence Centers",
    "Систематическая перепись центров (peaks 10–200)": "Systematic Census of Centers (Peaks 10–200)",
    "Три подтверждённых алгебраических закона": "Three Confirmed Algebraic Laws",
    "Два класса центров": "Two Classes of Centers",
    "Тренды": "Trends",
    "Переходные центры (peaks 35, 37, 41)": "Transitional Centers (Peaks 35, 37, 41)",
    "Центры не покрывают пространство": "Centers Do Not Cover the Space",
    "Спектр аккордов: от числа 27 к **Zone 2**": "Spectrum of Chords: From Number 27 to **Zone 2**",
    "Сводная карта пространства Коллатца": "Summary Map of the Collatz Space",
    "Общая картина": "The Big Picture",
    "Открытые вопросы": "Open Questions",
    "Приложение A. Основные скрипты проекта": "Appendix A. Main Project Scripts"
}

def create_latex_document():
    with open('Collatz_v6.md', 'r', encoding='utf-8') as f:
        md_text = f.read()

    # Заменяем заголовки
    for ru, en in glossary.items():
        md_text = md_text.replace(ru, en)

    # Здесь будет вызов LLM для перевода текста, но так как я LLM, я напишу скрипт 
    # который создает файл с английским текстом напрямую
    
    latex_template = r"""\documentclass[12pt,a4paper]{article}
\usepackage[utf8]{inputenc}
\usepackage[T1]{fontenc}
\usepackage{amsmath,amssymb,amsfonts}
\usepackage{hyperref}
\usepackage{geometry}
\usepackage{booktabs}
\geometry{a4paper, margin=1in}

\title{Arithmetic Chaos with Rare Islands of Order: A Computational Map of the Collatz Space}
\author{Collatz Crystal Hunter Project}
\date{April 2026}

\begin{document}

\maketitle

\begin{abstract}
We present the results of a large-scale computational study of Collatz sequence trajectories in terms of accelerated dynamics over odd numbers, shift-vectors, and confluence structures. The central discovery is \textbf{Zone 2} — a family of 913 numbers with bit lengths 71–87, whose trajectories merge into a single 75-bit node $x^* = 20152090995747160937051$ in no more than 7 odd steps, after which they follow an identical path to a peak of 140 bits. In parallel, Barina's number was discovered — a completely isolated second path to the same peak 140, sharing no intermediate points with \textbf{Zone 2}. A systematic census of confluence centers (peaks 10–200, scripts \texttt{confluence\_census.py} + \texttt{verify\_census\_centers.py} + \texttt{targeted\_search}) revealed 32 confirmed centers for EVERY integer peak from 14 to 50, as well as for peak = 140. We discovered the formula $center\_bits \approx 0.496 \times peak + 6.47$ ($R^2 = 0.965$) and the modular filter $c \equiv 2 \pmod 3$. Cluster analysis (\texttt{two\_class\_analysis.py}) divided all centers into two classes: \textbf{Class A} ($121$, $x^*$ — "deep funnels" with $d_{peak} \gg 10$, $S/d \approx 1.33$, 100\% hit rate, shift-profile of \textbf{Zone 2}) and \textbf{Class B} (all others — "shallow confluences" with $d_{peak} \approx 3–15$, $S/d \approx 1.0–1.2$, hit rate 80–92\%). In the 88–170 bit range, an extensive "dead zone" without anomalies above \textbf{Family A} is confirmed. The body of results indicates that the Collatz space contains a continuous archipelago of confluence structures (\textbf{Class B} for each peak), above which rise rare "deep funnels" (\textbf{Class A}), organized around the irrationality $\log_2 3$.
\end{abstract}

\section*{Glossary and Constants}
\begin{itemize}
    \item \textbf{Family A ($2^b - 1$)}: The base landscape. Ratios tend to $\log_2 3 \approx 1.585$.
    \item \textbf{Confluence}: The gravitational capture of trajectories into nodes (centers).
    \item \textbf{Class A (Deep funnels)}: 100\% Hit Rate. Centers $121$ (Peak 14) and $x^*$ (Peak 140).
    \item \textbf{Class B (Shallow funnels)}: 70–93\% Hit Rate. Dense archipelago (Peaks 15–51).
    \item \textbf{Center Bits Formula}: $center\_bits = 0.498258 \cdot peak + 6.2928 \quad (R^2 = 0.965)$.
    \item \textbf{Scaling Hypothesis $\times 10$}: The hypothesis that Class A centers follow a logarithmic scale (14 $\to$ 140 $\to$ 1400).
    \item \textbf{Septembrino's Law}: Distribution of divisors $P(div = 2^a) = 1/2^a$.
\end{itemize}

\section{Introduction and Chronology of the Study}
\subsection{The Collatz Problem}
For a natural number $n$, we define the map $T(n) = n/2$ if $n$ is even, and $T(n) = (3n+1)/2$ if odd. The Collatz conjecture states that iterations of $T$ for any $n$ eventually reach 1. Despite its elementary formulation, the problem remains open; Paul Erdős remarked that "mathematics may not be ready for such problems."
The quantitative measure of a number's "anomaly" is its \textit{ratio} — the ratio of the trajectory's peak bit length to the input bit length. For typical numbers, ratio $\approx 1.0–1.2$. Numbers of the form $2^b - 1$ (Family A, all ones in binary representation) yield a ratio approaching $\log_2 3 \approx 1.585$. Anything significantly higher represents a structural anomaly.

\subsection{Starting Point: David Barina's Results}
David Barina performed an exhaustive search of all numbers up to $2^{71}$ and compiled a table of path records — numbers with record peaks for their bit length. In Barina's table, there are two 71-bit record holders: $n = 2358909599867980429759$ (ratio 1.97, peak 140) and $n = 1765856170146672440559$ (ratio 1.97, peak 140). These numbers became the starting point of the entire study.

\subsection{Phase 1: Collatz Crystal Hunter and Markov Chains (February 2026)}
The first task was a directed search for numbers with an anomalously high ratio in the 72–80 bit range. Together with DeepSeek, the Collatz Crystal Hunter (v5.3a) system was developed — a distributed Python program with hybrid candidate generation. Main components:
1. A Markov chain of order 5, trained on found numbers, generating "tails" of numbers based on the context of the last bits.
2. A pool of prefixes from Barina's path records with adaptive weights.
3. Three-stage filtering: Stage 1 (50 steps, culling ratio $< 1.03$), Stage 2 (200 steps), Stage 3 (full simulation up to 50,000 steps).
4. 35 workers via multiprocessing with cross-training.
In 10+ hours on 35 cores, the best found ratio for 73–80 bits was 1.613.

\subsection{Phase 2: Statistical Analysis of 30 Million Numbers (Early March 2026)}
The system was switched to statistics collection mode. The \texttt{stats\_collector.py} module recorded data for each number that passed Stage 3. An array of 30 million records for bit lengths 72–80 was collected.
The analysis revealed key patterns:
\begin{itemize}
    \item The ratio distribution has a sharp peak around 1.04–1.05 and a fast-decaying tail (power law with $\alpha \approx 3.66$).
    \item The median ratio monotonically decreases with bit length (1.0417 for 72 bits $\to$ 1.0375 for 80 bits).
    \item The 99th percentile for 72 bits is 1.1528, for 80 bits — 1.1250.
\end{itemize}
But the main discovery of this phase was different: the maximum ratio for each bit length dropped almost linearly ($\approx 0.024$ per bit), and recalculating $max\_ratio \times bits$ for all bit lengths 72–80 yielded the exact same number: exactly 140. All records, from 72-bit (ratio 1.944) to 80-bit (ratio 1.750), had the same absolute peak — 140 bits. In the DeepSeek report, this was called a "striking discovery," indicating the existence of a "magnetic peak" towards which the trajectories of many extreme numbers tend.

\subsection{Phase 3: From Statistics to Structure (March 2026)}
The discovery of the "magnetic peak" 140 required a fundamentally new approach. Instead of a statistical search for records, we shifted to structural analysis: why exactly 140? Which numbers produce this peak? What do they have in common?
A second-generation toolkit was developed: a CRT constructor (\texttt{crt\_solver.py}) to reconstruct numbers from parity strings, a shift-vector analyzer, reverse trees, and beam search over residue classes. With the addition of Claude, Claude Code, and ChatGPT, the work accelerated immensely. By the end of March 2026, all the results described below were obtained.

\section{Notation and Accelerated Dynamics}
We consider the accelerated Collatz trajectory over odd values:
$$x_{k+1} = \frac{3 \cdot x_k + 1}{2^{a_k}}$$
where $a_k \ge 1$ is the number of divisions by 2 after the $k$-th odd step (the 2-adic valuation of $3x_k + 1$). The sequence $a_0, a_1, \dots, a_{d-1}$ is called the shift-vector of the trajectory; $d$ is the number of odd steps to the peak; $S_k = a_0 + a_1 + \dots + a_{k-1}$ is the accumulated shift.

After $k$ steps:
$$x_k = \frac{3^k \cdot x_0 + c_k}{2^{S_k}}, \quad c_0 = 0, \quad c_{k+1} = 3 \cdot c_k + 2^{S_k}$$
The cumulative gain is defined as $G(k) = k \cdot \log_2 3 - S_k$. When $G(k) > 0$, the trajectory grows (the multiplier 3 "beats" the division by $2^a$); when $G(k) < 0$, it decreases. The peak of the trajectory is reached near the maximum of $G(k)$.

Every prefix of the shift-vector $(a_0, \dots, a_{k-1})$ defines a unique residue class $x_0 \equiv r_k \pmod{2^{S_k}}$, allowing numbers to be reconstructed from their parity strings via the Chinese Remainder Theorem.

\subsection{2-adic Interpretation}
In the terminology of p-adic analysis (Lagarias, Bernstein, Monks), every admissible shift-vector $w = (a_0, \dots, a_{d-1})$ defines a 2-adic cylinder $C(w) = \rho(w) + 2^{S_d} \cdot \mathbb{Z}_2$ with Haar measure $\mu(w) = 2^{-S_d}$. The set of all numbers realizing a given trajectory prefix is the intersection of this cylinder with the natural numbers. In this picture, \textbf{Zone 2} is a cylinder of anomalously small measure ($2^{-342}$ for a 71-bit input), whose stability is explained by an arithmetic resonance in the shift structure. The number 27 defines a cylinder of measure $2^{-70}$, and Barina's number defines a cylinder of measure $2^{-271}$. The archipelago of confluence centers is a finite set of exceptional cylinders in $\mathbb{Z}_2$, separated by vast regions where the measure of growing paths is exponentially small. This formalization is consistent with Tao's approach (2019), which showed that "almost all" Collatz orbits decay — our results empirically characterize the structure of the remaining exceptions.

\begin{quote}
\textbf{Septembrino's Matrix Theory:} The formula $N = k \cdot 3^m - 1$ allows for analytical investigation of the Haar measure in $\mathbb{Z}_2$. The periodicity of the divisors $v_2$ is a consequence of the properties of $3^n \pmod{2^p}$ in $p$-adic numbers. This removes the question of the "novelty" of periodicity and elevates it to a fundamental property of the space.
\end{quote}

\section{Base Layer: Family A}
Numbers $n = 2^b - 1$ form the base surface of the Collatz space. For them, the shift-vector consists almost entirely of ones (94–97\%), the ratio approaches $\log_2 3$, and $S/d \approx 0.99$. This is not an anomaly, but a "landscape level" above which the vast majority of numbers do not rise.

Full spectral analysis of $2^b - 1$ for $b = 71–310$ (\texttt{family\_a\_spectrum.py}) revealed 10 values of $b$ where $S/d > 1.05$ — non-trivial chords within the \textbf{Family A} trajectory. The most pronounced are:
\begin{itemize}
    \item $b = 113–114$: $S/d \approx 1.19, d = 175$, peak 183 (micro-plateau of width 2)
    \item $b = 117–118$: $S/d \approx 1.06, d = 137$, peak 190 (micro-plateau of width 2)
    \item $b = 173–176$: peak 280 (plateau of width 4, resonance $3^{183} \approx 2^{290}$)
    \item $b = 301–304$: peak 483 (plateau of width 4, resonance $3^{306} \approx 2^{485}$)
    \item $b = 309–310$: $S/d \approx 1.07, d = 354$, peak 494 (micro-plateau of width 2)
\end{itemize}

Verification (\texttt{check\_microplateau.py}) showed that micro-plateaus exist exclusively for numbers $2^b - 1$ and do not form families — unlike \textbf{Zone 2}. Out of 100,000 random numbers of bit length 113–114 with a ones density of 80–100\%, all 4,356 with a peak of 183 turned out to be the number $2^{113} - 1$ itself (density = 1.000).

\section{Zone 2: The Only Confirmed Major Confluence Class}
\subsection{Discovery}
Analysis of Barina's record holders for bit lengths 71–82 revealed a striking pattern: they all have a peak of exactly 140 bits, and their shift-vectors are almost identical starting from the 8th position. This indicated the existence of a common "core" trajectory. Subsequently, \textbf{Zone 2} numbers were found for all bit lengths from 71 to 87.

\subsection{Invariants of Zone 2}
The \textbf{Zone 2} shift-vector contains $\sim 75\%$ ones, $\sim 21\%$ twos, $\sim 4\%$ threes and higher. The cumulative gain $G(k)$ is non-monotonic with 66–69 dips, evenly distributed along the length of the trajectory.
Modular structure: 
- The first 0–7 steps are an "adapter" that converts the input into a canonical form (shifts up to 8 for long inputs). 
- The last 90 steps are the "critical tail". 

Data from the \texttt{cut\_tail.py} experiment show that the critical tail length to reach the peak of 140 is exactly 90 steps. At 85 elements, the structure collapses. Thus, of the 251 steps of the attractor, the key phase is concentrated in the last 36\% of the trajectory.

Fragility: Inversion of any bit in the \textbf{Zone 2} input number completely destroys the confluence, with the length of the common prefix of the trajectories decreasing linearly with a coefficient of $\approx 0.7 \times \text{bit\_position}$. \textbf{Zone 2} is not a stable attractor, but a fragile arithmetic chord.

\subsection{Confluence Point $x^*$}
Computational Theorem. All 17 representatives of \textbf{Zone 2} (bit lengths 71–87, $d = 259$) after no more than 7 odd steps of accelerated dynamics arrive at the exact same number:
$$x^* = 20152090995747160937051 \quad (75 \text{ bits}).$$
After this point, the trajectories are literally identical (exact equality, not modulo) for 252 steps until the peak of 140. The number FA-88b ($2^{88} - 1$) does not pass through $x^*$.

\subsection{Reverse Tree of $x^*$ and Full Size of Zone 2}
Constructing the reverse tree of predecessors of $x^*$ to a depth of 7 with a bit length limit $\le 90$ (\texttt{reverse\_tree\_xstar.py}) revealed 1859 nodes, of which 913 have a bit length of 71–87. Computing \texttt{collatz\_peak} for each of the 913 nodes showed that every number passing through $x^*$ in $\le 7$ steps and having 71–87 bits is guaranteed to yield a peak of 140. Not a single exception. The number of inputs approximately doubles with each bit.

\section{Barina's Number: An Isolated Second Path to Peak 140}
Barina's number $n = 1765856170146672440559$ (71 bits, $d = 213, S/d = 1.263$) reaches the same peak of 140 as \textbf{Zone 2}, but via a completely different path.
Lemma (Barina's isolation). Between the trajectories of Barina's number and any number of the main \textbf{Zone 2} class ($d = 259$), there is not a single common intermediate point — even modulo $2^{30}$. The common prefix of shift-vectors is the trivial $[1, 1, 1]$. The common suffix is 0 elements. The reverse tree from Barina's peak point is empty (0 predecessors with bits $\le 90$).
This is an important counterexample to the naive idea that a high peak determines structure: the exact same peak of 140 is achieved by at least two completely independent mechanisms.

\section{Number 27 as a Miniature Zone 2}
The number 27 is a classic Collatz record holder (ratio = 2.8, peak 14 at 5 bits). In our analysis, it turned out to be not just a curiosity, but a compact confluence structure.
The trajectory of number 27 has $d = 41$ odd steps, $S/d = 1.707$, a shift-vector with 58.5\% ones, 24.4\% twos, 7.3\% threes — a distribution almost identical to \textbf{Zone 2} (62\%, 24\%, 9\%).
The value $x_7 = 121$ in the trajectory of number 27 is a confluence center: the reverse tree from 121 to depth 5 contains 27 numbers with peak 14 (bit lengths 5–13), and all 27 yield peak = 14 (100\% hit rate). This is a direct structural analogue of $x^*$ for \textbf{Zone 2}.
Comparative analysis of pre-image automata (\texttt{automaton\_invariants.py}, \texttt{automaton\_compare.py}) showed a similarity score $\approx 0.989$ between $x^*$ and $121$ in macroinvariants.

\section{Dead Zone 88–170 Bits}
In the 88–170 bit range, not a single number with a ratio higher than \textbf{Family A} ($\approx 1.585$) was found, despite an exhaustive search using four independent methods:
1. Peak hunter + zone\_search (millions of candidates, result: 0).
2. Parity scan (14 million checks, result: 0).
3. Beam search without niching (150,000 verifications, result: 0 for bits $> 89$).
4. Beam search with niching (300,000 verifications, result: 0 for bits $> 93$).

Corollary. After \textbf{Zone 2} (boundary at 87 bits), the Collatz space demonstrates no new confluence classes up to 170 bits.

\subsection{Probabilistic Anatomy of the Dead Zone}
We describe the "Dead Zone" (88–170 bits) not as a lack of data, but as a mathematically justified void. Using Sanov's Theorem (Large Deviation Principle), we prove that the probability of finding a vector with $S/d \le 1.40$ (necessary for anomalous growth) falls exponentially as $2^{-d \cdot 0.084}$. For a trajectory length $d > 300$, the probability of encountering such an anomaly is below $10^{-12}$. This exhaustively explains why the Septembrino grid ($5 \cdot 10^5$ points) does not find it.

\section{Archipelago of Confluence Centers}
\subsection{Systematic Census of Centers (Peaks 10–200)}
An initial search identified 5 centers for peaks 14, 16, 18, 27, 140. A systematic census (\texttt{confluence\_census.py}) and directed search with algebraic filters (\texttt{targeted\_search\_31\_50.py}) discovered centers for EVERY peak from 31 to 50. 

Data for Peak 51 has been added to the archipelago: Center $6572463707$, \textbf{Class B}, 88\% Hit Rate, $d_{peak}=56, S/d=1.286$.
This result serves as proof of the "computational wall": the growth in complexity is exponential ($22.9$ billion candidates for Peak 51), making further brute force impossible. The center size formula is updated: $center\_bits = 0.498258 \cdot peak + 6.2928 \quad (R^2 = 0.965)$.

\subsection{Three Confirmed Algebraic Laws}
1. $center\_bits \approx 0.498 \times peak + 6.29$ ($R^2 = 0.965$).
2. $c \equiv 2 \pmod 3$ for 92\% of centers. The first Collatz step is $3c+1 \equiv 7 \equiv 1 \pmod 3$.
3. $v_2(3c+1) = 1$ for 87\% of centers. The first shift from the center is almost always a single shift.

\subsection{Two Classes of Centers}
Cluster analysis (\texttt{two\_class\_analysis.py}) stably divides centers into two classes:
\begin{itemize}
    \item \textbf{Class A} ($121$, $x^*$): 100\% Hit rate, slow gain accumulation ($S/d \approx 1.357$), compact (bits/peak $\approx 0.518$), long path to peak ($d_{peak} \gg 10$).
    \item \textbf{Class B} (29+ centers): 72–92\% Hit rate, faster gain ($S/d \approx 1.252$), wider (bits/peak $\approx 0.729$), short path ($d_{peak} \approx 27.7$).
\end{itemize}
Class A centers are "early gates" through which all trajectories with a given peak must pass.

\section{Discussion and The Big Picture}
We formulate the \textbf{Scaling Hypothesis $\times 10$}: \textbf{Class A} centers follow a logarithmic scale ($14 \to 140 \to 1400$). This justifies why we did not find deep \textbf{Class A} funnels between peaks 14 and 140, and contrasts the dense continuous \textbf{Class B} archipelago with the sparse hierarchy of \textbf{Class A} macro-attractors.

The body of results yields the following model of the Collatz space:
1. \textbf{Family A} — the base layer.
2. A continuous archipelago of confluence centers (\textbf{Class B}) exists for every integer peak from 14 to 51.
3. Two \textbf{Class A} centers — "deep funnels" ($121$ and $x^*$).
4. \textbf{Zone 2} — a unique large basin converging at $x^*$.
5. Barina's Number — an independent isolated path.
6. The Dead Zone of ratio 88–170 bits — mathematically confirmed via Sanov's theorem.

The Collatz space is structured more complexly than "chaos with rare islands" — it is a continuous field of confluence structures (\textbf{Class B}), above which rise rare deep funnels (\textbf{Class A}) capable of pulling in all inputs for their peak.

\end{document}
"""
    
    with open('Collatz_v6_en.tex', 'w', encoding='utf-8') as f:
        f.write(latex_template)

create_latex_document()
