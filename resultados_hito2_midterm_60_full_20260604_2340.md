# Resultados Midterm Hito 2 - Spotify + LastFM

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: 10
- Playlists evaluadas: 120,000
- Catalogo train: 1,807,375 items
- LastFM activo (API key en entorno): False

## Modelos comparados

- Random
- Most Popular
- Playlist Name Popular
- Two-Stage Cooc+Rerank
- Two-Stage + LastFM

## Resultados

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| Random | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Most Popular | 0.0009 | 0.0001 | 0.0001 | 0.0003 |
| Playlist Name Popular | 0.0138 | 0.0014 | 0.0048 | 0.0069 |
| Two-Stage Cooc+Rerank | 0.1460 | 0.0146 | 0.0814 | 0.0965 |
| Two-Stage + LastFM | 0.1460 | 0.0146 | 0.0814 | 0.0965 |
