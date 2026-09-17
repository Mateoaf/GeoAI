# Análisis técnico y metodológico del código de prospectividad aurífera

Fecha de revisión: **10 de septiembre de 2026**. Proyecto inspeccionado: `GeoAI/GeoAI`. Informe basado en el código y productos locales presentes durante esta revisión.

## 1. Alcance, lectura y conclusión principal

El proyecto dispone de una cadena técnica sustancial desde el inventario de fuentes hasta el entrenamiento espacial anidado. Su resultado actual es un **experimento diagnóstico de favorabilidad relativa con candidatos del inventario**, todavía sin cierre científico de etiquetas, predictores, protocolo ni validación final. La existencia de modelos serializados y métricas reproducibles demuestra que hay una implementación ejecutada; no demuestra todavía capacidad contrastada de descubrimiento de depósitos nuevos.

La referencia a «14 notebooks» se ha interpretado como la serie que termina en el número 14. En disco existen **15 cuadernos, del 00 al 14**, que contienen **95 celdas de tipo código**, 91 con instrucciones ejecutables y cuatro vacías o compuestas exclusivamente por comentarios. Su fuente suma 786 líneas según `splitlines()`. Se explican todas las celdas, incluidas las exploratorias y las redundantes. Los números de celda utilizados son **índices del JSON desde cero**; se muestra también su posición desde uno. El contador `In[n]` guardado no identifica la posición de la celda y puede pertenecer a sesiones anteriores.

Se han leído los siete módulos funcionales de `src/geoau`, sus configuraciones, los ejecutores y validadores, las pruebas, los scripts históricos que explican la procedencia de los rásteres, el plan y documentación asociada. El cuaderno del vino en `informes/` es una referencia metodológica ajena a la serie de prospectividad y no se incluye en el análisis exhaustivo de celdas. Los cuadernos 15 y 16 aparecen previstos en el plan y no existen en la serie implementada.

El plan adjunto se trata como **documentación a contrastar**. Sus propuestas de descargas, entrenamiento, revisión experta o publicación no se han interpretado como órdenes nuevas del usuario. Este encargo consiste en analizar y redactar un informe: se han conservado los notebooks y el código operativo, incluido el cambio previo que Git ya registraba en el notebook 03.

La revisión combina cuatro niveles de evidencia: lectura estática de instrucciones y funciones; inspección de resultados persistidos; ejecución de la suite existente y de validadores de productos; y reproducciones pequeñas de comportamientos concretos. No se han vuelto a ejecutar los 15 notebooks ni se ha repetido el geoprocesamiento nacional o la búsqueda de modelos. Las salidas antiguas guardadas en una celda se describen como tales, sin afirmar que fueron producidas por el texto actual de esa misma celda.

### 1.1. Cómo utilizar el informe

Cada capítulo indica el propósito del notebook, sus entradas y salidas, la lógica delegada a Python y su relación con el plan. A continuación aparece una ficha por celda con el código original y una explicación de lo que consume, transforma, muestra o escribe. Al final se reúnen las diferencias con los 44 pasos del plan, los hallazgos priorizados y los límites de las comprobaciones.

Los enlaces a código remiten a los archivos del repositorio. Los intervalos de líneas se dan en el texto, porque corresponden a la copia analizada; el anexo `fuentes_analizadas_sha256.json` permite identificarla exactamente. La explicación de las funciones es necesaria: desde el notebook 03 una llamada de una sola línea puede desencadenar miles de operaciones espaciales, verificaciones de archivos y escritura de productos.

### 1.2. Inventario de la serie

| Notebook | Fase | Celdas totales | Celdas de código | Celdas con instrucciones ejecutables |
|---|---|---:|---:|---:|
| `00_configuracion_y_fuentes` | A | 30 | 16 | 16 |
| `01_indicios_limpieza_etiquetas` | B | 35 | 23 | 21 |
| `02_rejilla_armonizacion_cobertura` | C | 32 | 16 | 16 |
| `03_variables_geologia_estructuras` | D | 9 | 6 | 4 |
| `04_variables_geoquimicas` | D | 6 | 5 | 5 |
| `05_variables_relieve_hidrologia` | D | 5 | 4 | 4 |
| `06_matriz_variables_control` | D | 8 | 6 | 6 |
| `07_particiones_espaciales` | E | 6 | 3 | 3 |
| `08_muestreo_presencia_fondo` | E | 5 | 2 | 2 |
| `09_protocolo_PU_y_control` | E | 5 | 2 | 2 |
| `10_pipelines_y_contrato_entrenamiento` | F | 5 | 2 | 2 |
| `11_referencias_y_regresion_logistica` | F | 4 | 2 | 2 |
| `12_random_forest_espacial` | F | 4 | 2 | 2 |
| `13_comparacion_modelos` | F | 5 | 3 | 3 |
| `14_ablaciones_PU_y_cierre` | F | 6 | 3 | 3 |

### 1.3. Arquitectura efectiva

```text
Fuentes locales + config/project.yaml
  └─ 00 / local_sources.py → A: catálogo, hashes, lectura
       └─ 01 / labels.py → B: conciliación, geometría, candidatos y revisión
            └─ 02 / territory.py + additional_layers.py
                 → C: máscara, rejilla, armonización, cobertura
                 └─ 03 geología/estructuras ┐
                    04 geoquímica         ├─ features.py → D
                    05 relieve/hidrología ┘
                    06 matriz y roles → Grid_Master_Au + X + calidad + etiquetas
                         └─ 07 particiones ┐
                            08 muestras    ├─ evaluation.py → E
                            09 contrato    ┘
                                 └─ 10 pipelines ┐
                                    11 referencias/logística
                                    12 Random Forest
                                    13 alternativas/comparación
                                    14 ablaciones/PU/cierre
                                      → training.py → F: modelos y predicciones OOF

G: aceptación, explicación y aplicabilidad → pendiente
H: mapas finales, objetivos e inferencia de entrega → pendiente
```

Los ficheros YAML enlazan ejecuciones concretas. B permite escoger la última A satisfactoria, pero C fija una B, D fija una C, E fija una D y F fija una E. Los JSON `current_run.json` de D/E/F facilitan continuar la ejecución correspondiente. Un directorio reciente no equivale automáticamente a una ejecución completa.

La implementación efectiva utiliza módulos planos en `src/geoau`, no la jerarquía de subpaquetes propuesta en el plan ni el paquete `geoai_gold_spain` anunciado en el README histórico. El diseño modular permite reutilizar algoritmos sin copiar grandes bloques en Jupyter; su debilidad práctica es que el usuario debe conocer los contratos entre ejecuciones, configuraciones y manifiestos.

## 2. Estado real y significado de las cifras

| Concepto | Evidencia local | Interpretación |
|---|---:|---|
| Fuentes del último inventario A | 93; cero errores de lectura; un archivo sin datos | Estado posterior a la auditoría original del plan |
| Registros de la base canónica | 11.732 | Filas del inventario general |
| Registros con Au observado | 790 | Au reconocido en `Sustancia`; aún candidatos |
| Posiciones Au distintas | 787 | Coincidencia geométrica, no depósitos independientes |
| Candidatos asociados a rejilla C/D | 789 | Uno queda fuera de la máscara candidata |
| Celdas ocupadas por candidatos en D | 691 | Varios indicios pueden compartir celda |
| Celdas terrestres de D | 496.855 | Todas las intersecciones de área positiva con la máscara |
| Área de la máscara en EPSG:25830 | 493.639,6117 km² | Superficie proyectada del ámbito candidato, no certificación catastral |
| Predictores candidatos en D | 168 | Banco de representaciones; F usa subconjuntos |
| Predictores de la referencia F | 93 | 87 numéricos y seis categóricos antes de codificación |
| Territorio elegible E, `eligible_geo4` | 472.548 celdas | Geología, relieve y Au/As/Sb/Bi con soporte requerido |
| Celdas candidatas elegibles E | 666 | Sustitutos diagnósticos de P |
| Reserva elegible | 72.061 celdas; 23 candidatas | 15,25 % del área elegible aproximadamente |
| Evaluación externa de desarrollo | 400.487 celdas; 643 candidatas | Cobertura conjunta de los cinco tests externos |
| Celdas positivas revisadas | **0** | Bloqueo científico principal |
| Modelos externos guardados en F | 60 | Familias, ablaciones y miembros adicionales de bagging |
| Archivos de predicciones F | 85 | Incluyen referencias, variantes y selección anidada |

La secuencia **790 → 787 → 789 → 691 → 666 → 643 + 23** mezcla unidades diferentes y debe leerse con cuidado: registros, posiciones, registros asignados, celdas ocupadas, celdas elegibles y reparto desarrollo/reserva. No es una serie de eliminaciones sucesivas de depósitos.

D ofrece 478.443 celdas en `eligible_geology_terrain`, 472.548 en `eligible_geo4` y 288.822 en `eligible_geo9`. Exigir los nueve elementos reduce mucho el soporte, en particular tras el control RGB de Zn/W. Las comparaciones F mantienen `eligible_geo4` incluso cuando una ablación prescinde de geoquímica; así se compara la información de las variables sobre el mismo territorio. Esa decisión limita también el alcance de las conclusiones: no evalúa las zonas adicionales que podría cubrir un modelo sin geoquímica.

La máscara es la componente de mayor área del archivo GISCO 2024 generalizado a 1:1.000.000. Las otras componentes se inventarían aparte. Por tanto, el producto no representa toda España, ni todos sus componentes terrestres, ni una máscara peninsular de precisión local. El piloto sigue sin delimitarse y justificarse geológicamente; el ensayo técnico ya abarca el territorio peninsular elegible.

### 2.1. Ejecuciones que forman la cadena examinada

| Fase | Directorio bajo `reports/` |
|---|---|
| A | `fase_a/20260908T085134_494059Z` |
| B | `fase_b/20260908T085820_294458Z` |
| C | `fase_c/20260908T122215_992338Z` |
| D | `fase_d/20260909T104712_606095Z` |
| E | `fase_e/20260909T124128_606717Z` |
| F | `fase_f/20260909T184735_016759Z` |

El paso vectorial C utiliza además una caché anterior fijada en `grid.yaml`. D recuperó bloques compatibles de una ejecución previa, dejando constancia en `reuse_audit.json`. Esta reutilización forma parte del diseño y necesita verificarse por hashes y equivalencia del cálculo, no por coincidencia de nombres de archivo.

## 3. Conceptos que conectan las fases

**Presencia observada y presencia revisada.** Encontrar el token `oro` o `au` identifica un registro candidato. La confirmación final exige presencia y geometría revisadas, y tipología revisada en los objetivos específicos. Una ausencia del token o una revisión que rechace un registro no equivale a ausencia demostrada de mineralización.

**Unidad estadística.** El aprendizaje usa una fila por celda. La tabla de relaciones conserva varios indicios y depósitos por celda sin multiplicar las filas de X. Los grupos de proximidad sirven para explorar dependencia; una cadena de puntos a menos de 500 m puede tener extremos mucho más alejados y no se convierte automáticamente en un depósito.

**Cobertura y valor.** Un cero puede ser una clase geoquímica válida, una fracción litológica nula o una longitud cartografiada nula. `NaN` indica falta de valor utilizable según su contrato. La ausencia de trazas de fallas o de puntos de campaña no demuestra que el territorio esté suficientemente estudiado.

**Soporte espacial.** La celda de salida mide 1 km de lado, pero el contenido puede proceder de una cartografía regional, cuatro píxeles de 500 m, un centro fijo o un vecindario circular. La resolución del archivo no crea detalle geológico que la fuente no contiene. Todos los positivos y U reciben las mismas variables territoriales calculadas en D.

**Aprendizaje P/U.** El cero de `sample_class` codifica territorio no etiquetado. La salida de `predict_proba` es la respuesta del clasificador bajo ese diseño y sus hipótesis. El sesgo en el registro de positivos puede depender de las características del territorio; el bagging de U no lo corrige automáticamente. Esta limitación se corresponde con la formulación de PU con selección dependiente de características de [Bekker y Davis, 2018](https://proceedings.mlr.press/v94/bekker18a.html).

**Separación y anidamiento.** Los folds internos deciden parámetros y ratios; los externos evalúan ese procedimiento. Una reserva adicional permanece sin predicciones. Aprender medianas, escalas o categorías con todo el conjunto antes de dividirlo introduciría información de evaluación: el proyecto evita ese patrón mediante pipelines ajustados por entrenamiento, de acuerdo con las [prácticas de scikit-learn sobre fuga de información](https://scikit-learn.org/stable/common_pitfalls.html).

**Cierre técnico y cierre científico.** Un manifiesto correcto demuestra identidad de archivos. Una prueba sintética demuestra un comportamiento bajo sus entradas. Ninguno acredita por sí solo la leyenda de una capa, la independencia de depósitos ni la validez de una predicción prospectiva. Las banderas de bloqueo del proyecto reflejan esa distinción.


## 4. Notebook 00 — Configuración y fuentes locales

Corresponde a la fase A, pasos 01–06 del plan. Recibe los archivos originales y `config/project.yaml`; entrega un inventario con hashes, un catálogo, diagnósticos de lectura y una especificación todavía candidata. Su centro funcional es [local_sources.py](../../src/geoau/local_sources.py).

### 4.1. Qué hace el módulo que utiliza

`local_path` resuelve rutas dentro de la raíz y rechaza URL o escapes hacia otros directorios. `discover_sources` reúne las extensiones configuradas de la raíz y la carpeta hidrográfica; no incorpora recursivamente los productos de `reports/`. `sha256_file` lee bloques de 8 MiB para identificar el contenido sin cargar todo el archivo en memoria.

`gpkg_info` consulta `gpkg_contents` y `gpkg_geometry_columns` mediante SQLite en lectura. Cuenta filas y registra esquemas; no valida todas las geometrías. `read_table` conserva atributos como texto, incluidos ceros iniciales, vacíos y el literal `NA`. `read_vector` exige autorización explícita para una carga completa y para la conversión preliminar de curvas; cuando recibe `bbox`, transforma sus límites desde el CRS declarado al de la capa.

`inspect_source` distingue inspección de GPKG, TIFF, CSV, Excel, shapefiles, QGIS y ZIP. Captura excepciones por fuente y las registra como `error`, sin convertirlas en una falsa carga válida. Los TIFF se resumen mediante metadatos y una vista reducida: no se realiza aquí una auditoría estadística exhaustiva. El control final repite la verificación de originales para detectar cambios durante la lectura.

#### NB00 · Celda 2 — Entorno, raíz e importaciones

Posición 3 del cuaderno; contador guardado: 17. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
from pathlib import Path
import importlib.util
import sys

PROJECT_ROOT_OVERRIDE = None  # Ejemplo: Path(r"D:/Datos/Proyecto Con Luis")
required = ["pandas", "geopandas", "pyogrio", "shapely", "pyproj", "rasterio",
            "openpyxl", "yaml", "matplotlib", "nbformat", "nbclient", "ipykernel"]
missing = [name for name in required if importlib.util.find_spec(name) is None]
if missing:
    raise RuntimeError(f"Faltan dependencias: {missing}. Selecciona .venv-fase-a o instala requirements-fase-a.txt.")

start = Path(PROJECT_ROOT_OVERRIDE or Path.cwd()).resolve()
candidates = [candidate for parent in (start, *start.parents)
              for candidate in (parent, parent / "Proyecto Con Luis")]
ROOT = next((p for p in candidates if (p / "config/project.yaml").is_file()
             and (p / "src/geoau/local_sources.py").is_file()), None)
if ROOT is None:
    raise FileNotFoundError("Indica PROJECT_ROOT_OVERRIDE: no se localiza el proyecto.")
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

import pandas as pd
import numpy as np
from IPython.display import display
from geoau.local_sources import (
    load_config, local_path, discover_sources, environment_info, inventory, catalog_frame,
    read_table, iter_csv, read_vector, read_raster_preview, read_raster_window,
    write_reports, write_json, verify_unchanged,
)
CONFIG = load_config(ROOT)
pd.set_option("display.max_colwidth", 90)
print("Raíz:", ROOT)
print("Intérprete:", sys.executable)
display(pd.Series(environment_info()["packages"], name="versión").to_frame())
```

Comprueba que los paquetes enumerados puedan localizarse con `find_spec`; si falta alguno, interrumpe antes del inventario. Busca la raíz entre el directorio actual y sus ancestros, con una alternativa histórica llamada `Proyecto Con Luis`. Añade `src` al principio de `sys.path` para importar el paquete local, carga el YAML y muestra versiones. `PROJECT_ROOT_OVERRIDE` permite resolver aperturas desde otra carpeta. La comprobación inicial no incluye todos los paquetes usados después —por ejemplo NumPy— ni acredita compatibilidad binaria; las importaciones y pruebas posteriores completan parcialmente ese control. No instala dependencias.

#### NB00 · Celda 4 — Especificación y descubrimiento de archivos

Posición 5 del cuaderno; contador guardado: 18. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
display(pd.json_normalize({"scope": CONFIG["scope"], "model_design": CONFIG["model_design"]}).T)
paths = discover_sources(ROOT, CONFIG)
print(f"{len(paths)} archivos locales; {sum(p.stat().st_size for p in paths)/1e9:.2f} GB.")
display(pd.Series([p.suffix.lower() for p in paths]).value_counts().rename_axis("formato").to_frame("archivos"))
```

`json_normalize(...).T` transforma las decisiones anidadas de ámbito y diseño en una tabla vertical. `discover_sources` obtiene las rutas y `stat().st_size` suma su volumen; `value_counts` cuenta formatos. Son magnitudes calculadas sobre el contenido descubierto, no cifras pegadas desde el plan. La salida histórica informa 93 archivos. El listado sólo describe disponibilidad local: un archivo existente puede estar vacío, ser únicamente visual o carecer de geometría.

#### NB00 · Celda 6 — Inventario completo y hashes

Posición 7 del cuaderno; contador guardado: 19. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
# Lee aproximadamente el volumen total de las fuentes para el hash.
# Para una exploración rápida puedes poner False, pero el manifiesto no quedará congelado por hash.
CONFIG["inspection"]["compute_sha256"] = True
registros = inventory(ROOT, CONFIG)
catalogo = catalog_frame(registros)
display(catalogo[["path", "role", "status", "row_count", "bytes"]])
print("Estado de lectura:")
display(catalogo.groupby("status", dropna=False).size().to_frame("archivos"))
```

Activa explícitamente `compute_sha256=True`, recorre las fuentes con `inventory` y aplana sus metadatos mediante `catalog_frame`. La tabla separa ruta, papel, estado, filas y bytes; el agrupamiento final muestra cuántos archivos tienen cada estado. Leer hashes tiene coste de disco proporcional al volumen de las fuentes, aunque las previsualizaciones sean pequeñas. El parámetro puede ponerse a falso para explorar, pero B requiere una A satisfactoria con hashes completos; no sería una sustitución equivalente del procedimiento reproducible.

#### NB00 · Celda 8 — Fuentes canónicas candidatas e incidencias

Posición 9 del cuaderno; contador guardado: 20. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
por_ruta = {item["path"]: item for item in registros}
fuentes = {alias: local_path(ROOT, name) for alias, name in CONFIG["canonical_candidates"].items()}
canonicas = pd.DataFrame([
    {"alias": alias, "archivo": path.name, "existe": path.is_file(),
     "estado": por_ruta.get(path.relative_to(ROOT).as_posix(), {}).get("status", "ausente")}
    for alias, path in fuentes.items()
])
display(canonicas)
display(catalogo[catalogo.status.isin(["sin_datos", "error", "auxiliar_sin_raster"])][["path", "status", "error"]])
errores_lectura = catalogo[catalogo.status.eq("error")]
print("Errores de lectura:", len(errores_lectura))
print("Los archivos sin datos se catalogan; no se sustituyen por tablas inventadas.")
```

Construye `por_ruta` para consultar rápidamente el inventario y `fuentes` para traducir alias como `contactos_geode` a nombres reales. Después comprueba existencia y estado de cada candidata, y muestra archivos vacíos, errores y XML auxiliares sin TIFF. `errores_lectura` se conserva para el cierre. Que `IndiciosII.gpkg` sea la fuente canónica candidata significa que las siguientes fases parten de ella; no declara resueltas sus discrepancias con CSV y Excel.

#### NB00 · Celda 10 — Carga de las tres copias de indicios

Posición 11 del cuaderno; contador guardado: 21. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
indicios = read_vector(fuentes["indicios"], max_features=None, allow_full=True)
indicios_csv = read_table(ROOT / "IndiciosII.csv", nrows=None)
indicios_excel = read_table(ROOT / "Indicios.xlsx", nrows=None)
tablas = {"indicios_csv": indicios_csv, "indicios_excel": indicios_excel}
vectores = {"indicios": indicios}

resumen_indicios = pd.DataFrame([
    {"fuente": name, "filas": len(table),
     "codigos_distintos": table["Codigo_indicio"].nunique(),
     "crs_geometria": str(getattr(table, "crs", "No contiene geometría"))}
    for name, table in [("GPKG", indicios), ("CSV", indicios_csv), ("Excel", indicios_excel)]
])
display(resumen_indicios)
display(indicios.head())
display(indicios_csv.head())
print("Primer código CSV:", repr(indicios_csv.iloc[0]["Codigo_indicio"]))
```

Carga la geometría completa del GPKG y lee CSV/Excel como texto. Conserva tres objetos separados y calcula filas, códigos únicos y CRS. Esto evita que versiones sucesivas de los mismos indicios se sumen como observaciones independientes. La impresión con `repr` del primer código sirve para comprobar que se mantienen ceros iniciales. Las diferencias de unicidad que aparecen aquí explican por qué una unión o concatenación ingenua multiplicaría la evidencia.

#### NB00 · Celda 12 — Vectores completos moderados y muestras de capas grandes

Posición 13 del cuaderno; contador guardado: 22. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
for alias in ("litologia", "edades"):
    record = por_ruta[fuentes[alias].relative_to(ROOT).as_posix()]
    if record.get("row_count", 0) > CONFIG["inspection"]["max_full_vector_features"]:
        raise RuntimeError(f"{alias}: supera el límite de carga completa; utilizar muestra o bbox.")
    vectores[alias] = read_vector(fuentes[alias], max_features=None, allow_full=True)

muestras_vectores = {}
for record in registros:
    if record["format"] != ".gpkg" or record["status"] in ("sin_datos", "error"):
        continue
    for layer in record["details"]["layers"]:
        key = record["path"] + "|" + layer["table_name"]
        muestras_vectores[key] = read_vector(local_path(ROOT, record["path"]),
                                             layer=layer["table_name"], max_features=5,
                                             read_geometry=False)
hidrografia_muestra = read_vector(fuentes["hidrografia"], max_features=100)
print("Vectores completos:", {key: len(value) for key, value in vectores.items()})
print("Capas internas con muestra de atributos:", len(muestras_vectores))
display(vectores["litologia"].head())
display(hidrografia_muestra.head())
```

Carga litología y edades completas sólo si el recuento inventariado no supera `max_full_vector_features`. Para cada capa interna de cada GPKG no vacío obtiene cinco registros de atributos con `read_geometry=False`, lo que evita convertir curvas durante ese muestreo. Añade cien geometrías hidrográficas. Se separan así cargas completas de tablas manejables y lecturas parciales de capas millonarias. Las primeras filas de una capa no constituyen una muestra representativa de todos sus tipos o territorios.

#### NB00 · Celda 13 — Visualización del diccionario de muestras

Posición 14 del cuaderno; contador guardado: 23. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
display(muestras_vectores)
```

Muestra `muestras_vectores`, creado en la celda anterior. No transforma ni persiste información. Es una celda exploratoria que puede producir una salida muy extensa; su utilidad es inspeccionar nombres y atributos. No sustituye una comprobación sistemática de tipos, nulos, dominios y geometrías completas.

#### NB00 · Celda 15 — Prueba de transformación y previsualización de curvas

Posición 16 del cuaderno; contador guardado: 24. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
from pyproj import Transformer

tr = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
easting, northing = tr.transform(-3.0, 40.0)
assert abs(easting - 500000) < 1
assert 4_400_000 < northing < 4_500_000

curvas_preview = read_vector(fuentes["contactos_geode"], max_features=5,
                             allow_curve_conversion=True)

display(curvas_preview.head())
print("CRS nativo de curvas:", curvas_preview.crs)
print("Geometrías devueltas por GDAL:", curvas_preview.geom_type.unique())
assert len(curvas_preview) > 0 and curvas_preview.crs is not None

# Recorte de demostración; NO fija el piloto del proyecto.
indicios_recorte = read_vector(fuentes["indicios"], bbox=(-7.5, 42.0, -5.0, 43.5),
                               bbox_crs="EPSG:4326", max_features=100)
display(indicios_recorte.head())
```

Transforma el punto de longitud −3°, latitud 40° de EPSG:4326 a EPSG:25830 con `always_xy=True`. Comprueba que el meridiano central produce aproximadamente 500.000 m de este y un norte plausible. Después autoriza una muestra de cinco curvas GEODE y comprueba que el lector devuelve datos con CRS. Finalmente lee un recorte de indicios con `bbox_crs` explícito. Son pruebas de funcionamiento del entorno, no selección del piloto ni certificación nacional de la conversión de curvas.

#### NB00 · Celda 16 — Segunda muestra de contactos

Posición 17 del cuaderno; contador guardado: 25. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
contactos = read_vector(fuentes["contactos_geode"], read_geometry=True, max_features=100, allow_curve_conversion=True)
display(contactos.head())
```

Lee cien entidades de contactos con geometría y conversión de curvas permitida. Amplía la inspección visual de la celda anterior; no crea una capa armonizada ni calcula distancias. `display(contactos.head())` sólo muestra cinco filas de las cien cargadas. Repetir la celda vuelve a leer la fuente, sin modificarla.

#### NB00 · Celda 18 — Tablas de muestra y lectura por bloques

Posición 19 del cuaderno; contador guardado: 26. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
muestras_tablas = {
    item["path"]: read_table(local_path(ROOT, item["path"]), nrows=5,
                             encoding=CONFIG["inspection"]["csv_encoding"],
                             sep=CONFIG["inspection"]["csv_separator"])
    for item in registros if item["format"] in (".csv", ".xlsx") and item["status"] != "error"
}
display(pd.DataFrame([{"archivo": key, "columnas": len(value.columns), "filas_muestra": len(value)}
                      for key, value in muestras_tablas.items()]))
with iter_csv(ROOT / "ContactosFallasMagna50.csv", chunksize=1000) as bloques:
    primer_bloque_contactos = next(bloques)
display(primer_bloque_contactos.head())
```

Genera una muestra de cinco filas para cada CSV y Excel legible, respetando la codificación y separador del YAML. Resume columnas y tamaño de muestra. Después abre `ContactosFallasMagna50.csv` como lector por bloques y extrae el primero, de mil filas, dentro de un gestor de contexto que cierra el recurso. Este bloque demuestra lectura escalable; no cuenta aquí toda la tabla ni recupera geometría desde los atributos tabulares.

#### NB00 · Celda 20 — Metadatos de bandas y ventanas de ráster

Posición 21 del cuaderno; contador guardado: 27. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
rasters = {item["path"]: local_path(ROOT, item["path"])
           for item in registros if item["format"] in (".tif", ".tiff") and item["status"] != "error"}
bandas = []
for item in registros:
    if item["path"] not in rasters:
        continue
    meta = item["details"]
    for index, description in enumerate(meta["descriptions"], 1):
        bandas.append({"archivo": item["path"], "banda": index, "descripcion": description,
                       "crs": meta["crs"], "resolucion": meta["resolution"],
                       "nodata": meta["nodata"], "uso": item["role"]})
bandas = pd.DataFrame(bandas)
display(bandas)

au_preview, au_meta = read_raster_preview(fuentes["geoquimica_au"], band=1)
mdt_preview, mdt_meta = read_raster_preview(fuentes["relieve"], band=1)
au_ventana, ventana_meta = read_raster_window(fuentes["geoquimica_au"],
    col_off=1000, row_off=600, width=128, height=128, bands=(1, 2, 3, 4))
print("Ventana nativa Au:", au_ventana.shape, "— con máscara:", np.ma.isMaskedArray(au_ventana))
print("Clases observadas en la vista reducida:", np.unique(au_preview.compressed()))
```

Reúne rutas de TIFF legibles y crea una fila descriptiva por banda: índice, descripción, CRS, resolución, NoData y uso previsto. Genera vistas reducidas de Au y elevación y una ventana nativa de 128×128 píxeles con cuatro bandas de Au. `compressed()` elimina elementos enmascarados para enumerar clases visibles. La vista usa vecino más próximo y sirve para inspección; las clases observadas en ella pueden no incluir todas las clases del ráster original.

#### NB00 · Celda 21 — Figura de geoquímica y elevación

Posición 22 del cuaderno; contador guardado: 28. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
import matplotlib.pyplot as plt

fig, axes = plt.subplots(1, 2, figsize=(12, 5))
for ax, array, meta, title, cmap in [
    (axes[0], au_preview, au_meta, "Au: clases cartográficas (vista reducida)", "viridis"),
    (axes[1], mdt_preview, mdt_meta, "Elevación original: revisión pendiente", "terrain"),
]:
    left, bottom, right, top = meta["bounds"]
    artist = ax.imshow(array, extent=(left, right, bottom, top), origin="upper", cmap=cmap)
    ax.set_title(title)
    ax.set_xlabel("X · EPSG:25830")
    ax.set_ylabel("Y · EPSG:25830")
    fig.colorbar(artist, ax=ax, shrink=.7)
plt.tight_layout()
plt.show()
```

Representa las dos vistas reducidas con la extensión espacial de sus metadatos, dos paletas y barras de color. `origin='upper'` refleja el orden de filas de los rásteres. El eje se rotula como EPSG:25830 de forma literal: convendría derivar esa etiqueta del CRS comprobado si se amplía el lector a fuentes distintas. El mapa de Au visualiza códigos de clases, aunque la barra continua de colores pueda sugerir otra lectura; no es un mapa de concentraciones analíticas ni de prospectividad.

#### NB00 · Celda 22 — Inspección específica del shapefile hidrográfico

Posición 23 del cuaderno; contador guardado: 29. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
shapefiles = [local_path(ROOT, item["path"]) for item in registros
              if item["format"] == ".shp" and item["status"] != "error"]
muestras_shp = {path.name: read_vector(path, max_features=5) for path in shapefiles}

#imprimir de la primera linea de cada shapefile, la variable geometry, pero que no se corte al mostrarla

print(muestras_shp["red-hidrografica2022-27_marzo2023.shp"].geometry.head())
```

Construye de nuevo un diccionario de muestras de shapefiles y accede al nombre exacto `red-hidrografica2022-27_marzo2023.shp`. Imprime sus geometrías. La celda fallaría con `KeyError` si cambiase el nombre o no existiera esa fuente, aunque el descubrimiento general funcionase. El comentario pide que la geometría no se corte, pero `geometry.head()` no configura por sí mismo una impresión íntegra de WKT; el resultado sigue sujeto al formato de visualización de pandas/GeoPandas.

#### NB00 · Celda 24 — Shapefiles y referencias QGIS

Posición 25 del cuaderno; contador guardado: 30. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
shapefiles = [local_path(ROOT, item["path"]) for item in registros
              if item["format"] == ".shp" and item["status"] != "error"]
muestras_shp = {path.name: read_vector(path, max_features=5) for path in shapefiles}
for name, sample in muestras_shp.items():
    print(name, "CRS:", sample.crs)
    display(sample.head())
referencias_qgis = pd.DataFrame([ref for item in registros
                               for ref in item["details"].get("references", [])])
display(referencias_qgis)
if not referencias_qgis.empty:
    display(referencias_qgis[referencias_qgis.local_exists.eq(False)])
```

Repite las muestras de shapefile, muestra sus CRS y primeras filas y reúne referencias extraídas del QGZ. `inspect_qgis` abre el ZIP y el XML local, sin consultar servicios. El filtro `local_exists.eq(False)` identifica rutas locales rotas; los servicios remotos se registran con existencia local no aplicable. Es un diagnóstico de referencias: la visibilidad de una capa remota en QGIS no significa que sus datos cuantitativos estén descargados.

#### NB00 · Celda 26 — Escritura de informes de A

Posición 27 del cuaderno; contador guardado: 31. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
RUN_DIR = write_reports(ROOT, CONFIG, registros)
write_json(RUN_DIR / "resumen_indicios.json", resumen_indicios.to_dict("records"))
bandas.to_csv(RUN_DIR / "bandas_raster.csv", index=False, encoding="utf-8-sig")
canonicas.to_csv(RUN_DIR / "fuentes_canonicas.csv", index=False, encoding="utf-8-sig")
fig.savefig(RUN_DIR / "vista_previa_rasters.png", dpi=130, bbox_inches="tight")
print("Resultados:", RUN_DIR)
display(pd.read_json(RUN_DIR / "pendientes.json"))
```

`write_reports` crea una carpeta de ejecución bajo el directorio configurado y escribe manifiesto, catálogo, configuración, entorno y pendientes. También congela todas las distribuciones instaladas en `environment.freeze.txt` y registra un hash de los tipos/fuentes de las celdas de 00, excluyendo outputs y metadatos de ejecución. Esta celda añade resumen de indicios, bandas, fuentes canónicas y la figura previamente creada. `RUN_DIR` identifica el producto que podrán consumir las fases siguientes. Los pendientes proceden de la configuración y pueden necesitar actualización cuando se recuperan nuevas fuentes: no son una comprobación automática de todas las necesidades científicas.

#### NB00 · Celda 28 — Integridad y cierre de carga

Posición 29 del cuaderno; contador guardado: 32. Fuente: [00_configuracion_y_fuentes.ipynb](../../notebooks/00_configuracion_y_fuentes.ipynb).

```python
cambios = verify_unchanged(ROOT, registros, rehash=CONFIG["inspection"]["compute_sha256"])
control = {
    "fuentes_inspeccionadas": len(registros),
    "errores_lectura": len(errores_lectura),
    "fuentes_sin_datos": int(catalogo.status.eq("sin_datos").sum()),
    "fuentes_modificadas": cambios,
    "hashes_completos": all(item["sha256"] for item in registros),
    "estado": "carga_local_completada" if not cambios and errores_lectura.empty else "requiere_resolver_errores",
    "limpieza_geologica_realizada": False,
    "datos_remotos_descargados": False,
}
write_json(RUN_DIR / "control_cierre.json", control)
display(pd.Series(control, dtype=object).to_frame("resultado"))
assert not cambios, "Las fuentes cambiaron durante la ejecución; revisar antes de continuar."
assert errores_lectura.empty, f"Hay {len(errores_lectura)} errores. Consulta manifest.json."
print("Carga local finalizada. Fuentes disponibles en `fuentes`, `vectores`, `tablas` y `rasters`.")
print("Siguiente tarea: conciliar indicios y revisar sus coordenadas y etiquetas.")
```

Reverifica tamaño, fechas y hashes conforme a `verify_unchanged`, construye `control_cierre.json` y exige que no haya originales modificados ni errores de lectura. `hashes_completos` informa si todas las fuentes están identificadas por contenido. Mantiene expresamente sin realizar la limpieza geológica y sin descargas remotas. La salida habilita la carga de B, pero no significa que se hayan resuelto licencias, revisión de leyendas, geometría completa o ámbito del piloto.

### 4.2. Relación con el plan

La fase A implementa bien el inventario local, la trazabilidad y los lectores. La especificación geológica y el piloto continúan pendientes. El paso 06 se ha concretado principalmente como registro de carencias y catálogo de entradas; el notebook no ejecuta un proceso de recuperación remota. Los archivos añadidos posteriormente se reconocen mediante nuevos inventarios, por lo que los nueve GPKG vacíos de la auditoría de septiembre 5 no describen el estado de septiembre 8.

## 5. Notebook 01 — Indicios, limpieza y etiquetas

Corresponde a B, pasos 07–12. Parte de una A satisfactoria y de `config/labels.yaml`. Produce conciliación, inventario normalizado, cuarentena, candidatos, relaciones de proximidad y plantilla de revisión. El módulo [labels.py](../../src/geoau/labels.py) conserva evidencia original y evita declarar negativos geológicos.

### 5.1. Lógica de etiquetas y dependencia

`normalize` aplica Unicode NFKC, reduce espacios y trata una lista explícita de tokens nulos. `key` elimina acentos y diferencias de mayúsculas para comparar. `substance_tokens` separa coma, punto y coma y barra vertical; no separa `/` porque puede formar parte de una descripción mineral. Au se reconoce por igualdad exacta con `oro`/`au`, evitando coincidencias parciales.

`normalize_indicios` conserva atributos con sufijo `_raw`, WKT y CRS original. Reproyecta a 4326 y asigna `record_id = gpkg:<hash de fuente>:<fila>`. Es estable para esa copia y orden de lectura, no un identificador geológico universal. La morfología `Filoniana` sugiere roca y `Aluvionar` sugiere aluvial; otras morfologías quedan desconocidas y ninguna se declara automáticamente orogénica.

`geometry_qc` comprueba punto válido, coordenadas finitas, rangos y ventanas de plausibilidad. Puede contrastar una máscara y límites administrativos si se aportan. En la configuración actual faltan esos dos apoyos y el archivo de revisión. Una geometría puede superar plausibilidad y seguir sin estar contrastada provincialmente. X/Y tabulares se comparan geodésicamente sólo si podrían ser longitud/latitud; no se infiere su CRS ni se desplaza el punto a ciegas.

`group_candidates` calcula distancias geodésicas entre pares y componentes conexas a 250, 500 y 1.000 m. Para 790 candidatos su coste cuadrático es manejable; no escalaría igual a millones de puntos. Sus IDs derivan de los miembros y cambian cuando éstos cambian. `define_labels` exige confirmación de presencia, validación geométrica y código no duplicado para P revisado. Los IDs de depósito y distrito proceden exclusivamente de revisión documental.

#### NB01 · Celda 1 — Configuración de la fase B

Posición 2 del cuaderno; contador guardado: 1. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
from pathlib import Path
import sys, json
import pandas as pd
import numpy as np
import geopandas as gpd
import yaml
from IPython.display import display

PROJECT_ROOT_OVERRIDE = None
start = Path(PROJECT_ROOT_OVERRIDE or Path.cwd()).resolve()
candidates = [p for parent in (start, *start.parents) for p in (parent, parent / "Proyecto Con Luis")]
ROOT = next((p for p in candidates if (p / "config/labels.yaml").is_file()
             and (p / "src/geoau/labels.py").is_file()), None)
if ROOT is None:
    raise FileNotFoundError("Indica PROJECT_ROOT_OVERRIDE o abre el notebook dentro del proyecto.")
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))

from geoau.local_sources import local_path, read_table, read_vector, sha256_file, verify_unchanged, write_json
from geoau.labels import (load_phase_a, reconcile, normalize_indicios, apply_reviews, geometry_qc,
                         group_candidates, define_labels, coverage_at_points, export_phase_b)
CONFIG = yaml.safe_load((ROOT / "config/labels.yaml").read_text(encoding="utf-8"))
assert CONFIG["schema_version"] == 1
assert CONFIG["proposal_cluster_m"] in CONFIG["cluster_radii_m"]
assert CONFIG["xy_discrepancy_m"] >= 0 and min(CONFIG["cluster_radii_m"]) > 0
pd.set_option("display.max_colwidth", 90)
print("Python:", sys.executable)
display(pd.Series(CONFIG, dtype=object).to_frame("configuración"))
```

Localiza la raíz, importa el módulo y carga `labels.yaml`. Las aserciones comprueban versión de esquema, que el radio propuesto esté entre los radios evaluados y que las tolerancias tengan signo válido. Muestra la configuración, donde `review_file`, máscara y límites administrativos son actualmente nulos. NumPy y GeoPandas se importan antes de la comprobación de raíz; una dependencia ausente provocaría el error de importación correspondiente. Esta celda prepara el entorno, sin crear etiquetas por sí misma.

#### NB01 · Celda 2 — Carga de la A enlazada y huella de la fuente

Posición 3 del cuaderno; contador guardado: 2. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
A_RUN, MANIFEST_A, CONFIG_A, originales = load_phase_a(ROOT, CONFIG)
canonical_name = CONFIG_A["canonical_candidates"]["indicios"]
CONFIG["source_sha256"] = next(r["sha256"] for r in MANIFEST_A["sources"] if r["path"] == canonical_name)
print("Fase A utilizada:", A_RUN)
display(pd.DataFrame([{"fuente": k, "filas": len(v), "columnas": len(v.columns)} for k,v in originales.items()]))
```

`load_phase_a` busca la última ejecución satisfactoria si no se fija una ruta. Revalida las fuentes inventariadas y exige los campos necesarios de GPKG/CSV/Excel. Añade a `CONFIG` el hash de la base canónica que se usará en `record_id`. La tabla muestra cuántas filas y columnas tiene cada fuente. Seleccionar una A diferente puede cambiar IDs y volver incompatibles las revisiones anteriores: es una protección de versión, no una pérdida accidental de ceros de código.

#### NB01 · Celda 3 — Exploración de la base completa

Posición 4 del cuaderno; contador guardado: 3. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
display(originales["gpkg"])
```

Muestra `originales['gpkg']` sin modificarlo. La representación de Jupyter normalmente limita filas/columnas, aunque el objeto contiene toda la base. Esta vista ayuda a reconocer atributos, pero no sustituye un análisis completo de nulos, coordenadas o sustancias. No aporta nuevas observaciones al conjunto.

#### NB01 · Celda 4 — Celda vacía

Posición 5 del cuaderno; contador guardado: sin contador. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
# Celda original vacía; no contiene instrucciones.
```

No contiene instrucciones, no tiene efecto en el estado y no acredita una etapa implementada. Se registra para mantener correspondencia exacta entre el informe y las posiciones reales del notebook.

#### NB01 · Celda 6 — Primera conciliación y visualización completa

Posición 7 del cuaderno; contador guardado: 4. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
conciliacion, duplicados_fuentes = reconcile(originales, CONFIG["gold_tokens"])
display(conciliacion)
```

`reconcile` agrupa cada fuente por código normalizado y compara conjuntos de valores. Produce una fila por código, conteos por fuente y banderas de discrepancia, además de una tabla independiente de códigos repetidos. La celda muestra el resultado completo. No concatena registros de las tres copias. El cálculo se repite inmediatamente en la celda 7; esta primera llamada es redundante desde el punto de vista del flujo reproducible.

#### NB01 · Celda 7 — Conciliación, resumen de duplicados y Au fuera de la base

Posición 8 del cuaderno; contador guardado: 5. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
conciliacion, duplicados_fuentes = reconcile(originales, CONFIG["gold_tokens"])
display(conciliacion.head())
display(pd.DataFrame([
    {"fuente": source, "codigos_presentes": int(conciliacion[f"n_{source}"].gt(0).sum()),
     "codigos_repetidos": int(conciliacion[f"n_{source}"].gt(1).sum())}
    for source in originales
]))
display(conciliacion[conciliacion.conflicto_au].head(20))
au_solo_copias = conciliacion[conciliacion.n_gpkg.eq(0) &
    (conciliacion.au_csv.fillna(False).eq(True) | conciliacion.au_excel.fillna(False).eq(True))]
print("Códigos con Au en otras copias y ausentes del GPKG:", len(au_solo_copias))
display(au_solo_copias)
```

Vuelve a calcular los dos objetos anteriores. Resume códigos presentes y repetidos por fuente; muestra conflictos de Au y localiza códigos auríferos presentes en CSV/Excel pero ausentes del GPKG. `au_solo_copias` queda disponible para exportación. El uso de `fillna(False)` aquí sólo responde a si una copia contiene evidencia textual para ese código; no convierte territorio U en ausencia geológica. Los casos extra se entregan para conciliación y no se añaden automáticamente como positivos.

#### NB01 · Celda 9 — Conteo inicial de valores nulos

Posición 10 del cuaderno; contador guardado: 6. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
originales["gpkg"].isna().sum()
```

`isna().sum()` cuenta nulos reconocidos por pandas en la base vectorial. Es una inspección previa a la normalización. No incluye necesariamente cadenas vacías, espacios o expresiones como `s/d`, que se tratarán después. La salida no es suficiente para concluir que un atributo esté completo desde el punto de vista semántico.

#### NB01 · Celda 10 — Normalización y propagación de conflictos

Posición 11 del cuaderno; contador guardado: 7. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
normalizados = normalize_indicios(originales["gpkg"], CONFIG)
flags = conciliacion.set_index("Codigo_indicio")["conflicto_au"]
normalizados["conflicto_au"] = normalizados.Codigo_indicio.map(flags).fillna(False).astype(bool)
assert len(normalizados) == len(originales["gpkg"])
assert normalizados.record_id.is_unique
display(normalizados[["Codigo_indicio_raw", "Codigo_indicio", "Sustancia_raw", "sustancias_tokens",
                       "au_observado", "label_observada", "Morfologia", "tipo_au_propuesto"]].head(12))
display(normalizados.groupby(["au_observado","tipo_au_propuesto"], dropna=False).size().to_frame("registros"))
```

Crea el inventario normalizado y agrega `conflicto_au` mediante una correspondencia por `Codigo_indicio`. Las aserciones conservan número de registros e IDs únicos. La selección mostrada relaciona texto original, tokens, etiqueta observada y tipología propuesta. Esta celda intenta mantener los conflictos visibles junto a cada registro; sin embargo, la siguiente vuelve a crear `normalizados` y pierde esa columna. El comportamiento se ha reproducido sobre la base local sin exportar cambios.

#### NB01 · Celda 11 — Segunda normalización que sobrescribe la anterior

Posición 12 del cuaderno; contador guardado: 8. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
normalizados = normalize_indicios(originales["gpkg"], CONFIG)
assert len(normalizados) == len(originales["gpkg"])
assert normalizados.record_id.is_unique
display(normalizados[["Codigo_indicio_raw", "Codigo_indicio", "Sustancia_raw", "sustancias_tokens",
                       "au_observado", "label_observada", "Morfologia", "tipo_au_propuesto"]].head(12))
display(normalizados.groupby(["au_observado","tipo_au_propuesto"], dropna=False).size().to_frame("registros"))
```

Repite `normalize_indicios` y asigna su resultado al mismo nombre `normalizados`. Conserva atributos originales y vuelve a comprobar filas/IDs, pero **elimina `conflicto_au` añadido en la celda 10**, ya que la función no lo crea. La tabla de conciliación independiente continúa existiendo y los conflictos no desaparecen de todos los informes; lo que se pierde es su propagación al inventario que se usa después. Conviene dejar una sola normalización y un único bloque posterior de enriquecimiento de conflictos.

#### NB01 · Celda 12 — Vista de los registros con Au observado

Posición 13 del cuaderno; contador guardado: 9. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
au_observados = normalizados[normalizados.au_observado]

display(au_observados)

au_observados.isna().sum()
```

Filtra `au_observado` para obtener `au_observados`, muestra el subconjunto y cuenta sus nulos. Es diagnóstico, no selección de P revisados. Más adelante `candidatos` también puede incluir registros confirmados documentalmente que no contengan Au en el texto original, por lo que ambos subconjuntos no tienen por qué coincidir si se incorporan revisiones.

#### NB01 · Celda 14 — Entradas opcionales y revisión documentada

Posición 15 del cuaderno; contador guardado: 10. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
extra_inputs = []
def optional_input(config_key):
    name = CONFIG.get(config_key)
    if not name:
        return None
    path = local_path(ROOT, name)
    if not path.is_file():
        raise FileNotFoundError(path)
    extra_inputs.append({"role": config_key, "path": str(path.relative_to(ROOT)), "sha256": sha256_file(path)})
    if path.suffix.lower() == ".shp":
        for ext in (".dbf", ".shx", ".prj", ".cpg"):
            part = path.with_suffix(ext)
            if part.is_file():
                extra_inputs.append({"role": config_key+ext, "path": str(part.relative_to(ROOT)), "sha256": sha256_file(part)})
    return path

review_path = optional_input("review_file")
revision = read_table(review_path, nrows=None) if review_path else None
normalizados, decisiones = apply_reviews(normalizados, revision)
print("Decisiones incorporadas:", len(decisiones))
```

Define `optional_input`, que resuelve una ruta configurada, exige su existencia y guarda su SHA-256. Si es shapefile, añade componentes auxiliares existentes. Lee el CSV de revisión si se especifica y ejecuta `apply_reviews`. Cada decisión sustantiva requiere ID de esta versión, valores permitidos, revisor, fecha, evidencia y motivo. Una corrección de coordenadas exige longitud y latitud juntas y geometría marcada como validada. Con la configuración actual no se incorpora ninguna decisión; los campos de revisión quedan vacíos.

#### NB01 · Celda 16 — Control geométrico

Posición 17 del cuaderno; contador guardado: 11. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
mask_path, admin_path = optional_input("territory_mask"), optional_input("admin_boundaries")
mascara = read_vector(mask_path, layer=CONFIG["territory_layer"], max_features=None, allow_full=True) if mask_path else None
limites = read_vector(admin_path, layer=CONFIG["admin_layer"], max_features=None, allow_full=True) if admin_path else None
qc = geometry_qc(normalizados, CONFIG, mask=mascara, admin=limites)
display(qc.groupby(["geo_cuarentena", "motivo_geo"],dropna=False).size().to_frame("registros"))
display(qc.xy_estado.value_counts().to_frame("registros"))
display(qc.loc[qc.geo_cuarentena, ["record_id","Codigo_indicio","Nombre_mina","Provincia","lon","lat","motivo_geo"]])
print("No se han inferido coordenadas para registros en cuarentena.")
```

Carga máscara y límites sólo si están configurados, y llama a `geometry_qc`. Muestra cuarentenas, estados de X/Y e identificadores de registros problemáticos. Las ventanas geográficas amplias descartan incoherencias graves pero contienen también territorio extranjero y mar; no reemplazan fronteras. El resultado local de B contiene tres registros generales en cuarentena y ninguno de los 790 Au. Esto acredita el control básico ejecutado, no validación provincial ni revisión experta de sus posiciones.

#### NB01 · Celda 17 — Inspección de coordenadas tabulares de CRS desconocido

Posición 18 del cuaderno; contador guardado: 12. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
display(qc[qc["xy_estado"] == "crs_tabular_desconocido"].head(10))
display(qc[qc["xy_estado"] == "crs_tabular_desconocido"].geometry.head(10))
#recoger filas donde x_raw es igual que lon y y_raw igual que lat 
#normalizados[normalizados["X_raw"].eq(normalizados["lon"]) & normalizados["Y_raw"].eq(normalizados["lat"])]
#normalizados["X_raw"]
```

Muestra diez filas cuyo X/Y no puede compararse razonablemente como longitud/latitud y sus geometrías. No convierte esas columnas ni corrige el GPKG. Los comentarios inferiores son fragmentos exploratorios inactivos. Es importante que una geometría usable y unos X/Y de CRS desconocido pueden coexistir: el proyecto conserva esa discrepancia para investigar la procedencia de ambas representaciones.

#### NB01 · Celda 19 — Estados de confirmación

Posición 20 del cuaderno; contador guardado: 13. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
display(qc.estado_presencia.value_counts(dropna=False).to_frame("registros"))
```

Cuenta `estado_presencia`, incluyendo nulos. Permite distinguir decisiones documentadas de campos vacíos. No realiza confirmaciones ni asigna tipología. En ausencia del archivo de revisión, el predominio de valores vacíos es esperado y explica por qué la fase B no produce positivos revisados.

#### NB01 · Celda 20 — Candidatos, posiciones y grupos de proximidad

Posición 21 del cuaderno; contador guardado: 14. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
# Una confirmación documentada puede incorporar un registro sin Au en el texto original.
candidatos = qc[qc.au_observado | qc.estado_presencia.eq("confirmada")].copy()
candidatos, pares, sensibilidad = group_candidates(candidatos, CONFIG["cluster_radii_m"])
display(sensibilidad)
coincidentes = candidatos[candidatos.position_id.notna() & candidatos.position_id.duplicated(keep=False)]
display(coincidentes[["Codigo_indicio","Nombre_mina","Morfologia","position_id","lon","lat"]])
representantes_posicion = candidatos[candidatos.position_id.notna()].sort_values("record_id").drop_duplicates("position_id")
print("Registros candidatos:",len(candidatos), "Posiciones distintas localizables:", len(representantes_posicion))
display(pares.head(15))
```

Selecciona registros con Au observado o presencia confirmada y calcula posiciones exactas, pares cercanos y sensibilidad de componentes. Muestra posiciones compartidas y obtiene un representante por posición ordenando `record_id`. Este representante es una elección técnica determinista, no el indicio de mayor confianza ni un depósito único. `group_candidates` conserva filas pero no agrupa como válidas aquellas en cuarentena o rechazadas; los grupos resultantes no sustituyen a `deposit_id`.

#### NB01 · Celda 22 — Inspección de un grupo concreto

Posición 23 del cuaderno; contador guardado: 15. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
display(candidatos[candidatos["proximity_group_500m"] == "prox500_96cac903f1250bae"])
```

Filtra un ID de proximidad literal a 500 m. La salida depende de esa versión de fuentes y de la composición del grupo. Si cambian datos o IDs puede quedar vacía sin lanzar error; por eso no es una prueba ni una regla reutilizable de selección. No modifica `candidatos`.

#### NB01 · Celda 23 — Segunda celda vacía

Posición 24 del cuaderno; contador guardado: sin contador. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
# Celda original vacía; no contiene instrucciones.
```

No ejecuta código. Se conserva en el inventario para explicar por qué los índices no son consecutivos al contar únicamente operaciones sustantivas.

#### NB01 · Celda 24 — Mapa de grupos con modificación del objeto de trabajo

Posición 25 del cuaderno; contador guardado: 16. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Asegurar que lon y lat son numéricos
candidatos['lon'] = pd.to_numeric(candidatos['lon'], errors='coerce')
candidatos['lat'] = pd.to_numeric(candidatos['lat'], errors='coerce')
candidatos = candidatos.dropna(subset=['lon', 'lat'])

# 2. Generar IDs enteros deterministas para los grupos (rápido y vectorizado)
cluster_ids, _ = pd.factorize(candidatos['proximity_group_500m'])

# Paleta discreta de alto contraste cíclica para muchos grupos
cmap = plt.get_cmap('tab20')
colores = cmap(cluster_ids % 20)

# 3. Crear el lienzo/recuadro
fig, ax = plt.subplots(figsize=(10, 8), facecolor='white')

# Proporción 1:1 obligatoria para que el mapa no se aplaste o estire
ax.set_aspect('equal')

# 4. Dibujar todos los puntos de golpe en el espacio de coordenadas
scatter = ax.scatter(
    candidatos['lon'],
    candidatos['lat'],
    c=colores,
    s=200,             # Tamaño del punto adaptado a alta densidad
    alpha=0.4,        # Transparencia para ver zonas de sobreexposición/densidad
    edgecolors='none'
)

# 5. Configurar el recuadro para que actúe como marco cartográfico
ax.set_title("Distribución Espacial de Clústeres (Proyección Cartográfica)", fontsize=13, pad=12)
ax.set_xlabel("Longitud Oeste / Este (°)", fontsize=10)
ax.set_ylabel("Latitud Norte (°)", fontsize=10)

# Opcional: cuadrícula suave de referencia
ax.grid(True, linestyle='--', alpha=0.3, color='gray')

# Márgenes limpios alrededor de los puntos extremos
lon_min, lon_max = candidatos['lon'].min(), candidatos['lon'].max()
lat_min, lat_max = candidatos['lat'].min(), candidatos['lat'].max()
pad_x = (lon_max - lon_min) * 0.04
pad_y = (lat_max - lat_min) * 0.04

ax.set_xlim(lon_min - pad_x, lon_max + pad_x)
ax.set_ylim(lat_min - pad_y, lat_max + pad_y)

plt.tight_layout()
plt.show()
```

Convierte `lon`/`lat` a números, sustituye `candidatos` por su subconjunto sin nulos y factoriza IDs para asignar colores cíclicos de `tab20`. El mapa usa puntos grandes, transparencia, límites con margen y ejes de longitud/latitud. **El filtrado actúa sobre el mismo objeto que después alimenta `define_labels` y la exportación**: futuros candidatos sin coordenadas desaparecerían de esa rama, aunque permanezcan en el inventario general `qc`. Debe hacerse sobre una copia de visualización. En los 790 Au actuales no hay cuarentenas y no se ha demostrado una pérdida efectiva de filas por esta celda.

`set_aspect('equal')` iguala grados dibujados en ambos ejes; no convierte el gráfico en una proyección métrica ni corrige la diferencia de longitud física de un grado de longitud y de latitud. `factorize` da códigos según el orden de aparición: los colores son reproducibles para ese orden, no una identidad estable de grupo frente a reordenaciones.

#### NB01 · Celda 26 — Etiquetas finales y elegibilidad revisada

Posición 27 del cuaderno; contador guardado: 17. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
etiquetas = define_labels(candidatos)
display(etiquetas.groupby(["tipo_au_propuesto","tipologia_estado"],dropna=False).size().to_frame("registros"))
display(etiquetas[["elegible_general_revisada","elegible_roca_revisada","elegible_aluvial_revisada"]].sum().to_frame("positivos revisados"))
assert not etiquetas.label_au_final.eq("0").any()
assert not etiquetas.loc[etiquetas.geo_cuarentena,"elegible_general_revisada"].any()
```

`define_labels` conserva tipología propuesta cuando no hay revisión y separa la confianza de presencia. La elegibilidad general exige presencia confirmada y geometría validada; roca/aluvial exigen además tipología revisada específica. Los rechazados se rotulan como excluidos sin equivalencia con ausencia. Las aserciones impiden una etiqueta textual `0` y positivos revisados en cuarentena. El resultado actual es cero en las tres elegibilidades: el cuaderno prepara revisión, no la suplanta.

#### NB01 · Celda 28 — Cobertura puntual de candidatos

Posición 29 del cuaderno; contador guardado: 18. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
raster_aliases = {alias: local_path(ROOT, name) for alias,name in CONFIG_A["canonical_candidates"].items()
                  if alias.startswith("geoquimica_") or alias == "relieve"}
indexed_a = {r["path"]: r for r in MANIFEST_A["sources"]}
for alias, path in raster_aliases.items():
    record = indexed_a.get(path.relative_to(ROOT).as_posix())
    if not record or record["status"] in ("error","sin_datos"):
        raise RuntimeError(f"{alias} no está disponible en el manifiesto fase A.")
cobertura = coverage_at_points(etiquetas, raster_aliases)
display(pd.crosstab(cobertura.fuente, cobertura.estado))
sin_cobertura = cobertura[cobertura.estado.ne("valor_valido")]
display(sin_cobertura.head(20))
```

Selecciona los nueve rásteres geoquímicos y el MDT del catálogo A, comprueba que estén disponibles y muestrea su banda 1 en la geometría de cada candidato usable. `coverage_at_points` distingue valor válido, NoData, fuera de extensión y geometría no muestreada. La cobertura se calcula en el punto real; posteriormente la cobertura por celda puede ser diferente porque agrega superficie. Las tablas no imputan ni eliminan indicios sin valor.

#### NB01 · Celda 29 — Repetición de la tabla de cobertura

Posición 30 del cuaderno; contador guardado: 19. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
display(pd.crosstab(cobertura.fuente, cobertura.estado))
```

Vuelve a mostrar la tabla cruzada fuente/estado creada en la celda anterior. No repite el muestreo ni modifica `cobertura`. Es redundancia visual y puede retirarse en una limpieza editorial sin alterar el resultado del cálculo.

#### NB01 · Celda 31 — Representatividad territorial y tipológica

Posición 32 del cuaderno; contador guardado: 20. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
import matplotlib.pyplot as plt
fig, axes = plt.subplots(1, 2, figsize=(13,5))
plot_data = etiquetas.loc[~etiquetas.geo_cuarentena]
for tipo, group in plot_data.groupby("tipo_au_propuesto"):
    axes[0].scatter(group.lon, group.lat, s=8, alpha=.6, label=tipo)
axes[0].set(xlabel="Longitud", ylabel="Latitud", title="Au: tipología propuesta, EPSG:4326")
axes[0].legend()
top = etiquetas.Provincia.fillna("Sin provincia").value_counts().head(12)
top.sort_values().plot.barh(ax=axes[1], color="#356f91")
axes[1].set(title="Registros por provincia declarada", xlabel="Registros; no depósitos independientes")
plt.tight_layout()
plt.show()
display(etiquetas.groupby("Zona_Geode",dropna=False).size().to_frame("registros; dominio declarado"))
```

Dibuja candidatos localizables por tipología propuesta y un gráfico de registros por provincia declarada. Cuenta también registros por `Zona_Geode` declarada. Los ejes y títulos reconocen que los conteos son de registros; no se han depurado depósitos independientes ni se ha transformado `Zona_Geode` en distrito metalogenético. La concentración en unas provincias puede reflejar tanto geología como historia de observación y no permite separar ambas causas con estas figuras.

#### NB01 · Celda 33 — Exportación y cierre B

Posición 34 del cuaderno; contador guardado: 21. Fuente: [01_indicios_limpieza_etiquetas.ipynb](../../notebooks/01_indicios_limpieza_etiquetas.ipynb).

```python
RUN_DIR, control = export_phase_b(ROOT, CONFIG, A_RUN, MANIFEST_A, qc, etiquetas,
    conciliacion, duplicados_fuentes, decisiones, pares, sensibilidad, cobertura, extra_inputs)
au_solo_copias.to_csv(RUN_DIR / "au_ausentes_de_base_canonica.csv", index=False, encoding="utf-8-sig")
representantes_posicion.drop(columns="geometry").to_csv(RUN_DIR / "representantes_posicion_no_depositos.csv", index=False, encoding="utf-8-sig")
fig.savefig(RUN_DIR / "representatividad_au.png", dpi=140, bbox_inches="tight")
changes = verify_unchanged(ROOT, MANIFEST_A["sources"], rehash=True)
extra_changes = [r["path"] for r in extra_inputs if sha256_file(local_path(ROOT,r["path"])) != r["sha256"]]
control["fuentes_modificadas"] = changes
control["entradas_adicionales_modificadas"] = extra_changes
control["estado_ejecucion"] = "completada" if not changes and not extra_changes else "error_integridad"
write_json(RUN_DIR / "control_cierre.json", control)
assert not changes and not extra_changes, "Fuentes modificadas durante la ejecución: revisar trazabilidad."
print("Resultados:", RUN_DIR)
display(pd.Series(control, dtype=object).to_frame("resultado"))
```

`export_phase_b` conserva tablas de conciliación, decisiones, proximidad, cobertura, plantilla, candidatos y cuarentena; escribe GPKG y CSV e inventaría código y entradas. Sólo escribiría el GPKG de revisados si hubiera filas. La celda añade Au ausentes de la base, representantes de posición y la figura, y reverifica todas las fuentes de A y entradas adicionales. El cierre técnico no cierra científicamente B. B no publica un manifiesto final exhaustivo de hashes de sus salidas; C congela los productos B que consume al empezar, dejando constancia explícita de esa limitación temporal.

### 5.2. Valoración respecto al plan

La conciliación y preservación de originales están implementadas. La deduplicación llega a códigos y posiciones, y propone agrupaciones geométricas; la identificación geológica de depósitos/distritos y la tipología revisada siguen abiertas. El contraste administrativo opcional tampoco está activo. Las celdas 11 y 24 merecen corregirse antes de incorporar revisión real, porque introducen efectos de estado fuera del módulo probado.

## 6. Notebook 02 — Rejilla, armonización y cobertura

Corresponde a C, pasos 13–17. Recibe B, las fuentes inventariadas, una máscara local y `grid.yaml`. Genera la estructura territorial uniforme que permite pasar de registros puntuales a una matriz completa P/U. Utiliza [territory.py](../../src/geoau/territory.py) y [additional_layers.py](../../src/geoau/additional_layers.py).

### 6.1. Rejilla y agregación

La malla fuente tiene 2.200×1.820 píxeles de 500 m; la de destino, 1.100×910 celdas de 1 km. El origen es (−50.000, 4.860.000) m en EPSG:25830 y las filas avanzan hacia el sur. `grid_spec` impone estos dos tamaños de píxel y el ámbito peninsular implementado. Cambiar sólo `resolution_m` a 500 no activa una sensibilidad a 500 m: la función lo rechaza porque requiere otro contrato de extracción.

`land_areas` rasteriza el interior y calcula intersecciones exactas con la máscara en píxeles de borde. Comprueba que su suma conserve el área de la máscara. `aggregate_sum` reorganiza bloques 2×2 y suma. Para una celda, la fracción válida es `Σ área terrestre de píxeles válidos / Σ área terrestre de sus cuatro píxeles`. La media continua se pondera por esa área válida. Para categorías se suman áreas por clase, se normalizan sobre área válida y gana la moda de mayor área; los empates favorecen la clase menor.

`make_grid` conserva toda celda con tierra, calcula centros, fila/columna, área y elegibilidad costera desde 50 % de tierra. Los IDs codifican versión, fila y columna. No genera millones de polígonos para persistir la malla: la geometría es reconstruible desde la especificación. Las medidas de distorsión se calculan como diagnóstico muestreado en la proyección y no como certificado de equivalencia de áreas.

### 6.2. Armonización vectorial

La versión sin caché pagina por FID creciente y usa el índice RTree del GPKG para un recorte rectangular con margen de 20 km. Compara el recuento leído con una consulta independiente para detectar truncación. Reproyecta, elimina Z/M del cálculo 2D, repara geometrías inválidas y audita cambios. Los tipos incompatibles se ponen en cuarentena: el comentario sobre `GeometryCollection` es más amplio que el filtro real, que admite tipos lineales o poligonales simples/múltiples, no colecciones arbitrarias.

Para GEODE contrasta una muestra de linealización de curvas con pasos angulares de 1° y 0,5°, exigiendo una diferencia Hausdorff de hasta 1 m. No es una prueba sobre todas las curvas. La caché compara funciones mediante AST, parámetros, máscara, fuentes y hashes de los productos antes de copiar. Para polígonos estima huella mediante centros de píxeles de 500 m; para líneas registra presencia de trazas y no la interpreta como cobertura del levantamiento.

#### NB02 · Celda 2 — Inicialización y especificación espacial

Posición 3 del cuaderno; contador guardado: 35. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / "config/project.yaml").is_file())
if str(ROOT / "src") not in sys.path:
    sys.path.insert(0, str(ROOT / "src"))
import yaml
import numpy as np
import pandas as pd
import geopandas as gpd
import matplotlib.pyplot as plt
from IPython.display import display
from geoau.territory import (start_run, grid_spec, load_mask, land_areas, make_grid,
    feature_dictionary, align_rasters, harmonize_vectors, coverage_products, finish_run)
CONFIG = yaml.safe_load((ROOT / "config/grid.yaml").read_text(encoding="utf-8"))
SPEC = grid_spec(CONFIG)
pd.set_option("display.max_colwidth", 95)
print("Intérprete:", sys.executable)
display(pd.Series(CONFIG).to_frame("configuración"))
```

Detecta raíz, importa módulos y lee `grid.yaml`. `grid_spec` añade transformadas afines y formas a la configuración y valida el contrato implementado. Muestra el intérprete y los parámetros. A diferencia de 00/01, `next(...)` no usa un valor por defecto: abrir fuera del árbol esperado produce `StopIteration`, menos informativo que un error que solicite raíz. No realiza todavía geometría ni escritura de productos.

#### NB02 · Celda 4 — Inicio de C con entradas verificadas

Posición 5 del cuaderno; contador guardado: 36. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
RUN_DIR, FUENTES, MANIFEST_A, ENTRADAS_C, indicios = start_run(ROOT, CONFIG)
print("Resultados:", RUN_DIR)
display(indicios.Codigo_indicio_raw)
print("Candidatos de B:", len(indicios))
print("Positivos revisados de B:", int(indicios.elegible_general_revisada.sum()))
display(indicios[["record_id", "Codigo_indicio", "Provincia", "tipo_au_propuesto",
                  "elegible_general_revisada"]].head())
```

`start_run` comprueba el cierre B, localiza su A enlazada, valida fuentes y entradas, verifica procedencia de la máscara y congela archivos de entrada. Crea la carpeta de ejecución y sus subdirectorios. Lee los candidatos B y muestra sus códigos y elegibilidad revisada. Esta función no toma una A más reciente ajena a B: conserva la cadena. Los resultados candidatos B se sellan al inicio de C porque B no los había sellado exhaustivamente al finalizar.

#### NB02 · Celda 6 — Máscara y ámbitos de España

Posición 7 del cuaderno; contador guardado: 37. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
mascara = load_mask(ROOT, CONFIG, RUN_DIR)
display(pd.read_csv(RUN_DIR / "ambitos_espana.csv").groupby("ambito").agg(
    componentes=("ambito", "size"), area_km2=("area_km2_epsg3035", "sum")))
print("Área candidata en UTM30, km²:", mascara.area / 1e6)
```

Carga el archivo territorial, exige país ES, CRS y geometrías válidas, descompone componentes y calcula sus áreas en EPSG:3035 para escoger la mayor. Exporta todas las componentes y una máscara de la principal reproyectada a 25830. La tabla identifica lo incluido y lo fuera de alcance. El área impresa se mide ya en UTM30, por lo que difiere conceptualmente del área equivalente usada para escoger la componente.

#### NB02 · Celda 7 — Visualización de la geometría de máscara

Posición 8 del cuaderno; contador guardado: 38. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
mascara
```

Devuelve el objeto Shapely `mascara` para su representación automática. No modifica el ámbito ni calcula cobertura. Su dibujo permite una comprobación visual general, pero no resolver precisión de costa, pequeños islotes, fronteras o componentes omitidas por el criterio de mayor área.

#### NB02 · Celda 9 — Área terrestre y creación de malla

Posición 10 del cuaderno; contador guardado: 39. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
area_terrestre_500m = land_areas(mascara, SPEC["native_shape"], SPEC["native_transform"])
grid = make_grid(area_terrestre_500m, SPEC, RUN_DIR)
display(grid[grid["land_fraction"] == 0].head())
display(grid[["land_area_m2", "land_fraction"]].describe())
print("Celdas terrestres:", len(grid), "de", SPEC["width"] * SPEC["height"])
display(pd.read_csv(RUN_DIR / "distorsion_crs.csv")[["linear_scale_error_pct", "area_scale_error_pct"]].agg(["min", "max"]))
```

Calcula áreas de píxel nativo y las agrega en `make_grid`; exporta malla, especificación, fracción terrestre y diagnóstico de distorsión. La consulta `land_fraction == 0` debe quedar vacía porque sólo se conservan áreas positivas. La salida de 496.855 celdas describe la máscara candidata actual. El denominador rectangular de 1.001.000 celdas incluye mar y territorio ajeno, por lo que no puede usarse directamente como área española evaluable.

#### NB02 · Celda 11 — Exploración de las celdas terrestres

Posición 12 del cuaderno; contador guardado: 40. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
display(grid[grid["land_fraction"] > 0])
```

Muestra las filas con fracción terrestre mayor que cero. Por construcción son todas las filas de `grid`, por lo que no introduce una selección adicional. Es útil como inspección de estructura e IDs; no aplica todavía el umbral costero ni los requisitos de datos de cada modelo.

#### NB02 · Celda 13 — Diccionario de soporte

Posición 14 del cuaderno; contador guardado: 41. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
diccionario = feature_dictionary(RUN_DIR)
display(diccionario)
```

`feature_dictionary` escribe y muestra los nombres conceptuales, fuentes, unidades, soporte y política de ausentes. Algunas variables sólo quedan previstas para D. La columna `same_for_P_U_inference=True` expresa el contrato de extracción uniforme. Este diccionario inicial no contiene todavía las 168 variables efectivamente calculadas ni sus decisiones semánticas finales; D construye su diccionario más detallado.

#### NB02 · Celda 15 — Alineación de geoquímica y elevación

Posición 16 del cuaderno; contador guardado: 42. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
fracciones_raster = align_rasters(ROOT, FUENTES, area_terrestre_500m, SPEC, RUN_DIR)
display(pd.read_csv(RUN_DIR / "raster_alignment.csv"))
```

`align_rasters` abre los nueve elementos y el MDT y exige igualdad exacta de CRS, forma y transformada nativa. No corrige de forma silenciosa un desfase: falla si la fuente no está anidada. Lee la banda 1 por bloques y aplica media ponderada para elevación o moda/proporciones para clases, con NoData separado del cero. Produce TIFF a 1 km y fracciones válidas. El control RGB se ejecutará después en 04 y puede reducir la cobertura inicialmente calculada aquí.

#### NB02 · Celda 16 — Vista de fracciones de Au

Posición 17 del cuaderno; contador guardado: 43. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
display(pd.DataFrame(fracciones_raster["geoquimica_au"]).head())
```

Convierte la matriz de fracciones de soporte de Au en un DataFrame y muestra sus primeras filas. Los valores representan proporción válida, no clase modal ni contenido de oro. Es una inspección de la matriz rectangular; no está limitada a las filas terrestres del DataFrame `grid`.

#### NB02 · Celda 18 — Armonización o recuperación de vectores

Posición 19 del cuaderno; contador guardado: 44. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
fracciones_vector, control_vectores = harmonize_vectors(ROOT, FUENTES, mascara,
    area_terrestre_500m, SPEC, RUN_DIR)
display(control_vectores.drop(columns=["reader_warnings", "z_m_policy", "semantic_status"]))
```

Llama a `harmonize_vectors` con el margen, máscara y configuración espacial. La ejecución actual utiliza el checkpoint fijado por `vector_cache_run` y verifica su compatibilidad antes de copiarlo. La tabla de control resume paginación, entidades, geometrías, cobertura y cambios, aunque la visualización elimina columnas largas de advertencias y semántica. Ocultarlas en pantalla no equivale a resolverlas: permanecen en el CSV del producto.

#### NB02 · Celda 20 — Capas adicionales recuperadas

Posición 21 del cuaderno; contador guardado: 45. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
from geoau.additional_layers import harmonize_additional
control_adicionales = harmonize_additional(ROOT, FUENTES, mascara, area_terrestre_500m, SPEC, RUN_DIR)
display(control_adicionales[["familia", "source_features", "kept_with_margin", "invalid_before",
                              "quarantine_count", "outside_scope_margin", "support_role"]])
display(pd.read_csv(RUN_DIR / "additional_attribute_qc.csv"))
```

Armoniza ocho familias adicionales: vuelos magnéticos/radiométricos, magnetotelúrica, medidas estructurales, petrofísica, buzamientos, cuaternario, gravimetría y zonas GEODE. El módulo conserva atributos y Z original en puntos cuando procede, inspecciona rangos angulares y reconoce el papel de cada fuente. Una línea de vuelo no se transforma en anomalía magnética ni una localización EDI en resistividad. El control es de ocupación/huella y atributos; la lista de campos cuantitativos útiles sigue dependiendo de metadatos verificados.

#### NB02 · Celda 22 — Productos territoriales de cobertura

Posición 23 del cuaderno; contador guardado: 46. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
grid_cobertura, cobertura_ambitos, decisiones, indicios_celda, estados = coverage_products(
    ROOT, grid, {**fracciones_raster, **fracciones_vector}, indicios, mascara, SPEC, RUN_DIR)
display(decisiones)
display(cobertura_ambitos[cobertura_ambitos.ambito.eq("peninsula")])
display(indicios_celda.estado_territorial.value_counts().to_frame("registros"))
```

Une fracciones a la malla, define estados de costa y soporte, asigna candidatos a celdas y calcula resúmenes por ámbito y bloques diagnósticos. La asignación comprueba que el punto esté cubierto por la máscara y usa intervalos semiabiertos: un punto exactamente en borde este/sur pasa a la celda adyacente. Conserva una fila por indicio y agrega sus conteos después. `prediction_allowed=False` en toda la malla evita confundir cobertura de datos con autorización de predicción.

#### NB02 · Celda 24 — Consulta de soporte adicional y relaciones exactas

Posición 25 del cuaderno; contador guardado: 47. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
soporte_adicional = pd.read_csv(RUN_DIR / "additional_support_by_scope.csv")
display(soporte_adicional[soporte_adicional.ambito.eq("peninsula")])
relaciones = pd.read_csv(RUN_DIR / "indicios_zonas_cuaternario.csv")
display(relaciones.groupby(["familia","estado"]).record_id.nunique().to_frame("registros_distintos"))
```

Lee resúmenes de las ocho capas y relaciones punto–polígono con zonas/cuaternario. En líneas/puntos la presencia en una celda no se convierte en área válida de levantamiento. La relación puntual exacta puede mostrar ausencia de intersección aunque haya una huella en otra parte de la misma celda. El texto `sin_interseccion_NO_ausencia` mantiene esa diferencia; no prueba que no existan materiales o depósitos aluviales.

#### NB02 · Celda 26 — Casos sin geoquímica y comparación B–C

Posición 27 del cuaderno; contador guardado: 48. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
sin_geoquimica = pd.read_csv(RUN_DIR / "revision_au_sin_geoquimica.csv", dtype={"Codigo_indicio": str})
print("Registros distintos sin geoquímica puntual:", sin_geoquimica.record_id.nunique())
display(sin_geoquimica[["record_id", "fuente", "estado", "cell_id", "coverage_decision", "decision"]].head(50))
contraste = pd.read_csv(RUN_DIR / "contraste_cobertura_puntual_B_C.csv")
display(contraste.groupby(["estado_B", "estado_C", "_merge"], dropna=False).size().to_frame("muestreos"))
```

Lee todos los candidatos con alguna falta de geoquímica puntual y cuenta `record_id` distintos, no filas elemento–indicio. El resultado guardado es siete registros con al menos una carencia; el recuento de cinco del plan pertenece a una auditoría anterior y otro detalle de muestreo. La comparación externa B/C se realiza por `record_id` y fuente con unión 1:1, comprobando coherencia entre ambas fases. No impone el recuento antiguo ni rellena huecos con cero.

#### NB02 · Celda 28 — Mapa de cobertura

Posición 29 del cuaderno; contador guardado: 49. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
from matplotlib.colors import ListedColormap, BoundaryNorm
from matplotlib.patches import Patch
colores = ["#c8c8c8", "#31866d", "#e3b84b", "#bf5856"]
fig, ax = plt.subplots(figsize=(12, 9))
extent = (SPEC["origin_x"], SPEC["origin_x"] + SPEC["width"] * 1000,
          SPEC["origin_y"] - SPEC["height"] * 1000, SPEC["origin_y"])
ax.imshow(np.ma.masked_equal(estados, 0), extent=extent, origin="upper",
          cmap=ListedColormap(colores), norm=BoundaryNorm([.5,1.5,2.5,3.5,4.5], 4), interpolation="nearest")
pts = indicios.to_crs(SPEC["crs"])
pts = pts[~pts.geo_cuarentena]
ax.scatter(pts.geometry.x, pts.geometry.y, s=3, c="#20242a", alpha=.4)
ax.legend(handles=[Patch(color=c, label=l) for c,l in zip(colores,
    ["Costera <50 % tierra", "Soporte básico candidato", "Candidato reducido", "Soporte insuficiente"])], loc="lower right")
ax.set(xlabel="Este (m), ETRS89 / UTM 30N", ylabel="Norte (m)",
       title="Cobertura regional candidata; no es un mapa de favorabilidad", xlim=extent[:2], ylim=extent[2:])
ax.set_aspect("equal")
fig.text(.5, .02, "Límites: © EuroGeographics · GISCO 2024, 1:1.000.000 · Puntos: candidatos BDMIN", ha="center", fontsize=9)
fig.tight_layout(rect=[0,.035,1,1])
fig.savefig(RUN_DIR / "mapa_cobertura.png", dpi=150)
plt.show()
display(cobertura_ambitos[cobertura_ambitos.familia.eq("geoquimica_au") &
                         cobertura_ambitos.ambito.ne("peninsula")].sort_values("porcentaje_area_valida").head(15))
```

Representa la matriz de estados con colores discretos y oculta el fondo rectangular de código cero. Añade los candidatos fuera de cuarentena reproyectados al CRS de la malla y una leyenda de soporte. Guarda la figura y muestra bloques con peor cobertura de Au. La extensión usa el literal 1.000 m, coherente con el contrato actual pero no genérico. Este mapa explica disponibilidad de información; sus zonas verdes no son zonas favorables a oro.

#### NB02 · Celda 30 — Aserciones finales, integridad y sellado C

Posición 31 del cuaderno; contador guardado: 50. Fuente: [02_rejilla_armonizacion_cobertura.ipynb](../../notebooks/02_rejilla_armonizacion_cobertura.ipynb).

```python
assert control_adicionales.pagination_complete.all()
assert grid_cobertura.cell_id.is_unique
assert len(indicios_celda) == len(indicios)
assert grid_cobertura.n_candidatos.sum() == indicios_celda.cell_id.notna().sum()
assert not grid_cobertura.prediction_allowed.any()
assert control_vectores.pagination_complete.all()
control = finish_run(ROOT, RUN_DIR, MANIFEST_A, ENTRADAS_C, grid_cobertura, indicios_celda, control_vectores)
display(pd.Series(control, dtype=object).to_frame("resultado"))
print("Resultados conservados en:", RUN_DIR)
```

Exige paginación completa de vectores base y adicionales, IDs de celda únicos, conservación de la relación indicio–celda y ausencia de autorización de predicción. `finish_run` repite hashes de originales y entradas congeladas, escribe pendientes y sella productos. El control local informa 789 candidatos asignados y uno fuera de máscara, todos sin revisión positiva. Las pruebas cubren integridad y geometría operativa; la máscara generalizada, huellas de levantamiento y revisión geológica continúan pendientes.

### 6.3. Diferencia entre las coberturas C y D

C utiliza huellas poligonales estimadas en centros de 500 m para diagnóstico de disponibilidad. D recalcula intersecciones exactas por categoría y rechaza ciertos solapes y atributos ausentes. Además, 04 filtra colores de geoquímica. Por ello una cobertura favorable en C no obliga a que la misma celda sea elegible en D: la fase de variables añade requisitos de calidad más estrictos.


## 7. Notebook 03 — Geología y estructuras

Corresponde al núcleo de D, pasos 18–20. Utiliza [features.py](../../src/geoau/features.py), especialmente `geology` (líneas 311–357), `lines` (400–453) y las funciones de caché. Produce 49 variables geológicas y 24 estructurales, con calidad separada. Las seis asociaciones litológicas adicionales se incorporan en 06.

### 7.1. Ejecuciones, reutilización y coste

`ensure_run` intenta continuar una D compatible; si cambia configuración o código, inicia una nueva y busca bloques reutilizables. `context` comprueba fuentes externas, manifiesto C y sus productos cada vez que se invoca un bloque. `cached` acepta un bloque sólo si los archivos sellados conservan sus hashes. Este diseño es deliberadamente estricto y permite reproducibilidad, aunque reverificar repetidamente grandes productos produce coste de lectura considerable.

La equivalencia para reutilizar bloques se basa en una lista manual de funciones de cálculo convertidas a AST, parámetros relevantes y constantes. Ignora diferencias cosméticas como números de línea; no ignora cambios de algoritmos incluidos en la lista. Si una refactorización añade una dependencia nueva, debe actualizarse esa lista: no es un análisis automático completo del grafo de dependencias. Los ficheros importados que ya se congelan por hash se verifican adicionalmente.

### 7.2. Geología: área cartografiada, no composición mineral

La extracción efectiva emplea `Litologia` de la capa regional y `SISTEMA` de edades. Aunque C armoniza `recintos`, D no utiliza todavía sus unidades detalladas para el banco principal. `geology` enumera descripciones originales, asigna IDs ordenados y escribe diccionarios. En teselas de 100×100 celdas intersecta cada celda con la máscara y disuelve polígonos por categoría antes de medir superficies; así evita doble conteo de polígonos de la misma clase.

Para una celda terrestre de área A y categoría k calcula `f_k = área(unión de polígonos k ∩ celda ∩ máscara) / A`. La cobertura es el área de la unión de categorías dividida por A. El solape entre categorías se mide como la suma de sus áreas menos el área de la unión. Sólo admite celdas con al menos 95 % de área de atributo conocido y solape no mayor de `max(1 m², A·10⁻⁶)`.

Las fracciones se expresan sobre área terrestre total, por lo que pueden sumar entre aproximadamente 0,95 y 1 cuando se tolera una pequeña parte sin cartografía. No deben forzarse a sumar exactamente uno como las proporciones geoquímicas, cuyo denominador es el área válida. La clase dominante corresponde a mayor área, con desempate por descripción ordenada. Una unidad mixta conserva su descripción: no se inventa su porcentaje interno de granito, mármol u otra litología.

### 7.3. Estructuras: distancias y densidades

`structural_class` normaliza texto y excluye agua, bordes, límites, escombreras, cortas y símbolos. Separa falla/cizalla, cabalgamiento y contacto intrusivo, y divide cada grupo entre cartografiado y supuesto/oculto/inferido. El resultado son seis grupos. No utiliza todos los contactos, pliegues o medidas estructurales como predictores por el simple hecho de que existan archivos.

La distancia se calcula con `STRtree.query_nearest` desde el centro fijo de la celda a una traza, hasta 10 km. Un resultado sin traza en ese radio es `NaN`, acompañado por una bandera de calidad. Puede significar distancia superior al límite o falta de cartografía: el valor no permite distinguirlos. La distancia tampoco es la distancia mínima entre toda la superficie de la celda y la traza.

Para densidades, `line_lengths` disuelve trazas geométricamente coincidentes, mide longitud intersectada por celda y reparte líneas sobre bordes compartidos. Después `fftconvolve` aplica un círculo aproximado mediante pesos de intersección círculo–celda a radios de 1, 5 y 10 km. La fórmula es `densidad = 1.000 · Σ(w_j L_j) / Σ(w_j A_j)`, con L en metros y A en m², resultando km/km². Se utiliza área terrestre, no área de levantamiento acreditada. El reparto de longitud dentro de cada celda se considera uniforme: a 1 km de radio esta aproximación subcelda puede ser especialmente relevante.

#### NB03 · Celda 1 — Inicio o continuación de D

Posición 2 del cuaderno; contador guardado: 1. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/features.py').exists())
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
import pandas as pd
import matplotlib.pyplot as plt
from geoau import features as fd

import importlib
importlib.reload(fd)
RUN = fd.ensure_run(ROOT)
print(RUN)
```

Busca la raíz por la existencia de `features.py`, importa pandas, gráficos y el módulo, lo recarga y llama a `ensure_run`. `reload` permite que el kernel vea cambios de código, mientras los hashes determinan si puede continuar el mismo producto. El resultado guardado informa reutilización de cinco bloques compatibles. Recargar un módulo no equivale por sí mismo a validar los datos; la comprobación de entradas ocurre en `context` al ejecutar las funciones de bloque.

#### NB03 · Celda 3 — Variables geológicas

Posición 4 del cuaderno; contador guardado: 2. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
geology, geology_quality = fd.geology(ROOT, RUN)
display(geology.head())
display(geology_quality.describe())
```

`fd.geology` carga un bloque sellado o ejecuta las intersecciones y los criterios anteriores. Devuelve `geology` con `cell_id` y predictores y `geology_quality` con cobertura, solapes y ausencia de atributos. `head()` puede mostrar filas sin valores al comienzo geográfico de la rejilla; eso no significa que toda la geología esté vacía. `describe()` de calidad permite evaluar distribución de soporte pero no valida las equivalencias de las unidades.

#### NB03 · Celda 4 — Ejemplo comentado de lectura de calidad geológica

Posición 5 del cuaderno; contador guardado: 3. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
#import pyarrow.parquet as pq

# Leer tabla completa
#table = pq.read_table("C:\\Users\\Lenovo\\Desktop\\PROYECTO IA\\Proyecto Con Luis\\reports\\fase_d\\20260908T183653_990856Z\\blocks\\geology_quality.parquet")

# Convertir a DataFrame de pandas si es necesario
#df = table.to_pandas()

#df[df.sum(axis=1, numeric_only=True) > 0]

#display(df)
```

Todas las líneas están comentadas: no se importa PyArrow ni se lee el archivo de la ruta antigua. El fragmento muestra un intento de inspeccionar un Parquet y filtrar sumas numéricas positivas. Esa suma no sería un criterio geológico general, porque mezcla cantidades distintas. La ruta absoluta pertenece a una ejecución histórica; al quedar inactiva no condiciona la ejecución actual, pero convendría sustituirla por una ruta basada en `RUN` si se reutiliza.

#### NB03 · Celda 5 — Ejemplo comentado de calidad estructural

Posición 6 del cuaderno; contador guardado: 4. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
#import pyarrow.parquet as pq

# Leer tabla completa
#table = pq.read_table("C:\\Users\\Lenovo\\Desktop\\PROYECTO IA\\Proyecto Con Luis\\reports\\fase_d\\20260909T085704_618911Z\\blocks\\structural_quality.parquet")

# Convertir a DataFrame de pandas si es necesario
#df = table.to_pandas()
#display(df)
```

También es una celda sin instrucciones ejecutables. Contiene una ruta absoluta de un producto estructural antiguo y un ejemplo de lectura/conversión a pandas. Se contabiliza como celda de código del notebook, pero no produce variables ni diagnósticos en una ejecución completa.

#### NB03 · Celda 7 — Variables estructurales

Posición 8 del cuaderno; contador guardado: 5. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
structural, structural_quality = fd.lines(ROOT, RUN)
display(structural.describe())
```

`fd.lines(ROOT, RUN)` usa por defecto la única fuente estructural admitida, GEODE, con seis grupos y cuatro variables por grupo: una distancia y tres densidades. Esta decisión evita sumar directamente copias GEODE/MAGNA, aunque no resuelve desplazamientos o duplicación imperfecta dentro de una misma fuente. La tabla descriptiva muestra distribución y faltantes; por ejemplo, las distancias pueden tener menos observaciones que las densidades porque la búsqueda se limita a 10 km y la densidad cartografiada permite cero.

#### NB03 · Celda 8 — Diccionario estructural y continuidad

Posición 9 del cuaderno; contador guardado: 6. Fuente: [03_variables_geologia_estructuras.ipynb](../../notebooks/03_variables_geologia_estructuras.ipynb).

```python
display(pd.read_csv(RUN / 'dictionaries/estructuras.csv'))
print('Continuar con 04 usando esta ejecución:', RUN)
```

Muestra `dictionaries/estructuras.csv`, que relaciona descripción original, número de entidades y grupo asignado. Éste es el punto de revisión semántica de reglas textuales: encontrar `Falla` no acredita por sí mismo certeza geométrica ni cobertura suficiente. El mensaje final indica la ejecución que debe continuar 04. No realiza nuevos cálculos ni aprueba las reglas.

### 7.4. Limitaciones específicas

Los pasos de estructuras avanzadas —orientaciones axiales, intersecciones topológicas, distancias a pliegues y estadísticas de buzamiento— permanecen pendientes. La fuente geológica regional puede limitar capacidad de detectar controles más finos. Las asociaciones y fracciones originales redundantes elevan el número de columnas respecto al presupuesto inicial de 25–50 del plan. La revisión ha reproducido un caso sintético de borde costero donde `line_lengths`, al recibir el borde del rectángulo global, reparte la mitad de una traza sobre el borde de la única celda terrestre; se detalla en hallazgos, sin extrapolar su magnitud a todo el territorio.

## 8. Notebook 04 — Geoquímica por clases y control RGB

Desarrolla el paso 21; el 22, mejora con datos analíticos cuantitativos, sigue pendiente. [features.py](../../src/geoau/features.py), líneas 456–546, lee paletas, comprueba color, agrega clases y registra calidad. Genera 79 variables: nueve modas y 70 proporciones de clases. F selecciona una representación por elemento dentro de cada conjunto de variables.

### 8.1. Procedencia y control de clasificación

Los scripts históricos descargaron mapas renderizados y asignaron a cada píxel visible el color de paleta más cercano. Las bandas de valores representativos, límites y clases provienen de esa misma asignación; no son cuatro mediciones independientes. `local_palettes` extrae las constantes mediante `ast.literal_eval` sin importar ni ejecutar los scripts de descarga. Esto evita efectos secundarios y preserva la paleta utilizada, pero una paleta local coherente todavía requiere contraste con la leyenda oficial.

`color_quality` calcula distancia euclídea RGB entre el píxel y el color de su clase declarada. El píxel se acepta si es visible, tiene clase entera válida, distancia ≤2 y una separación de al menos 10 respecto a la segunda clase más cercana; además la clase declarada debe ser la más cercana. El control examina colores únicos para limitar memoria. Con cuatro bandas exige alfa 255. Clase cero sigue siendo válida.

Las clases aceptadas se agregan de 500 m a 1 km ponderando por tierra. Se publican predictores sólo si la fracción RGB válida alcanza 95 %. Las proporciones suman uno sobre el área válida; no describen incertidumbre de concentración dentro de los intervalos. La comparación de tolerancias 0, 2 y 8 es un diagnóstico: la configuración no acepta automáticamente las discrepancias de ocho niveles detectadas en Zn/W.

#### NB04 · Celda 1 — Recuperación de ejecución y versiones adicionales

Posición 2 del cuaderno; contador guardado: 1. Fuente: [04_variables_geoquimicas.ipynb](../../notebooks/04_variables_geoquimicas.ipynb).

```python
from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/features.py').exists())
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
import pandas as pd
import matplotlib.pyplot as plt
from geoau import features as fd

import importlib
importlib.reload(fd)
RUN = fd.current_run(ROOT)
print(RUN)
import importlib.metadata
fd.write_json(RUN / 'environment_fase_d.json', {p: importlib.metadata.version(p) for p in ('numpy', 'scipy', 'pyarrow')})
```

Carga el módulo D y recupera `current_run`, que exige coincidencia del YAML con el snapshot. Escribe `environment_fase_d.json` con versiones de NumPy, SciPy y PyArrow. Esa escritura aporta trazabilidad, pero después del cierre D el archivo puede estar incluido en el manifiesto: reejecutar esta celda con versiones distintas puede modificar un archivo sellado y hacer fallar controles posteriores. La respuesta correcta sería iniciar una ejecución nueva, no cambiar el sello para ocultar la diferencia.

#### NB04 · Celda 2 — Extracción y auditoría RGB

Posición 3 del cuaderno; contador guardado: 2. Fuente: [04_variables_geoquimicas.ipynb](../../notebooks/04_variables_geoquimicas.ipynb).

```python
geochemistry, geochemistry_quality = fd.geochemistry(ROOT, RUN)
display(pd.read_csv(RUN / 'geoquimica_rgb_qc.csv'))
```

Ejecuta o recupera `geochemistry` y muestra `geoquimica_rgb_qc.csv`. El informe registra píxeles válidos originales, aceptados/rechazados, diferencias de moda respecto a C, celdas con soporte suficiente y que la leyenda oficial aún no está validada. Se escriben TIFF de clases/proporciones controladas y tablas de predictores/calidad. El cambio de cobertura respecto a 02 es deliberado: C comprobaba máscaras y códigos, mientras D exige además consistencia del color.

#### NB04 · Celda 3 — Inspección de predictores y calidad

Posición 4 del cuaderno; contador guardado: 3. Fuente: [04_variables_geoquimicas.ipynb](../../notebooks/04_variables_geoquimicas.ipynb).

```python
display(geochemistry.head())
display(geochemistry_quality.describe())
```

Muestra primeras filas del banco geoquímico y estadísticas de la tabla de calidad. Una celda puede tener valores de algunos elementos y `NaN` en otros. Las columnas de proporciones no deben incorporarse junto a la moda del mismo elemento por defecto: representan la misma evidencia con distinta agregación. La selección efectiva se determina después en `training.feature_sets`.

#### NB04 · Celda 4 — Filtrado visual correcto de presencia de datos

Posición 5 del cuaderno; contador guardado: 4. Fuente: [04_variables_geoquimicas.ipynb](../../notebooks/04_variables_geoquimicas.ipynb).

```python
# Cero es una clase v?lida: filtrar presencia de datos, no valores > 0.
cols_modal = geochemistry.columns[geochemistry.columns.str.endswith('_modal')]

df_limpio = geochemistry[geochemistry[cols_modal].notna().any(axis=1)]

df_limpio
```

Identifica columnas cuyo nombre termina en `_modal` y construye `df_limpio` con filas que tienen al menos una moda no nula. Usa `notna()` y no `>0`, de modo que conserva la clase cero. Es una vista alternativa y no sustituye el objeto `geochemistry` que se integra en 06. Tener al menos un elemento presente tampoco equivale a cumplir el soporte `eligible_geo4`, que exige los cuatro elementos seleccionados.

#### NB04 · Celda 5 — Histogramas de clases

Posición 6 del cuaderno; contador guardado: 5. Fuente: [04_variables_geoquimicas.ipynb](../../notebooks/04_variables_geoquimicas.ipynb).

```python
geochemistry.filter(regex='_clase_modal$').hist(figsize=(14, 9), bins=8)
plt.tight_layout()
plt.show()
```

Dibuja un histograma de cada moda con ocho bins y ajusta la figura. Permite reconocer distribución y clases dominantes en las celdas con valor. Para códigos discretos serían más explícitas barras por clase con límites alineados; ocho bins comunes no coinciden necesariamente con los siete niveles de Au/W. El gráfico cuenta celdas, no estaciones analíticas ni depósitos. No evalúa normalidad de concentraciones químicas reales.

### 8.2. Lectura geológica

Una anomalía cartográfica de sedimentos puede estar relacionada con transporte y fuentes aguas arriba. Este bloque no modela cuencas, procedencia de sedimento ni contaminación histórica. Utilizar Au externo no demuestra por sí solo fuga de etiquetas; exige estudiar la procedencia de la capa y sus relaciones con los indicios. La ablación con/sin Au ayuda a medir dependencia predictiva, pero no sustituye esa revisión.

## 9. Notebook 05 — Relieve e hidrología

Desarrolla el paso 23 y la base del 24; la geofísica del paso 25 y la hidrología aluvial detallada quedan pendientes. Calcula seis variables de relieve y cuatro hidrográficas en [features.py](../../src/geoau/features.py).

### 9.1. Fórmulas reales del relieve

La pendiente se deriva en la malla nativa de 500 m. Para píxel p, `dz/dx = (z_este − z_oeste)/(2p)` y análogamente en y. La pendiente en grados es `atan(sqrt((dz/dx)² + (dz/dy)²)) · 180/π`. Se exige centro y los cuatro vecinos finitos, por propagación de NaN y máscara. El signo norte/sur del gradiente no afecta a la magnitud de pendiente.

Para radios de 1 y 5 km se construye un disco de **centros** de píxeles, incluido el centro. Se calcula número de píxeles válidos, suma de alturas y suma de cuadrados mediante convolución. `TPI = z_centro − media_vecindario`; `desv_elevacion = sqrt(max(0, media(z²) − media(z)²))`. La segunda magnitud es desviación típica poblacional de elevaciones, no el índice TRI de otro algoritmo. Se exige al menos 95 % de los centros nominales del disco válidos y centro válido.

El cero que aparece en la suma de la convolución sólo sirve para anular términos inválidos; el denominador cuenta datos válidos. Por tanto, no se interpreta como elevación cero en océano o huecos. Después las derivadas de 500 m se agregan con media ponderada por área terrestre válida a 1 km y se exige nuevamente soporte ≥95 %. Cerca de costa y frontera, enmascarar a tierra española antes del cálculo reduce el soporte de vecindarios aunque el MDT tuviera alturas al otro lado de la frontera.

#### NB05 · Celda 1 — Contexto de D

Posición 2 del cuaderno; contador guardado: 1. Fuente: [05_variables_relieve_hidrologia.ipynb](../../notebooks/05_variables_relieve_hidrologia.ipynb).

```python
from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/features.py').exists())
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
import pandas as pd
import matplotlib.pyplot as plt
from geoau import features as fd

import importlib
importlib.reload(fd)
RUN = fd.current_run(ROOT)
print(RUN)
```

Importa el módulo y recupera la ejecución actual según el YAML. Debe ser la misma iniciada por 03. Esta celda no abre el MDT ni recalcula relieve. Los bloques invocados después harán la verificación profunda de entradas y podrán reutilizar productos ya sellados.

#### NB05 · Celda 2 — Cálculo de relieve

Posición 3 del cuaderno; contador guardado: 2. Fuente: [05_variables_relieve_hidrologia.ipynb](../../notebooks/05_variables_relieve_hidrologia.ipynb).

```python
terrain, terrain_quality = fd.terrain(ROOT, RUN)
display(terrain.describe())
```

`fd.terrain` lee exclusivamente la banda de elevación del MDT original, verifica rejilla y máscaras y reconstruye las seis variables mediante las fórmulas anteriores. No reutiliza las bandas derivadas históricas de pendiente/TPI/TRI. Devuelve predictores y fracciones válidas y guarda TIFF por variable. La tabla descriptiva resume media, dispersión y límites; que la elevación media tenga dato en toda la malla no implica que TPI de 5 km lo tenga, por sus requisitos de vecindario.

#### NB05 · Celda 3 — Cálculo hidrográfico

Posición 4 del cuaderno; contador guardado: 3. Fuente: [05_variables_relieve_hidrologia.ipynb](../../notebooks/05_variables_relieve_hidrologia.ipynb).

```python
hydrology, hydrology_quality = fd.lines(ROOT, RUN, hydro=True)
display(hydrology)
```

`fd.lines(..., hydro=True)` activa el mismo motor espacial de distancias y longitud/área para el grupo único `cauce`. Produce distancia al cauce hasta 10 km y densidades aproximadas a 1, 5 y 10 km. La red es la capa hidrográfica disponible, con sus posibles omisiones de cabeceras y tramos; el resultado no equivale a distancia al drenaje real completo. No calcula dirección de flujo, acumulación, cuencas, terrazas ni altura relativa al cauce.

#### NB05 · Celda 4 — Calidad de relieve y continuidad

Posición 5 del cuaderno; contador guardado: 4. Fuente: [05_variables_relieve_hidrologia.ipynb](../../notebooks/05_variables_relieve_hidrologia.ipynb).

```python
display(terrain_quality.describe())
print('Continuar con 06 para integrar y verificar.')
```

Muestra estadísticas de las fracciones válidas de cada variable y señala que la integración corresponde a 06. La calidad se mantiene fuera de X y permite localizar dónde faltan vecinos o datos. No imprime `hydrology_quality` aquí, aunque el objeto existe y se incorpora posteriormente; los indicadores hidrográficos de falta de traza y cobertura de levantamiento continúan siendo relevantes.

### 9.2. Alcance del modelo aluvial

Relieve regional y proximidad al cauce pueden formar parte de una referencia general, pero no realizan el modelo aluvial descrito en el plan. Faltan diferenciación de terrazas, MDT de detalle, acondicionamiento hidrológico y agrupación por cuencas. La configuración F usa el objetivo general. Las categorías roca/aluvial propuestas en B no acreditan dos modelos específicos ejecutados.

## 10. Notebook 06 — Matriz, roles y cierre técnico

Implementa el paso 26 y cierre técnico D. Su función central es `assemble`, líneas 677–772 de [features.py](../../src/geoau/features.py). Une cinco bloques, añade seis asociaciones litológicas y separa predictores, calidad y etiquetas.

### 10.1. Contrato de integración

El banco queda compuesto por 49 variables geológicas, 24 estructurales, 79 geoquímicas, seis de relieve, cuatro de hidrología y seis asociaciones: **168**. Las asociaciones agrupan descripciones explícitas de granitoides, unidades mixtas con granitoides, volcanitas, rocas básicas/ultrabásicas, gneises y gravas/arenas/limos. Son fracciones de unidades cartográficas, no estimaciones de mineralogía interna. Algunas duplican o suman fracciones ya presentes, lo que debe considerarse en regularización e interpretación de importancias.

Las uniones se validan como 1:1 por `cell_id`. Se exige que todos los bloques cubran la misma rejilla y que sus nombres no colisionen. `validate_matrix` rechaza IDs inválidos, infinitos, fracciones fuera de rango, distancias/densidades negativas, pendientes imposibles y proporciones geoquímicas incompletas o no normalizadas. Las tablas de indicios se conservan aparte y sus conteos se agregan por celda.

`X_features.parquet` incluye predictores candidatos y `cell_id`; **la clave debe retirarse antes de entrenar**, como hace F. `calidad_y_soporte.parquet` reúne auxiliares y máscaras; `etiquetas_por_celda.parquet` distingue `P_revisado`, `candidato_no_revisado` y `U`. El maestro completo combina estos papeles, por lo que no puede pasarse entero a un clasificador.

`partition_id = row // 100` crea bandas de almacenamiento. El fichero monolítico y cada partición se escriben con temporal y reemplazo atómico. Esa partición no está diseñada como fold espacial de evaluación. El diccionario de roles lo marca como auxiliar.

#### NB06 · Celda 1 — Recuperación de ejecución

Posición 2 del cuaderno; contador guardado: 2. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/features.py').exists())
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
import pandas as pd
import matplotlib.pyplot as plt
from geoau import features as fd

import importlib
importlib.reload(fd)
RUN = fd.current_run(ROOT)
print(RUN)
```

Importa el módulo D y recupera el mismo `RUN` de 03–05. No reconstruye por sí solo bloques faltantes. La secuencia debe haber generado o recuperado geología, estructuras, geoquímica, relieve e hidrología antes de llamar a integración.

#### NB06 · Celda 2 — Ensamblado y control de cierre

Posición 3 del cuaderno; contador guardado: 2. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
X, quality, labels = fd.assemble(ROOT, RUN)
display(fd.read_json(RUN / 'control_cierre.json'))
```

`assemble` verifica entradas y, si D ya está sellada, comprueba el manifiesto y devuelve los tres Parquet existentes. Si no está cerrada, integra bloques, asociaciones, etiquetas, roles, soporte, diccionarios y manifiesto. La salida observada son 496.855 celdas y 168 variables candidatas. `approved_training_columns` se escribe vacío y las banderas científicas permanecen falsas: la terminación técnica acredita la matriz y su estructura, no aprueba el entrenamiento científico.

#### NB06 · Celda 3 — Faltantes, estados de etiqueta y ampliaciones

Posición 4 del cuaderno; contador guardado: 3. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
display(pd.read_csv(RUN / 'variables_qc.csv').sort_values('missing_fraction', ascending=False).head(25))
display(labels.estado_etiqueta.value_counts())
display(fd.read_json(RUN / 'pending_extensions.json'))
```

Ordena `variables_qc.csv` por fracción faltante, muestra los estados de etiqueta y lee `pending_extensions.json`. Las distancias a contactos intrusivos supuestos presentan un faltante especialmente alto. Es importante distinguir no encontrar una traza en 10 km de no tener la fuente; la imputación posterior no resolverá esa ambigüedad semántica. El JSON de ampliaciones documenta geofísica, estructuras avanzadas, aluvial, leyendas y cobertura pendientes.

#### NB06 · Celda 4 — Soporte de modelos, roles y particiones Parquet

Posición 5 del cuaderno; contador guardado: 4. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
display(pd.read_csv(RUN / 'soporte_modelos.csv'))
display(pd.read_csv(RUN / 'column_roles.csv').role.value_counts())
display(pd.read_parquet(RUN / 'Grid_Master_Au', columns=['cell_id', 'partition_id'], filters=[('partition_id', '==', 0)]).head())
```

Muestra cuántas celdas y candidatos cumplen cada combinación de soporte, cuenta roles del maestro y lee sólo la partición 0 de `Grid_Master_Au`. El filtro Parquet reduce lectura sin cambiar la definición de los datos. En la salida hay 168 predictores, 73 auxiliares, tres columnas de etiqueta y una clave. El nombre `partition_id` identifica almacenamiento; reutilizarlo como CV sería una decisión nueva ajena al diseño E.

#### NB06 · Celda 6 — Mapa de pendiente como revisión espacial

Posición 7 del cuaderno; contador guardado: 5. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
plot = quality[['cell_id', 'x_center', 'y_center']].merge(X[['cell_id', 'pendiente_grados']], on='cell_id', validate='one_to_one')
fig, ax = plt.subplots(figsize=(11, 8))
m = ax.scatter(plot.x_center, plot.y_center, c=plot.pendiente_grados, s=1, cmap='terrain', rasterized=True)
ax.set_aspect('equal')
ax.set_title('Pendiente media por celda · grados · no es prospectividad')
fig.colorbar(m, ax=ax, label='grados')
plt.show()
```

Une coordenadas auxiliares y pendiente mediante `validate='one_to_one'`, representa todos los centros con color y mantiene escala métrica igual. Las coordenadas sólo sirven para dibujo y no se agregan a X. El mapa permite detectar huecos y discontinuidades, pero una figura continua y plausible no confirma los procesos geológicos ni la exactitud del MDT. El título evita interpretarlo como prospectividad.

#### NB06 · Celda 7 — Verificación final de productos

Posición 8 del cuaderno; contador guardado: 6. Fuente: [06_matriz_variables_control.ipynb](../../notebooks/06_matriz_variables_control.ipynb).

```python
fd.verify_records(RUN, fd.read_json(RUN / 'outputs_manifest.json'))
print('Productos sellados verificados:', RUN)
```

Recalcula los hashes de todos los productos listados en `outputs_manifest.json`. Si un archivo ha cambiado o desaparecido, `verify_records` lanza un error. Es un control de integridad de la ejecución D, independiente de las estadísticas o del mapa anteriores. El mensaje de productos verificados no es una autorización de producción: esa decisión continúa bloqueada en los propios archivos de control.

### 10.2. Selección de soporte y posible sesgo

`eligible_geology_terrain` exige elegibilidad costera y datos de litología dominante, edad dominante, elevación y pendiente. No exige que todas las variables de TPI o distancias estén presentes. `eligible_geo4` añade Au/As/Sb/Bi; `eligible_geo9` añade los nueve elementos. Los faltantes restantes podrán imputarse dentro del entrenamiento. Escoger este territorio condiciona el problema que se evalúa: los resultados no deben aplicarse silenciosamente a celdas que fueron descartadas por cobertura.


## 11. Notebook 07 — Particiones espaciales y reserva

Implementa pasos 27–28 mediante [evaluation.py](../../src/geoau/evaluation.py). Carga la D fijada por `evaluation.yaml`, con objetivo `general`, soporte `eligible_geo4`, bloques de 50 km, cinco folds externos, tres internos y separación de 5 km. El modo actual es diagnóstico.

### 11.1. Disponibilidad científica

`source_data` verifica productos D y selecciona columnas de identidad/soporte sin cargar X para crear particiones. `choose_labels` selecciona registros del objetivo que estén dentro de soporte; en diagnóstico usa candidatos y en validado sólo revisados. Valida booleanos explícitamente para evitar el error de convertir la cadena `"False"` a verdadero.

`readiness` exige positivos revisados, IDs de depósito y distrito, predictores aprobados, un mapa territorial de distritos coherente con los registros, distritos elegidos para reserva y protocolo revisado. Para aluvial exige además cuencas. Los datos actuales no superan esas condiciones; cambiar `mode` no evita el bloqueo. La función es un control programático de requisitos, no la revisión experta de su contenido.

### 11.2. Construcción de unidades, folds y separaciones

`connected_units` asigna bloques de 50 km desde fila/columna, y une transitivamente bloques ligados por el mismo depósito o distrito. En diagnóstico añade grupos de proximidad de 500 m. Si hay cartografía territorial de distritos/cuencas, agrupa también sus celdas. Esas unidades completas son lo que se reparte entre folds: no se trocean por balancear el número de registros.

`seed_for` deriva enteros de SHA-256 a partir de semilla y etiquetas del procedimiento. La reserva diagnóstica toma aproximadamente el 15 % del **número de unidades**, ordenadas por hash; no busca el 15 % exacto de área ni de positivos. En los productos actuales contiene 72.061 celdas elegibles y 23 candidatas. El resto contiene 643 celdas candidatas.

La separación usa una transformada de distancia entre centros y la cota conservadora `d_inferior = max(0, d_centros − √2·resolución)`. Restar dos semidiagonales de celda evita tratar como suficiente una distancia que sólo existe entre centros. La cota no es la distancia exacta entre polígonos recortados por costa. Se excluye del entrenamiento lo que no alcanza los 5 km frente a región de test y reserva, incluyendo referencias espaciales sin soporte; esto puede ser más conservador que separar únicamente muestras.

Los folds se asignan por hash de unidad, sin scores. Se prueban menos folds si no hay suficientes unidades con P en train/test; este ajuste de factibilidad usa distribución de positivos, no rendimiento de modelos. Dentro de cada entrenamiento externo se crean sus propios folds internos con nuevas separaciones. Las membresías distinguen `train`, `test`, `spatial_gap`, `holdout`, `outside_support` y `outside_parent`.

#### NB07 · Celda 1 — Preparación de E y lectura de requisitos

Posición 2 del cuaderno; contador guardado: 1. Fuente: [07_particiones_espaciales.ipynb](../../notebooks/07_particiones_espaciales.ipynb).

```python
from pathlib import Path
import sys
import importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/geoau/evaluation.py').is_file())
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))
from geoau import evaluation as ev
importlib.reload(ev)

RUN = ev.ensure_run(ROOT)
display(ev.read_json(RUN / "readiness.json"))
```

Localiza la raíz, recarga `evaluation` y llama a `ensure_run`. Si hay ejecución compatible la recupera; en caso contrario crea una nueva tras verificar D y configuración. Muestra `readiness.json`, que explicita siete carencias principales en el estado actual. Crear E en diagnóstico autoriza construir diseños de evaluación, pero no transforma los candidatos en P revisados ni cambia la lista de predictores aprobados de D.

#### NB07 · Celda 3 — Construcción de particiones y diagnóstico de tamaños

Posición 4 del cuaderno; contador guardado: 2. Fuente: [07_particiones_espaciales.ipynb](../../notebooks/07_particiones_espaciales.ipynb).

```python
summary = ev.build_splits(ROOT, RUN)
display(summary)
display(pd.read_csv(RUN / "block_sensitivity.csv"))
display(ev.read_json(RUN / "split_plan.json"))
```

`build_splits` calcula o recupera las membresías selladas. Guarda relaciones de unidades, positivos seleccionados, planes, resúmenes y sensibilidad de tamaños 25/50/100 km. Esa sensibilidad cuenta bloques y unidades disponibles; no estima autocorrelación ni compara rendimiento. El producto real contiene cinco diseños externos y quince internos, veinte en total. Las comprobaciones de disponibilidad mínima operan sobre unidades espaciales con candidatos, no sobre un número acreditado de depósitos geológicos independientes.

#### NB07 · Celda 5 — Mapa de folds y reserva

Posición 6 del cuaderno; contador guardado: 3. Fuente: [07_particiones_espaciales.ipynb](../../notebooks/07_particiones_espaciales.ipynb).

```python
import matplotlib.pyplot as plt
territory = pd.read_parquet(RUN / 'territory.parquet')
units = pd.read_parquet(RUN / 'design/spatial_units.parquet')
view = territory.merge(units, on='cell_id', validate='one_to_one')
fig, ax = plt.subplots(figsize=(10, 8))
development = view[~view.holdout]
plot = ax.scatter(development.x_center, development.y_center,
                  c=development.outer_fold, cmap='tab10', s=.2, rasterized=True)
reserve = view[view.holdout]
ax.scatter(reserve.x_center, reserve.y_center, color='black', s=.2, label='Reserva')
ax.set(aspect='equal', xlabel='ETRS89 / UTM 30N · metros', ylabel='Metros',
       title='Asignación territorial diagnóstica; consultar máscaras para buffers y soporte')
ax.legend(); fig.colorbar(plot, ax=ax, label='Fold externo'); plt.show()
```

Une `territory.parquet` y las unidades 1:1, dibuja desarrollo coloreado por fold y reserva en negro. La figura incluye el diseño territorial y no aplica todas las máscaras específicas de cada membresía; por ello no permite leer directamente qué centros quedan finalmente en train después del buffer. El título y el texto remiten correctamente a las máscaras. La asignación de colores no representa score, geología ni calidad del modelo.

### 11.3. Interpretación y límites

Un fold externo contiene varias unidades geográficas y no necesariamente una única región contigua. La capacidad medida es transferencia a esas zonas retenidas bajo el diseño de bloques, no validación leave-one-district-out acreditada. Faltan depósitos/distritos y justificación empírica de 50 km/5 km. La cota mínima de separación entre train y test/reserva en los productos es 5.293,99 m. Pasar ese control prueba separación geométrica conservadora, no independencia geológica absoluta.

## 12. Notebook 08 — Muestreo presencia–fondo

Implementa el paso 29 y prepara el 30. Las funciones principales son `background_pool`, `stratified_u` y `build_samples` de [evaluation.py](../../src/geoau/evaluation.py), líneas 329–432.

### 12.1. Construcción del universo U

Para cada membresía se toman sólo celdas `train`; se separan las P seleccionadas de ese entrenamiento y se aplica un buffer de 250 m calculado conservadoramente entre huellas de celdas de 1 km. Las posiciones de P externas o de reserva no se usan para vaciar el pool U. Así no se facilita artificialmente la tarea evitando fondo cerca de los positivos retenidos.

El buffer de 250 m no equivale a excluir todo un distrito de 5 km. Ambos radios tienen fines distintos: incertidumbre/proximidad alrededor de P de entrenamiento frente a separación entre desarrollo y evaluación. La discretización impone saltos: entre centros a 2 km, la cota inferior es unos 586 m, mientras entre vecinos diagonales de 1 km por eje es cero. No se debe interpretar este procedimiento como un buffer circular exacto de 250 m alrededor del punto del indicio.

### 12.2. Diseño estratificado e inclusión

Se solicitan ratios U:P de 1, 3 y 10, con tres realizaciones. Si n≥H, donde H es el número de bloques con pool, se asigna inicialmente una U por bloque y se reparte el resto según área y capacidad. Dentro de cada bloque se muestrea sin reemplazo. Para n<H se eligen n bloques al azar y una celda por bloque seleccionado.

En el primer caso la probabilidad de inclusión de una celda del bloque h es `π_h = n_h/N_h`. En el segundo, `π_h = (n/H)·(1/N_h)`. Los pesos guardados son `1/π_h` y `área_celda/π_h`. La probabilidad 1 que se asigna a P significa que todas las P observadas de ese entrenamiento se incluyen en la muestra, no que su probabilidad de descubrimiento o registro en la población sea uno.

`sample_class=1` corresponde a `P_candidate_proxy` en diagnóstico o a `P_reviewed` en validado; `sample_class=0` siempre acompaña `U_unlabelled`. Las muestras se generan desde cada train interno completo de forma independiente del subconjunto externo, respetando sus propios buffers.

#### NB08 · Celda 1 — Generación de muestras P/U

Posición 2 del cuaderno; contador guardado: 1. Fuente: [08_muestreo_presencia_fondo.ipynb](../../notebooks/08_muestreo_presencia_fondo.ipynb).

```python
from pathlib import Path
import sys
import importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/geoau/evaluation.py').is_file())
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))
from geoau import evaluation as ev
importlib.reload(ev)

RUN = ev.current_run(ROOT)
samples = ev.build_samples(ROOT, RUN)
display(samples)
```

Recupera E e invoca `build_samples`. La función exige las particiones de 07, selecciona P/pool por membresía y crea nueve diseños por split: tres ratios por tres realizaciones. Guarda un Parquet de muestra y otro de asignación por estrato, con semilla derivada e inclusión. El resultado actual suma **20×3×3 = 180 muestras**. Si el pool es menor que lo solicitado, conserva lo disponible y registra `pool_capped`, ratio realizado y tamaño solicitado; no duplica U para aparentar el ratio.

#### NB08 · Celda 3 — Resumen y ejemplo de diseño

Posición 4 del cuaderno; contador guardado: 2. Fuente: [08_muestreo_presencia_fondo.ipynb](../../notebooks/08_muestreo_presencia_fondo.ipynb).

```python
display(samples.groupby(['level', 'ratio_requested']).agg(
    designs=('sample_id','size'), min_P=('n_P','min'), max_P=('n_P','max'),
    min_U=('n_U','min'), capped=('pool_capped','sum')))
example = samples.sample_id.iloc[0]
display(pd.read_parquet(RUN / f'samples/{example}.parquet').head())
display(pd.read_parquet(RUN / f'samples/{example}_allocation.parquet').head())
```

Agrupa el resumen por nivel externo/interno y ratio, mostrando número de diseños, mínimos/máximos de P y U y casos limitados por el pool. Lee la primera muestra y su tabla de asignación. Es una inspección explicativa de artefactos ya construidos; no selecciona un ratio ganador. Ésa será una decisión del bucle interno de F, mientras el territorio de evaluación queda constante.

### 12.3. Aspectos todavía no resueltos

No se ha incorporado una superficie de esfuerzo de observación verificable. Muestrear U de forma territorial no elimina el sesgo de localización de P. En futuros objetivos específicos, otros tipos de indicios pueden formar parte del territorio no etiquetado del objetivo; deben seguir identificados como desconocidos y estudiarse en sensibilidad, sin presentarlos como negativos geológicos. La selección diagnóstica tampoco debería reintroducir registros explícitamente rechazados si se añaden revisiones en B: actualmente no hay decisiones de ese tipo en la cadena examinada.

## 13. Notebook 09 — Contrato P/U y cierre de E

Fija el contrato del paso 30 y verifica la terminación técnica de E. Aquí no se entrenan clasificadores ni se estima prevalencia. El bagging previsto se ejecutará en 14.

#### NB09 · Celda 1 — Cierre técnico y contrato de aprendizaje

Posición 2 del cuaderno; contador guardado: 1. Fuente: [09_protocolo_PU_y_control.ipynb](../../notebooks/09_protocolo_PU_y_control.ipynb).

```python
from pathlib import Path
import sys
import importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents]
            if (p / 'src/geoau/evaluation.py').is_file())
if str(ROOT / 'src') not in sys.path: sys.path.insert(0, str(ROOT / 'src'))
from geoau import evaluation as ev
importlib.reload(ev)

RUN = ev.current_run(ROOT)
control = ev.finish_run(ROOT, RUN)
display(control)
display(ev.read_json(RUN / "learning_contract.json"))
```

Recupera E y llama a `finish_run`, que verifica etapas de particiones y muestras, reevalúa requisitos científicos, escribe control y sella productos. Muestra además `learning_contract.json`: referencia P/U, elección interna del ratio, evaluación territorial completa, reserva sin ajuste, pesos y agregación de scores. La ejecución actual queda técnicamente completa con `training_allowed=False`; el contrato no confunde ese bloqueo con prohibición de cualquier ensayo diagnóstico posterior explícitamente separado.

#### NB09 · Celda 3 — Verificación de manifiesto y comprobación de autorización

Posición 4 del cuaderno; contador guardado: 2. Fuente: [09_protocolo_PU_y_control.ipynb](../../notebooks/09_protocolo_PU_y_control.ipynb).

```python
ev.verify(RUN, ev.read_json(RUN / 'outputs_manifest.json'))
try:
    ev.assert_ready_for_training(ROOT, RUN)
    print('Protocolo aprobado para fase F.')
except ValueError as error:
    if control.get('training_allowed'): raise
    print(str(error))
    display(control['reasons_not_ready'])
print('Ejecución:', RUN)
```

Verifica los archivos sellados e intenta `assert_ready_for_training`. En diagnóstico captura el `ValueError` esperado y muestra por qué no está aprobado. Si el control indicara autorización pero el guard fallara, vuelve a lanzar el error, evitando ocultar una inconsistencia. La captura no concede aprobación: permite que el notebook termine informando correctamente del bloqueo. F tiene una vía de diagnóstico explícita distinta del modo validado.

### 13.1. Qué entrega y qué falta

E proporciona un protocolo técnico comprobable y congelado: territorio, unidades, particiones, muestras y decisiones. No cierra científicamente tamaño de bloques, representatividad, depósitos, distritos ni cuencas. La transición a un experimento validado necesita nuevos productos de B/D/E con revisión trazable; cambiar únicamente una bandera en F no satisface esos requisitos.

## 14. Notebook 10 — Pipelines y contrato de entrenamiento

Implementa el paso 31 con [training.py](../../src/geoau/training.py). Verifica E y D, congela familias/candidatos/conjuntos X y prepara marcos de evaluación antes de ajustar modelos.

### 14.1. Construcción real de X

`feature_sets` separa familias por nombres del diccionario D. El conjunto denominado `geology` incluye **geología, asociaciones y estructuras**, no sólo litología. Las variantes son 79 predictores base; 85 con relieve; 88 al añadir As/Sb/Bi; 89 al añadir Au; 93 al añadir hidrología; y 120 al sustituir las cuatro modas por 31 proporciones geoquímicas, conservando hidrología.

`authorize_columns` exige pertenencia a la lista candidata o aprobada, existencia de diccionario y ausencia de una lista de auxiliares/etiquetas prohibidas. No selecciona columnas mirando correlación con todo y. Las litologías/edades dominantes y modas geoquímicas se codifican como categorías. Las clases geoquímicas tienen orden conceptual, pero la implementación one-hot actual no impone una relación ordinal o monótona al modelo.

### 14.2. Pipeline, paso por paso

`FeatureGuard` exige un DataFrame con nombres **y orden** exactamente congelados. Convierte numéricos sin coerción silenciosa de texto inválido y trata infinitos como ausentes. En categorías antepone `v:` a valores presentes y usa `__MISSING__` para nulos. No aprende estadísticas en esta conversión.

`ColumnTransformer` divide numéricas y categóricas y descarta cualquier resto. Numéricas: `SimpleImputer(strategy='median', keep_empty_features=True)`; sólo logística añade `StandardScaler`. Categóricas: `SafeOneHot` aprende valores del train y reserva `__UNKNOWN__` y `__MISSING__`; categorías nuevas se asignan al primero. Se utiliza matriz densa float32 en la codificación y `sparse_threshold=0`, aspecto relevante si crece mucho la cardinalidad.

Para una variable numérica totalmente ausente en train, `keep_empty_features=True` mantiene la columna con relleno cero, conforme al comportamiento documentado de [SimpleImputer](https://scikit-learn.org/stable/modules/generated/sklearn.impute.SimpleImputer.html). Es un relleno interno del modelo; no reescribe la capa geocientífica. Aun así, si la variable es una distancia, cero tiene un significado físico fuerte y esta política necesita una evaluación específica de sensibilidad y aplicabilidad.

Los árboles no llevan escalado. Random Forest desactiva OOB como evaluación; HistGradientBoosting desactiva `early_stopping` y usa one-hot en lugar de categorías nativas. Logística emplea `lbfgs`, hasta 3.000 iteraciones y regularización controlada por C; no se ha implementado aquí la ElasticNet que anuncia el README histórico.

### 14.3. Marco de evaluación fijo

Para cada split se guardan **todas** las celdas `role=test` con su área. Antes del ajuste se marcan sus P y una muestra auxiliar reproducible de hasta 10.000 U para AP/ROC-AUC. Los modelos comparten estas mismas celdas; cambiar ratio de entrenamiento no cambia la prueba. El desempate de scores usa hash de celda independiente de etiquetas. No se construyen predicciones ni métricas de reserva.

#### NB10 · Celda 1 — Preparación de F

Posición 2 del cuaderno; contador guardado: 1. Fuente: [10_pipelines_y_contrato_entrenamiento.ipynb](../../notebooks/10_pipelines_y_contrato_entrenamiento.ipynb).

```python
from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)

RUN = tr.ensure_run(ROOT)
display(ev.read_json(RUN/"control_cierre.json"))
display(ev.read_json(RUN/"config_snapshot.json"))
```

Localiza y recarga `training`, recupera o crea F con `ensure_run` y muestra control y configuración. `check_inputs` exige compatibilidad E/F, ratios y realizaciones disponibles y permiso explícito `allow_diagnostic_fit` para diagnóstico. En validado ejecutaría además el guard científico de E. Congela código, configuración, versiones, listas y marcos de evaluación. La salida de `scientific_training_allowed=False` coexistiendo con diagnóstico activo es coherente: se permite probar el código sin atribuir validez científica a los candidatos.

#### NB10 · Celda 3 — Inspección del esquema y los candidatos

Posición 4 del cuaderno; contador guardado: 2. Fuente: [10_pipelines_y_contrato_entrenamiento.ipynb](../../notebooks/10_pipelines_y_contrato_entrenamiento.ipynb).

```python
schema = ev.read_json(RUN/'feature_schema.json')
display(pd.DataFrame([{'set': name, 'predictors': len(v['columns']), 'categorical': len(v['categorical'])}
                      for name, v in schema.items()]))
display(ev.read_json(RUN/'candidates.json'))
```

Muestra tamaños de los seis conjuntos, número de categóricas y candidatos por familia. `candidates` predefine tres configuraciones para cada familia con ratios 3/1/10. El primer RF tiene 500 árboles, hoja mínima 5, `sqrt` y profundidad ilimitada; los demás exploran parámetros por semilla. El ratio cambia conjuntamente con hiperparámetros: estas tres alternativas no permiten aislar el efecto exclusivo del ratio. El número de candidatos es igual entre familias, pero no el coste ni la amplitud efectiva de búsqueda.

### 14.4. Cómo se calcula la métrica central

`metrics` ordena scores descendentes y resuelve empates con `tie_key`. Acumula `land_area_m2` y selecciona el prefijo de celdas completas cuya suma no excede 1 %, 5 % o 10 % del área. El presupuesto realizado puede quedar ligeramente por debajo; se guarda en `area_fraction_*`.

En diagnóstico, `recovery_at_05 = celdas candidatas dentro del prefijo / celdas candidatas del test`. En validado, el numerador y denominador son depósitos distintos y un depósito se recupera si alguna de sus celdas entra. Si un test tiene 100 celdas candidatas y recupera 40 dentro del presupuesto, la recuperación es 0,40; no significa que el 40 % de las celdas priorizadas contengan oro.

`average_precision_PU` utiliza AP de scikit-learn en la muestra P/U fija, una suma de precisiones ponderadas por incrementos de recall, distinta del área trapezoidal de una curva PR. Esta distinción sigue la [definición oficial de average_precision_score](https://scikit-learn.org/stable/modules/generated/sklearn.metrics.average_precision_score.html). Su valor depende del diseño de P/U; una precisión frente a U no estima directamente la tasa de descubrimiento en campo. `roc_auc_PU` también utiliza ese marco etiquetado de observación.

## 15. Notebook 11 — Referencias y regresión logística

Implementa el paso 32. Ofrece controles mínimos para que una métrica alta se compare con referencias informativas sobre el mismo territorio. El ajuste de logística comparte el mecanismo anidado que usarán las demás familias.

### 15.1. Referencias efectivas

La referencia constante asigna 0,5 a toda celda; el ranking territorial se produce por desempate de hash, mientras su ROC-AUC es 0,5. La aleatoria genera un valor reproducible por hash distinto. Ambas deben interpretarse como referencias de orden sin evidencia geológica.

La regla ilustrativa es `s = 0,5·exp(−d_falla/5.000) + 0,5·f_granitoides`. Una distancia ausente se convierte en infinito y aporta cero; la fracción granitoide ausente aporta cero. Es una hipótesis regional sencilla y explícita, no una regla metalogenética universal ni un modelo aluvial. El tratamiento de ausentes aquí difiere del de los clasificadores, lo que también condiciona su rendimiento como referencia.

### 15.2. Flujo compartido de `fit_family`

Para cada externo, se recorre cada candidato y cada interno. `fit_one` lee la muestra E correspondiente y verifica que sus IDs pertenezcan al train; crea un pipeline nuevo y ajusta todas sus transformaciones sólo allí. `evaluate_model` predice todas las celdas del test interno por lotes de 20.000 y calcula métricas. Se promedia recuperación al 5 % con igual peso por fold y se desempata por ID predefinido.

La decisión se guarda antes de evaluar el externo. Se reajusta el candidato elegido sobre su train externo, se predice su test y se guardan pipeline completo, parámetros, variables, semilla reproducible, tiempos, tamaños P/U, hash de muestra y scores OOF. Los modelos internos se descartan de memoria; sus configuraciones y muestras permiten reconstrucción. La política `fit_weighting=none` usa el diseño muestreado sin pesos adicionales; `normalized_design_u` normalizaría pesos de área/inclusión de U para conservar su masa total.

#### NB11 · Celda 1 — Evaluación de referencias

Posición 2 del cuaderno; contador guardado: 1. Fuente: [11_referencias_y_regresion_logistica.ipynb](../../notebooks/11_referencias_y_regresion_logistica.ipynb).

```python
from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)

RUN = tr.current_run(ROOT)
references = tr.fit_references(ROOT, RUN)
display(references)
```

Recupera F y ejecuta `fit_references`. Aunque la función se llama `fit`, las tres referencias no aprenden un estimador: calculan scores predefinidos sobre los cinco tests externos y los evalúan. Guarda quince archivos de predicción, métricas y fórmula de la regla geológica. No utiliza los resultados para elegir una regla diferente ni abre reserva.

#### NB11 · Celda 3 — Entrenamiento anidado de logística

Posición 4 del cuaderno; contador guardado: 2. Fuente: [11_referencias_y_regresion_logistica.ipynb](../../notebooks/11_referencias_y_regresion_logistica.ipynb).

```python
logistic = tr.fit_family(ROOT, RUN, "logistic")
display(logistic)
```

Ejecuta `fit_family(..., 'logistic')`. Cada candidato combina C y ratio; los valores iniciales de C son 1, 0,1 y 10. Un C menor implica mayor regularización. El escalado de numéricas y la codificación categórica se reaprenden en cada entrenamiento. Con cinco externos, tres internos y tres candidatos se realizan 45 ajustes internos y cinco reajustes externos para la familia. La tabla devuelta contiene las métricas externas del candidato que ganó internamente en cada fold.

### 15.3. Lectura de resultados

La logística diagnóstica recupera en promedio el 43,98 % de las celdas candidatas al priorizar el 5 % del área, frente a aproximadamente 5 % de la referencia aleatoria. Este contraste es evidencia de señal predictiva respecto a los candidatos bajo el diseño actual. No permite separar por sí solo señal geológica y sesgo de inventario ni demuestra recuperación de depósitos independientes.

## 16. Notebook 12 — Random Forest espacial

Implementa el paso 33. Random Forest promedia numerosos árboles entrenados con aleatoriedad de muestras y subconjuntos de variables. Esa capacidad para relaciones no lineales no suprime la necesidad de particiones espaciales y revisión de las fuentes.

#### NB12 · Celda 1 — Ajuste y evaluación anidada de Random Forest

Posición 2 del cuaderno; contador guardado: 1. Fuente: [12_random_forest_espacial.ipynb](../../notebooks/12_random_forest_espacial.ipynb).

```python
from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)

RUN = tr.current_run(ROOT)
rf = tr.fit_family(ROOT, RUN, "random_forest")
display(rf)
```

Recupera F y ejecuta la misma función `fit_family` con `random_forest`. Usa los marcos E/F ya congelados, 500 árboles por candidato, cinco externos y tres internos. `min_samples_leaf` controla cuánto pueden adaptarse las hojas a pocos ejemplos; profundidad y `max_features` limitan complejidad y diversidad. OOB queda desactivado y no se usa como prueba de transferencia espacial. Los scores externos sólo se calculan después de guardar la elección interna.

#### NB12 · Celda 3 — Parámetros seleccionados por fold

Posición 4 del cuaderno; contador guardado: 2. Fuente: [12_random_forest_espacial.ipynb](../../notebooks/12_random_forest_espacial.ipynb).

```python
display(pd.DataFrame(ev.read_json(RUN/"random_forest_selections.json")))
```

Lee `random_forest_selections.json` y muestra candidato, ratio, parámetros y recuperación interna media. La selección puede variar entre folds porque cambia el territorio de aprendizaje. En la ejecución examinada gana el candidato 02 con ratio 10 en cuatro folds y el candidato 00 con ratio 3 en uno. Esto no demuestra que 10:1 sea universalmente mejor: el ratio está asociado a otros parámetros y los datos de entrenamiento difieren.

### 16.1. Interpretación y reproducibilidad

La media externa RF de recuperación al 5 % es 52,20 %, y AP P/U media 0,1654. La dispersión entre folds es considerable y no es un intervalo de confianza basado en depósitos independientes. Los metadatos registran RSS del proceso después del ajuste: no es pico de memoria ni consumo exclusivo del modelo. Los pipelines guardados contienen guard, transformaciones y estimador; conservar sólo el bosque sin codificadores haría incompatible una inferencia posterior.

## 17. Notebook 13 — Alternativas y comparación

Implementa el paso 34 con ExtraTrees e HistGradientBoosting. No ejecuta XGBoost, LightGBM, CatBoost, KNN, SVM ni Naïve Bayes, aunque aparezcan mencionados como ampliaciones o en documentación histórica.

### 17.1. Diferencias de algoritmos

ExtraTrees construye árboles con mayor aleatoriedad en umbrales y agrega sus respuestas. Comparte en el código la familia de parámetros de RF, pero sus mecanismos internos y defaults no son idénticos. HistGradientBoosting añade iterativamente árboles que corrigen errores de la función objetivo y discretiza numéricos para el cálculo. Aquí usa 100 iteraciones predefinidas, tasa de aprendizaje y complejidad de hojas, sin parada temprana basada en una partición aleatoria oculta.

#### NB13 · Celda 1 — ExtraTrees anidado

Posición 2 del cuaderno; contador guardado: 1. Fuente: [13_comparacion_modelos.ipynb](../../notebooks/13_comparacion_modelos.ipynb).

```python
from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)

RUN = tr.current_run(ROOT)
extra = tr.fit_family(ROOT, RUN, "extra_trees")
display(extra)
```

Recupera F y llama a `fit_family(..., 'extra_trees')`. Igual que RF, utiliza tres candidatos de 500 árboles y selecciona dentro de cada externo, con sus propias realizaciones deterministas del estimador. Comparte muestras para un mismo ratio/split, predictores de referencia y test fijo. El resultado actual tiene recuperación media al 5 % de 46,17 %. No es una ablación de aleatoriedad controlando cada diferencia de algoritmo, sino comparación de procedimientos de ajuste predefinidos.

#### NB13 · Celda 2 — HistGradientBoosting anidado

Posición 3 del cuaderno; contador guardado: 2. Fuente: [13_comparacion_modelos.ipynb](../../notebooks/13_comparacion_modelos.ipynb).

```python
boost = tr.fit_family(ROOT, RUN, "hist_boosting")
display(boost)
```

Ejecuta la cuarta familia. El constructor impone `early_stopping=False` y `categorical_features=None` porque las categorías ya están codificadas. Explora tasas 0,1/0,05/0,15, tamaños de hojas y ratios asociados. La recuperación media externa al 5 % es 53,39 %. Es mayor que la media RF en esta tabla descriptiva, pero por sí sola no autoriza proclamar un ganador final tras inspeccionar los tests externos.

#### NB13 · Celda 4 — Comparación agregada por familia

Posición 5 del cuaderno; contador guardado: 3. Fuente: [13_comparacion_modelos.ipynb](../../notebooks/13_comparacion_modelos.ipynb).

```python
families = ev.read_json(RUN/'config_snapshot.json')['families']
comparison = pd.concat([pd.read_csv(RUN/f'{f}_outer_metrics.csv') for f in families])
display(comparison.groupby('family')[['recovery_at_05','average_precision_PU','roc_auc_PU']].agg(['mean','std']))
```

Lee los CSV externos de las cuatro familias, los concatena y calcula media y desviación estándar de recuperación, AP y ROC-AUC. Cada fold tiene el mismo peso, aunque área y número de candidatos varíen. La desviación estándar de pandas utiliza corrección muestral; no debe confundirse con incertidumbre por celda del bagging. La tabla no incluye todavía las referencias en esta vista —el cierre 14 sí genera una comparación conjunta— ni calcula intervalos pareados por unidades.

### 17.2. Cómo interpretar la comparación

Las familias comparten el marco de prueba y el número de candidatos, lo que permite comparaciones pareadas dentro de fold. AP cambia también con la proporción P/U del fold, porque se mantienen todas las P y hasta 10.000 U. La media de AP de cinco folds no es una precisión poblacional. El procedimiento final de F elegirá también la **familia** por sus medias internas, no por escoger la fila con mayor media externa de esta pantalla.

## 18. Notebook 14 — Ablaciones, bagging de U y cierre

Implementa el paso 35 y la agregación del paso 30. Utiliza `run_sensitivity` y `finish_run` de [training.py](../../src/geoau/training.py), líneas 401–490. Produce contrastes de familias de variables y variación del fondo, y documenta la selección anidada completa.

### 18.1. Ablaciones y control experimental

Para cada externo se ajustan los seis conjuntos X con un RF fijo de 150 árboles, hoja mínima 5, `sqrt`, profundidad ilimitada, ratio 3 y realización 0. Se conserva soporte `eligible_geo4`, train, test y semilla del estimador para el mismo fold. Así la diferencia principal entre estas variantes es el conjunto de variables. No se deben comparar sus resultados como si se hubiera usado el RF optimizado de 500 árboles de 12: la referencia interna apropiada es el conjunto completo de **esa misma ablación fija**.

Las seis variantes son base geológica/estructural; añadir relieve; añadir As/Sb/Bi; añadir Au; añadir hidrología; y sustituir las modas de Au/As/Sb/Bi por proporciones conservando hidrología. No se evalúan aquí cambios de resolución, buffers, confianza de etiquetas o geofísica. Esos cambios requieren nuevas ejecuciones anteriores que mantengan la cadena de evidencia.

### 18.2. Bagging de U

Para cada fold se reutiliza el RF seleccionado internamente con realización 0 y se ajustan dos modelos adicionales con realizaciones U 1 y 2. Mantiene P, parámetros y territorio test. El score final es `media(s_0, s_1, s_2)`; la dispersión es `sqrt(media((s_r − media_s)²))`, desviación poblacional de tres miembros.

También cambia la semilla del estimador con la realización. Por tanto, la dispersión combina cambio de U y aleatoriedad del RF; no aísla exclusivamente el efecto del fondo, no es un intervalo de confianza de presencia y no estima prevalencia. Los tres miembros son pocos para caracterizar estabilidad fina. La mejora mediante bagging es una hipótesis a evaluar, no una propiedad garantizada: en esta ejecución su recuperación media al 5 % es ligeramente inferior a RF individual.

#### NB14 · Celda 1 — Ejecución de sensibilidad

Posición 2 del cuaderno; contador guardado: 1. Fuente: [14_ablaciones_PU_y_cierre.ipynb](../../notebooks/14_ablaciones_PU_y_cierre.ipynb).

```python
from pathlib import Path
import sys, importlib
import pandas as pd
from IPython.display import display
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p/'src/geoau/training.py').is_file())
if str(ROOT/'src') not in sys.path: sys.path.insert(0, str(ROOT/'src'))
from geoau import training as tr
from geoau import evaluation as ev
importlib.reload(tr)

RUN = tr.current_run(ROOT)
sensitivity = tr.run_sensitivity(ROOT, RUN)
display(sensitivity)
```

Recupera F y exige que las cuatro familias estén terminadas. `run_sensitivity` ajusta seis ablaciones por cada uno de los cinco externos y dos RF adicionales de bagging por externo; guarda modelos, predicciones individuales, media/dispersión y métricas. Son 30 ajustes de ablación y diez miembros nuevos de PU. Si existe un sello completo de sensibilidad se verifica y reutiliza; un procesamiento parcial no recibe aprobación por tener algunos archivos presentes.

#### NB14 · Celda 3 — Cierre de F y procedimiento seleccionado

Posición 4 del cuaderno; contador guardado: 2. Fuente: [14_ablaciones_PU_y_cierre.ipynb](../../notebooks/14_ablaciones_PU_y_cierre.ipynb).

```python
control = tr.finish_run(ROOT, RUN)
display(control)
display(pd.read_csv(RUN/'nested_procedure_metrics.csv'))
display(ev.read_json(RUN/'pending_experiments.json'))
```

`finish_run` verifica referencias, cuatro familias y sensibilidad. Genera comparación conjunta y, en cada externo, elige familia/candidato exclusivamente por `mean_inner_recovery_at_05`, con desempates predefinidos. Copia sus predicciones a `nested_selected_*`, calcula métricas del procedimiento de selección y guarda contrato, pendientes y manifiesto final. Mantiene `scientific_validation_complete`, `prediction_allowed` y `production_allowed` en falso. La reserva sigue sin predicciones ni métricas.

#### NB14 · Celda 4 — Gráfico comparativo y verificación final

Posición 5 del cuaderno; contador guardado: 3. Fuente: [14_ablaciones_PU_y_cierre.ipynb](../../notebooks/14_ablaciones_PU_y_cierre.ipynb).

```python
import matplotlib.pyplot as plt
table = pd.read_csv(RUN/'comparison_by_fold.csv')
fig, ax = plt.subplots(figsize=(10, 5))
for name, part in table.groupby('family'):
    ax.plot(part.split_id, part.recovery_at_05, marker='o', label=name)
ax.set(ylabel='Fracción de celdas candidatas recuperadas al 5 % del área',
       xlabel='Fold externo', title='Ensayo diagnóstico · sin interpretación probabilística')
ax.legend(bbox_to_anchor=(1.02, 1)); fig.tight_layout(); plt.show()
ev.verify(RUN, ev.read_json(RUN/'outputs_manifest.json'))
```

Lee `comparison_by_fold.csv`, dibuja recuperación al 5 % por fold para referencias y familias y comprueba el manifiesto F. El gráfico usa como unidad celdas candidatas, coherente con diagnóstico. El rótulo tendría que adaptarse al modo validado si se incorporan depósitos revisados. La figura no decide el ganador del procedimiento ni cambia umbrales; la selección ya se hizo con datos internos.

### 18.3. Presupuesto real y alcance de cierre

La configuración corresponde a 180 ajustes internos —4 familias×5 externos×3 internos×3 candidatos—, 20 reajustes externos, 30 ablaciones y diez modelos nuevos de bagging: **240 ajustes** del diseño completo. Se guardan 60 pipelines externos; los 180 internos no se serializan. Las referencias no requieren ajuste. La presencia de 60 archivos en F y de una carpeta raíz `models/` vacía son compatibles: se guardan dentro del directorio de ejecución, no en el directorio histórico anunciado por el README.

El cierre permite inspeccionar una cadena técnica reproducible. Falta la fase G de revisión, explicación, estabilidad por grupos y aplicabilidad; también H de reentrenamiento autorizado, mapas de entrega, objetivos e inferencia por coordenadas. No existe todavía un mapa final validado ni un servicio de predicción operativo acreditado por estos notebooks.


## 19. Resultados diagnósticos comprobados

Las cifras siguientes se han leído y agregado desde `reports/fase_f/20260909T184735_016759Z/comparison_by_fold.csv`. Los validadores han recomputado las métricas a partir de las predicciones guardadas. Son medias de cinco folds con igual peso; ± indica desviación estándar entre folds, no intervalo de confianza ni incertidumbre física sobre presencia de oro.

| Procedimiento | Recuperación al 5 % del área | AP P/U media | ROC-AUC P/U media |
|---|---:|---:|---:|
| Constante con desempate por hash | 0,0543 ± 0,0214 | 0,0127 | 0,5000 |
| Aleatorio reproducible | 0,0500 ± 0,0129 | 0,0129 | 0,4849 |
| Regla geológica ilustrativa | 0,0632 ± 0,0423 | 0,0178 | 0,6336 |
| Regresión logística | 0,4398 ± 0,1159 | 0,1027 | 0,8719 |
| Random Forest | 0,5220 ± 0,1097 | 0,1654 | 0,8965 |
| ExtraTrees | 0,4617 ± 0,1306 | 0,1355 | 0,8905 |
| HistGradientBoosting | 0,5339 ± 0,0622 | 0,1524 | 0,9032 |

El valor de 0,5339 significa que, en promedio entre folds, se recupera aproximadamente el 53,39 % de las **celdas con candidatos de inventario** al priorizar hasta el 5 % de su área de test. No significa 53,39 % de probabilidad de encontrar oro, ni 53,39 % de depósitos revisados, ni 53,39 % de éxito prospectivo en lugares desconocidos.

RF tiene mayor AP media que boosting, pero boosting mayor recuperación al 5 %. No es contradicción: las métricas valoran aspectos distintos del ranking y del conjunto P/U. Según el plan, la métrica operativa primaria es la recuperación territorial. Aun así, elegir una familia global después de ver esta tabla consumiría información externa de desarrollo y requeriría validación posterior; F conserva la selección de familia por resultados internos de cada fold.

### 19.1. Ablaciones y bagging

| Variante | Recuperación media al 5 % | Condición de comparación |
|---|---:|---|
| Geología + estructuras | 0,4368 | RF fijo, 150 árboles, ratio 3 |
| Añadir relieve | 0,4442 | Mismo diseño y soporte |
| Añadir As/Sb/Bi | 0,4662 | Mismo diseño y soporte |
| Añadir Au | 0,4688 | Mismo diseño y soporte |
| Añadir hidrología | 0,5066 | Referencia completa de la ablación fija |
| Proporciones en lugar de las cuatro modas | 0,5043 | Conserva hidrología; mismo RF fijo |
| Bagging de tres realizaciones U | 0,5093 | RF elegido internamente; comparar con RF 0,5220 |

En este ensayo, el incremento medio al añadir Au después de As/Sb/Bi es pequeño, alrededor de 0,0026. Hidrología muestra un incremento mayor, alrededor de 0,0378 respecto a la variante anterior. Son diferencias exploratorias sobre celdas candidatas y un mismo territorio con geoquímica disponible. No se han calculado aquí intervalos pareados por depósitos/bloques para afirmar significación o transferencia general. La mejora no debe interpretarse como causalidad geológica.

La variante de proporciones no supera claramente a la modal en la media de este contraste, y bagging no mejora recuperación media respecto al RF individual seleccionado. Ambos resultados son útiles porque impiden asumir que más columnas o más miembros siempre mejoran la métrica principal. Tampoco prueban que esas variantes sean inútiles bajo etiquetas o protocolos revisados.

## 20. Correspondencia con los 44 pasos del plan

«Implementado» describe código y artefactos técnicos comprobables. «Parcial» indica funciones disponibles pero requisitos o productos incompletos. «Pendiente» no significa necesariamente un defecto: el plan prevé extensiones condicionadas a datos y revisión.

| Paso | Entrega prevista | Estado y ubicación efectiva |
|---:|---|---|
| 01 | Especificación de experimento y piloto | Parcial: `project.yaml`; piloto y objetivos científicos por cerrar |
| 02 | Entorno reproducible y pruebas GIS | Implementación técnica A y dependencias por fase; falta un cierre único de dependencias de F |
| 03 | Inventario/manifiesto de fuentes | Implementado en 00 con hashes y estados |
| 04 | Lectores y acceso a datos | Implementado en `local_sources.py`; geometría avanzada se resuelve en C |
| 05 | Catálogo y clasificación de fuentes | Implementado técnicamente en A; procedencia/licencias/semántica no todas verificadas |
| 06 | Resolver o recuperar entradas necesarias | Parcial: pendientes A y ocho capas adicionales integradas en C; no descarga desde 00 |
| 07 | Conciliación de indicios | Implementada en 01; discrepancias no resueltas individualmente |
| 08 | Normalizar conservando originales | Implementado; celda 11 de 01 elimina el indicador propagado de conflicto |
| 09 | Verificación territorial y administrativa | Parcial: QC básico y cuarentena; máscara/admin de B sin configurar |
| 10 | Códigos, posiciones y depósitos | Parcial: posiciones/grupos de proximidad; sin depósitos/distritos revisados |
| 11 | Contexto aurífero revisado | Plantilla y validadores implementados; cero positivos revisados |
| 12 | Representatividad y sesgo | EDA de registros; análisis por depósitos/distritos y esfuerzo pendiente |
| 13 | Máscara y rejilla | Implementado en 02; máscara regional candidata, sólo componente principal |
| 14 | Soporte uniforme por variable | Diccionario C y definición efectiva D implementados |
| 15 | Reproyección y saneamiento | Implementado con QC y caché; linealización contrastada en muestra |
| 16 | Alineación de rásteres | Implementada para mallas exactamente anidadas 500 m→1 km |
| 17 | Cobertura por ámbito/familia | Implementada; la cobertura de levantamientos estructurales sigue desconocida |
| 18 | Litología, edad y unidades | Parcial: cartografía regional y asociaciones explícitas; recintos detallados y jerarquía geológica pendientes |
| 19 | Variables estructurales | Base GEODE implementada; densidades aproximadas y semántica pendiente |
| 20 | Estructuras avanzadas | Pendiente: intersecciones, orientación, pliegues y buzamientos como predictores |
| 21 | Geoquímica clasificada | Implementada con QC RGB; leyenda, unidades, medio y extracción aún por validar |
| 22 | Geoquímica analítica cuantitativa | Pendiente/opcional; no se han creado análisis a partir de colores |
| 23 | Relieve reconstruido | Implementado con máscara, fórmulas y radios explícitos |
| 24 | Hidrología/aluvial | Distancia/densidad regional implementadas; terrazas, cuencas y altura relativa pendientes |
| 25 | Geofísica cuantitativa | Pendiente; C incorpora diagnóstico de fuentes, no bloques predictivos aprobados |
| 26 | `Grid_Master_Au` y roles | Implementado en 06; 168 candidatos, sin predictores aprobados |
| 27 | Particiones espaciales y separación | Implementado diagnóstico en 07; faltan grupos y justificación científica |
| 28 | Reserva y anidamiento | Implementado técnico; reserva de unidades geográficas, no distritos acreditados |
| 29 | Muestras U por entrenamiento | Implementado en 08: 180 diseños; alternativa por esfuerzo pendiente |
| 30 | P/U y bagging | Contrato en 09, clasificadores en F, bagging en 14; sin estimar prevalencia |
| 31 | Pipelines sin aprendizaje global | Implementado en 10, guard y pruebas de transformaciones por train |
| 32 | Referencias mínimas | Implementadas constante/aleatoria/regla/logística en 11 |
| 33 | Random Forest anidado | Ejecutado diagnóstico; tres candidatos, no búsqueda de 20–30 |
| 34 | Comparación gradual | Cuatro familias implementadas; alternativas avanzadas opcionales pendientes |
| 35 | Ablaciones y sensibilidad | Seis conjuntos y tres fondos; 500 m, etiquetas, buffers y geofísica pendientes |
| 36 | Métricas territoriales y espaciales | Núcleo ya implementado en F; falta cierre G por depósitos/distritos e intervalos por grupos |
| 37 | Explicación sobre retenidos | Pendiente: permutación por familias, SHAP y revisión sistemática de casos/artefactos |
| 38 | Estabilidad y aplicabilidad | Parcial: dispersión del bagging; no hay área de aplicabilidad ni diagnóstico completo de extrapolación |
| 39 | Criterios de aceptación | Pendiente; no hay aprobación científica ni operativa |
| 40 | Reentrenamiento e inferencia final | Pendiente; scores OOF no son reentrenamiento final de entrega |
| 41 | Objetivos geológicos | Pendiente; no hay delimitación final roca/aluvial aprobada |
| 42 | Revisión de objetivos/campañas | Pendiente; requiere evidencia y revisión geológica |
| 43 | Entrega, QGIS e inferencia puntual | Pendiente; la API y rutas del README histórico no existen como producto actual |
| 44 | Mantenimiento y revalidación | Parcial: fundamentos de hashes/versionado; sin ciclo de sustitución de modelo validado |

### 20.1. Cambios relevantes respecto al documento de septiembre 5

La afirmación histórica de que faltan módulos, pruebas y modelos ya no describe todo el repositorio: existen `src/geoau`, 62 pruebas y modelos dentro de F. En cambio, la advertencia de no usar los benchmarks antiguos del README continúa siendo pertinente. Los archivos vacíos de la primera auditoría han cambiado de estado tras recuperación; el inventario A más reciente sólo informa un archivo sin datos.

El diseño llegó hasta una ejecución diagnóstica peninsular antes de cerrar el piloto y los positivos revisados. Puede ser útil para comprobar ingeniería y detectar problemas, pero no constituye el hito V1 validado del plan. El siguiente avance científico prioritario no es agregar más algoritmos: es completar y propagar revisión de etiquetas, depósitos, cartografía y protocolo.

## 21. Hallazgos priorizados y acciones concretas

Se distingue entre hechos reproducidos, riesgos inferidos del código y tareas científicas pendientes. La prioridad indica el impacto sobre la interpretación o reproducibilidad; no implica que todos los puntos sean errores que hayan afectado a los resultados actuales.

### H01 — Falta la evidencia necesaria para presentar un modelo validado

**Prioridad alta; hecho comprobado.** B/D/E contienen cero positivos revisados; D no aprueba columnas de entrenamiento; no hay depósitos/distritos y cartografía territorial revisada ni criterios de aceptación cerrados. Los controles científicos y producción están correctamente bloqueados. Evidencia: `control_cierre.json` de B–F, `feature_allowlist.json` D y `readiness.json` E.

**Acción:** completar revisión documentada por indicio y depósito, justificar ámbito y particiones y generar nuevas ejecuciones dependientes. Hace falta además una vía versionada para aprobar predictores: `assemble` escribe actualmente una lista aprobada vacía de forma incondicional. La fase de revisión debe aportar un artefacto auditable de aprobación; editar manualmente un JSON sellado rompe la cadena y no es un procedimiento de aceptación.

### H02 — El notebook 01 pierde `conflicto_au` en ejecución secuencial

**Prioridad alta para incorporar revisiones; reproducido.** La celda 10 propaga conflictos por código y la 11 reconstruye `normalizados` sin esa columna. La conciliación independiente sigue conservando conflictos, pero el inventario que alimenta revisiones y QC pierde ese indicador. Los tests del módulo no ejecutan esta secuencia completa de celdas.

**Acción:** una única normalización y propagación posterior de conflictos; comprobar al final de la secuencia que el indicador existe y coincide con la conciliación. No es necesario rehacer el algoritmo de normalización para resolver un error de orquestación del notebook.

### H03 — Una celda de visualización modifica candidatos usados posteriormente

**Prioridad alta para datos futuros; riesgo confirmado en el código, sin pérdida efectiva demostrada en los Au actuales.** La celda 24 de 01 convierte coordenadas y reasigna `candidatos = candidatos.dropna(...)`. Un registro sin coordenadas quedaría fuera de la rama de etiquetas/exportación por haber dibujado un mapa. Su persistencia en `qc` no evita una discrepancia entre el inventario y las tablas específicas Au.

**Acción:** crear `candidatos_mapa = candidatos.copy()` y filtrar sólo esa vista. Registrar candidatos excluidos del cálculo espacial por motivo, conservándolos en las tablas de revisión. Añadir una comprobación de invariancia del conjunto de IDs antes/después de figuras.

### H04 — Reproducción de F ligada a una carpeta externa antigua

**Prioridad alta de portabilidad; hecho comprobado.** Los 60 metadatos de modelos incluyen `sample_path` absoluto bajo `.../Proyecto Con Luis/...`, fuera de la raíz actual `.../GeoAI/GeoAI`. `scripts/validar_fase_f.py` abre directamente esa ruta. En este equipo la carpeta antigua todavía existe, los hashes concuerdan y la validación pasa; eso no demuestra reproducción autónoma de una copia trasladada a otro equipo.

**Acción:** guardar ruta relativa al proyecto o a la ejecución E junto a su hash. En la validación resolverla desde la raíz actual y comprobar pertenencia a la E declarada. Conservar la ruta de origen como metadato informativo si interesa. La comprobación definitiva debe realizarse desde una copia aislada que no pueda leer la carpeta histórica.

### H05 — El ejecutor raíz y buena parte del README son incompatibles con la estructura actual

**Prioridad alta de uso; ausencia de destinos comprobada.** `run_pipeline.py` invoca `src/build_ml_dataset_v2.py`, `src/run_spatial_experiments_v2.py`, `src/build_interactive_map_v2.py` y `tests/test_geoai_hardened_suite.py`, ninguno presente. El README anuncia otro paquete, otros notebooks, 906 positivos, métricas y una API por coordenadas que no corresponden a esta cadena.

**Acción:** reescribir el punto de entrada alrededor de los ejecutores reales, o marcar claramente el CLI como histórico hasta reemplazarlo. Consolidar README con el estado A–F, rutas correctas y los límites actuales. Los avisos al principio del README ayudan, pero no eliminan las instrucciones contradictorias posteriores.

### H06 — Pérdida de media longitud en un caso de borde terrestre

**Prioridad media; reproducción sintética, impacto nacional no cuantificado.** `lines` pasa a `line_lengths` el borde del rectángulo total del ráster. `line_lengths` considera compartido un segmento sobre borde de celda que no esté en ese borde exterior. Si sólo una celda con tierra participa y su borde coincide con la costa sobre una línea de rejilla, reparte la mitad como si existiera una segunda celda contabilizada. En el caso mínimo revisado, una traza de 10 m produce 5 m.

**Acción:** repartir por multiplicidad real de celdas procesadas o reconocer los bordes del dominio terrestre efectivo, manteniendo el reparto correcto entre teselas. Incluir ejemplos de costa/huecos sobre rejilla y comprobar conservación de longitud. No se afirma que todas las densidades actuales estén divididas por dos: el caso requiere una coincidencia geométrica específica.

### H07 — Ausencia de traza y distancia superior al límite comparten `NaN`

**Prioridad científica alta; diseño explícito con consecuencias.** Las distancias quedan ausentes cuando no hay traza a 10 km, y las densidades pueden valer cero sin huella de levantamiento acreditada. F imputa medianas; una columna totalmente ausente recibe cero dentro del pipeline. Esto puede hacer que una celda muy alejada o no cartografiada reciba una distancia típica, o cero en un train sin observaciones de esa variable.

**Acción:** separar censura por radio de falta de cobertura cuando las fuentes lo permitan. Estudiar distancia truncada acompañada de indicador, exclusión de variables casi vacías o dominios de aplicabilidad. Las alternativas deben contrastarse dentro de la validación interna y sin introducir máscaras de campaña como predictores de forma inadvertida. El hecho de que la imputación no use test evita una fuga estadística, pero no resuelve la semántica del dato ausente.

### H08 — Geoquímica validada contra paletas locales, todavía no contra significado analítico

**Prioridad científica alta; limitación reconocida.** La coherencia RGB descarta clasificaciones dudosas, pero no certifica medio, extracción, umbral, unidad ni procedencia del dato cartográfico. La pérdida de soporte Zn/W muestra además que exigir todos los elementos cambia mucho el ámbito.

**Acción:** revisar leyendas oficiales y metadatos de cada capa; conservar mapas de aceptación/rechazo y estudiar independencia de minería/contaminación y soporte sedimentario. Si se recuperan valores analíticos, crear una versión distinta, sin presentar puntos medios de intervalos como medidas continuas.

### H09 — Geología regional, redundancia y estructuras incompletas

**Prioridad científica media/alta.** D usa litología/edades regionales, aunque C tenga recintos detallados. Retiene dominantes, fracciones y asociaciones superpuestas; el conjunto completo F supera el presupuesto inicial de variables del plan. Pliegues, orientaciones, geofísica y aluvial detallado aún no están implementados como bloques.

**Acción:** revisar jerarquía geológica y elegir representaciones según evidencia, con control de cardinalidad y redundancia. La selección estadística aprendida debe entrar dentro del pipeline interno. Validar el valor de datos detallados antes de expandir la matriz por disponibilidad de archivos.

### H10 — La búsqueda mezcla efecto del ratio y del hiperparámetro

**Prioridad media; limitación experimental explícita.** Con tres candidatos, cada ratio corresponde a parámetros diferentes. Las medias por candidato sirven para seleccionar una alternativa conjunta, pero no identifican cuánto de la diferencia se debe al ratio o a la complejidad del modelo. El mismo número de candidatos entre familias tampoco iguala coste computacional.

**Acción:** una vez revisado el protocolo, predefinir una búsqueda mayor y un contraste pequeño que mantenga parámetros al cambiar ratio. No explorar todas las combinaciones sobre el test externo ni elegir una configuración después de ver la reserva.

### H11 — La reserva y los grupos aún no responden a la unidad geológica del plan

**Prioridad científica alta.** La reserva de aproximadamente 15 % de unidades contiene sólo 23 de las 666 celdas candidatas elegibles, alrededor de 3,45 %. Los bloques del diagnóstico evitan una partición puntual aleatoria, pero falta explicar su relación con distritos, independencia efectiva y objetivo de transferencia.

**Acción:** revisar depósitos y territorio antes de una evaluación científica, estudiar dependencia espacial y diseñar reserva geológica con capacidad informativa. La lectura de estos recuentos no autoriza escoger una reserva nueva por una métrica favorable. No se ha abierto aquí la reserva para calcular scores.

### H12 — Reejecución y generadores de notebooks tienen comportamientos diferentes

**Prioridad media de mantenimiento.** Los generadores 00/01/02 escriben sus destinos sin protección de existencia; los generadores D/E/F conservan notebooks existentes. Por tanto, ejecutar un creador antiguo puede borrar anotaciones/salidas manuales, mientras ejecutar uno posterior no actualiza cambios en la plantilla. A sí registra un hash del tipo/fuente del cuaderno 00, pero no hay un contrato uniforme que vincule las salidas antiguas de toda la serie al texto actual de cada celda. Un contador de ejecución o un output sin error no demuestra esa correspondencia.

**Acción:** separar creación, actualización y ejecución, con respaldo o propuesta de diferencias para actualizaciones. Sellar también el contenido fuente de notebooks consumidos cuando se publican resultados y usar ejecuciones completas desde kernel limpio para comprobar su orquestación. Esta revisión no ha ejecutado generadores ni sobrescrito cuadernos.

### H13 — Dependencias y versiones no tienen una única fuente de verdad

**Prioridad media de instalación.** `pyproject.toml`, `requirements.txt` y archivos por fase no enumeran exactamente el mismo entorno. Por ejemplo, el paquete base no declara todos los componentes usados por notebooks y fases actuales; los locks A/D no constituyen un lock completo F. El entorno local tiene scikit-learn 1.9.0 y pasa unittest; `pytest` no estaba instalado, aunque se mencione en dependencias generales.

**Acción:** consolidar dependencias base y extras por fase, fijar un entorno completo probado y documentar la orden real de pruebas. No deducir incompatibilidad de Python 3.14 sólo por el aviso antiguo del plan: el entorno concreto de esta revisión ejecutó satisfactoriamente las pruebas. Tampoco deducir que cualquier instalación mínima declarada reproduzca ese entorno.

### H14 — Condiciones de calidad no equivalen todavía a una máscara de aplicabilidad

**Prioridad alta para publicación.** Los conjuntos elegibles y el estado de categorías desconocidas protegen aspectos de soporte, pero no miden novedad multivariante, cambio de dominio geológico ni representatividad respecto a train. El bagging guarda dispersión de tres ajustes y no satisface todo el paso 38.

**Acción:** implementar G con explicaciones sobre datos retenidos, diagnóstico de extrapolación y reglas de no evaluable. Después cerrar criterios de aceptación y H. Un mapa suave de scores o varias métricas altas no sustituyen esa decisión.

## 22. Código auxiliar e histórico

### 22.1. Scripts de adquisición geoquímica

Los scripts de Au/As/Sb/Bi y el batch de Hg/Cu/Pb/Zn/W siguen una secuencia similar: fijar rutas y paleta; solicitar imagen renderizada del servicio; clasificar colores por distancia mínima; crear TIFF de clase y valores representativos/límites; vectorizar clases; y, cuando corresponde, muestrear sobre el mismo inventario de indicios. El número de filas enriquecidas no es número de muestras nuevas.

En `generar_mapa_geoquimica_oro.py`, `clasificar_pixeles` acepta los píxeles con alfa no nulo y elige `argmin` sin umbral de rechazo. `generar_geotiff` guarda cuatro bandas derivadas de esa clasificación y `generar_vector_geopackage` produce polígonos de clases. Las etiquetas de funciones que hablan de valores continuos o atributos analíticos son más fuertes que lo que realmente crean. El control de 04 mejora esta debilidad al exigir coherencia RGB, sin inventar análisis químicos.

Estos scripts contienen rutas históricas y pueden descargar/escribir datos. La fase D sólo lee sus constantes mediante AST; no los ejecuta ni necesita importar sus efectos secundarios. Para regenerar fuentes habría que crear una ejecución de adquisición versionada con parámetros y metadatos adecuados.

### 22.2. Dos implementaciones históricas de relieve que no deben confundirse

`descargar_mdt_cnig.py` solicita elevación, la reproyecta/remuestrea y calcula gradientes y estadísticas locales tras sustituir huecos por cero para ciertas operaciones. Su banda denominada TRI es una desviación local basada en momentos; su comentario de ventana 3×3 como radio 1,5 km no representa correctamente ese soporte.

`generar_topografia_mdt_cnig.py` utiliza otra implementación: copia una respuesta WCS con offsets redondeados, calcula derivadas tipo Sobel, TPI respecto a ocho vecinos y una raíz de media de diferencias cuadráticas usando `np.roll`. El redondeo de offsets puede desalinear datos si el origen recibido no cae en la rejilla; `np.roll` conecta bordes opuestos en sus desplazamientos. Tampoco debe generalizarse a este script la fórmula exacta de TRI del anterior: son derivados distintos.

El notebook 05 corrige la dependencia de esas bandas reconstruyendo relieve desde la banda de elevación con definiciones explícitas. Queda pendiente acreditar la procedencia y precisión de la elevación fuente: recalcular derivadas no corrige retroactivamente un posible error de georreferenciación en un MDT ya producido.

### 22.3. Ejecutores y validadores

`scripts/ejecutar_notebook_00.py`, 01 y 02 usan un kernel temporal configurado con `sys.executable`, ejecutan desde `notebooks/` y guardan la salida cuando termina correctamente. Los ejecutores D/E/F permiten `--desde`/`--hasta`, transmiten progreso y guardan un `.failed.ipynb` en caso de error. Esto ayuda a inspeccionar fallos sin reemplazar el cuaderno original con una ejecución incompleta.

Los validadores D/E/F revisan productos sin recalcular la cadena nacional. D comprueba matrices y roles; E recorre muestras, reservas, buffers y pesos; F reconstituye selecciones internas, recomputa métricas, comprueba imputación/categorías aprendidas y reproduce predicciones de control. Su resultado depende también de que los metadatos apunten a las muestras correctas, incluida la limitación de rutas absolutas de H04.

## 23. Comprobaciones realizadas y sus límites

### 23.1. Suite de pruebas existente

Se ejecutó desde la raíz actual:

```powershell
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -v
```

Resultado: **62 pruebas, todas satisfactorias**, en 9,552 segundos según unittest. Se observaron avisos de futura deprecación de operaciones de `Affine`, no fallos. El código operativo no se modificó para conseguir este resultado.

| Archivo | Pruebas | Qué comprueba principalmente |
|---|---:|---|
| `test_local_sources.py` | 6 | Ceros de ID, CSV, rutas, curvas, máscaras, ventanas y hashes |
| `test_labels.py` | 6 | Tokens, originales, conciliación, geometría, revisión y proximidad |
| `test_territory.py` | 11 | Área terrestre, costa/huecos, clases, alineación, geometría y paginación |
| `test_additional_layers.py` | 3 | Conservación de puntos/Z, QC angular y restricciones de caché |
| `test_features.py` | 14 | Intersecciones, distancias, longitudes, relieve, RGB, matriz y escritura |
| `test_evaluation.py` | 12 | Grupos, separación, muestras, autorización, hashes y anidamiento |
| `test_training.py` | 10 | Guard, imputación por train, categorías, métricas, serialización y selección interna |

Son pruebas sustantivas con ejemplos conocidos y algunos flujos sintéticos integrados. No constituyen una ejecución completa de los 15 notebooks ni cubren todas las decisiones geológicas. En particular, no detectaban la sobrescritura entre celdas 10/11 de 01 ni el caso costero concreto de H06.

### 23.2. Validadores sobre productos reales

| Comprobación | Resultado de esta revisión | Alcance |
|---|---|---|
| `scripts/validar_fase_d.py` | Correcto, código 0 | Matriz, particiones, roles, etiquetas, rangos y hashes |
| `scripts/validar_fase_e.py` | Correcto, código 0 | 180 muestras; hashes, anidamiento, reserva, distancias, etiquetas y pesos |
| `scripts/validar_fase_f.py` | Correcto, código 0 | 60 pipelines y 85 archivos OOF; selección, imputación, categorías, métricas y bagging |

F reproduce **15 predicciones de control por pipeline**, seleccionadas a lo largo del archivo de cada modelo; no se volvió a predecir todo el territorio con cada modelo. Las métricas de comparación sí se recomputaron desde los scores completos ya guardados. Las medianas, escalas y categorías se contrastaron con las muestras que indica cada metadato. Los logs se conservan en `validacion_fase_d.txt`, `validacion_fase_e.txt`, `validacion_fase_f.txt` y el resumen en `resultado_validadores.json`.

### 23.3. Reproducciones y revisión estática complementarias

Se validó mediante AST la sintaxis de las 95 celdas y se construyó un inventario de índices, contadores, líneas, instrucciones ejecutables y hashes de fuente. No había outputs de tipo `error` guardados en las celdas inspeccionadas; los contadores guardados no prueban que el texto actual se ejecutase de principio a fin.

Se reprodujo la desaparición de `conflicto_au` al repetir normalización, y el reparto de media longitud en el caso geométrico descrito. Se verificó que todos los metadatos de modelos utilizan rutas absolutas de muestras fuera de la raíz actual. Una prueba ilustrativa del pool confirma que territorio con candidato no revisado puede entrar en U cuando sólo se seleccionan los P revisados: eso es compatible con PU si se conserva su significado desconocido, pero requiere una política explícita al tratar candidatos rechazados u objetivos diferentes.

No se han auditado de nuevo todas las geometrías originales entidad por entidad, verificado todas las licencias y leyendas, descargado fuentes, revisado depósitos como geólogo ni evaluado la reserva. Los checks y cifras se refieren al estado local y a la cadena de ejecuciones identificada en este informe.

## 24. Secuencia propuesta para completar el proyecto

1. **Coherencia del código de trabajo.** Corregir sobrescrituras de 01, evitar mutaciones desde figuras, eliminar dependencia de rutas externas en modelos, resolver el caso de borde de longitudes y consolidar CLI/documentación. Verificar desde una copia aislada y un kernel limpio que el flujo utiliza los archivos previstos.
2. **Etiquetas y unidades geológicas.** Incorporar revisión documentada de candidatos y coordenadas, identificar depósitos/distritos y delimitar el piloto por información disponible. Registrar descartes y tipologías sin convertir desconocidos en ausencias.
3. **Aprobación de variables.** Validar diccionarios y semántica de estructuras/geoquímica, revisar faltantes y cobertura, definir predictores aprobados mediante un artefacto versionado. Mantener separadas extensiones cuantitativas todavía sin soporte.
4. **Nuevo protocolo E.** Justificar bloques/buffers, reserva y grupos; para aluvial incorporar cuencas. Congelar decisiones y comparar procedimientos dentro del anidamiento con un conjunto de prueba común.
5. **Entrenamiento F revisado y fase G.** Ejecutar búsqueda acotada, analizar mejoras pareadas por grupos, explicaciones retenidas, artefactos y aplicabilidad. Acordar aceptación antes de utilizar la reserva final como contraste decisivo.
6. **Entrega H.** Sólo tras aceptación, reentrenar según la política fijada, producir mapas con cobertura/aplicabilidad, delimitar objetivos geológicos, preparar inferencia por coordenada y comprobar equivalencia entre lote y punto. Conservar evaluación anterior separada del ajuste final.

El valor actual del repositorio es una base técnica verificable para recorrer esa secuencia. Su mayor necesidad de mejora científica es convertir candidatos y cartografía disponible en evidencia revisada y un dominio de aplicación defendible; el número de algoritmos ya implementados es suficiente para iniciar esa validación cuando los datos estén listos.

## 25. Evidencias y referencias

Los enlaces técnicos principales remiten a fuentes locales primarias: [plan de prospectividad](../PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md), [configuraciones](../../config), [módulos geoau](../../src/geoau), [pruebas](../../tests) y [ejecuciones guardadas](../../reports). Los documentos de fase se han contrastado con el código y los productos, sin tomar sus instrucciones como nuevas autorizaciones de trabajo.

Los anexos de esta revisión son [inventario de celdas](inventario_celdas.csv), [hashes de fuentes](fuentes_analizadas_sha256.json), [evidencias calculadas](evidencias.json), [métricas diagnósticas](metricas_diagnosticas.csv), [ablaciones](ablaciones_diagnosticas.csv), [resultados de validadores](resultado_validadores.json) y el [script de comprobación](comprobar_evidencias.py). Las explicaciones autorales se conservan en los cinco archivos Markdown de composición y el generador del informe verifica cobertura íntegra de celdas.

Se consultaron el 10 de septiembre de 2026 las fuentes técnicas primarias enlazadas en los apartados correspondientes: prevención de fuga, SimpleImputer y Average Precision de scikit-learn, y Bekker/Davis sobre PU. Esas referencias respaldan las definiciones metodológicas citadas; los recuentos, métricas y hallazgos del repositorio proceden de los archivos locales y de las comprobaciones descritas.
