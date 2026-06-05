# Resultados Midterm Hito 2 - Spotify + LastFM

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: 10
- Playlists evaluadas: 3,000
- Catalogo train: 120,591 items
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
| Most Popular | 0.0010 | 0.0001 | 0.0003 | 0.0004 |
| Playlist Name Popular | 0.0043 | 0.0004 | 0.0010 | 0.0017 |
| Two-Stage Cooc+Rerank | 0.0257 | 0.0026 | 0.0073 | 0.0115 |
| Two-Stage + LastFM | 0.0257 | 0.0026 | 0.0073 | 0.0115 |
