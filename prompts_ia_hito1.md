# Prompts sinteticos usados con IA - Hito 1

Estos prompts resumen el uso de IA generativa como apoyo durante el Hito 1. La IA se uso para estructurar, revisar y verificar; las decisiones metodologicas y la interpretacion final fueron realizadas por el grupo.

1. **Revision del enunciado y checklist**

   > Revisa el PDF del enunciado del proyecto y compara sus requisitos para el Hito 1 con los archivos actuales del repositorio. Indica que falta, que esta cubierto y que deberia transformarse en informe escrito.

   https://chatgpt.com/share/69fe7497-b264-83e9-af99-d39056a4bdc1

2. **Actualizacion al dataset definitivo**

   > Actualiza el proyecto para usar el dataset Spotify Playlists de Kaggle (`andrewmvd/spotify-playlists`) ubicado en `data/spotify_dataset.csv`. Revisa columnas, estructura del archivo y adapta el enfoque del Hito 1 al problema de recomendacion de canciones para completar playlists.

   https://chatgpt.com/share/69fe757d-a82c-83e9-ba6e-c106809575d2

3. **Procesamiento eficiente del CSV grande**

   > El CSV pesa aproximadamente 1.18 GB y tiene millones de filas. Propone una estrategia reproducible para calcular estadisticas globales y generar una muestra del 30% de playlists completas sin cargar todo el archivo en memoria con pandas.

   https://chatgpt.com/share/69fe74e5-c4d0-83e9-911f-0ecdaddd7898

4. **Implementacion y verificacion de baselines**

   > Implementa un script reproducible que calcule EDA, construya una muestra deterministica del 30% preservando playlists, evalue Random, Most Popular y un baseline especifico basado en nombre de playlist usando HitRate@10, Precision@10, MAP@10 y nDCG@10.

   https://chatgpt.com/share/69fe7523-8ac0-83e9-a7c6-0a46f9c092a0

5. **Generacion de figuras**

   > Genera figuras para el informe: distribucion de tamano de playlists, top artistas, distribucion de popularidad de canciones en escala log-log y comparacion de metricas de baselines.

   https://chatgpt.com/share/69fe74e5-c4d0-83e9-911f-0ecdaddd7898

6. **Redaccion del informe en LaTeX**

   > Crea un informe en LaTeX de 3 a 4 paginas para IIC3633 Sistemas Recomendadores, Pontificia Universidad Catolica de Chile, Marzo-Julio 2026. Debe incluir problema, objetivos, analisis descriptivo, baselines, resultados, plan Midterm, limitaciones, bibliografia y link al repositorio.

7. **Justificacion del uso de DuckDB**

   > Agrega al informe y README una explicacion tecnica de por que se uso DuckDB en vez de cargar el CSV completo con pandas. Incluye citas a DuckDB como base de datos analitica embebida y a su documentacion de lectura CSV.

8. **Declaracion de uso de IA**

   > Agrega una seccion breve y transparente sobre el uso de IA generativa para apoyar formato, redaccion, verificacion de codigo y checklist del enunciado, aclarando que las decisiones metodologicas e interpretacion final son responsabilidad del grupo.

