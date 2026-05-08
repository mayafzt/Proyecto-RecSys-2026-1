# Resultados preliminares Hito 1 - Spotify Playlists

## Dataset completo

- Registros: 12,199,339
- Usuarios: 15,889
- Artistas: 271,369
- Tracks por nombre: 1,854,175
- Items artista-track: 2,614,129
- Playlists usuario-nombre: 225,591

## Muestra utilizada

Para este Hito 1 se uso una muestra deterministica del 30% de las playlists, preservando playlists completas mediante hashing de `user_id` y `playlistname`. Esto reduce el costo computacional sobre un CSV de 1.18 GB, mantiene reproducibilidad y es suficiente para el objetivo del hito: exploracion preliminar e implementacion de baselines.

- Registros en muestra: 3,721,218
- Usuarios en muestra: 12,745
- Playlists en muestra: 68,012
- Items artista-track en muestra: 1,273,839
- Mediana de canciones por playlist: 16.0
- Promedio de canciones por playlist: 54.71

## Evaluacion

Para cada playlist con al menos 3 canciones, se oculto la ultima cancion como test y se entreno con el resto.

- Playlists evaluadas: 63,851
- Catalogo de entrenamiento: 1,258,737 items

## Baselines

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| Random | 0.0000 | 0.0000 | 0.0000 | 0.0000 |
| Most Popular | 0.0011 | 0.0001 | 0.0001 | 0.0004 |
| Playlist Name Popular | 0.0119 | 0.0012 | 0.0041 | 0.0058 |
