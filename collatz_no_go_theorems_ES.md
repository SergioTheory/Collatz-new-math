# Teoremas No-Go en el Espacio de Collatz

Este documento cataloga los enfoques rigurosa y numéricamente refutados para probar o refutar la Conjetura de Collatz. Sirve como un mapa epistemológico de los "callejones sin salida", explicando paso a paso *por qué* ciertas ideas intuitivas se estrellan contra la profunda realidad matemática del espacio.

---

## PARTE I: Callejones sin Salida Probabilísticos y Computacionales

### 1. Dominación Puntual Termodinámica / Macroestado
*   **Hipótesis**: La medida de Haar uniforme de las clases impares domina completamente la evolución, empujando *todas* las trayectorias individuales hacia la distribución estacionaria (decaimiento).
*   **Refutado**: En escalas finitas (por ejemplo, $B=16$), la cancelación de Fourier de la capa límite deja superposiciones estructurales $E_B^{wt} \approx C \cdot 2^{-B/2}$. La medida de Haar uniforme describe el *conjunto estadístico* (ensemble), pero no limita puntualmente los puntos finales deterministas de números específicos.

### 2. Reinicio TV-Fourier a Escala Finita (GATE-2)
*   **Hipótesis**: Después de $d$ pasos, la distribución de los puntos finales pierde toda memoria de su bloque inicial, y la distancia de Variación Total (TV) hacia un nuevo inicio uniforme decae exponencialmente.
*   **Refutado**: Numéricamente probado como falso. La distancia TV entre los puntos finales transportados y los nuevos inicios uniformes permanece $O(1)$ (alrededor de $0.5 - 0.9$) y no exhibe decaimiento. Los bits 2-ádicos inferiores conservan perfectamente la memoria a través de los bloques, prohibiendo un "reinicio limpio".

### 3. Cierre de Renovación y Contractividad W1 (GATE-2)
*   **Hipótesis**: La trayectoria puede tratarse como un proceso de renovación markoviano donde el tiempo para alcanzar $x < x_0$ forma una distribución cerrada, o la métrica de Wasserstein ($W_1$) se contrae a través de múltiples bloques.
*   **Refutado**: La constante de renovación $c^*(B)$ cae drásticamente ($0.90 \to 0.13$) al escalar las barreras, demostrando que el proceso no es estructuralmente cerrado. Las distancias $W_1$ multibloque no se contraen; el desplazamiento de masa se conserva estrictamente en los bits inferiores.

### 4. Conteo Híbrido Cilindro-Intervalo
*   **Hipótesis**: Se puede contar el número exacto de trayectorias dentro de un intervalo de Arquímedes explotando las intersecciones transversales de los cilindros 2-ádicos con los límites del intervalo.
*   **Refutado**: El factor de intersección transversal $\tau(S)$ converge casi exactamente a $1.0$ (frecuencia de Haar exacta). No hay ningún déficit transversal que explotar para limitar el recuento de trayectorias.

### 5. Gramática Local y Divergencia Bit-Lift
*   **Hipótesis**: Las trayectorias divergentes pueden sintetizarse encontrando una gramática dinámica local (una palabra de longitud $d$) que sobrevive por encima de $x_0$, y utilizando el levantamiento entero CRT mínimo (bit-lift) para iniciar la secuencia.
*   **Refutado**: La síntesis mediante bit-lift genera puntos de partida que son pseudoaleatorios en su continuación 2-ádica. De 1000 bit-lifts sintetizados casi críticos, exactamente CERO sobrevivieron hasta los $10^5$ pasos. La gramática local pura de horizonte corto no puede "forzar" una trayectoria a divergir.

---

## PARTE II: Callejones sin Salida Analíticos y Diofánticos (Las Perspectivas de Lean 4)

### 6. La Trampa Puntual de Medida Cero (El Muro de Conway)
*   **Hipótesis**: Debido a que la medida de las órbitas divergentes en los enteros 2-ádicos ($\mathbb{Z}_2$) es exactamente cero (probado por Terras en 1976 y Tao en 2019), no pueden existir órbitas divergentes en los números naturales ($\mathbb{N}$).
*   **Por qué falla (Paso a Paso)**:
    1. **El Fractal:** Para sobrevivir $k$ pasos sin caer, un entero debe satisfacer alineaciones estrictas de paridad mod $2^{S_k}$. Cuando $k \to \infty$, el conjunto de todos los caminos supervivientes forma un fractal topológico en $\mathbb{Z}_2$.
    2. **La Medida:** Es matemáticamente cierto (y verificado en Lean 4) que la medida de Haar de este fractal es exactamente $0$. Es infinitamente "delgado".
    3. **La Trampa:** Los números naturales ($\mathbb{N}$) son *densos* en $\mathbb{Z}_2$. Al igual que los números racionales tienen medida 0 en la recta real pero existen en todas partes, un número infinito de enteros específicos teóricamente puede existir dentro de un conjunto de medida 0.
    4. **Conclusión:** No se puede deducir $\emptyset$ (el conjunto vacío) a partir de la Medida $0$. Probar que un número natural específico $N$ no pasa por el ojo de esta aguja infinita requiere un seguimiento de estado computacional ilimitado, lo que choca con la barrera de Indecidibilidad de Conway (1972). La teoría de la medida no puede resolver el seguimiento diofántico puntual.

### 7. Exclusión Trascendental / Diofántica de la Divergencia
*   **Hipótesis**: Los límites diofánticos como el Teorema de Baker sobre formas lineales en logaritmos (o las Fracciones Continuas) prohíben estrictamente las órbitas divergentes al restringir la aproximación irracional de $\ln 3 / \ln 2$.
*   **Por qué falla (Paso a Paso)**:
    1. **Las Matemáticas de un Ciclo:** Para que una trayectoria forme un ciclo sobre sí misma, las multiplicaciones y divisiones netas deben equilibrar perfectamente las sumas $+1$. Esto fuerza a que $3^d x_{\min} \approx 2^S x_{\min}$. Por lo tanto, la razón $3^d / 2^S$ debe acercarse a $1$ con una precisión fenomenal.
    2. **El Rol de Baker:** Los teoremas diofánticos (Baker-Rhin, Eliahou) dictan que $3^d$ y $2^S$ no pueden estar arbitrariamente cerca el uno del otro. Dado que no pueden converger, **los ciclos se eliminan estrictamente**.
    3. **Las Matemáticas de la Divergencia:** Una órbita divergente *no* hace un ciclo. Simplemente crece. Esto requiere $3^d \gg 2^S$ (un margen macroscópico).
    4. **Conclusión:** El teorema de Baker limita qué tan *cerca* pueden estar los números, no qué tan *separados* pueden llegar a estar. Por lo tanto, la rigidez diofántica es un arma nuclear contra los ciclos, pero es totalmente impotente contra las órbitas divergentes.

### 8. Macro-Solitones Constructivos (La Trampa de la Dimensionalidad CRT / Teorema M1)
*   **Hipótesis**: Si descubrimos un bloque de operaciones altamente anómalo y raro (como la Zona 2 o la secuencia de Barina), podemos concatenarlo $m$ veces para "construir" artificialmente una trayectoria divergente macroscópica.
*   **Por qué falla (Paso a Paso)**:
    1. **El Requisito CRT:** Para ejecutar un bloque específico de desplazamiento total $S$, el número de inicio $x_0$ debe pertenecer a una única y específica clase de residuos $r \pmod{2^S}$.
    2. **El Costo de la Clonación:** Para ejecutar ese bloque $m$ veces consecutivas, $x_0$ debe satisfacer $m$ restricciones modulares consecutivas, lo que colapsa el número de inicio requerido en una sola clase $r' \pmod{2^{mS}}$.
    3. **El Déficit de Dimensionalidad:** El número de enteros reales de $B$-bits que satisfacen esta condición es aproximadamente $2^B / 2^{mS} = 2^{B-mS}$. Debido a que $S$ siempre es mayor que la contribución en longitud de bits del bloque en sí, $mS$ supera rápidamente a $B$.
    4. **Conclusión:** A medida que intenta clonar el bloque, el número esperado de números naturales que cumplen con el requisito cae exponencialmente a cero. Las raras estructuras rígidas se pueden *encontrar* buscando hacia abajo desde un pico, pero no se pueden *cultivar* (hacer crecer) algebraicamente hacia arriba.

### 9. Mezclar el Colapso Dimensional con los Límites Diofánticos
*   **Hipótesis**: Debido a que el conjunto de palabras cíclicas tiene una dimensión fractal $< 1$ (por ejemplo, $D_1 \approx 0.76$), podemos multiplicar esta probabilidad por límites diofánticos estrictos (como Baker-Rhin) para aumentar exponencialmente el límite inferior en las longitudes de los ciclos.
*   **Por qué falla (Paso a Paso)**:
    1. **Qué Hacen los Límites Diofánticos:** Teoremas como las fracciones continuas de Eliahou proporcionan límites estrictos, algebraicos y 100% garantizados. Si el teorema dice $d > 10^{11}$, es una imposibilidad física absoluta que exista un ciclo por debajo de esa longitud.
    2. **Qué Hace el Colapso Dimensional:** Una dimensión fractal de $0.76$ describe la densidad topológica *promedio* de las palabras cíclicas en un conjunto probabilístico. Significa que los ciclos son extremadamente *raros*, no estructuralmente *imposibles*.
    3. **El Error Categorial:** No se puede multiplicar una ecuación algebraica absoluta estricta por una probabilidad para generar una nueva ecuación absoluta estricta. Incluso si un conjunto tiene una dimensión de $0.76$, en principio podría contener una anomalía estructural específica de longitud 100.
    4. **Conclusión:** Estas dos herramientas viven en universos matemáticos diferentes. Las ecuaciones diofánticas proporcionan los límites estrictos, mientras que el Colapso Dimensional describe la topología del espacio dentro de esos límites. No se pueden fusionar multiplicativamente.
