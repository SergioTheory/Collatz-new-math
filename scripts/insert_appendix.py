import os

def insert_appendix(filename, is_ru=False):
    with open(filename, 'r', encoding='utf-8') as f:
        content = f.read()
        
    marker = r"\section*{Data Availability" if not is_ru else r"\section*{Доступность данных"
    
    if is_ru:
        appendix_text = r"""
\appendix
\section{Природа Инстантона (Экспедиция B)}
Здесь мы формализуем инстантон Zone 2 как возмущение 2-адической неподвижной точки.

\begin{lemma}[2-адический вакуум]
Пусть $I_a(x) = \frac{2^a x - 1}{3}$ --- обратный шаг, и $I = I_1 \circ I_1 \circ I_2$ (композиция, сопряженная прямому паттерну $(2,1,1)$). Тогда $I$ является сжатием на $\mathbb{Z}_2$ с коэффициентом $2^{-4}$ и, по теореме Банаха, имеет единственную неподвижную точку $\xi \in \mathbb{Z}_2$. Алгебраически $\xi = -29/11$, что порождает периодическую обратную орбиту с точной плотностью $S/d = 4/3$. Любая конечная обратная орбита, тенирующая $\xi$ с точностью $2^{-m}$ на $d$ шагах, имеет $S/d = 4/3 + O(1/d) + O(2^{-m})$.
\end{lemma}

\begin{lemma}[Баланс gain/заряды]
Для любого shift-вектора $w$ длины $d$ с суммой $S = \frac{4}{3}d + \delta$, где $\delta$ --- суммарный избыток сдвигов относительно вакуума, суммарный gain равен $G(d) = d(\log_2 3 - 4/3) - \delta$. Для компенсации граничных условий $G^* = P - B$ требуется суммарный «заряд» $\delta = d(\log_2 3 - 4/3) - (P - B)$.
Для ядра Zone 2 ($d=251$, $P-B \approx 68.4$) наблюдается $\delta \approx -0.67$, что подтверждает малую плотность дефектов.
\end{lemma}

\textbf{Открытый вопрос (Гипотеза B3: центр как log-середина).} Эмпирически для центров Класса A (полные воронки) выполняется $bits(c) \approx P/2 + 6.5$. Предполагается, что центр --- это глубочайший общий узел, в котором мера цилиндра еще достаточна для захвата всех входов. Численный тест на 34 подтвержденных центрах показывает среднее отклонение $\approx 6.75$, в то время как переходные центры (HR $< 1$) значительно отклоняются (среднее $\approx 4.4$), что делает $\alpha = 1/2$ маркером полной конфлюэнтности.

"""
    else:
        appendix_text = r"""
\appendix
\section{Nature of the Instanton (Expedition B)}
Here we formalize the Zone 2 instanton as a perturbation of a 2-adic fixed point.

\begin{lemma}[2-adic vacuum]
Let $I_a(x) = \frac{2^a x - 1}{3}$ be the inverse step, and $I = I_1 \circ I_1 \circ I_2$ (the composition conjugate to the forward pattern $(2,1,1)$). Then $I$ is a contraction on $\mathbb{Z}_2$ with ratio $2^{-4}$ and by Banach's fixed-point theorem has a unique fixed point $\xi \in \mathbb{Z}_2$. Algebraically $\xi = -29/11$, which generates a periodic inverse orbit with exact density $S/d = 4/3$. Any finite inverse orbit shadowing $\xi$ to precision $2^{-m}$ over $d$ steps has $S/d = 4/3 + O(1/d) + O(2^{-m})$.
\end{lemma}

\begin{lemma}[Gain/charge balance]
For any shift vector $w$ of length $d$ with sum $S = \frac{4}{3}d + \delta$, where $\delta$ is the total excess of shifts relative to the vacuum, the total gain is $G(d) = d(\log_2 3 - 4/3) - \delta$. To match the boundary conditions $G^* = P - B$, a total ``charge'' $\delta = d(\log_2 3 - 4/3) - (P - B)$ is required.
For the Zone 2 core ($d=251$, $P-B \approx 68.4$), we observe $\delta \approx -0.67$, confirming the low defect density.
\end{lemma}

\textbf{Open Question (Hypothesis B3: center as log-midpoint).} Empirically, for Class A centers (complete funnels), $bits(c) \approx P/2 + 6.5$. We conjecture that the center is the deepest common node where the cylinder measure is still sufficient to capture all inputs. Numerical tests on 34 confirmed centers show a stable offset of $\approx 6.75$, whereas transitional centers (HR $< 1$) deviate significantly (mean $\approx 4.4$), making $\alpha = 1/2$ a marker of complete confluence.

"""
    
    if marker in content:
        new_content = content.replace(marker, appendix_text + marker)
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(new_content)
        print(f"Successfully inserted appendix into {filename}")
    else:
        print(f"Marker not found in {filename}")

if __name__ == "__main__":
    insert_appendix("C:\\Users\\Admin\\Documents\\Collatz\\docs\\Collatz_v11_en.tex", is_ru=False)
    insert_appendix("C:\\Users\\Admin\\Documents\\Collatz\\docs\\Collatz_v11_ru.tex", is_ru=True)
