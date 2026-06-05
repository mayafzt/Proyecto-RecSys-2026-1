# Runbook Midterm Escalado (Entrega manana 20:00)

Objetivo: correr mas volumen hoy en paralelo, dejando trazabilidad y resultados comparables.

## Requisitos

- Dataset en `data/spotify_dataset.csv`
- Entorno Python con `requirements.txt`
- Al menos un equipo con 32 GB RAM

## Variables del pipeline

- `MIDTERM_SAMPLE_PERCENT`: porcentaje de playlists por hash (ej. 30)
- `MIDTERM_MAX_SAMPLE_PLAYLISTS`: tope de playlists de la muestra (0 = sin tope)
- `MIDTERM_MAX_EVAL_PLAYLISTS`: playlists evaluadas en leave-last-out
- `MIDTERM_OUTPUT_PREFIX`: nombre base de salida (`.csv` y `.md`)
- `LASTFM_API_KEY`: opcional para activar senal LastFM

## Plan recomendado para HOY (paralelo)

### Equipo A (32 GB RAM) - corrida principal comparable con Hito 1

```powershell
$env:MIDTERM_SAMPLE_PERCENT="30"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="0"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="63851"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_midterm_30_full"
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

Si se queda sin memoria, fallback inmediato:

```powershell
$env:MIDTERM_SAMPLE_PERCENT="30"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="45000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="45000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_midterm_30_fallback"
python hito2_spotify_lastfm_midterm.py
```

### Equipo B - corrida de sensibilidad

```powershell
$env:MIDTERM_SAMPLE_PERCENT="20"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="30000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="30000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_midterm_20_sens"
Remove-Item Env:LASTFM_API_KEY -ErrorAction SilentlyContinue
python hito2_spotify_lastfm_midterm.py
```

### Equipo C (si existe) - corrida con LastFM

```powershell
$env:MIDTERM_SAMPLE_PERCENT="20"
$env:MIDTERM_MAX_SAMPLE_PLAYLISTS="20000"
$env:MIDTERM_MAX_EVAL_PLAYLISTS="20000"
$env:MIDTERM_OUTPUT_PREFIX="resultados_hito2_midterm_20_lastfm"
$env:LASTFM_API_KEY="TU_API_KEY"
python hito2_spotify_lastfm_midterm.py
```

## Que archivos debes traer de cada equipo

- `resultados_hito2_midterm_*.csv`
- `resultados_hito2_midterm_*.md`

## Criterio para elegir resultado principal del informe

1. Priorizar corrida con mayor cobertura de playlists evaluadas sin fallas.
2. Mantener comparabilidad con Hito 1 (ideal: 30%).
3. Reportar una corrida principal y una de sensibilidad para robustez.

## Comando rapido para ver resumen en consola

```powershell
Get-ChildItem resultados_hito2_midterm_*.csv | Select-Object Name,Length,LastWriteTime
```
