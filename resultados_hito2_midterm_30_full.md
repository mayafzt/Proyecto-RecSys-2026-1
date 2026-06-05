# Resultados Midterm Hito 2 - Spotify + LastFM

## Configuracion

- Split: leave-last-out por playlist (minimo 3 canciones).
- Top-K: 10
- Playlists evaluadas: 63,851
- Catalogo train: 1,226,786 items
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
| Most Popular | 0.0011 | 0.0001 | 0.0001 | 0.0004 |
| Playlist Name Popular | 0.0125 | 0.0012 | 0.0046 | 0.0064 |
| Two-Stage Cooc+Rerank | 0.1210 | 0.0121 | 0.0648 | 0.0778 |
| Two-Stage + LastFM | 0.1210 | 0.0121 | 0.0648 | 0.0778 |
