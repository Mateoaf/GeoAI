"""Construye el notebook didáctico 00. Ejecutar solo para regenerar su contenido."""
from pathlib import Path
from textwrap import dedent
import nbformat as nbf

root = Path(__file__).resolve().parents[1]
cells = []
def md(text): cells.append(nbf.v4.new_markdown_cell(dedent(text).strip()))
def code(text): cells.append(nbf.v4.new_code_cell(dedent(text).strip()))

md('''
# 00 · Configuración y fuentes locales

Este cuaderno implementa la **fase A** del plan: configuración, entorno, manifiesto,
lectores, catálogo y pendientes. Su objetivo es dejar las fuentes accesibles y trazables
para `01_indicios_limpieza_etiquetas`.

Trabajamos exclusivamente con los archivos descargados. Los servicios de QGIS se
registran como referencias; **no se realiza ninguna descarga de datos**. Las fuentes se
abren en lectura y los informes se escriben en `reports/fase_a/<ejecución>/`.

Una capa cargada no significa una capa limpia: conservamos CRS, atributos, máscaras y
valores originales. No se aplica todavía reproyección, imputación, deduplicación,
construcción del target ni entrenamiento de Random Forest.

**Cómo ejecutarlo en VS Code:** selecciona el intérprete
`Proyecto Con Luis/.venv-fase-a/Scripts/python.exe` y pulsa **Ejecutar todo**.
En otra máquina, desde la raíz del proyecto:

```powershell
python -m venv .venv-fase-a
.\\.venv-fase-a\\Scripts\\python.exe -m pip install -r requirements-fase-a.txt
```

El manifiesto SHA-256 lee todos los bytes de las fuentes: la primera ejecución puede
tardar varios minutos. No se cargan simultáneamente todas las geometrías en RAM.
''')
md('''
## 1. Localizar el proyecto y verificar el entorno

La raíz se detecta desde el workspace, la carpeta del proyecto o `notebooks/`.
Si abres Jupyter desde otra ubicación, indica `PROJECT_ROOT_OVERRIDE`. No hay rutas
personales incrustadas ni instalaciones automáticas dentro del cuaderno.
''')
code('''
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
''')
md('''
## 2. Especificación y decisiones pendientes

La configuración propone 1 km y EPSG:25830 para el diseño peninsular futuro. No
reproyecta capas ni declara una cobertura nacional validada. El piloto queda pendiente.
El paso 06 del plan se adapta a este encargo local: **registramos qué falta recuperar**.
Los datos adicionales se incorporarán cuando estén disponibles localmente.
''')
code('''
display(pd.json_normalize({"scope": CONFIG["scope"], "model_design": CONFIG["model_design"]}).T)
paths = discover_sources(ROOT, CONFIG)
print(f"{len(paths)} archivos locales; {sum(p.stat().st_size for p in paths)/1e9:.2f} GB.")
display(pd.Series([p.suffix.lower() for p in paths]).value_counts().rename_axis("formato").to_frame("archivos"))
''')
md('''
## 3. Inventariar, calcular hashes e inspeccionar

Se inspeccionan los archivos fuente de la raíz y la carpeta del shapefile. Se excluyen
entornos, notebooks, informes generados y código: no son nuevas observaciones GIS.
Se cuentan registros por bloques en CSV y mediante SQLite en GPKG. La muestra de
atributos conserva nombres y valores; la validez de geometrías completas sigue pendiente.

SHA-256 identifica exactamente la copia local. La fecha del archivo no se presenta
como fecha de descarga y una licencia desconocida queda sin verificar.
''')
code('''
# Lee aproximadamente el volumen total de las fuentes para el hash.
# Para una exploración rápida puedes poner False, pero el manifiesto no quedará congelado por hash.
CONFIG["inspection"]["compute_sha256"] = True
registros = inventory(ROOT, CONFIG)
catalogo = catalog_frame(registros)
display(catalogo[["path", "role", "status", "row_count", "bytes"]])
print("Estado de lectura:")
display(catalogo.groupby("status", dropna=False).size().to_frame("archivos"))
''')
md('''
## 4. Fuentes canónicas, archivos vacíos y problemas de lectura

Los alias señalan fuentes **candidatas**, no certificados de calidad. El GPKG de indicios
será la base de trabajo; Excel y CSV se conservan separados para conciliar diferencias.
`contactos_geode` apunta al nombre local real `contactos-002.gpkg`.
''')
code('''
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
''')
md('''
## 5. Cargar los indicios y las tablas de contraste

Aquí sí cargamos las tres fuentes completas, por su tamaño reducido. Los campos
tabulares se leen como texto para conservar códigos y ceros iniciales. No se infieren
tipos químicos ni se convierte `X/Y` en geometría: ese saneamiento pertenece a fase B.

No se concatenan las tres tablas. Los recuentos se calculan sobre los archivos actuales,
no se copian del informe de auditoría.
''')
code('''
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
''')
md('''
## 6. Cargar vectores canónicos con límites de memoria

Litología y edades se cargan completas. Recintos, contactos, fallas, pliegues y red
hidrográfica se muestran con lectura acotada. El catálogo permite acceder a todas las
capas internas; no se omiten los GPKG que no son canónicos.

Las capas con curvas se previsualizan como atributos. La prueba geoespacial siguiente
autoriza su conversión únicamente para comprobar compatibilidad de lectura.
''')
code('''
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
''')
md('''
## 7. Pruebas geoespaciales del entorno

La conversión temporal de coordenadas comprueba la instalación; no reemplaza las
coordenadas originales. Las curvas leídas por GDAL pueden perder M o ser linealizadas:
la advertencia se conserva y el resultado no se usa como capa limpia.

Los filtros espaciales exigen `bbox_crs`, porque las capas locales usan distintos CRS.
''')
code('''
from pyproj import Transformer

tr = Transformer.from_crs("EPSG:4326", "EPSG:25830", always_xy=True)
easting, northing = tr.transform(-3.0, 40.0)
assert abs(easting - 500000) < 1
assert 4_400_000 < northing < 4_500_000

curvas_preview = read_vector(fuentes["contactos_geode"], max_features=5,
                             allow_curve_conversion=True)
print("CRS nativo de curvas:", curvas_preview.crs)
print("Geometrías devueltas por GDAL:", curvas_preview.geom_type.unique())
assert len(curvas_preview) > 0 and curvas_preview.crs is not None

# Recorte de demostración; NO fija el piloto del proyecto.
indicios_recorte = read_vector(fuentes["indicios"], bbox=(-7.5, 42.0, -5.0, 43.5),
                               bbox_crs="EPSG:4326", max_features=100)
display(indicios_recorte.head())
''')
md('''
## 8. Registrar todos los CSV y Excel locales

Los maestros enriquecidos son versiones derivadas de los indicios, no nuevas muestras.
La colección `muestras_tablas` permite inspeccionarlos sin combinarlos.
Para trabajar con un CSV grande, `iter_csv` devuelve bloques y evita una carga completa.
''')
code('''
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
''')
md('''
## 9. Abrir los rásteres por bandas y ventanas

`rasters` guarda rutas locales, no archivos permanentemente abiertos. Los lectores
cierran cada dataset al terminar. La banda 1 de geoquímica contiene **clases**;
las bandas de valor medio/mínimo/máximo representan intervalos cartográficos.
Las clases cero se conservan. Las máscaras distinguen NoData de valores válidos.

Una vista reducida sirve para inspección visual, no para medir cobertura o entrenar.
''')
code('''
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
''')
code('''
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
''')
md('''
## 10. Shapefile, respaldos y referencias QGIS

El shapefile se lee con sus componentes. El ZIP se inventaría sin extraerlo.
Los servicios remotos del QGZ se listan sin conectarse a ellos; una URL no se declara
disponible ni se interpreta como dato local. Un recuento igual entre SHP y GPKG no
demuestra equivalencia de geometrías: la conciliación espacial sigue pendiente.
''')
code('''
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
''')
md('''
## 11. Guardar manifiesto, configuración, entorno y pendientes

Cada ejecución crea un directorio nuevo. `manifest.json` guarda los hashes, capas,
bandas, muestras y problemas; `catalogo.csv` permite revisar el resultado en Excel.
`environment.freeze.txt` registra las versiones realmente instaladas, incluidas las
dependencias transitivas; no promete compatibilidad con otro sistema operativo.

El manifiesto registra tanto archivos canónicos como derivados y componentes del SHP.
Sus hashes permiten detectar cambios, pero no prueban autenticidad del organismo productor.
''')
code('''
RUN_DIR = write_reports(ROOT, CONFIG, registros)
write_json(RUN_DIR / "resumen_indicios.json", resumen_indicios.to_dict("records"))
bandas.to_csv(RUN_DIR / "bandas_raster.csv", index=False, encoding="utf-8-sig")
canonicas.to_csv(RUN_DIR / "fuentes_canonicas.csv", index=False, encoding="utf-8-sig")
fig.savefig(RUN_DIR / "vista_previa_rasters.png", dpi=130, bbox_inches="tight")
print("Resultados:", RUN_DIR)
display(pd.read_json(RUN_DIR / "pendientes.json"))
''')
md('''
## 12. Control de cierre y contrato para el siguiente notebook

Se vuelven a verificar tamaño, fecha y SHA-256 de las fuentes: la fase A no debe
modificarlas. Un error de lectura queda documentado y detiene el cierre. Los GPKG
vacíos y fuentes ausentes son carencias de datos, no se ocultan ni se consideran
pruebas fallidas del lector.

El siguiente notebook consumirá el manifiesto y la configuración, volverá a abrir
las rutas canónicas y comenzará la conciliación y limpieza. No necesita que este
kernel permanezca abierto ni que se serialicen objetos Python inseguros.
''')
code('''
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
''')
md('''
**Notas de diseño y referencias:**

- Los límites de lectura, filtros por `bbox` y lectura de atributos usan la API
  documentada de [Pyogrio](https://pyogrio.readthedocs.io/en/latest/introduction.html).
- Las ventanas preservan la transformada del recorte siguiendo
  [Rasterio](https://rasterio.readthedocs.io/en/stable/topics/windowed-rw.html).
- No se calculan features predictoras, métricas ML ni una cobertura española certificada
  a partir de estas vistas. Esas decisiones permanecen en las fases siguientes del plan.
''')
nb = nbf.v4.new_notebook(cells=cells, metadata={
    'kernelspec': {'display_name': 'Python (GeoAu · fase A)', 'language': 'python', 'name': 'geoau-fase-a'},
    'language_info': {'name': 'python'},
})
dest = root / 'notebooks/00_configuracion_y_fuentes.ipynb'
dest.parent.mkdir(exist_ok=True)
nbf.validate(nb)
nbf.write(nb, dest)
print(dest)
