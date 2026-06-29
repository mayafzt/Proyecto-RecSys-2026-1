# Resultados Finales APC - Spotify

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: 10
- Playlists evaluadas: 63,851
- Catalogo train: 1,226,786 items
- LastFM activo: False
- LastFM llamadas usadas: 0 / 0

## Modelos comparados

- Baselines: Random, Most Popular, Playlist Name Popular.
- Comparadores mas fuertes: Sequential Markov, Collaborative ItemKNN.
- Metodo principal y ablations: Two-Stage Hybrid + variantes sin cada senal.

## Resultados

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 | ILD@10 | Novelty@10 | CatalogCoverage@10 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: | ---: |
| Sequential Markov | 0.1257 | 0.0126 | 0.0813 | 0.0919 | 0.9752 | 16.5699 | 0.0910 |
| Two-Stage Hybrid | 0.1254 | 0.0125 | 0.0684 | 0.0817 | 0.6151 | 18.8468 | 0.1566 |
| Ablation sin pop | 0.1239 | 0.0124 | 0.0679 | 0.0810 | 0.6194 | 19.1389 | 0.1620 |
| Ablation sin name | 0.1176 | 0.0118 | 0.0631 | 0.0758 | 0.6373 | 18.8606 | 0.1527 |
| Ablation sin artist | 0.1143 | 0.0114 | 0.0619 | 0.0740 | 0.6774 | 18.9800 | 0.1541 |
| Collaborative ItemKNN | 0.0966 | 0.0097 | 0.0551 | 0.0647 | 0.7392 | 19.0408 | 0.1447 |
| Ablation sin cooc | 0.0387 | 0.0039 | 0.0162 | 0.0214 | 0.5394 | 16.0911 | 0.0740 |
| Playlist Name Popular | 0.0123 | 0.0012 | 0.0046 | 0.0064 | 0.6715 | 16.5373 | 0.0623 |
| Most Popular | 0.0011 | 0.0001 | 0.0001 | 0.0004 | 1.0000 | 12.8632 | 0.0000 |
| Random | 0.0000 | 0.0000 | 0.0000 | 0.0000 | 0.9998 | 20.7408 | 0.4057 |

## Archivos para paper/poster

- Tabla principal: resultados_hito2_final_30_full.csv
- Ejemplos cualitativos (recomendaciones y perfiles): resultados_hito2_final_30_full_ejemplos.csv
- Analisis por segmentos (tamano playlist x popularidad objetivo): resultados_hito2_final_30_full_segmentos.csv
