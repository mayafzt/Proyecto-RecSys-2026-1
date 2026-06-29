# Hallazgos Finales para Poster y Paper

## 1) Mensaje principal
El sistema Two-Stage Hybrid logra rendimiento competitivo en HitRate@10 y mejora fuerte en cobertura y novedad frente a comparadores simples, mientras que Sequential Markov lidera en MAP@10 y nDCG@10.

## 2) Resultados principales (corrida 30 full)

- Two-Stage Hybrid: HitRate@10=12.54%, MAP@10=6.84%, nDCG@10=8.17%, ILD@10=0.615, Novelty@10=18.847, CatalogCoverage@10=15.66%.
- Sequential Markov: HitRate@10=12.57%, MAP@10=8.13%, nDCG@10=9.19%, CatalogCoverage@10=9.10%.
- Collaborative ItemKNN: HitRate@10=9.66%, MAP@10=5.51%, CatalogCoverage@10=14.47%.

Comparaciones directas relevantes:
- Hybrid vs ItemKNN: HitRate@10 +2.88 pp, MAP@10 +1.34 pp, Cobertura +1.19 pp.
- Hybrid vs Markov: HitRate@10 -0.02 pp, MAP@10 -1.29 pp, nDCG@10 -1.01 pp, Cobertura +6.56 pp.

## 3) Ablations (aporte de senales)

Caida de MAP@10 respecto de Two-Stage Hybrid:
- Sin cooc: -5.22 pp
- Sin artist: -0.65 pp
- Sin name: -0.53 pp
- Sin pop: -0.05 pp

Interpretacion corta:
- Cooc es la senal estructural mas critica (mayor caida al removerla).
- Artist y name aportan mejora incremental importante en ranking.
- Popularidad tiene efecto menor en MAP@10, pero ayuda en estabilidad de cobertura.

## 4) Analisis por segmentos

- Head + short playlists: HitRate@10=28.70%, MAP@10=16.59%.
- Head + medium playlists: HitRate@10=28.72%, MAP@10=16.18%.
- Tail + long playlists: HitRate@10=0.59%, MAP@10=0.22%.
- Hallazgo: el modelo rinde muy bien en head/mid y cae fuerte en tail, lo que abre espacio para mejoras de long-tail en trabajo futuro.

## 5) Robustez (20 sens)

- Two-Stage Hybrid mantiene desempeno competitivo en sensibilidad: HitRate@10=9.34%, MAP@10=4.57%. 
- El orden relativo principal se mantiene: Markov fuerte en precision/ranking y Hybrid fuerte en cobertura/novedad.

## 6) Ejemplos cualitativos para poster

Ejemplo con error (hit@10=0):
- Playlist: "HARD ROCK 2010"
- Perfil: size=long; target_pop=tail
- Target: "cocktail slippers" - "you do run"
- Top-10: "lissie" - "look away" | "lissie" - "loosen the knot" | "crowded house" - "it's only natural" | "crowded house" - "everything is good for you" | "lissie" - "stranger" | "lissie" - "bully" | "joshua radin" - "only you - imogen heap mix" | "elvis costello & the attractions" - "big boys" | "joshua radin" - "free of me" | "crowded house" - "fingers of love"

## 7) Texto sugerido para conclusiones del paper

Nuestros resultados muestran que una arquitectura de dos etapas basada en co-ocurrencia y reranking logra un balance competitivo entre exactitud y cobertura del catalogo. En particular, el sistema propuesto iguala o supera a comparadores colaborativos simples en HitRate@10 y mejora de forma consistente la novedad y cobertura, mientras que un baseline secuencial tipo Markov conserva ventaja en MAP@10 y nDCG@10. Las ablaciones confirman que la co-ocurrencia es la senal mas determinante del pipeline, seguida por las senales de artista y nombre de playlist. Finalmente, el analisis por segmentos evidencia que el metodo funciona mejor en objetivos de popularidad alta/media y playlists cortas/medias, manteniendo como desafio abierto el desempeno sobre cola larga.