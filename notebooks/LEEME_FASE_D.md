# Fase D · Crear variables geocientíficas

Esta fase consume la ejecución C `20260908T122215_992338Z`, indicada en
`config/features.yaml`. Conserva la rejilla peninsular de 1 km, su `cell_id` y
la máscara candidata. No modifica A, B, C, los archivos originales ni sus notebooks.

## Instalación y ejecución

Usar el mismo intérprete `.venv-fase-a` de los cuadernos anteriores. Desde la raíz
**Proyecto Con Luis**, en PowerShell:

```powershell
& '.\.venv-fase-a\Scripts\python.exe' -m pip install -r requirements-fase-d.txt
& '.\.venv-fase-a\Scripts\python.exe' scripts/ejecutar_notebooks_fase_d.py
```

`requirements-fase-d.lock.txt` registra las versiones instaladas durante esta
implementación. El cuaderno 04 añade las versiones de NumPy, SciPy y PyArrow a
`environment_fase_d.json`, complementando el registro del entorno heredado de A.

También se pueden ejecutar las celdas desde VS Code, seleccionando ese intérprete:

1. `03_variables_geologia_estructuras.ipynb`: inicia una ejecución D, crea los
   diccionarios y calcula geología/edad y estructuras GEODE.
2. `04_variables_geoquimicas.ipynb`: verifica los colores locales y genera clases
   modales y proporciones controladas.
3. `05_variables_relieve_hidrologia.ipynb`: deriva el terreno y la red hidrográfica.
4. `06_matriz_variables_control.ipynb`: integra, audita, visualiza y sella resultados.

No es necesario volver a ejecutar 00–02. El cálculo nacional de vectores puede
tardar; trabaja por teselas para limitar memoria. Los cuadernos muestran progreso.
Los scripts de creación no sobrescriben notebooks existentes.

**Reejecutar `start_run` del 03 inicia otra ejecución.** Para continuar el mismo
trabajo desde el 03, usar `RUN = fd.current_run(ROOT)` en esa celda. Los bloques
terminados se reutilizan solo después de verificar sus hashes. Para continuar a
partir del cuaderno 04 desde consola:

```powershell
& '.\.venv-fase-a\Scripts\python.exe' scripts/ejecutar_notebooks_fase_d.py --desde 4
```

`reports/fase_d/current_run.json` identifica la ejecución que usarán 04–06. Cada
cuaderno imprime su ruta. También puede fijarse `RUN = ROOT / 'reports/fase_d/…'`
explícitamente. No ejecutar varias secuencias a la vez usando el puntero compartido.
Si cambia una fuente, configuración o código congelado, iniciar una nueva ejecución.

## Métodos y decisiones

### Geología y edad (paso 18)

Intersecciones exactas entre polígonos y la parte terrestre de cada celda. Se
disuelve por descripción para evitar doble superficie dentro de una categoría;
se mide el solape entre categorías. Se conservan las descripciones originales,
incluidas las unidades mixtas. Los IDs de categoría tienen su diccionario por
ejecución y no deben interpretarse como números ordinales ni compararse entre
ejecuciones sin comprobar el diccionario.

Se exige al menos 95 % de superficie terrestre con atributo y un solape entre
categorías no superior a `max(1 m², área terrestre × 1e-6)`. Las celdas que no
cumplen conservan NaN en sus variables y sus indicadores de calidad. La fracción
se divide por superficie terrestre, no por superficie cartografiada: puede sumar
menos de uno. La dominante desempata por descripción ordenada.

Las fracciones actuales corresponden a **unidades cartográficas**. Una unidad
«cuarcitas, pizarras, areniscas y calizas» no se reparte arbitrariamente entre
cuatro rocas. La agrupación en granitoides/metasedimentos/etc. requiere la revisión
del diccionario; permanece pendiente en `pending_extensions.json`.

### Estructuras (pasos 19–20)

V1 usa exclusivamente GEODE. No suma MAGNA, ni longitudes de símbolos de medidas
estructurales. El diccionario exporta todas las descripciones y sus recuentos.
Clasifica fallas/cizallas, cabalgamientos y contactos intrusivos; distingue
supuestas/ocultas/inferidas del resto cartografiado. «Cartografiada» **no certifica
observación de campo**. Lo no reconocido queda excluido para revisión.

Distancias exactas del centro a la traza disponible hasta 10 km. Si no hay una
traza en ese radio, NaN y bandera auxiliar; no cero ni una distancia inventada.
La búsqueda utiliza el margen conservado por C. Sin huellas de levantamiento no
se puede acreditar la ausencia de estructuras, tampoco con distancia finita.

Las densidades son **experimentales y aproximadas**: longitud geométrica por celda
de 1 km, disuelta/nodada para no contar coincidencias exactas dos veces; media
longitud en fronteras compartidas; solo longitud dentro de la máscara. Se agregan
con pesos de intersección círculo/celda y se dividen por el área terrestre del
mismo soporte. Esto supone longitud uniformemente distribuida dentro de cada
celda; no es una intersección exacta de todas las trazas con cada círculo. La
aproximación puede ser relevante en radio 1 km y debe contrastarse antes de
seleccionar estas variables. Los campos se llaman `dens_aprox_...`.

No se eliminan casi duplicados por tolerancias arbitrarias. No se crean
intersecciones mineralizantes ni orientaciones a partir de símbolos sin leyenda.

### Geoquímica (pasos 21–22)

Lectura segura de las constantes de los scripts históricos mediante `ast`, sin
ejecutar descargas ni modificaciones históricas. Para cada píxel se contrasta su
RGB con el color de la clase que declara la banda 1; umbral inicial cero y alfa
255. Se rechazan colores distintos/transparentes y clases inválidas.

Se reconstruye la agregación a 1 km para aplicar la nueva máscara RGB, conservando
la misma rejilla y ponderación terrestre de C. Se informa del cambio de moda
respecto a C. Se exige 95 % de área válida para las columnas del maestro; los TIFF
conservan además valores parciales y su banda de soporte para diagnóstico.

Clase 0 es válida. Moda: empate a clase menor. Proporciones: superficie por clase
sobre superficie válida. Son dos representaciones alternativas, no nueve análisis
químicos independientes ni concentraciones. No se calculan ratios/logaritmos de
códigos. Las leyendas locales se exportan con su estado pendiente; coincidir con
un color local no valida la leyenda oficial, medio, extracción o resolución real.

**Hallazgo de la primera ejecución:** la tolerancia cero conserva todos los
píxeles terrestres originalmente válidos de Au/As/Sb/Bi. En Hg/Cu/Pb rechaza muchos
píxeles por diferencias de color de hasta `sqrt(2)` en distancia RGB; Zn/W tienen
también diferencias de hasta 8. Eso no demuestra que las clases químicas estén
mal asignadas: revela que los colores exportados y las constantes históricas no
coinciden exactamente. La ejecución conserva el criterio estricto y hace visible
la pérdida de soporte. Revisar `geoquimica_rgb_qc.csv` antes de seleccionar esos
elementos. `diagnostico_tolerancia_rgb.csv` documenta la sensibilidad sobre todos
los píxeles fuente válidos de la extensión (no solo tierra peninsular).

Para estudiar otra tolerancia, modificar `rgb_max_distance` y comenzar una nueva
ejecución; contrastar también leyenda, medio y extracción, no elegir la tolerancia
porque mejore una métrica del modelo. Los productos C originales siguen disponibles.

### Relieve e hidrografía (pasos 23–24)

Elevación: banda 1 del MDT de 500 m, verificada contra la fuente A enlazada.
Pendiente: `atan(sqrt(dx² + dy²))` en grados, diferencias centrales con centro y
cuatro vecinos válidos. TPI: z menos la media de los centros dentro del círculo,
incluyendo el central. Desviación de elevación: desviación estándar poblacional
local, no TRI. Radios de 1 y 5 km; al menos 95 % de centros válidos del vecindario.
No se refleja el terreno en bordes ni se sustituye NoData por elevación cero.

Las derivadas se calculan a 500 m y luego se promedian a 1 km con área terrestre
válida. El vecindario usa centros discretos, no integra exactamente el disco.
En costa y bordes puede haber NaN por soporte insuficiente, y eso se conserva.

Hidrografía: distancia y densidades con el método lineal anterior. No equivale a
un modelo de placeres. Terrazas, MDT fino, cuencas y conexión aguas arriba son
ampliaciones pendientes; los recintos cuaternarios actuales tienen descripción
genérica y no permiten asignar terrazas automáticamente.

### Geofísica y matriz (pasos 25–26)

Las ocho capas adicionales recuperadas siguen disponibles en C. No se interpolan
localizaciones ni símbolos. La gravimetría cuantitativa requiere control de unidades,
campañas y soporte; las orientaciones requieren leyendas y depuración angular.
Estas extensiones se registran, no son requisitos del bloque regional inicial.

`Grid_Master_Au.parquet` contiene una fila por celda y las variables candidatas,
en grupos de filas de 50.000 para lectura eficiente. Coordenadas/calidad y etiquetas
se guardan separadas. No se duplican filas por los varios indicios en una celda.
U significa no etiquetado; los candidatos no revisados tienen otro estado.

## Productos de cada ejecución

- `blocks/`: tablas Parquet por familia, calidad, diccionario y manifiesto de hashes.
- `dictionaries/`: categorías originales, reglas estructurales y leyendas locales.
- `rasters/`: geoquímica controlada y relieve con bandas de soporte.
- `Grid_Master_Au.parquet`: X candidata y `cell_id`, sin etiquetas ni coordenadas.
- `calidad_y_soporte.parquet`: rejilla e indicadores de extracción, separados de X.
- `etiquetas_por_celda.parquet` y `relacion_indicios_celda.parquet`: etiquetas y
  trazabilidad de todos los indicios, incluido el que está fuera de máscara.
- `feature_dictionary.csv`, `feature_allowlist.json`, `variables_qc.csv`.
- `inputs.json`, configuración, código, entorno, pendientes y controles de cierre.
- `outputs_manifest.json`: integridad de los productos finalizados.

`candidate_columns` es la lista explícita de X generada. **`approved_training_columns`
está vacía**, `prediction_allowed` es falso y el cierre científico permanece falso:
faltan revisión semántica, cobertura de levantamientos y etiquetas validadas.
No activar esas banderas para eludir las revisiones. Imputación, selección de
variables, codificación, particiones y Random Forest corresponden a E/F.

## Verificación

```powershell
& '.\.venv-fase-a\Scripts\python.exe' -m unittest discover -s tests -p test_features.py -v
& '.\.venv-fase-a\Scripts\python.exe' scripts/validar_fase_d.py
```

Casos conocidos: solapes, duplicados y fronteras, distancias sin trazas, pendiente
de un plano, huecos del terreno, clase cero, rechazo RGB y detección de modificaciones.

Referencias técnicas consultadas para la implementación:
[consultas espaciales de Shapely](https://shapely.readthedocs.io/en/2.1.2/strtree.html),
[convolución y tratamiento de bordes de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.ndimage.convolve.html).
