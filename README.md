# Proyecto IIC3633 - Sistemas Recomendadores

Pontificia Universidad Catolica de Chile  
Marzo-Julio 2026

**Integrantes:** Agustin Llambias, Amaya Quero, Larry Uribe

Este repositorio contiene el avance del Hito 1 del proyecto: recomendacion musical personalizada usando playlists de Spotify.

Ademas, incluye el avance de Hito 2 (midterm): enfoque de dos etapas para Automatic Playlist Continuation con enriquecimiento opcional desde LastFM.

## Archivos principales

- `Informe_Hito_1_Overleaf.tex`: informe en LaTeX listo para compilar en Overleaf.
- `Informe_Hito_2_Midterm_Overleaf.tex`: informe Midterm (Hito 2) en LaTeX, con metodologia especifica retrieval + reranking.
- `Hito_1_Propuesta.md`: version Markdown de la propuesta.
- `Hito_1_Spotify.ipynb`: notebook ejecutado del pipeline final con Spotify Playlists.
- `hito1_spotify_baselines.py`: script reproducible con EDA, muestra del 30%, baselines y figuras.
- `hito2_spotify_lastfm_midterm.py`: script de Midterm con metodo principal two-stage (co-ocurrencia + reranking) y senal LastFM opcional.
- `resultados_hito1_spotify.md`: resumen de resultados generado por el script.
- `resultados_hito1_spotify.csv`: tabla de metricas exportada.
- `resultados_hito2_midterm.md`: resumen de resultados del pipeline de Midterm.
- `resultados_hito2_midterm.csv`: tabla de metricas del pipeline de Midterm.
- `figures/`: figuras usadas por el informe LaTeX.
- `prompts_ia_hito1.md`: resumen de prompts usados para documentar apoyo de IA.
- `requirements.txt`: dependencias Python usadas por el pipeline.
- `Enunciado_Proyecto_Final_RecSys_2026_1.pdf`: enunciado del proyecto.

## Dataset

Fuente: [Spotify Playlists en Kaggle](https://www.kaggle.com/datasets/andrewmvd/spotify-playlists).

El archivo activo es:

```text
data/spotify_dataset.csv
```

El CSV no se versiona en Git porque pesa aproximadamente 1.18 GB. Para este Hito 1 se usa una muestra deterministica del 30% de playlists, preservando playlists completas mediante hashing de `user_id` y `playlistname`. La justificacion esta documentada en el informe.

## Por que DuckDB

El pipeline usa DuckDB para leer y consultar el CSV completo antes de pasar a pandas. La razon es que el archivo tiene 12.2M filas y pesa aproximadamente 1.18 GB; cargarlo completo como un unico DataFrame no es necesario para el Hito 1 y puede ser lento o inestable en memoria.

DuckDB permite ejecutar consultas SQL analiticas directamente sobre archivos CSV locales, por lo que se usa para:

- calcular estadisticas globales del dataset completo;
- construir una muestra deterministica del 30% preservando playlists completas;
- evitar materializar todo el CSV en memoria antes de reducir la escala.

Despues de esa reduccion, pandas se usa para baselines, metricas y figuras.

Referencias:

- Raasveldt, M. y Muhleisen, H. DuckDB: An Embeddable Analytical Database. CIDR, 2020. https://duckdb.org/library/duckdb/
- DuckDB Documentation. CSV Import. https://duckdb.org/docs/stable/data/csv/overview

## Baselines

- Random
- Most Popular
- Playlist Name Popular

## Reproduccion

1. Descargar el dataset desde Kaggle.
2. Dejar el CSV como `data/spotify_dataset.csv`.
3. Instalar dependencias:

```powershell
python -m pip install -r requirements.txt
```

4. Ejecutar:

```powershell
python hito1_spotify_baselines.py
```

Para Midterm (Hito 2):

```powershell
python hito2_spotify_lastfm_midterm.py
```

Opcional: activar enriquecimiento LastFM configurando API key en el entorno antes de ejecutar:

```powershell
$env:LASTFM_API_KEY="TU_API_KEY"
python hito2_spotify_lastfm_midterm.py
```

5. Revisar:

```text
resultados_hito1_spotify.md
resultados_hito1_spotify.csv
figures/
```

Para compilar el informe en Overleaf, subir `Informe_Hito_1_Overleaf.tex` junto con la carpeta `figures/`.

Para el informe Midterm, subir `Informe_Hito_2_Midterm_Overleaf.tex` junto con los archivos de resultados que se quieran citar en el documento.

## Uso de IA

Se utilizo IA generativa como apoyo para estructurar el informe, revisar cumplimiento del enunciado, depurar/verificar codigo, justificar el uso de DuckDB y preparar el formato LaTeX. Las decisiones metodologicas, seleccion del dataset, interpretacion de resultados y validacion final son responsabilidad del grupo.

Las conversaciones compartidas y prompts sinteticos estan documentados en `prompts_ia_hito1.md`. URLs principales:

- Revision del enunciado y checklist: https://chatgpt.com/share/69fe7497-b264-83e9-af99-d39056a4bdc1
- Actualizacion al dataset Spotify: https://chatgpt.com/share/69fe757d-a82c-83e9-ba6e-c106809575d2
- Procesamiento eficiente del CSV y figuras: https://chatgpt.com/share/69fe74e5-c4d0-83e9-911f-0ecdaddd7898
- Implementacion y verificacion de baselines: https://chatgpt.com/share/69fe7523-8ac0-83e9-a7c6-0a46f9c092a0
