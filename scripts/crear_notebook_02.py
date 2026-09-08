"""Construye el cuaderno explicativo de fase C; ejecutar sobrescribe sus salidas."""
from pathlib import Path
import nbformat as nbf

root = Path(__file__).resolve().parents[1]
cells = []


def md(text):
    cells.append(nbf.v4.new_markdown_cell(text.strip()))


def code(text):
    cells.append(nbf.v4.new_code_cell(text.strip()))


md('''
# 02 · Rejilla, armonización y cobertura territorial

Implementa los pasos **13–17 de la fase C** del plan. Continúa los cuadernos 00 y 01
desde archivos persistidos, sin depender de sus kernels. El procesamiento reutilizable
está en `src/geoau/territory.py`; las decisiones reproducibles, en `config/grid.yaml`.

**Entregables:** rejilla territorial de 1 km con área terrestre, diccionario de soportes,
ocho familias vectoriales saneadas, diez rásteres agregados, `coverage.gpkg`, mapa,
diagnósticos por bloques de 50 km y correspondencia indicio–celda.

Ejecuta todo con `.venv-fase-a/Scripts/python.exe`. El saneamiento completo de las
capas millonarias tarda y escribe varios GB por ejecución. Cada ejecución tiene una
carpeta nueva; los originales y las fases anteriores se conservan.

Máscara candidata: GISCO Countries 2024, escala 1:1.000.000.
© EuroGeographics para los límites administrativos. Fuente consultada el 7/9/2026.
Sus condiciones específicas permiten uso no comercial y exigen atribución; no se
presupone autorización comercial. Véanse las referencias al final.
''')
md('''
## 1. Lectura crítica del plan y contrato entre fases

La fase A acredita fuentes locales y hashes. La fase B seleccionada terminó su ejecución,
pero mantiene pendientes la revisión de presencia, depósitos, distritos y territorio.
Los candidatos Au no se convierten aquí en positivos revisados. Las numerosas filas
de maestros enriquecidos tampoco se añaden como muestras nuevas.

| Decisión | Aplicación en C | Límite que conserva |
|---|---|---|
| Ámbito | Componente continental principal de España | Islas y enclaves se inventarían fuera de V1 |
| Frontera | Máscara independiente de los TIFF | Generalización cartográfica; revisión costera pendiente |
| Rejilla | 1 km ETRS89/UTM 30N, origen fijo | Área proyectada; se cuantifica distorsión |
| Etiquetas | Relación registro–celda, sin multiplicar celdas | No se deducen depósitos ni ausencias |
| Geoquímica | Banda de clases, moda y proporciones alternativas | No son análisis continuos; validación RGB/leyenda en D |
| Estructuras | Geometría lineal 2D, códigos y fuente conservados | Limpieza semántica y deduplicación entre fuentes en D |
| Cobertura | Disponibilidad por superficie y bloques | Sin huellas de levantamiento no se acredita cobertura de líneas |

**La finalización informática no cierra automáticamente el hito H2 científico.**
Las limitaciones restantes quedan en `control_cierre.json`; no se emite favorabilidad.
''')
code('''
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
''')
md('''
## 2. Recuperar las entradas exactas de A y B

Se fija explícitamente la ejecución de B en configuración. Se sigue su enlace a A y
se comprueba el hash de ese manifiesto, las 93 fuentes y las entradas adicionales de B.
No se elige una fase A diferente por ser más reciente. Las salidas de B no tenían un
manifiesto de hashes propio: C registra sus hashes al abrirlas, sin fingir una firma
histórica inexistente. La máscara nueva tiene procedencia y SHA-256 independientes.
''')
code('''
RUN_DIR, FUENTES, MANIFEST_A, ENTRADAS_C, indicios = start_run(ROOT, CONFIG)
print("Resultados:", RUN_DIR)
print("Candidatos de B:", len(indicios))
print("Positivos revisados de B:", int(indicios.elegible_general_revisada.sum()))
display(indicios[["record_id", "Codigo_indicio", "Provincia", "tipo_au_propuesto",
                  "elegible_general_revisada"]].head())
''')
md('''
## 3. Máscara y ámbitos — paso 13

Se selecciona la componente mayor por área en EPSG:3035, no por grados cuadrados ni
por extensión de la geoquímica. Esa componente define la península continental;
las islas costeras separadas también quedan fuera de esta primera versión. Todas
las componentes españolas se guardan en `coverage.gpkg/ambitos_espana` con su estado.

Es una máscara regional **candidata**, no una delimitación topográfica fina. No permite
certificar por sí sola costa exacta, aguas interiores ni localización administrativa.
No se mueven indicios para hacerlos coincidir con ella.
''')
code('''
mascara = load_mask(ROOT, CONFIG, RUN_DIR)
display(pd.read_csv(RUN_DIR / "ambitos_espana.csv").groupby("ambito").agg(
    componentes=("ambito", "size"), area_km2=("area_km2_epsg3035", "sum")))
print("Área candidata en UTM30, km²:", mascara.area / 1e6)
''')
md('''
## 4. Rejilla estable y política costera — paso 13

La caja fija tiene **1.100 × 910 celdas de 1 km**, pero solo se guardan filas con
intersección terrestre positiva. `cell_id` combina versión, fila y columna; no depende
del número de indicios, de la cobertura ni del orden de lectura.

El área se calcula intersectando la máscara con el soporte fuente de 500 m y sumando
bloques 2×2. Los píxeles interiores tienen su área completa; en el borde se usa overlay
geométrico exacto. Se comprueba que la suma conserva el área de la máscara.

Se conservan también las celdas con poca tierra. Para el diagnóstico de elegibilidad
se exige inicialmente al menos **50 % terrestre**, umbral configurable fijado antes
de modelizar. Los centros siguen siendo los centros de los cuadrados, incluso si
caen en mar: no se cambian solo para las presencias. La inferencia futura usará ese
mismo soporte. El área efectiva siempre será terrestre, no el número de cuadrados.
''')
code('''
area_terrestre_500m = land_areas(mascara, SPEC["native_shape"], SPEC["native_transform"])
grid = make_grid(area_terrestre_500m, SPEC, RUN_DIR)
display(grid.head())
display(grid[["land_area_m2", "land_fraction"]].describe())
print("Celdas terrestres:", len(grid), "de", SPEC["width"] * SPEC["height"])
display(pd.read_csv(RUN_DIR / "distorsion_crs.csv")[["linear_scale_error_pct", "area_scale_error_pct"]].agg(["min", "max"]))
''')
md('''
`grid_spec.json` contiene transformada GDAL, CRS, origen, extensión y forma. Se guarda
`grid_1km.csv.gz`, reconstruible desde fila/columna, en lugar de cientos de miles de
polígonos repetidos. `coverage.gpkg` contiene geometrías agrupadas de los estados.
Cambiar origen, resolución o ámbito exige una nueva versión de rejilla. El contraste
a 500 m del plan será un experimento posterior, no un segundo modelo creado aquí.
''')
md('''
## 5. Diccionario de extracción — paso 14

El diccionario fija el contrato P/U/inferencia. En las celdas costeras, medias y
proporciones usan el área terrestre válida de cada píxel fuente. La fracción válida
divide área con dato entre área terrestre total, no entre toda la celda incluyendo mar.

Litología/edad se definirán mediante intersecciones y fracciones; las distancias, desde
el centro fijo; las densidades, mediante longitud por superficie en ventanas. En fase C
no se confunde un diagnóstico de cobertura con una variable geológica terminada.
La fórmula y ventana de cada derivado de relieve se deben fijar en D antes de calcularlo.
''')
code('''
diccionario = feature_dictionary(RUN_DIR)
display(diccionario)
''')
md('''
## 6. Agregación de rásteres y máscaras — paso 16

Los nueve TIFF geoquímicos y el MDT deben coincidir exactamente con la rejilla fuente
de 500 m. Si cambia CRS, forma u origen, el proceso se detiene: no disimula un desfase
con remuestreo automático. Lee por ventanas y agrega bloques 2×2 sin desplazar píxeles.

- **Geoquímica:** banda 1, códigos enteros 0–6 u 0–7. Moda ponderada por superficie
  terrestre válida; en empate gana el código menor. Se exportan las proporciones como
  alternativa de representación. No incluir moda y todas las proporciones como
  evidencias independientes sin un experimento justificado.
- **Relieve:** solo elevación, media ponderada; pendiente/TPI/TRI antiguos no se heredan.
- **Ausencia de dato:** `-9999` en el producto; fracción válida 0 dentro de tierra sin
  datos. Fuera de tierra, fracción NoData. **Clase 0 es una clase válida**.

Se conservan las carencias; no se interpolan códigos, ni se convierten intervalos en
mediciones. Revisar clasificación desde RGB y unidades pertenece al paso 21 de D.
''')
code('''
fracciones_raster = align_rasters(ROOT, FUENTES, area_terrestre_500m, SPEC, RUN_DIR)
display(pd.read_csv(RUN_DIR / "raster_alignment.csv"))
''')
md('''
## 7. Saneamiento vectorial por lotes — paso 15

Se usa el índice espacial del GeoPackage y se pagina por FID ordenado, comprobando
el recuento contra una consulta independiente. Se leen entidades del ámbito más un
margen de **20 km**, suficiente para las ventanas iniciales de hasta 10 km. Se
conservan las geometrías completas que intersectan el margen para evitar cortar trazas.

Las coordenadas se transforman a EPSG:25830; Z/M no se utilizan. La linealización GDAL
tiene paso angular de 1° y se contrasta con 0,5° en 1.000 entidades de GEODE mediante
Hausdorff en metros. Este contraste es muestral: no certifica todas las curvas ni una
tolerancia métrica global. Las advertencias del lector quedan registradas.

`make_valid` repara geometrías inválidas, conservando códigos y `source_fid`. Se registran
áreas/longitudes antes y después, cambios de tipo y rechazos. Geometrías vacías o de
dimensión inesperada quedan en el registro de incidencias para revisión por FID.
No se sustituyen por geometrías inventadas ni se mezclan GEODE y MAGNA.

La fracción cubierta por polígonos es una **estimación por centros de 500 m** ponderada
por tierra. Los solapes cuentan multiplicidad de entidades; no demuestran duplicación
de contenido. En líneas se guarda presencia de trazas, que **no acredita cobertura
del levantamiento**. Clasificar fallas/contactos, revisar discontinuidades por hoja y
resolver duplicados entre fuentes sigue pendiente.
''')
code('''
fracciones_vector, control_vectores = harmonize_vectors(ROOT, FUENTES, mascara,
    area_terrestre_500m, SPEC, RUN_DIR)
display(control_vectores.drop(columns=["reader_warnings", "z_m_policy", "semantic_status"]))
''')
md('''
## 8. Cobertura, relación con indicios y decisiones — paso 17

Se calcula cobertura de cada familia por superficie y por bloques de diagnóstico de
50 km; estos bloques no son distritos ni folds. La provincia del indicio sigue siendo
un atributo declarado. La cobertura poligonal mantiene su precisión estimada de 500 m.

El umbral inicial es **95 % del área terrestre válida por familia**. Los estados son:

| Estado | Regla | Interpretación |
|---|---|---|
| Costera de baja fracción | Tierra <50 % | Conservada; fuera de elegibilidad inicial |
| Soporte básico candidato | Litología + edad + elevación + nueve elementos ≥95 % | Disponibilidad; pendiente estructuras y validez semántica |
| Candidato reducido | Geología y elevación ≥95 %, geoquímica incompleta | Comparar versión reducida en fases posteriores |
| Soporte insuficiente | No cumple geología/elevación | No emitir predicción |

`prediction_allowed=False` en todos los estados: aquí aún no existe un modelo validado.
No se etiqueta como ausencia un territorio sin dato o sin presencia revisada.

Cada punto pertenece como máximo a una celda con intervalos semiabiertos: en un borde
interior se asigna al este/sur. Los puntos fuera de máscara o en cuarentena se conservan
con motivo, sin asignación automática. Varios registros comparten celda sin multiplicar
filas de la rejilla; no se deduce que formen un depósito independiente.
''')
code('''
grid_cobertura, cobertura_ambitos, decisiones, indicios_celda, estados = coverage_products(
    ROOT, grid, {**fracciones_raster, **fracciones_vector}, indicios, mascara, SPEC, RUN_DIR)
display(decisiones)
display(cobertura_ambitos[cobertura_ambitos.ambito.eq("peninsula")])
display(indicios_celda.estado_territorial.value_counts().to_frame("registros"))
''')
md('''
## 9. Los indicios Au sin geoquímica: revisión explícita

Se repite el muestreo puntual de la fase B y se contrasta por `record_id` y fuente.
Se muestran todos los casos sin dato, sin imponer que el recuento siga siendo cinco
si cambian las entradas. La cobertura de su celda puede mejorar por otros píxeles;
eso no crea una observación en el punto original. La causa geológica/cartográfica
del hueco exige revisar el RGB y su leyenda, no rellenarlo con cero.
''')
code('''
sin_geoquimica = pd.read_csv(RUN_DIR / "revision_au_sin_geoquimica.csv", dtype={"Codigo_indicio": str})
print("Registros distintos sin geoquímica puntual:", sin_geoquimica.record_id.nunique())
display(sin_geoquimica[["record_id", "fuente", "estado", "cell_id", "coverage_decision", "decision"]].head(50))
contraste = pd.read_csv(RUN_DIR / "contraste_cobertura_puntual_B_C.csv")
display(contraste.groupby(["estado_B", "estado_C", "_merge"], dropna=False).size().to_frame("muestreos"))
''')
md('''
## 10. Mapa de cobertura y distribución de carencias

El mapa representa soporte de datos, no favorabilidad. Los puntos se dibujan como
candidatos del inventario, sin afirmar revisión geológica. La tabla muestra los bloques
con menor cobertura de Au; permite localizar carencias que una media peninsular oculta.
''')
code('''
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
''')
md('''
## 11. Controles de cierre y trazabilidad

Los controles ejecutados verifican conservación de área, IDs únicos, relación muchos
a uno sin duplicación, paginación íntegra, categorías válidas, proporciones que suman
uno y coincidencia de píxel en todos los TIFF escritos. Los hashes se vuelven a
comprobar al finalizar; se sella también cada producto para las fases siguientes.

Las pruebas sintéticas adicionales están en `tests/test_territory.py`: clase cero,
NoData, empate, ponderación terrestre, huecos/islas pequeñas, límite de extensión,
bordes de celda y reparación de geometrías. Se ejecutan junto con las pruebas de A/B.
''')
code('''
assert grid_cobertura.cell_id.is_unique
assert len(indicios_celda) == len(indicios)
assert grid_cobertura.n_candidatos.sum() == indicios_celda.cell_id.notna().sum()
assert not grid_cobertura.prediction_allowed.any()
assert control_vectores.pagination_complete.all()
control = finish_run(ROOT, RUN_DIR, MANIFEST_A, ENTRADAS_C, grid_cobertura, indicios_celda, control_vectores)
display(pd.Series(control, dtype=object).to_frame("resultado"))
print("Resultados conservados en:", RUN_DIR)
''')
md('''
## 12. Qué se entrega a las fases siguientes

- `grid_1km.csv.gz` + `grid_spec.json`: geometría reconstruible, IDs y área terrestre.
- `feature_dictionary.csv`: soporte uniforme de extracción y variables aún pendientes.
- `vectors/*.gpkg`: familias separadas, CRS métrico, geometrías 2D y FID de origen.
- `rasters/*_1km.tif`: clases/proporciones, elevación y máscaras alineadas.
- `coverage.gpkg`: máscara, ámbitos españoles y estados territoriales.
- `coverage_by_cell.csv.gz`, `coverage_by_scope_family.csv`, `coverage_decisions.csv`:
  soporte por celda, familia y bloque, con estados explícitos.
- `indicios_celda_cobertura.csv`: enlace completo con B, sin deducir nuevos positivos.
- Informes geométricos, revisión de Au sin dato, mapa, hashes y control de cierre.

Antes de declarar H2 aceptado: validar la máscara candidata, revisar incidencias
geométricas y cobertura por hoja/dominio, y resolver las huellas de levantamiento.
Antes de modelizar: completar fase D, revisar etiquetas y depósitos, elegir piloto
por evidencia territorial/geológica y fijar particiones. No se elige el piloto por
el porcentaje que resulte más favorable en este cuaderno.

Referencias primarias para las decisiones implementadas:

- [Plan local, fase C](../informes/PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md).
- [GISCO Countries 2024: API de unidades y escalas](https://gisco-services.ec.europa.eu/distribution/v2/countries/countries-2024-units.html).
- [GISCO: atribución y condiciones de límites administrativos](https://ec.europa.eu/eurostat/web/gisco/geodata/administrative-units).
- [GDAL: configuración de linealización de arcos](https://gdal.org/en/stable/user/configoptions.html).
''')

nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python (geoau fase A)', 'language': 'python', 'name': 'python3'},
    'language_info': {'name': 'python', 'version': '3.14.7'}})
nbf.validate(nb)
from actualizar_notebook_02_capas import extend_notebook
nb = extend_notebook(nb)
nbf.write(nb, root / 'notebooks/02_rejilla_armonizacion_cobertura.ipynb')
print('Notebook 02 creado:', len(cells), 'celdas')
