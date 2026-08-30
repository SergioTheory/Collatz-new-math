# Théorèmes No-Go dans l'Espace de Collatz

Ce document catalogue les approches rigoureusement et numériquement réfutées pour prouver ou infirmer la conjecture de Collatz. Il sert de carte épistémologique des "impasses", expliquant étape par étape *pourquoi* certaines idées intuitives se brisent contre la profonde réalité mathématique de l'espace.

---

## PARTIE I : Impasses Probabilistes et Computationnelles

### 1. Domination Ponctuelle Thermodynamique / Macro-état
*   **Hypothèse** : La mesure de Haar uniforme des classes impaires domine complètement l'évolution, poussant *toutes* les trajectoires individuelles vers la distribution stationnaire (déclin).
*   **Réfuté** : À des échelles finies (par exemple, $B=16$), l'annulation de Fourier de la couche limite laisse des chevauchements structurels $E_B^{wt} \approx C \cdot 2^{-B/2}$. La mesure de Haar uniforme décrit l'*ensemble* statistique, mais ne limite pas ponctuellement les points finaux déterministes de nombres spécifiques.

### 2. Redémarrage TV-Fourier à Échelle Finie (GATE-2)
*   **Hypothèse** : Après $d$ étapes, la distribution des points finaux perd toute mémoire de son bloc de départ, et la distance de Variation Totale (TV) vers un nouveau redémarrage uniforme décroît exponentiellement.
*   **Réfuté** : Numériquement prouvé faux. La distance TV entre les points finaux transportés et les nouveaux départs uniformes reste $O(1)$ (autour de $0.5 - 0.9$) et ne présente aucune décroissance. Les bits 2-adiques de poids faible conservent parfaitement la mémoire à travers les blocs, interdisant une "table rase".

### 3. Clôture de Renouvellement et Contractivité W1 (GATE-2)
*   **Hypothèse** : La trajectoire peut être traitée comme un processus de renouvellement markovien où le temps pour atteindre $x < x_0$ forme une distribution fermée, ou la métrique de Wasserstein ($W_1$) se contracte à travers de multiples blocs.
*   **Réfuté** : La constante de renouvellement $c^*(B)$ chute drastiquement ($0.90 \to 0.13$) lors du franchissement des barrières d'échelle, prouvant que le processus n'est pas structurellement fermé. Les distances $W_1$ multi-blocs ne se contractent pas ; le déplacement de masse est strictement préservé dans les bits inférieurs.

### 4. Comptage Hybride Cylindre-Intervalle
*   **Hypothèse** : On peut compter le nombre exact de trajectoires à l'intérieur d'un intervalle archimédien en exploitant les intersections transversales des cylindres 2-adiques avec les limites de l'intervalle.
*   **Réfuté** : Le facteur d'intersection transversale $\tau(S)$ converge presque exactement vers $1.0$ (fréquence de Haar exacte). Il n'y a aucun déficit transversal à exploiter pour limiter le comptage des trajectoires.

### 5. Grammaire Locale et Divergence Bit-Lift
*   **Hypothèse** : Les trajectoires divergentes peuvent être synthétisées en trouvant une grammaire dynamique locale (un mot de longueur $d$) qui survit au-dessus de $x_0$, et en utilisant le soulèvement entier TRC minimum (bit-lift) pour démarrer la séquence.
*   **Réfuté** : La synthèse via bit-lift génère des points de départ qui sont pseudo-aléatoires dans leur continuation 2-adique. Sur 1000 bit-lifts synthétisés quasi-critiques, exactement ZÉRO ont survécu jusqu'à $10^5$ étapes. La grammaire locale pure à horizon court ne peut pas "forcer" une trajectoire à diverger.

---

## PARTIE II : Impasses Analytiques et Diophantiennes (Les Découvertes de Lean 4)

### 6. Le Piège Ponctuel de la Mesure Nulle (Le Mur de Conway)
*   **Hypothèse** : Parce que la mesure des orbites divergentes dans les entiers 2-adiques ($\mathbb{Z}_2$) est exactement zéro (prouvé par Terras en 1976 et Tao en 2019), les orbites divergentes dans les entiers naturels ($\mathbb{N}$) ne peuvent pas exister.
*   **Pourquoi cela échoue (Étape par Étape)** :
    1. **Le Fractal :** Pour survivre $k$ étapes sans chuter, un entier doit satisfaire à des alignements stricts de parité mod $2^{S_k}$. Quand $k \to \infty$, l'ensemble de tous les chemins survivants forme un fractal topologique dans $\mathbb{Z}_2$.
    2. **La Mesure :** Il est mathématiquement vrai (et vérifié dans Lean 4) que la mesure de Haar de ce fractal est exactement $0$. Il est infiniment "fin".
    3. **Le Piège :** Les entiers naturels ($\mathbb{N}$) sont *denses* dans $\mathbb{Z}_2$. Tout comme les nombres rationnels ont une mesure 0 sur la droite réelle mais existent partout, un nombre infini d'entiers spécifiques peut théoriquement exister à l'intérieur d'un ensemble de mesure 0.
    4. **Conclusion :** On ne peut pas déduire $\emptyset$ (l'ensemble vide) de la Mesure $0$. Prouver qu'un entier naturel spécifique $N$ ne passe pas par le chas de cette aiguille infinie nécessite un suivi d'état computationnel illimité, ce qui se heurte à la barrière de l'Indécidabilité de Conway (1972). La théorie de la mesure ne peut pas résoudre le suivi diophantien ponctuel.

### 7. Exclusion Transcendante / Diophantienne de la Divergence
*   **Hypothèse** : Les bornes diophantiennes comme le Théorème de Baker sur les formes linéaires de logarithmes (ou les Fractions Continues) interdisent strictement les orbites divergentes en restreignant l'approximation irrationnelle de $\ln 3 / \ln 2$.
*   **Pourquoi cela échoue (Étape par Étape)** :
    1. **Les Mathématiques d'un Cycle :** Pour qu'une trajectoire boucle sur elle-même (cycle), les multiplications et divisions nettes doivent parfaitement équilibrer les additions $+1$. Cela force $3^d x_{\min} \approx 2^S x_{\min}$. Par conséquent, le rapport $3^d / 2^S$ doit s'approcher de $1$ avec une précision phénoménale.
    2. **Le Rôle de Baker :** Les théorèmes diophantiens (Baker-Rhin, Eliahou) dictent que $3^d$ et $2^S$ ne peuvent pas être arbitrairement proches l'un de l'autre. Puisqu'ils ne peuvent pas converger, **les cycles sont strictement tués**.
    3. **Les Mathématiques de la Divergence :** Une orbite divergente ne boucle *pas*. Elle croît simplement. Cela nécessite $3^d \gg 2^S$ (une marge macroscopique).
    4. **Conclusion :** Le théorème de Baker limite la *proximité* des nombres, non leur *éloignement*. Par conséquent, la rigidité diophantienne est une arme nucléaire contre les cycles, mais elle est totalement impuissante contre les orbites divergentes.

### 8. Macro-Solitons Constructifs (Le Piège de la Dimensionnalité CRT / Théorème M1)
*   **Hypothèse** : Si nous découvrons un bloc d'opérations hautement anormal et rare (comme la Zone 2 ou la séquence de Barina), nous pouvons le concaténer $m$ fois pour "construire" artificiellement une trajectoire divergente macroscopique.
*   **Pourquoi cela échoue (Étape par Étape)** :
    1. **L'Exigence du TRC (Théorème des Restes Chinois) :** Pour exécuter un bloc spécifique de décalage total $S$, le nombre de départ $x_0$ doit appartenir à une seule classe de résidus spécifique $r \pmod{2^S}$.
    2. **Le Coût du Clonage :** Pour exécuter ce bloc $m$ fois de suite, $x_0$ doit satisfaire à $m$ contraintes modulaires consécutives, ce qui réduit le nombre de départ requis à une seule classe $r' \pmod{2^{mS}}$.
    3. **Le Déficit de Dimensionnalité :** Le nombre d'entiers réels de $B$-bits satisfaisant cette condition est d'environ $2^B / 2^{mS} = 2^{B-mS}$. Parce que $S$ est toujours plus grand que la contribution en longueur de bits du bloc lui-même, $mS$ dépasse rapidement $B$.
    4. **Conclusion :** Au fur et à mesure que vous essayez de cloner le bloc, le nombre attendu d'entiers naturels qui remplissent la condition chute exponentiellement à zéro. Les structures rigides rares peuvent être *trouvées* en cherchant vers le bas depuis un sommet, mais elles ne peuvent pas être *cultivées* (développées) algébriquement vers le haut.

### 9. Mélanger le Collapsus Dimensionnel avec les Bornes Diophantiennes
*   **Hypothèse** : Parce que l'ensemble des mots cycliques a une dimension fractale $< 1$ (par exemple, $D_1 \approx 0.76$), nous pouvons multiplier cette probabilité par des limites diophantiennes strictes (comme Baker-Rhin) pour augmenter exponentiellement la limite inférieure sur les longueurs de cycle.
*   **Pourquoi cela échoue (Étape par Étape)** :
    1. **Ce que font les Bornes Diophantiennes :** Les théorèmes comme les fractions continues d'Eliahou fournissent des limites strictes, algébriques et garanties à 100%. Si le théorème dit $d > 10^{11}$, il est d'une impossibilité physique absolue qu'un cycle existe en dessous de cette longueur.
    2. **Ce que fait le Collapsus Dimensionnel :** Une dimension fractale de $0.76$ décrit la densité topologique *moyenne* des mots cycliques dans un ensemble probabiliste. Cela signifie que les cycles sont extrêmement *rares*, et non structurellement *impossibles*.
    3. **L'Erreur Catégorielle :** Vous ne pouvez pas multiplier une équation algébrique absolue stricte par une probabilité pour générer une nouvelle équation absolue stricte. Même si un ensemble a une dimension de $0.76$, il pourrait, en principe, contenir une anomalie structurelle spécifique de longueur 100.
    4. **Conclusion :** Ces deux outils vivent dans des univers mathématiques différents. Les équations diophantiennes fournissent les limites strictes, tandis que le Collapsus Dimensionnel décrit la topologie de l'espace à l'intérieur de ces limites. Ils ne peuvent pas être fusionnés de manière multiplicative.
