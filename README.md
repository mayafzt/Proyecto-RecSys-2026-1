# Proyecto IIC3633 - Sistemas Recomendadores

Pontificia Universidad Catolica de Chile  
Marzo-Julio 2026

**Integrantes:** Agustin Llambias, Amaya Quero, Larry Uribe

Este repositorio contiene el avance del Hito 1 del proyecto: recomendacion musical personalizada usando playlists de Spotify.

Ademas, incluye la version final de Hito 2 para Automatic Playlist Continuation (APC), con comparaciones metodologicas mas fuertes, ablations por senal, analisis por segmentos y ejemplos cualitativos.

## Archivos principales

- `Informe_Hito_1_Overleaf.tex`: informe en LaTeX listo para compilar en Overleaf.
- `Informe_Hito_2_Midterm_Overleaf.tex`: informe Midterm (Hito 2) en LaTeX, con metodologia especifica retrieval + reranking.
- `Hito_1_Propuesta.md`: version Markdown de la propuesta.
- `Hito_1_Spotify.ipynb`: notebook ejecutado del pipeline final con Spotify Playlists.
- `hito1_spotify_baselines.py`: script reproducible con EDA, muestra del 30%, baselines y figuras.
- `hito2_spotify_lastfm_midterm.py`: script APC final con baselines, comparadores fuertes (secuencial y colaborativo), modelo two-stage hibrido, ablations por senal, metricas de diversidad/novedad y export de ejemplos/segmentos.
- `resultados_hito1_spotify.md`: resumen de resultados generado por el script.
- `resultados_hito1_spotify.csv`: tabla de metricas exportada.
- `resultados_hito2_midterm.md`: resumen de resultados del pipeline APC.
- `resultados_hito2_midterm.csv`: tabla de metricas del pipeline APC.
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

Para APC final (Hito 2):

```powershell
python hito2_spotify_lastfm_midterm.py
```

Opcional: activar senal LastFM de forma acotada (solo para ablacion), configurando variables de entorno antes de ejecutar:

```powershell
$env:MIDTERM_ENABLE_LASTFM="1"
$env:MIDTERM_LASTFM_MAX_CALLS="1500"
$env:LASTFM_API_KEY="TU_API_KEY"
python hito2_spotify_lastfm_midterm.py
```

Variables utiles del pipeline APC:

- `MIDTERM_SAMPLE_PERCENT`
- `MIDTERM_MAX_SAMPLE_PLAYLISTS`
- `MIDTERM_MAX_EVAL_PLAYLISTS`
- `MIDTERM_OUTPUT_PREFIX`
- `MIDTERM_ENABLE_LASTFM`
- `MIDTERM_LASTFM_MAX_CALLS`

5. Revisar:

```text
resultados_hito1_spotify.md
resultados_hito1_spotify.csv
figures/
```

Para compilar el informe en Overleaf, subir `Informe_Hito_1_Overleaf.tex` junto con la carpeta `figures/`.

Para el informe Midterm/final, subir `Informe_Hito_2_Midterm_Overleaf.tex` junto con los archivos de resultados que se quieran citar en el documento.

Archivos de salida APC final:

- `{prefix}.csv`: tabla principal con metricas de ranking, diversidad y novedad.
- `{prefix}.md`: resumen legible para el informe.
- `{prefix}_ejemplos.csv`: ejemplos cualitativos de recomendaciones y perfiles.
- `{prefix}_segmentos.csv`: desempeno por segmento (tamano de playlist y popularidad del target).

## Uso de IA

De acuerdo con la politica del curso, se permite el uso de modelos de lenguaje como apoyo en el desarrollo de las evaluaciones, siempre que no reemplacen el trabajo de los estudiantes y que su uso sea citado junto con los enlaces a las conversaciones correspondientes.

En este proyecto, la IA se uso como apoyo para revisar cumplimiento del enunciado, mejorar redaccion tecnica y realizar revision focalizada de codigo. Las decisiones metodologicas, la implementacion del pipeline, la ejecucion experimental y la validacion final de resultados fueron realizadas por el equipo.

Documentacion de prompts:

- Hito 1: `prompts_ia_hito1.md`
- Hito 2: `prompts_ia_hito2.md`

Links compartidos (Hito 2):

- GPT - checklist de cumplimiento H2: https://chatgpt.com/share/6a231209-00d8-83e9-9b47-af6bf766130f
- GPT - revision metodologica APC: https://chatgpt.com/share/6a231279-57c8-83e9-a121-f4a0b2c40d96
- GPT - apoyo redaccion/compactacion: https://chatgpt.com/share/6a2312f0-c50c-83e9-b915-75fadc5af70c
- Gemini - checklist de cumplimiento H2: https://gemini.google.com/share/92eda9e80714
- Gemini - revision metodologica APC: https://gemini.google.com/share/c7a08a7cbfb8
- Gemini - apoyo redaccion/compactacion: https://gemini.google.com/share/349243cd448f

Links compartidos (Hito 2, revision parcial de codigo):

- GPT - revision de funciones claves: https://chatgpt.com/share/6a231747-8fe4-83e9-ab2d-b75b42c7c85c
- Gemini - code review focalizado: https://gemini.google.com/share/6c68fb1a7981
