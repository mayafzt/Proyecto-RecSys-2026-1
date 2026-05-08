# Proyecto IIC3633 - Sistemas Recomendadores

Este repositorio contiene el avance del Hito 1 del proyecto del curso.

**Curso:** Sistemas recomendadores  
**Integrantes:** Agustin Llambias, Amaya Quero, Larry Uribe

## Archivos principales

- `Hito_1_Propuesta.md`: propuesta escrita para el Hito 1, incluyendo problema, objetivos, baselines, plan Midterm y bibliografia.
- `Informe_Hito_1_Overleaf.tex`: informe en LaTeX listo para compilar en Overleaf.
- `Informe H1.pdf`: PDF compilado del informe para entrega.
- `figures/`: figuras usadas por el informe LaTeX.
- `Hito_1_LastFM.ipynb`: notebook principal ejecutado con el dataset real de Last.fm.
- `Hito_1.ipynb`: notebook preliminar original del dominio musical.
- `hito1_lastfm_baselines.py`: script reproducible con EDA basico y baselines sobre el CSV real de Last.fm.
- `resultados_hito1_lastfm.md`: resultados generados por el script.
- `resultados_hito1_lastfm.csv`: tabla de metricas exportada desde el notebook.
- `Nube.png`: visualizacion generada durante el analisis exploratorio.
- `Enunciado_Proyecto_Final_RecSys_2026_1.pdf`: enunciado del proyecto.

## Baselines preliminares

El notebook contiene el analisis del dataset utilizado y los primeros modelos:

- Random
- Most Popular
- Favorite Artist Popular

## Dataset

Fuente propuesta para la entrega: [Last.FM_dataset en Kaggle](https://www.kaggle.com/datasets/harshal19t/lastfm-dataset).

El dataset fue descargado con `kagglehub` y copiado a `data/Last.fm_data.csv`. Los archivos grandes del dataset no se versionan en Git.

> Nota de consistencia: el notebook original fue escrito para un CSV musical normalizado con columnas tipo `user_id`, `artist_name`, `track_name` y, cuando existe, `playlist_name`. El script `hito1_lastfm_baselines.py` ya trabaja con las columnas reales de Last.fm: `Username`, `Artist`, `Track`, `Album`, `Date` y `Time`.

## Reproduccion

1. Descargar el dataset desde Kaggle o usar `kagglehub.dataset_download("harshal19t/lastfm-dataset")`.
2. Dejar el CSV como `data/Last.fm_data.csv`.
3. Ejecutar `jupyter nbconvert --to notebook --execute Hito_1_LastFM.ipynb --inplace`.
4. Alternativamente, ejecutar `python hito1_lastfm_baselines.py`.
5. Revisar `resultados_hito1_lastfm.md` y la propuesta `Hito_1_Propuesta.md`.

Para compilar el informe en Overleaf, subir `Informe_Hito_1_Overleaf.tex` junto con la carpeta `figures/`.
