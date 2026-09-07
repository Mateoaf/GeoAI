"""Generador del cuaderno 01; el código de procesamiento reside en geoau.labels."""
from pathlib import Path
from textwrap import dedent
import nbformat as nbf

root = Path(__file__).resolve().parents[1]
cells = []
def md(s): cells.append(nbf.v4.new_markdown_cell(dedent(s).strip()))
def code(s): cells.append(nbf.v4.new_code_cell(dedent(s).strip()))

md('''
# 01 · Indicios: limpieza y definición de etiquetas

Implementa los pasos **07–12 de la fase B** y utiliza las fuentes, configuración y
hashes guardados por `00_configuracion_y_fuentes`. No depende de variables de su kernel.
Usa el mismo entorno `.venv-fase-a`; no requiere instalar nuevas librerías.

**Entregables:** conciliación por código, atributos normalizados conservando originales,
control geográfico, cuarentena, candidatos Au, grupos de proximidad, cobertura puntual,
análisis de representatividad y plantilla para incorporar revisión geológica.

No se considera ausencia de oro un registro de otro mineral. Una coincidencia de
coordenadas o proximidad no acredita un mismo depósito. No se presenta una propuesta
de tipología como interpretación genética validada. No se crea aún la rejilla, ni se
construyen negativos, ni se entrena un modelo.

Ejecuta **todas las celdas en orden**. La verificación de hashes lee los archivos de
fase A, y puede tardar. Los resultados de cada ejecución se guardan en un directorio nuevo.
''')
md('''
## 1. Entorno y configuración

`config/labels.yaml` contiene los umbrales y las fuentes opcionales. Con `phase_a_run: null`
se selecciona la última fase A satisfactoria con hashes. Puedes fijar una ruta relativa
como `reports/fase_a/20260906T142956_752136Z` para reproducir una ejecución concreta.
Si los datos han cambiado desde ese manifiesto, la carga se detiene: ejecuta de nuevo 00.
''')
code('''
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
''')
code('''
A_RUN, MANIFEST_A, CONFIG_A, originales = load_phase_a(ROOT, CONFIG)
canonical_name = CONFIG_A["canonical_candidates"]["indicios"]
CONFIG["source_sha256"] = next(r["sha256"] for r in MANIFEST_A["sources"] if r["path"] == canonical_name)
print("Fase A utilizada:", A_RUN)
display(pd.DataFrame([{"fuente": k, "filas": len(v), "columnas": len(v.columns)} for k,v in originales.items()]))
''')
md('''
## 2. Conciliar GPKG, CSV y Excel — paso 07

Se comparan conjuntos de atributos por `Codigo_indicio`, conservando multiplicidades.
No se hace una unión fila a fila ni un cruce muchos-a-muchos. `ESRI_OID` no se usa como
clave común entre versiones. Las diferencias X/Y son **textuales**, no certifican
desplazamiento: el CRS de esos campos aún no está documentado.

La base GPKG sigue siendo candidata canónica por la decisión de fase A. Las diferencias
de Au entre copias generan una lista de revisión, no borrados ni nuevas presencias automáticas.
''')
code('''
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
''')
md('''
## 3. Normalizar sin perder originales — paso 08

Los campos originales pasan a `*_raw`; se conservan WKT, CRS y hash de la copia.
Los identificadores de revisión incluyen el hash del archivo: una revisión de otra
versión no se aplica accidentalmente a una fila distinta.

La detección de oro utiliza tokens exactos `oro`/`au`, con normalización de texto y
separación por comas, punto y coma o barra vertical. No encuentra falsos positivos
en «fluorita», «bauxita» o «aurífero» por coincidencia parcial. El orden de sustancias
no permite identificar por sí solo Au principal o acompañante.
''')
code('''
normalizados = normalize_indicios(originales["gpkg"], CONFIG)
flags = conciliacion.set_index("Codigo_indicio")["conflicto_au"]
normalizados["conflicto_au"] = normalizados.Codigo_indicio.map(flags).fillna(False).astype(bool)
assert len(normalizados) == len(originales["gpkg"])
assert normalizados.record_id.is_unique
display(normalizados[["Codigo_indicio_raw", "Codigo_indicio", "Sustancia_raw", "sustancias_tokens",
                       "au_observado", "label_observada", "Morfologia", "tipo_au_propuesto"]].head(12))
display(normalizados.groupby(["au_observado","tipo_au_propuesto"], dropna=False).size().to_frame("registros"))
''')
md('''
## 4. Incorporar revisiones documentadas, si existen

La primera ejecución no necesita un fichero de revisión. Se generará una plantilla.
Para usar decisiones posteriores, copia esa plantilla a `data/review/`, rellénala y
configura `review_file`. Conserva `record_id` y todas las columnas.

Valores admitidos: presencia `confirmada/rechazada/pendiente`; geometría
`validada/rechazada/pendiente`; tipología `roca/aluvial/mixto/desconocido`.
Cada decisión necesita **revisor, fecha ISO, evidencia y motivo**. Una corrección de
posición requiere ambas coordenadas en EPSG:4326 y geometría validada. El código no
inventa coordenadas ni aplica cambios de huso por conjetura. Los originales permanecen.
''')
code('''
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
''')
md('''
## 5. Geometría, X/Y, territorio y cuarentena — paso 09

Se comprueban punto, validez, finitud, rango geográfico y ventanas amplias de plausibilidad.
**Las ventanas no son España:** incluyen mar y países vecinos. Sin máscara oficial,
`territorio_estado=pendiente_mascara`; sin límites administrativos no se certifica provincia
ni municipio. La posición no se cambia para hacerla coincidir con su provincia declarada.

X/Y solo se comparan con la geometría bajo la hipótesis explícita de que sean longitud/latitud.
Los valores fuera de ese rango se marcan como CRS tabular desconocido. Se conservan como
incidencia sin invalidar automáticamente una geometría oficial plausible.

Puedes proporcionar una máscara y límites locales en `labels.yaml`. Los nombres
administrativos se comparan con normalización de tildes y mayúsculas; diferencias como
«A Coruña»/«Coruña» seguirán requiriendo diccionario o revisión, nunca corrección silenciosa.
''')
code('''
mask_path, admin_path = optional_input("territory_mask"), optional_input("admin_boundaries")
mascara = read_vector(mask_path, layer=CONFIG["territory_layer"], max_features=None, allow_full=True) if mask_path else None
limites = read_vector(admin_path, layer=CONFIG["admin_layer"], max_features=None, allow_full=True) if admin_path else None
qc = geometry_qc(normalizados, CONFIG, mask=mascara, admin=limites)
display(qc.groupby(["geo_cuarentena", "motivo_geo"],dropna=False).size().to_frame("registros"))
display(qc.xy_estado.value_counts().to_frame("registros"))
display(qc.loc[qc.geo_cuarentena, ["record_id","Codigo_indicio","Nombre_mina","Provincia","lon","lat","motivo_geo"]])
print("No se han inferido coordenadas para registros en cuarentena.")
''')
md('''
## 6. Coincidencias y sensibilidad de agrupación — paso 10

La tabla normalizada conserva todas las filas. Se marcan códigos repetidos y se agrupan
posiciones exactas; los representantes de posición se muestran aparte sin borrar evidencias.
Las componentes conexas a 250/500/1.000 m se obtienen con distancia geodésica WGS84,
no en grados ni Web Mercator. Las cadenas de vecinos pueden extenderse más que el radio.

`proximity_group_*` es un grupo de candidatos para revisión/prevención de fuga, no
`deposit_id`. Los IDs de depósito y distrito únicamente se incorporan mediante revisión.
Las agrupaciones se recalculan cuando se corrigen coordenadas; no equivalen a folds.
''')
code('''
# Una confirmación documentada puede incorporar un registro sin Au en el texto original.
candidatos = qc[qc.au_observado | qc.estado_presencia.eq("confirmada")].copy()
candidatos, pares, sensibilidad = group_candidates(candidatos, CONFIG["cluster_radii_m"])
display(sensibilidad)
coincidentes = candidatos[candidatos.position_id.notna() & candidatos.position_id.duplicated(keep=False)]
display(coincidentes[["Codigo_indicio","Nombre_mina","Morfologia","position_id","lon","lat"]])
representantes_posicion = candidatos[candidatos.position_id.notna()].sort_values("record_id").drop_duplicates("position_id")
print("Registros candidatos:",len(candidatos), "Posiciones distintas localizables:", len(representantes_posicion))
display(pares.head(15))
''')
md('''
## 7. Etiquetas candidatas y revisadas — paso 11

`label_observada=P` significa Au citado en el inventario; `U` significa sin evidencia
de Au registrada y **no es una ausencia**. Filoniana propone roca sin inferir génesis
orogénica; aluvionar propone aluvial. El resto queda desconocido hasta revisión.

El conjunto revisado exige confirmación documentada de presencia y geometría, no estar
en cuarentena y código no ambiguo. Los subtipos revisados requieren además una decisión
explícita de tipología. Una tipología mixta no se convierte automáticamente en positivo
de ambos submodelos. Ninguna salida se presenta como matriz de entrenamiento lista.
''')
code('''
etiquetas = define_labels(candidatos)
display(etiquetas.groupby(["tipo_au_propuesto","tipologia_estado"],dropna=False).size().to_frame("registros"))
display(etiquetas[["elegible_general_revisada","elegible_roca_revisada","elegible_aluvial_revisada"]].sum().to_frame("positivos revisados"))
assert not etiquetas.label_au_final.eq("0").any()
assert not etiquetas.loc[etiquetas.geo_cuarentena,"elegible_general_revisada"].any()
''')
md('''
## 8. Cobertura de fuentes en los indicios — paso 12

La disponibilidad se comprueba en la banda 1 de cada capa geoquímica y del MDT, con
su CRS y máscara. Clase cero es válida. Un punto sin geoquímica no se borra de las
etiquetas. Esta comprobación no certifica todas las bandas ni la cobertura territorial.
No se usa la capa geoquímica para decidir si el indicio es positivo.
''')
code('''
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
''')
md('''
## 9. Representatividad y sesgo espacial

El mapa presenta posiciones y tipos propuestos; las gráficas cuentan registros,
no descubrimientos independientes. La concentración en una provincia puede reflejar
tanto geología como investigación histórica. `Zona_Geode` del indicio es un atributo
declarado, no un cruce con dominios geológicos verificados.

Se dejan pendientes la asignación revisada de distritos y la elección de reservas.
No se usan provincias como folds ni se crea una rejilla provisional para contar celdas.
''')
code('''
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
''')
md('''
## 10. Exportación y control de integridad

Se guardan CSV, GeoPackage y configuración en una carpeta nueva. Si no hay positivos
revisados, no se crea un GPKG revisado vacío que pueda confundirse con un resultado
terminado. La plantilla se genera sin decisiones inventadas y nunca se sobreescribe
el fichero de revisión que hayas aportado.

La ejecución automática puede finalizar correctamente mientras la fase B científica
sigue abierta: máscara, revisión de etiquetas, depósitos y distritos requieren trabajo
posterior. `control_cierre.json` distingue ambos estados.
''')
code('''
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
''')
md('''
## 11. Cómo continuar la revisión

1. Revisar `reconciliacion_indicios.csv`, `au_ausentes_de_base_canonica.csv` y cuarentenas.
2. Copiar `plantilla_revision.csv` a una carpeta local de revisión y rellenar solo
   decisiones respaldadas por evidencia. No modificar IDs; conservar columnas.
3. Para un mismo depósito confirmado, asignar el mismo `deposit_id` a sus registros.
   `district_id` debe proceder de una delimitación revisada, no del algoritmo de proximidad.
4. Configurar la ruta en `config/labels.yaml` y volver a ejecutar el cuaderno.
5. Recuperar máscara/límites locales y completar geología antes de fijar la validación.

No se puede certificar desde BDMIN y proximidad por sí solos cuántos depósitos
independientes existen. El cuaderno deja esa incertidumbre visible y preserva todas
las relaciones para el diseño espacial posterior.

Referencia técnica: las distancias se calculan con
[PyProj Geod](https://pyproj4.github.io/pyproj/stable/api/geod.html);
el contraste opcional con polígonos usa
[GeoPandas sjoin](https://geopandas.org/en/stable/docs/reference/api/geopandas.sjoin.html).
''')
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python (GeoAu · fase A/B)', 'language':'python', 'name':'geoau-fase-a'},
    'language_info': {'name':'python'},
})
nbf.validate(nb)
path = root / 'notebooks/01_indicios_limpieza_etiquetas.ipynb'
nbf.write(nb,path)
print(path)
