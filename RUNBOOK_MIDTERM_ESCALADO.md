# Runbook Final (Paper + Poster)

Objetivo: cerrar la entrega final con comparaciones metodologicas mas fuertes, ablations por senal, analisis por segmentos, ejemplos cualitativos y metricas de diversidad/novedad.

## Requisitos

- Dataset en `data/spotify_dataset.csv`
- Entorno Python con `requirements.txt`
- Recomendado: ejecutar primero una corrida smoke para validar outputs

## Variables del pipeline

- `MIDTERM_SAMPLE_PERCENT`: porcentaje de playlists por hash (ej. 30)
- `MIDTERM_MAX_SAMPLE_PLAYLISTS`: tope de playlists de la muestra (0 = sin tope)
- `MIDTERM_MAX_EVAL_PLAYLISTS`: playlists evaluadas en leave-last-out
- `MIDTERM_OUTPUT_PREFIX`: nombre base de salida
- `MIDTERM_ENABLE_LASTFM`: `1` para activar senal LastFM (por defecto `0`)
- `MIDTERM_LASTFM_MAX_CALLS`: limite duro de llamadas API LastFM (por defecto `1500`)
- `LASTFM_API_KEY`: API key de LastFM cuando se habilita la senal

## Corrida smoke (obligatoria antes de larga)

```powershell
$env:MIDTERM_SAMPLE_PERCENT="10"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="3000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="1500"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_final_smoke"
Remove-Item Env:MIDTERM_ENABLE_LASTFM -ErrorAction SilentlyContinue
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

Outputs esperados:

- `resultados_hito2_final_smoke.csv`
- `resultados_hito2_final_smoke.md`
- `resultados_hito2_final_smoke_ejemplos.csv`
- `resultados_hito2_final_smoke_segmentos.csv`

## Plan recomendado final (sin dependencia de LastFM)

### Corrida principal (paper/poster)

```powershell
$env:MIDTERM_SAMPLE_PERCENT="30"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="0"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="63851"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_final_30_full"
Remove-Item Env:MIDTERM_ENABLE_LASTFM -ErrorAction SilentlyContinue
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

Si hay limitacion de RAM/tiempo, fallback inmediato:

```powershell
$env:MIDTERM_SAMPLE_PERCENT="30"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="45000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="45000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_final_30_fallback"
Remove-Item Env:MIDTERM_ENABLE_LASTFM -ErrorAction SilentlyContinue
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

### Corrida de sensibilidad

```powershell
$env:MIDTERM_SAMPLE_PERCENT="20"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="30000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="30000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_final_20_sens"
Remove-Item Env:MIDTERM_ENABLE_LASTFM -ErrorAction SilentlyContinue
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

### Corrida opcional de ablacion LastFM (acotada)

```powershell
$env:MIDTERM_SAMPLE_PERCENT="20"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="20000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="20000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_final_20_lastfm_ablation"
$env:MIDTERM_ENABLE_LASTFM="1"
$env:MIDTERM_LASTFM_MAX_CALLS="1500"
$env:LASTFM_API_KEY="TU_API_KEY"
python hito2_spotify_lastfm_midterm.py
```

Nota: LastFM se usa solo como analisis de ablacion, no como dependencia de la corrida principal.

## Que archivos debes traer de cada equipo

- `resultados_hito2_final_*.csv`
- `resultados_hito2_final_*.md`
- `resultados_hito2_final_*_ejemplos.csv`
- `resultados_hito2_final_*_segmentos.csv`

## Generar seccion final en LaTeX automaticamente

Cuando elijan la corrida ganadora (por ejemplo `resultados_hito2_final_30_full.csv`), generar la seccion final asi:

```powershell
python generar_seccion_resultados_midterm.py `
	--csv resultados_hito2_final_30_full.csv `
	--output seccion_resultados_midterm_auto.tex `
	--sample-percent 30 `
	--eval-playlists 63851
```

Luego en el informe principal pueden insertar:

```tex
\input{seccion_resultados_midterm_auto.tex}
```

## Criterio para elegir resultado principal del informe

1. Priorizar corrida con mayor cobertura de playlists evaluadas sin fallas.
2. Mantener comparabilidad con Hito 1 (ideal: 30%).
3. Incluir comparaciones fuertes: `Sequential Markov`, `Collaborative ItemKNN`, `Two-Stage Hybrid`.
4. Reportar ablations por senal: `cooc`, `pop`, `artist`, `name` y `lastfm` (si se activa).
5. Incluir diversidad (`ILD@10`), novedad (`Novelty@10`), segmentos y ejemplos cualitativos.

## Comando rapido para ver resumen en consola

```powershell
Get-ChildItem resultados_hito2_final_*.csv | Select-Object Name,Length,LastWriteTime
```

## Checklist final paper/poster

1. Tabla principal con todos los modelos y metricas top-10 + diversidad/novedad.
2. Figura o tabla corta de ablations (caida respecto al modelo principal).
3. Tabla por segmentos: tamano de playlist x popularidad del target.
4. Minimo 5 ejemplos cualitativos de recomendaciones (incluyendo aciertos y errores).
5. Declarar explicitamente que LastFM quedo como analisis opcional/acotado por costo-tiempo.
