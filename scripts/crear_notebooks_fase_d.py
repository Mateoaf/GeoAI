"""Genera solo notebooks nuevos; nunca sobrescribe cuadernos editados."""
from pathlib import Path
import nbformat as nb

ROOT=Path(__file__).resolve().parents[1]
setup='''from pathlib import Path
import sys
ROOT = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/features.py').exists())
if str(ROOT / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT / 'src'))
import pandas as pd
import matplotlib.pyplot as plt
from geoau import features as fd
'''
items=[
('03_variables_geologia_estructuras',[
('md','''# 03 · Geología y estructuras — fase D

Consume la fase C indicada en `config/features.yaml`. Ejecutar con el entorno `.venv-fase-a` y `requirements-fase-d.txt` instalado.

**Ejecutar la siguiente celda inicia una nueva ejecución D.** Los cuadernos 04–06 recuperan esa ejecución mediante `reports/fase_d/current_run.json`; se muestra su ruta para evitar mezclar productos. Para continuar una ejecución ya iniciada, sustituir `start_run(ROOT)` por `current_run(ROOT)`.

Las fracciones representan unidades cartográficas originales (incluidas mezclas), no porcentajes inventados de cada roca. GEODE es la única fuente estructural de V1. Las densidades son aproximaciones circulares a partir de longitudes por celda; no acreditan cobertura de levantamiento.'''),
('code',setup+'\nRUN = fd.start_run(ROOT)\nprint(RUN)'),
('md','## Unidades y edades\nIntersecciones exactas con la parte terrestre de cada celda. Se disuelve por categoría; los solapes entre categorías y atributos ausentes se auditan. Revisar `dictionaries/litologia.csv` y `edades.csv`.'),
('code',"geology, geology_quality = fd.geology(ROOT, RUN)\ndisplay(geology.head())\ndisplay(geology_quality.describe())"),
('md','## Estructuras\nLas reglas textuales excluyen agua/bordes y separan supuestas. Distancias a trazas hasta 10 km; sin coincidencia se conserva NaN y una bandera auxiliar. Revisar `dictionaries/estructuras.csv`. Las trazas cartografiadas no equivalen a una red completa.'),
('code',"structural, structural_quality = fd.lines(ROOT, RUN)\ndisplay(structural.describe())"),
('code',"display(pd.read_csv(RUN / 'dictionaries/estructuras.csv'))\nprint('Continuar con 04 usando esta ejecución:', RUN)")]),
('04_variables_geoquimicas',[
('md','''# 04 · Geoquímica por clases y control RGB

Se leen las paletas constantes de los scripts históricos mediante AST, sin ejecutarlos. Se exige coincidencia de color con la clase declarada y opacidad completa. Se reconstruye la agregación a 1 km solo para aplicar este control adicional; no se modifican los TIFF de A/C.

La coincidencia con la paleta local **no certifica la leyenda oficial ni el medio/extracción**. Se guardan esas limitaciones. Clase 0 válida; NoData no es cero. No se calculan concentraciones, ratios ni logaritmos. Moda y proporciones son representaciones alternativas.'''),
('code',setup+'\nRUN = fd.current_run(ROOT)\nprint(RUN)'),
('code',"geochemistry, geochemistry_quality = fd.geochemistry(ROOT, RUN)\ndisplay(pd.read_csv(RUN / 'geoquimica_rgb_qc.csv'))"),
('code',"display(geochemistry.head())\ndisplay(geochemistry_quality.describe())"),
('code',"geochemistry.filter(regex='_clase_modal$').hist(figsize=(14, 9), bins=8)\nplt.tight_layout()\nplt.show()")]),
('05_variables_relieve_hidrologia',[
('md','''# 05 · Relieve e hidrografía regional

Pendiente por diferencias centrales a 500 m (centro y cuatro vecinos válidos). TPI = elevación menos media de centros dentro del radio, incluyendo el centro. Rugosidad = desviación estándar poblacional de elevación, **no TRI**. Radios de 1 y 5 km; soporte mínimo 95 %. Sin rellenar huecos ni océano con elevación cero. Después se agregan las derivadas a 1 km por área terrestre válida.

La hidrografía aporta distancia a cauce y densidad aproximada de red. No se infieren terrazas, dirección de flujo ni depósitos aluviales a partir de estas variables. Gravimetría, orientaciones y cuencas quedan como extensiones explícitas; no se convierten localizaciones de campañas en anomalías.'''),
('code',setup+'\nRUN = fd.current_run(ROOT)\nprint(RUN)'),
('code',"terrain, terrain_quality = fd.terrain(ROOT, RUN)\ndisplay(terrain.describe())"),
('code',"hydrology, hydrology_quality = fd.lines(ROOT, RUN, hydro=True)\ndisplay(hydrology.describe())"),
('code',"display(terrain_quality.describe())\nprint('Continuar con 06 para integrar y verificar.')")]),
('06_matriz_variables_control',[
('md','''# 06 · Matriz territorial y controles — final técnico de fase D

Integra exclusivamente por `cell_id`, validando uniones 1:1 y cobertura de todas las celdas. El maestro contiene variables candidatas; geometría reconstruible y calidad están separadas. Los indicios se conservan en una relación auxiliar y se agregan a una fila por celda, sin convertir U en negativos.

No crea particiones, imputaciones ni Random Forest: corresponden a E/F. La lista de variables aprobadas para entrenamiento permanece vacía hasta revisión científica. No usar todas las columnas de calidad/etiquetas como X.'''),
('code',setup+'\nRUN = fd.current_run(ROOT)\nprint(RUN)'),
('code',"X, quality, labels = fd.assemble(ROOT, RUN)\ndisplay(fd.read_json(RUN / 'control_cierre.json'))"),
('code',"display(pd.read_csv(RUN / 'variables_qc.csv').sort_values('missing_fraction', ascending=False).head(25))\ndisplay(labels.estado_etiqueta.value_counts())\ndisplay(fd.read_json(RUN / 'pending_extensions.json'))"),
('md','## Revisión espacial\nEl mapa siguiente muestra una variable, no prospectividad. Revisar costa, huecos y discontinuidades entre hojas. Los bloques diagnósticos heredados de C no son particiones de validación.'),
('code',"plot = quality[['cell_id', 'x_center', 'y_center']].merge(X[['cell_id', 'pendiente_grados']], on='cell_id', validate='one_to_one')\nfig, ax = plt.subplots(figsize=(11, 8))\nm = ax.scatter(plot.x_center, plot.y_center, c=plot.pendiente_grados, s=1, cmap='terrain', rasterized=True)\nax.set_aspect('equal')\nax.set_title('Pendiente media por celda · grados · no es prospectividad')\nfig.colorbar(m, ax=ax, label='grados')\nplt.show()"),
('code',"fd.verify_records(RUN, fd.read_json(RUN / 'outputs_manifest.json'))\nprint('Productos sellados verificados:', RUN)")])]

for name,cells in items:
    path=ROOT/'notebooks'/f'{name}.ipynb'
    if path.exists():
        print('Se conserva:',path.name);continue
    book=nb.v4.new_notebook(cells=[nb.v4.new_markdown_cell(s) if kind=='md' else nb.v4.new_code_cell(s) for kind,s in cells])
    book.metadata.kernelspec={'name':'geoau-fase-a','display_name':'GeoAu fase A / D','language':'python'}
    book.metadata.language_info={'name':'python','version':'3.14'}
    if name.startswith('04_'):
        book.cells[1].source += "\nimport importlib.metadata\nfd.write_json(RUN / 'environment_fase_d.json', {p: importlib.metadata.version(p) for p in ('numpy', 'scipy', 'pyarrow')})"
    nb.validate(book);nb.write(book,path);print('Creado:',path.name)
