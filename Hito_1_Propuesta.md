# Hito 1: Propuesta, analisis y baselines

**Curso:** Sistemas recomendadores  
**Integrantes:** Agustin Llambias, Amaya Quero, Larry Uribe

## Titulo tentativo

Recomendacion musical personalizada a partir de historiales de escucha de Last.fm.

## Descripcion del problema y justificacion

Los servicios de musica digital concentran catalogos muy grandes, por lo que un usuario puede tener dificultades para descubrir canciones o artistas alineados con sus gustos. En este contexto, un sistema recomendador permite ordenar el catalogo y sugerir items relevantes usando informacion historica de interacciones. El proyecto se enfocara en recomendacion musical personalizada usando registros de escucha como retroalimentacion implicita: si un usuario escucho una cancion, se asume que existe una senal positiva de interes, aunque no haya una calificacion explicita.

El problema principal sera: dado el historial de escucha de un usuario, recomendar canciones o artistas que el usuario no haya escuchado previamente y que tengan alta probabilidad de ser relevantes para el. Este caso es representativo de sistemas recomendadores reales porque trabaja con datos implicitos, alta cardinalidad de items, sesgos de popularidad y posible dispersion de interacciones entre usuarios e items.

El dataset propuesto es Last.FM_dataset de Kaggle, disponible en https://www.kaggle.com/datasets/harshal19t/lastfm-dataset. En la version descargada se observan 166.153 registros de escucha, donde cada registro indica que usuario escucho una cancion, junto con artista, album, fecha y hora. Este tipo de dato permite formular el problema como recomendacion top-N usando interacciones usuario-item. Dado que no existen ratings explicitos, se interpreta cada escucha como feedback implicito positivo.

## Objetivos del proyecto

El objetivo general es construir y evaluar un sistema de recomendacion musical personalizada sobre datos de Last.fm, comparando baselines simples con metodos mas expresivos bajo un protocolo reproducible de evaluacion offline.

Los objetivos especificos son:

- Caracterizar el dataset mediante analisis descriptivo de usuarios, canciones, artistas e interacciones.
- Definir un protocolo de train/test que permita evaluar recomendacion top-N con datos implicitos.
- Implementar al menos tres modelos de referencia: Random, Most Popular y un modelo especifico al dominio musical.
- Comparar los modelos usando metricas de ranking como Hit Rate@K, Precision@K, MAP@K y nDCG@K.
- Desarrollar en la etapa Midterm un metodo mas avanzado, por ejemplo filtrado colaborativo item-item, factorizacion matricial para feedback implicito o un enfoque hibrido que incorpore metadatos musicales.
- Analizar criticamente las limitaciones del dataset y del protocolo de evaluacion, especialmente por el bajo numero de usuarios y la alta cantidad de items relevantes por usuario.

## Analisis descriptivo de los datos

La version descargada contiene 166.153 registros, 11 usuarios, 22.823 artistas, 67.241 nombres de tracks, 76.038 items unicos definidos como par artista-track y 38.629 albumes. No se encontraron duplicados exactos y existen 12 albumes faltantes. El rango temporal cubre escuchas entre el 1 y el 31 de enero de 2021.

La matriz usuario-item tiene sparsity aproximada de 0,8411, equivalente a una densidad de 15,89% sobre los pares usuario-item posibles. Aunque este valor es menos extremo que en datasets de recomendacion masivos, el catalogo sigue siendo amplio respecto del numero de usuarios. La distribucion de interacciones por usuario es desbalanceada: el usuario con menos registros tiene 1.063 escuchas, mientras que el maximo alcanza 33.695. A nivel de items tambien hay concentracion de popularidad: la mayoria de canciones aparece una o dos veces, mientras que algunos items populares superan ampliamente ese valor.

Los artistas mas escuchados en el dataset incluyen Sophie, Madlib, Bicep, Taylor Swift y Arlo Parks. Entre los items mas frecuentes aparecen, por ejemplo, "Metric - Cascades (Dirt Road Version)" y "Ocean Waves For Sleep - Rolling Ocean Waves". Estos patrones justifican incluir un baseline de popularidad y, al mismo tiempo, evaluar metodos personalizados que no se limiten a recomendar solamente los items globalmente dominantes.

## Baselines implementados o propuestos

### 1. Random

Este modelo recomienda K canciones al azar desde el conjunto de canciones observadas en entrenamiento. Es un baseline minimo que sirve para verificar que las metricas y el protocolo de evaluacion funcionen correctamente. Se espera que tenga desempeno muy bajo, especialmente cuando el catalogo es grande.

### 2. Most Popular

Este modelo recomienda las K canciones o artistas mas frecuentes en el conjunto de entrenamiento. No es personalizado, pero suele ser un baseline competitivo en dominios donde la popularidad esta muy concentrada. En el notebook preliminar, Most Popular supera a Random en Hit Rate@10, lo que confirma que la popularidad global captura parte de la senal del dataset.

### 3. Favorite Artist Popular

Como tercer baseline especifico al dominio musical se implemento un recomendador basado en los artistas favoritos del usuario. Primero se identifican los artistas mas escuchados por cada usuario en train. Luego se recomiendan canciones populares de esos artistas que el usuario no haya escuchado previamente. Si no se completa el top-K, el modelo rellena con canciones populares globales no vistas por el usuario.

Este baseline es simple, pero ya introduce personalizacion usando una senal musical interpretable: la afinidad historica usuario-artista.

### Resultados preliminares

Se implementaron los tres baselines en `hito1_lastfm_baselines.py`. La evaluacion usa split temporal por usuario: 80% de las interacciones para train y 20% para test. Para medir recomendacion de descubrimiento, los items relevantes son canciones futuras que el usuario no habia escuchado en train.

Adicionalmente, se dejo un notebook ejecutado, `Hito_1_LastFM.ipynb`, que contiene la carga del dataset, analisis descriptivo, visualizaciones, definicion de metricas, implementacion de baselines y exportacion de resultados.

| Modelo | HitRate@10 | Precision@10 | MAP@10 | nDCG@10 |
| --- | ---: | ---: | ---: | ---: |
| Random | 0,3636 | 0,0364 | 0,0074 | 0,0310 |
| Most Popular | 0,0909 | 0,0455 | 0,0202 | 0,0367 |
| Favorite Artist Popular | 0,4545 | 0,0455 | 0,0133 | 0,0459 |

Los resultados muestran que el baseline personalizado por artista obtiene el mayor HitRate@10 y nDCG@10, mientras que Most Popular logra el mejor MAP@10. Esto sugiere que la informacion de artistas aporta una senal personalizada util, pero aun hay espacio para mejorar el ordenamiento fino de las recomendaciones.

Es importante interpretar estos resultados con cautela. Random obtiene un HitRate@10 relativamente alto porque, bajo el split temporal utilizado, cada usuario conserva en promedio 2.291 items relevantes futuros. Por lo tanto, HitRate@10 es una metrica poco exigente en este primer experimento y debe complementarse con Precision@10, MAP@10 y nDCG@10. Para Midterm se propone evaluar tambien con negative sampling o con un test set mas restringido por usuario, de modo que la comparacion entre modelos sea mas exigente.

## Protocolo de evaluacion

Se utilizara una particion train/test temporal por usuario. Para cada usuario con al menos dos interacciones, se ordenaran las escuchas por fecha y hora, se usara el 80% inicial como train y el 20% final como test. Luego cada modelo generara un ranking top-K de canciones no vistas por el usuario en train.

Las metricas principales seran:

- Hit Rate@10: indica si al menos un item relevante aparece entre las 10 recomendaciones.
- Precision@10: mide la proporcion de recomendaciones relevantes dentro del top 10.
- MAP@10: considera la posicion de los aciertos en el ranking.
- nDCG@10: premia que los items relevantes aparezcan en posiciones mas altas.

Si se decide transformar conteos de escucha en ratings explicitos, tambien se podrian reportar MAE o RMSE para comparar prediccion de ratings, aunque para recomendacion musical top-N las metricas de ranking son mas adecuadas.

La decision de usar split temporal, en lugar de un split aleatorio, busca evitar filtracion de informacion futura hacia el entrenamiento. Esto es especialmente relevante en recomendacion musical, donde el gusto del usuario puede cambiar en el tiempo y donde un split aleatorio podria mezclar escuchas posteriores dentro de train.

## Limitaciones actuales

La principal limitacion del dataset descargado es el bajo numero de usuarios: existen solo 11 usuarios, aunque cada uno tiene muchas interacciones. Esto permite estudiar personalizacion a nivel individual, pero limita la generalizacion estadistica de los resultados y vuelve menos estable la comparacion agregada entre modelos. Por esta razon, las conclusiones del Hito 1 deben entenderse como evidencia preliminar y no como resultados finales.

Otra limitacion es que el dataset no incluye ratings explicitos ni informacion semantica rica como generos o tags. Para este hito se trabajo con feedback implicito y metadatos basicos de artista, track, album y tiempo. En Midterm se evaluara si conviene enriquecer el dataset con informacion externa o concentrarse en metodos colaborativos que exploten mejor la matriz de escuchas.

## Planificacion para Midterm

| Fecha | Actividad | Resultado esperado |
| --- | --- | --- |
| 08/05 | Cierre Hito 1 | Propuesta, EDA y baselines iniciales documentados. |
| 09/05 - 16/05 | Limpieza y normalizacion definitiva del dataset Last.fm | CSV procesado, matriz usuario-item y split reproducible. |
| 17/05 - 24/05 | Implementacion de filtrado colaborativo | Modelos user-user e item-item con similitudes coseno, Jaccard o Pearson/Spearman. |
| 25/05 - 31/05 | Implementacion de metodo avanzado | Factorizacion matricial para feedback implicito o modelo hibrido contenido + colaborativo. |
| 01/06 - 04/06 | Evaluacion y analisis | Tabla comparativa de metricas, analisis de errores y limitaciones. |
| 05/06 | Entrega Midterm | Informe intermedio con resultados preliminares del metodo avanzado. |

Los criterios de exito para Midterm seran:

- Superar el baseline Most Popular en al menos una metrica de ranking top-K.
- Mantener cobertura razonable de usuarios e items, evitando recomendar solo canciones muy populares.
- Reportar tiempos de ejecucion y limitaciones de memoria para justificar decisiones de muestreo o filtrado.
- Dejar el pipeline suficientemente documentado para reproducir los resultados.

## Riesgos y mitigaciones

Un primer riesgo es que el bajo numero de usuarios limite la validez externa de los resultados. Para mitigarlo se reportaran metricas por usuario, no solo promedios agregados, y se analizara la sensibilidad de los resultados al protocolo de evaluacion. Un segundo riesgo es que el dataset tenga pocas columnas de contenido. Si esto ocurre, se priorizara filtrado colaborativo item-item o factorizacion matricial. Un tercer riesgo es el costo computacional: algunos metodos exactos pueden ser caros si el catalogo crece mucho, por lo que se usaran matrices sparse, muestreo controlado y evaluacion por batches.

## Bibliografia relevante

- Harshalsps19t. Last.FM_dataset. Kaggle, 2023. https://www.kaggle.com/datasets/harshal19t/lastfm-dataset
- Sgardelis, K., Margaris, D., Spiliotopoulos, D. y Vassilakis, C. An evaluation review of user similarity metrics in sparse collaborative filtering datasets. International Journal of Data Science and Analytics, 2025. https://doi.org/10.1007/s41060-025-00846-4
- Koren, Y., Bell, R. y Volinsky, C. Matrix factorization techniques for recommender systems. Computer, 42(8), 30-37, 2009. https://doi.org/10.1109/MC.2009.263
- He, X., Deng, K., Wang, X., Li, Y., Zhang, Y. y Wang, M. LightGCN: Simplifying and Powering Graph Convolution Network for Recommendation. SIGIR, 2020. https://doi.org/10.1145/3397271.3401063
