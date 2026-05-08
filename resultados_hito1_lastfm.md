# Resultados preliminares Hito 1 - Last.fm

## Dataset

- Registros: 166,153
- Usuarios: 11
- Artistas: 22,823
- Tracks unicos por nombre: 67,241
- Items unicos artista-track: 76,038
- Albumes: 38,629
- Duplicados exactos: 0
- Albumes faltantes: 12
- Rango temporal: 2021-01-01 00:02:00 a 2021-01-31 23:59:00
- Sparsity usuario-item: 0.8411

## Evaluacion

Se uso split temporal por usuario con 80% de interacciones para train y 20% para test. Para evaluar recomendacion de descubrimiento, los items relevantes del test son canciones futuras que el usuario no habia escuchado en train.

- Filas de train: 132,919
- Usuarios evaluados: 11
- Items relevantes promedio por usuario: 2291.18

## Baselines

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| Random | 0.3636 | 0.0364 | 0.0074 | 0.0310 |
| Most Popular | 0.0909 | 0.0455 | 0.0202 | 0.0367 |
| Favorite Artist Popular | 0.4545 | 0.0455 | 0.0133 | 0.0459 |
