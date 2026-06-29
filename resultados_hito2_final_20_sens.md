# Resultados Finales APC - Spotify

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: 10
- Playlists evaluadas: 28,065
- Catalogo train: 696,943 items
- LastFM activo: False
- LastFM llamadas usadas: 0 / 0

## Modelos comparados

- Baselines: Random, Most Popular, Playlist Name Popular.
- Comparadores mas fuertes: Sequential Markov, Collaborative ItemKNN.
- Metodo principal y ablations: Two-Stage Hybrid + variantes sin cada senal.

## Resultados

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 | ILD@10 | Novelty@10 | CatalogCoverage@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sequential Markov | 0.0931 | 0.0093 | 0.0618 | 0.0693 | 0.9849 | 16.0352 | 0.0844 |
| Two-Stage Hybrid | 0.0934 | 0.0093 | 0.0457 | 0.0568 | 0.6613 | 18.3108 | 0.1419 |
| Ablation sin pop | 0.0925 | 0.0092 | 0.0451 | 0.0562 | 0.6656 | 18.5525 | 0.1459 |
| Ablation sin name | 0.0839 | 0.0084 | 0.0403 | 0.0504 | 0.6832 | 18.3241 | 0.1382 |
| Ablation sin artist | 0.0802 | 0.0080 | 0.0392 | 0.0487 | 0.7242 | 18.4328 | 0.1385 |
| Collaborative ItemKNN | 0.0642 | 0.0064 | 0.0333 | 0.0405 | 0.7903 | 18.3220 | 0.1254 |
| Ablation sin cooc | 0.0322 | 0.0032 | 0.0143 | 0.0184 | 0.5680 | 15.8100 | 0.0705 |
| Playlist Name Popular | 0.0104 | 0.0010 | 0.0032 | 0.0049 | 0.6849 | 16.3732 | 0.0631 |
| Most Popular | 0.0004 | 0.0000 | 0.0001 | 0.0001 | 1.0000 | 12.9614 | 0.0000 |
| Random | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.9999 | 19.7528 | 0.3319 |

## Archivos para paper/poster

- Tabla principal: resultados_hito2_final_20_sens.csv
- Ejemplos cualitativos (recomendaciones y perfiles): resultados_hito2_final_20_sens_ejemplos.csv
- Analisis por segmentos (tamano playlist x popularidad objetivo): resultados_hito2_final_20_sens_segmentos.csv
