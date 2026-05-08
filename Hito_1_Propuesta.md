# Hito 1: Propuesta, analisis y baselines

**Pontificia Universidad Catolica de Chile**  
**Curso:** IIC3633 Sistemas Recomendadores  
**Periodo:** Marzo-Julio 2026  
**Integrantes:** Agustin Llambias, Amaya Quero, Larry Uribe

## Titulo tentativo

Recomendacion musical personalizada usando playlists de Spotify.

## Descripcion del problema y justificacion

Los servicios de musica digital concentran catalogos muy grandes, por lo que un usuario puede tener dificultades para descubrir canciones alineadas con sus gustos o con el contexto de escucha que desea. En este proyecto se aborda un problema de recomendacion musical personalizada a partir de playlists: dado un conjunto de canciones ya presentes en una playlist, recomendar canciones candidatas que podrian completar o enriquecer esa playlist.

El dataset utilizado es Spotify Playlists de Kaggle, disponible en https://www.kaggle.com/datasets/andrewmvd/spotify-playlists. El archivo local utilizado es `data/spotify_dataset.csv`, con columnas `user_id`, `artistname`, `trackname` y `playlistname`. Cada registro indica que una cancion de un artista aparece en una playlist asociada a un usuario. Como no existen ratings explicitos, se interpreta la aparicion de una cancion en una playlist como feedback implicito positivo.

## Objetivos

El objetivo general es construir y evaluar un sistema de recomendacion musical para completar playlists de Spotify, comparando baselines simples con metodos personalizados bajo un protocolo reproducible de evaluacion offline.

Objetivos especificos:

- Caracterizar el dataset mediante analisis descriptivo de usuarios, artistas, canciones, playlists e interacciones.
- Definir un protocolo train/test para evaluar recomendacion top-N a nivel de playlist.
- Implementar al menos tres modelos de referencia: Random, Most Popular y un modelo especifico al dominio de playlists.
- Comparar los modelos usando HitRate@10, Precision@10, MAP@10 y nDCG@10.
- Desarrollar en Midterm un metodo mas avanzado, como filtrado colaborativo item-item, factorizacion matricial implicita o un enfoque hibrido basado en texto de playlists y co-ocurrencia de canciones.

## Analisis descriptivo

El archivo completo contiene:

- 12.199.339 registros validos.
- 15.889 usuarios.
- 271.369 artistas.
- 1.854.175 nombres de tracks.
- 2.614.129 items unicos definidos como par artista-cancion.
- 225.591 playlists usuario-nombre.

Para este Hito 1 se trabajo con una muestra deterministica del 30% de las playlists, preservando playlists completas mediante hashing de `user_id` y `playlistname`. Esta decision se justifica porque el CSV pesa aproximadamente 1,18 GB y el objetivo del hito es exploratorio: entender los datos, validar un protocolo de evaluacion e implementar baselines iniciales. La muestra es reproducible y suficientemente grande para observar patrones robustos.

Para procesar el archivo se utilizo DuckDB en vez de cargar el CSV completo directamente con pandas. DuckDB es una base de datos analitica embebida orientada a ejecutar consultas SQL eficientes sobre archivos locales. En este proyecto se uso para calcular estadisticas globales del CSV completo y construir la muestra reproducible del 30% sin materializar inicialmente los 12,2 millones de filas como un unico DataFrame en memoria. Luego se uso pandas para la evaluacion de baselines y visualizaciones.

La muestra contiene 3.721.218 registros, 12.745 usuarios, 150.326 artistas, 947.293 tracks, 1.273.839 items artista-cancion y 68.012 playlists. La mediana de canciones por playlist es 11 y el promedio es 54,71, lo que evidencia alta variabilidad en el tamano de playlists. Ademas, la distribucion de popularidad de canciones tiene cola larga: pocas canciones aparecen en muchas playlists y la mayoria aparece pocas veces.

## Baselines y protocolo experimental

La evaluacion usa un esquema leave-last-out por playlist. Para cada playlist con al menos tres canciones, se oculta la ultima cancion como item de test y se usan las canciones previas como contexto de entrenamiento. El modelo debe recomendar un ranking top-10 de canciones candidatas no vistas en esa playlist.

Se evaluaron 63.851 playlists de la muestra, con un catalogo de entrenamiento de 1.258.737 items.

Baselines implementados:

- **Random:** recomienda canciones aleatorias no presentes en la playlist.
- **Most Popular:** recomienda las canciones mas frecuentes del conjunto de entrenamiento, excluyendo las ya presentes en la playlist.
- **Playlist Name Popular:** usa tokens del nombre de la playlist para recomendar canciones populares en playlists con nombres similares. Es especifico al problema, porque explota informacion contextual de playlists.

Resultados preliminares:

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| Random | 0,0000 | 0,0000 | 0,0000 | 0,0000 |
| Most Popular | 0,0011 | 0,0001 | 0,0001 | 0,0004 |
| Playlist Name Popular | 0,0119 | 0,0012 | 0,0041 | 0,0058 |

Los resultados muestran que el baseline basado en nombre de playlist supera a Random y Most Popular en todas las metricas. Aunque los valores absolutos son bajos, esto es esperable por el tamano del catalogo y por la dificultad del protocolo: se intenta predecir una cancion especifica entre mas de un millon de candidatos.

## Planificacion Midterm

| Fecha | Actividad | Resultado esperado |
| --- | --- | --- |
| 08/05 | Cierre Hito 1 | Propuesta, EDA y baselines iniciales documentados. |
| 09/05 - 16/05 | Limpieza y normalizacion | Pipeline reproducible, validacion de muestra y matriz playlist-cancion. |
| 17/05 - 24/05 | Filtrado colaborativo | Modelos item-item basados en co-ocurrencia de canciones en playlists. |
| 25/05 - 31/05 | Metodo avanzado | Factorizacion matricial implicita o modelo hibrido texto + co-ocurrencia. |
| 01/06 - 04/06 | Evaluacion y analisis | Tabla comparativa, cobertura, analisis de errores y sensibilidad a muestra. |
| 05/06 | Entrega Midterm | Informe intermedio con resultados preliminares. |

## Limitaciones y riesgos

La principal limitacion del Hito 1 es el uso de una muestra del 30%. Esta muestra es suficientemente grande para analisis preliminar, pero no reemplaza una evaluacion final sobre el dataset completo o sobre varias muestras. Para mitigar este riesgo, la muestra se construyo de manera deterministica y preservando playlists completas.

Otra limitacion es que el dataset no incluye audio features, generos ni ratings explicitos. Por ello, los modelos iniciales dependen de popularidad, co-ocurrencia y texto de playlists. En Midterm se evaluaran metodos colaborativos mas fuertes y posibles enriquecimientos de contenido si existe una fuente confiable para cruzar metadatos.

## Bibliografia

- Andrew Mvd. Spotify Playlists. Kaggle. https://www.kaggle.com/datasets/andrewmvd/spotify-playlists
- Raasveldt, M. y Muhleisen, H. DuckDB: An Embeddable Analytical Database. CIDR, 2020. https://duckdb.org/library/duckdb/
- DuckDB Documentation. CSV Import. https://duckdb.org/docs/stable/data/csv/overview
- Koren, Y., Bell, R. y Volinsky, C. Matrix factorization techniques for recommender systems. Computer, 42(8), 30-37, 2009.
- Ricci, F., Rokach, L. y Shapira, B. Recommender Systems Handbook. Springer, 2015.
- He, X., Deng, K., Wang, X., Li, Y., Zhang, Y. y Wang, M. LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation. SIGIR, 2020.
