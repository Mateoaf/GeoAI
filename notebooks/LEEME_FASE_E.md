# Fase E · Evaluación espacial y aprendizaje presencia–fondo

Implementa los pasos 27–30 del plan mediante los cuadernos **07, 08 y 09** y `src/geoau/evaluation.py`. Consume la ejecución D `20260909T104712_606095Z`, sus relaciones indicio–celda y sus máscaras de soporte. No recalcula las fases A–D ni modifica `Grid_Master_Au`.

## Estado y alcance

La ejecución D está cerrada técnicamente, pero contiene **cero celdas positivas revisadas** y ninguna columna aprobada en `approved_training_columns`. Por eso `config/evaluation.yaml` usa `mode: diagnostic`. Los registros candidatos sirven para comprobar la mecánica espacial; se guardan como `P_candidate_proxy`. No se convierten en positivos confirmados. El cierre E conserva `training_allowed: false` y `prediction_allowed: false`.

El ámbito heredado es la componente peninsular principal a 1 km, no toda España incluyendo islas. El soporte elegido es `eligible_geo4`, definido en D. Se usan las claves y la cobertura de D; los predictores no se cargan para diseñar particiones. Las particiones de almacenamiento de `Grid_Master_Au` y sus bloques diagnósticos anteriores no se reutilizan como folds.

## Ejecución

Desde la raíz `Proyecto Con Luis`, con el entorno ya existente:

```powershell
.\.venv-fase-a\Scripts\python.exe scripts/ejecutar_notebooks_fase_e.py
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -p test_evaluation.py -v
.\.venv-fase-a\Scripts\python.exe scripts/validar_fase_e.py
```

No se requiere un entorno nuevo. `requirements-fase-e.txt` hereda las dependencias de D. También se pueden ejecutar los cuadernos manualmente en orden con el kernel del entorno existente. El runner usa explícitamente el intérprete que lo invoca y guarda las salidas en los cuadernos. Para continuar desde 08: `--desde 8`. Evitar ejecutar dos instancias simultáneas sobre una misma ejecución.

07 crea o recupera una ejecución en `reports/fase_e/<fecha_UTC>/`. 08 y 09 exigen esa ejecución. Se congelan configuración, código, manifiesto de D y cartografía territorial adicional si existe. Cambiar entradas exige una nueva ejecución desde 07. Los manifiestos comprueban SHA-256; no se reutilizan productos modificados silenciosamente.

## 07 · Particiones y reserva

1. Verificar los productos de D y la integridad de `cell_id` y etiquetas booleanas.
2. Consultar la disponibilidad científica en `readiness.json`.
3. Crear bloques de 50 km anclados al origen de la malla. Unir transitivamente todos los bloques conectados por `deposit_id` o `district_id`. En modo diagnóstico se añade `proximity_group_500m`: es un sustituto geométrico provisional, no una identificación de depósitos.
4. Comparar el número de bloques y unidades disponibles a 25/50/100 km. **Esta tabla no estima autocorrelación ni selecciona el tamaño óptimo**. Ese estudio y el objetivo de transferencia deben motivar la revisión científica posterior.
5. Reservar por semilla aproximadamente el 15 % de las unidades completas en diagnóstico. No necesariamente equivale al 15 % de área. La reserva no se presenta como distritos geológicos acreditados. En modo validado se reservan los distritos explícitos y todas sus unidades conectadas.
6. Asignar cinco folds externos de forma reproducible, sin utilizar valores de predictores ni rendimiento. Comprobar al menos una unidad con P en prueba y dos en entrenamiento; reducir el número de folds si falla. Estos mínimos prueban factibilidad técnica, no suficiencia estadística.
7. Retirar del entrenamiento una franja que garantice al menos 5 km respecto a prueba y reserva. La distancia entre centros se convierte en una cota conservadora entre las huellas cuadradas: `max(0, distancia_centros - sqrt(2)*resolucion)`. La garantía espacial puede retirar más área que una distancia exacta entre polígonos.
8. Dentro de cada entrenamiento externo crear tres folds internos, con la misma exclusión espacial y reserva. Si no son viables se prueban dos. Si siguen sin ser viables, se detiene el diseño para revisarlo; no se entrena con una partición vacía.

Salidas: `design/spatial_units.parquet`, `memberships/*.parquet`, `split_plan.json`, `split_summary.csv`, `block_sensitivity.csv`, `group_links.csv` y mapa en el cuaderno. Cada membresía registra `train`, `test`, `spatial_gap`, `holdout`, `outside_support` u `outside_parent`. En un split interno, `test` significa validación interna.

## 08 · Fondo U dentro de cada entrenamiento

Se usan todas las celdas P seleccionadas de ese entrenamiento, una vez por celda. Los registros originales siguen en la tabla relacionada. U se obtiene del soporte elegible de entrenamiento excluyendo sus P y un buffer de 250 m **entre huellas de celdas**. A 1 km esta es una exclusión conservadora, no una estimación de precisión de los indicios. Antes de aprobarla debe contrastarse con incertidumbre y agrupación documentadas. No se usa la posición de P de prueba para vaciar U.

Se generan ratios U:P de 1:1, 3:1 y 10:1, con tres realizaciones reproducibles para cada split. Si el fondo disponible es menor se limita la muestra y se registra el ratio efectivo. El muestreo es sin reemplazo dentro de cada realización; distintas realizaciones pueden compartir U.

El estrato es el bloque espacial original. Si la muestra alcanza todos los bloques, se asigna al menos una celda a cada bloque y el resto según su área terrestre disponible, respetando capacidad. Dentro de cada bloque se seleccionan celdas uniformemente: `pi = n_h/N_h`. Si hay menos muestras que bloques, se seleccionan `n` de los `H` bloques al azar y una celda por bloque: `pi = (n/H)/N_h`. Se registra esa probabilidad incondicional incluso para bloques no seleccionados.

Los pesos de U son `1/pi` y `land_area_m2/pi`. No son pesos de clase, ni pesos de observación de P. La inclusión de P igual a uno indica que se conserva el censo de P de entrenamiento; no que se conozca toda la mineralización existente. `sample_class=0` identifica U, **no ausencia de oro**.

Salidas: cada muestra en `samples/*.parquet`, su asignación por estrato en `*_allocation.parquet` y `sample_summary.csv`, con semilla, ratio, realización y disponibilidad. No se implementa una alternativa por esfuerzo de observación porque no existe una fuente verificada para ese propósito. Otros minerales no se convierten en negativos de Au.

## 09 · Contrato para fase F

La referencia P/U utiliza la realización 0; la alternativa PU utilizará varias realizaciones con los mismos P y exactamente la misma evaluación. La agregación prevista es la media de scores. Tres realizaciones permiten el piloto; aumentar hacia 20 depende de un análisis posterior de estabilidad, no de un requisito automático.

La evaluación territorial utiliza todas las celdas elegibles `role=test` de cada membresía, sin remuestrear el test según ratio o semilla. El contrato prepara los datos; el ajuste de clasificadores y el cálculo de métricas pertenecen a F/G. No se ha entrenado un Random Forest en E.

Imputación, codificación, selección de variables, algoritmo, ratio y parámetros se decidirán dentro del bucle interno. La evaluación externa mide el procedimiento de selección completo. Si sus resultados se usan para rediseñar el procedimiento, debe declararse esa selección y conservar la reserva final independiente. La reserva no se usa para ajustar ni para elegir repetidamente modelos.

Los scores distinguen presencia registrada frente a fondo bajo este diseño. No representan un porcentaje absoluto de encontrar oro. PU no elimina automáticamente el sesgo de observación ni identifica prevalencia. No se asume SCAR (registro aleatorio de positivos).

09 comprueba manifiestos y emite `control_cierre.json`, `learning_contract.json` y `outputs_manifest.json`. `assert_ready_for_training` impide presentar el protocolo diagnóstico como aprobado.

## Trabajo necesario para el cierre científico

1. Revisar etiquetas y tipologías en B, identificar depósitos y distritos reales y regenerar sus productos derivados en C/D. No editar directamente una ejecución sellada.
2. Aprobar explícitamente el conjunto de predictores en D después de resolver sus controles científicos.
3. Aportar una tabla territorial con `cell_id` único para toda la malla y `district_id`, no solo IDs asociados a los indicios. El código compara la cartografía con los distritos de P. Para aluvial, aportar además `catchment_id` completo y revisar la conectividad de cuencas.
4. Estudiar dependencia espacial, distancias entre depósitos y transferencia geográfica; fijar bloques, separaciones, buffer P y suficiencia de unidades independientes. Los valores actuales son hipótesis diagnósticas.
5. Fijar `territorial_groups_path`, distritos de reserva en `reserve_district_ids`, la nueva ejecución D, el objetivo y `protocol_reviewed: true`. Después solicitar `mode: validated`. El código rechaza el modo si faltan sus condiciones.
6. Revisar las nuevas particiones y sus tamaños antes del entrenamiento F. El cierre automatizado acredita condiciones registradas, no sustituye la revisión geológica. Si no caben reserva y validación anidada, se debe rediseñar el ámbito/protocolo y documentar la limitación; no abrir una reserva repetidamente.

Referencias metodológicas: [validación anidada, documentación de scikit-learn](https://scikit-learn.org/stable/auto_examples/model_selection/plot_nested_cross_validation_iris.html) y [Bekker y Davis, PU con selección dependiente de características](https://proceedings.mlr.press/v94/bekker18a.html).
