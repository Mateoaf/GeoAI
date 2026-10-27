"""Build and execute the real NB29 feature experiment with a workspace kernel."""
from pathlib import Path
import argparse
import json
import sys

import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import AsyncKernelManager
from jupyter_client.kernelspec import KernelSpecManager

ROOT = Path(__file__).resolve().parents[1]
NAME = "29_descriptores_corregidos_ablacion_y_reentrenamiento.ipynb"
DEFAULT_OUTPUT = "reports/reentrenamiento_nb29_descriptores_y_piloto_20261022"


def build(output):
    cells = []
    def md(text):
        cells.append(nbf.v4.new_markdown_cell(text))
    def code(text):
        cells.append(nbf.v4.new_code_cell(text))

    md("""# Notebook 29 · Descriptores corregidos, ablación y reentrenamiento real

Este cuaderno ejecuta el siguiente paso del NB28: **incorporar realmente los descriptores corregidos a modelos nuevos**, medir qué aporta cada uno y reajustar los modelos nacionales. También sustituye el catálogo inicial de dianas por un diseño prospectivo emparejado, con distancias verificables.

La hipótesis es comprobable, no una promesa de mejora: las interacciones sedimentarias/topográficas y espectrales pueden ayudar o empeorar el ranking. Se conservan los resultados completos en ambos casos.

**Diseño fijado antes de obtener resultados NB29:** ocho miembros, U:P=3:1 sin reemplazo, mismas semillas y particiones que NB27; cinco pliegues espaciales, siete rotaciones y tres pliegues internos con bloques de 50 km y buffer de 15 km. Endpoint principal: recuperación de depósitos en el 5% de celdas reservadas, comparando `max3_97` con `max3_95_ref`. La cartografía principal experimental se fija como `max3_97`, sin elegirla después de mirar el test.

Los territorios se han examinado en NB19–28. Se trata de un contraste exploratorio, no de un test externo nuevo. No se inventan nuevas mediciones analíticas, imágenes Sentinel-2 ni resultados de campo. Las covariables nuevas son interacciones de información cartográfica existente.

Implementación: `prospective_features.py`, `prospective_models.py` y `prospective_experiment.py`, en `src/geoau/`. Las celdas ejecutan los ajustes, muestran sus resultados y conservan los artefactos anteriores.""")
    code(f"""from pathlib import Path
import sys, json
import numpy as np
import pandas as pd
from IPython.display import display, Image, Markdown

ROOT = Path.cwd().resolve()
if not (ROOT / 'src').exists():
    ROOT = ROOT.parent
sys.path.insert(0, str(ROOT / 'src'))
from geoau.prospective_experiment import ProspectiveExperiment
from geoau.prospective_features import NEW_FEATURES
from geoau.prospective_models import METHODS29, REFERENCES29

exp = ProspectiveExperiment(ROOT, output={output!r})
print('Python:', sys.executable)
print('Resultados:', exp.output)
print('Dominio:', len(exp.data.grid), '| P elegibles:', len(exp.data.positives))
display(pd.Series(exp.cfg).to_frame('Diseño fijado antes de evaluar NB29'))
""")
    md("""## 1. Corregir la semántica antes de entrenar

El NB28 llamaba terrazas cuaternarias a `litologia_u000_fraccion`. Su leyenda real es una unidad mixta de areniscas, conglomerados, arcillas, calizas y evaporitas. El contexto de gravas/conglomerados/arenas/limos es **u012**. La edad cuaternaria u004 fue excluida del modelo inicial porque duplica exactamente u012; añadir ambas como observaciones distintas exageraría la información disponible.

El GPKG auxiliar de recintos cuaternarios se audita: sus registros tienen el mismo descriptor genérico y código geomorfológico 0. No permite identificar terrazas fluviales con respaldo suficiente y no se incorpora.

Las tipologías conservan la revisión del NB27: desconocidos en el global, siete celdas mixtas y epitermal limitado a los dos depósitos documentados de Rodalquilar. Primario no equivale exclusivamente a orogénico o varisco.""")
    code("""display(exp.audit_labels())
display(exp.prepare_features())
display(pd.read_csv(exp.output / 'contrato_descriptores_nb29.csv'))
display(exp.X[NEW_FEATURES].describe())
print('Número de variables:', len(exp.X.columns))
print('Ausentes conservados:')
display(exp.X[NEW_FEATURES].isna().sum().to_frame('sin_dato'))
""")
    md(r"""## 2. Hipótesis físicas y límites de las dos covariables

**Aluvial contextual:**

\[
A=\exp(-d_{cauce}/300)\exp(-pendiente/6)(0.25+0.75f_{u012})\exp[-\max(TPI_{1km},0)/50].
\]

Usa contexto sedimentario, cercanía a cauces, pendiente y posición respecto al relieve local. El TPI positivo atenúa posiciones elevadas; no se lo denomina energía hidráulica, área aportante ni terraza observada. Las escalas y el término de fondo son constantes heurísticas fijadas antes de evaluar, no ajustadas con el test.

**Alteración con suelo expuesto:**

\[
S=\log[1+\max(clip(SWIR,0,4)-1,0)]\log[1+\max(clip(Fe,0,5)-1,0)](1-clip(NDVI,0,1))^2.
\]

Se atenúan vegetación y extremos mediante una interacción de ratios MODIS. No es una medición de mineral ni una máscara QA. No aumenta la resolución del sensor ni reemplaza análisis de laboratorio. Los ausentes permanecen ausentes hasta la imputación de cada miembro; las estadísticas pathfinder y el preprocesamiento se aprenden exclusivamente dentro de su entrenamiento.

La ganancia de importancia interna de una covariable no prueba que mejore la generalización. Esa afirmación se comprueba mediante la ablación y la recuperación territorial.""")
    code("""contrastes = pd.DataFrame([
    {'procedimiento': 'mono95_ref', 'variables': 95, 'objetivo': 'control NB27 verificado'},
    {'procedimiento': 'mono96_aluvial', 'variables': 96, 'objetivo': 'aislar descriptor aluvial'},
    {'procedimiento': 'mono96_espectral', 'variables': 96, 'objetivo': 'aislar descriptor espectral'},
    {'procedimiento': 'mono97', 'variables': 97, 'objetivo': 'efecto conjunto y contraste de interacción'},
    {'procedimiento': 'max3_97 / fusion3_97', 'variables': 97, 'objetivo': 'mismos componentes; cambia la agregación'},
    {'procedimiento': 'max3_95_ref / fusion3_95_ref', 'variables': 95, 'objetivo': 'control de arquitectura NB27'},
    {'procedimiento': 'regla_geologica_ref', 'variables': '-', 'objetivo': 'referencia física fijada sin aprender del test'},
])
display(contrastes)
print('El control se reutiliza con hashes y entorno verificados; los modelos de 96/97 variables se entrenan realmente.')
""")
    md("""## 3. Entrenamiento y evaluación espacial real

Se guardan todas las filas de entrenamiento de cada miembro y se comparan con las del control. La única diferencia entre los modelos globales es el conjunto de columnas. Las ramas de 97 variables usan también las mismas muestras y semillas que sus ramas equivalentes del NB27.

Las CDF se ajustan con predicciones U fuera de pliegue dentro del entrenamiento. Los pesos de fusión se eligen con referencias cruzadas entre pliegues internos y AP P/U, conservando peso global >=0,1. Esta AP es un proxy de discriminación y no optimiza directamente recuperación territorial por área. No se utilizan estadísticas de las etiquetas externas ni normalización min/max del test.

Los scores son rankings relativos. La AP de la muestra P/U y Brier no estiman prevalencia ni probabilidad física de descubrir oro.""")
    code("""cv = exp.evaluate_cv()
display(cv[['method', 'roc_auc', 'average_precision', 'positive_cell_recovery_at_05', 'positive_cell_recovery_at_10']])
base_cv = cv.set_index('method').loc['mono95_ref']
delta_cv = cv.loc[cv.method.isin(['mono96_aluvial', 'mono96_espectral', 'mono97']), ['method', 'roc_auc', 'average_precision']].copy()
delta_cv['delta_auc_vs95'] = delta_cv.roc_auc - base_cv.roc_auc
delta_cv['delta_ap_vs95'] = delta_cv.average_precision - base_cv.average_precision
display(delta_cv)
""")
    md("""## 4. Recuperación de depósitos e incertidumbre

Se puntúan todas las celdas de las siete reservas y se seleccionan presupuestos exactos del 1/5/10/20%, con desempate por cell_id. Cada depósito se cuenta una sola vez.

La referencia aleatoria tiene en cuenta huellas multicelda, celdas compartidas y muestreo sin reemplazo. Se calcula la esperanza hipergeométrica exacta y se simulan 20.000 selecciones por presupuesto. Su intervalo nulo no es un intervalo de confianza de la probabilidad de descubrimiento.

La comparación pareada usa 10.000 remuestreos de los **siete grupos de rotación**, manteniendo juntas las observaciones territoriales de cada grupo. Es una estimación exploratoria con pocos grupos y territorios reutilizados. Las colas Monte Carlo no se presentan como una prueba confirmatoria ni se selecciona un presupuesto después de observar resultados.""")
    code("""rotaciones = exp.evaluate_rotations()
display(rotaciones[['method', 'n_deposits', 'captured_01', 'captured_05', 'captured_10', 'captured_20']])
display(pd.read_csv(exp.output / 'random_summary.csv'))
pareada = pd.read_csv(exp.output / 'paired_ablation_comparison.csv')
display(pareada.loc[pareada.budget_percent.eq(5)])
principal = pareada.loc[pareada.contrast.eq('max97_vs_max95') & pareada.budget_percent.eq(5)].iloc[0]
print(f"Contraste principal: {principal.delta_captured:+.0f} depósitos; intervalo de diferencia [{principal.ci025_pp:.2f}, {principal.ci975_pp:.2f}] puntos porcentuales")
""")
    md("""## 5. Reentrenamiento nacional y artefactos de inferencia

Se reajustan los modelos globales de 96/97 variables y los especialistas de 97 variables con **todas las P elegibles**, ocho miembros por componente y muestras U distintas por miembro. Se guardan los pipelines realmente ajustados, normalizadores y pesos. El objeto nacional permite predecir nuevas filas y reproducir el mapa.

`max3_97` es el mapa experimental principal predeclarado. Se conservan también los otros mapas aunque el resultado de algún método sea peor. Los scores de los controles mantienen sus hashes y se exportan identificados como referencias. La recuperación nacional sobre presencias de entrenamiento se muestra solo como descripción in-sample.""")
    code("""nacional = exp.fit_national()
display(nacional[['method', 'n_deposits', 'captured_deposits_at_01', 'captured_deposits_at_05', 'captured_deposits_at_10', 'captured_deposits_at_20']])
display(pd.Series(json.loads((exp.output / 'partitions/national_0/weights.json').read_text())).to_frame('peso_fusion_interna'))
ganancias = pd.read_csv(exp.output / 'national_feature_gain.csv')
display(ganancias.loc[ganancias.feature.str.contains('|'.join(NEW_FEATURES), regex=True)]
    .groupby(['component', 'feature']).gain.mean().rename('ganancia_media_entrenamiento').to_frame())
""")
    md("""## 6. Piloto prospectivo local con dianas y controles comparables

Se excluyen todas las celdas del inventario, incluidos registros no usados como P, y un entorno de 15 km respecto a sus centros. Se forman hasta **12 tripletes**: alta prioridad (percentil >=99,5), control medio (80–85) y control bajo (20–25). Cada triplete comparte litología dominante y región de 100 km; los controles quedan a <=75 km de la diana. Todos los sitios del piloto están separados >=10 km entre sí y no se repiten bloques de 50 km entre las dianas altas.

Las dianas altas se recorren ordenadas por score, no por el orden de filas. Si no hay controles admisibles se descarta esa diana y se registra el motivo. No se relajan requisitos para alcanzar doce tripletes. Los estratos bajos no se consideran estériles y la ausencia de inventario no prueba que un área esté inexplorada.

Se guarda un protocolo y un catálogo local con SHA-256. **No es una campaña ejecutada ni un registro público.** Antes del campo se fijan el procedimiento y límites de detección por sistema, el esfuerzo equivalente por triplete y la lectura independiente de resultados. Aún no hay etiquetas de descubrimiento nuevas.""")
    code("""protocolo = exp.prepare_pilot()
display(pd.Series(protocolo).to_frame('protocolo_local'))
piloto = pd.read_csv(exp.output / 'pilot_matched_triplets.csv')
display(piloto[['triplet_id', 'stratum', 'cell_id', 'score', 'percentile', 'distance_known_cell_m', 'substrate', 'region']])
print('Tripletes completos:', piloto.triplet_id.nunique(), '| Sitios:', len(piloto))
""")
    md("""## 7. Reproducibilidad, resultados y límites

La validación comprueba modelos guardados, 96/97 columnas realmente utilizadas, muestras pareadas con el control, pesos, referencias CDF solo internas, buffers, separación de bloques, estadísticas aprendidas, presupuestos, recuentos y geometría del piloto. Se reproducen predicciones desde los trece bundles y se verifica invariancia al lote.

Las conclusiones y figuras se generan desde esta ejecución. Una mejora interna requiere confirmación externa; una ausencia de mejora se conserva como resultado del experimento. Los artefactos NB27/NB28 permanecen intactos.""")
    code("""validacion = exp.validate()
display(pd.Series(validacion).to_frame('verificacion'))
for figura in exp.make_figures():
    display(Image(filename=str(figura)))
informe = exp.write_report()
exp.seal(informe)
display(Markdown(informe.read_text(encoding='utf-8').split('## Ajuste nacional')[0]))
print('Informe:', informe)
print('Modelo nacional:', exp.output / 'partitions/national_0/model.joblib')
print('Mapa principal:', exp.output / 'maps/NB29_max3_97_score.tif')
""")
    nb = nbf.v4.new_notebook(cells=cells)
    nb.metadata.update({"kernelspec": {"display_name": "Python (GeoAI)", "language": "python", "name": "python3"},
                        "language_info": {"name": "python", "version": sys.version.split()[0]}})
    return nb


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--output", default=DEFAULT_OUTPUT)
    parser.add_argument("--build-only", action="store_true")
    args = parser.parse_args()
    nb = build(args.output)
    nbf.validate(nb)
    path = ROOT / "notebooks" / NAME
    nbf.write(nb, path)
    print(f"NB29 construido: {path}", flush=True)
    if args.build_only:
        return
    runtime = ROOT / "reports/nb29_runtime_20261022"
    kernel_dir = runtime / "kernels/geoai_nb29"
    kernel_dir.mkdir(parents=True, exist_ok=True)
    env = {"PYTHONPATH": str(ROOT / "src"), "MPLCONFIGDIR": str(runtime / "matplotlib"),
        "JUPYTER_RUNTIME_DIR": str(runtime), "IPYTHONDIR": str(runtime / "ipython"), "PYTHONIOENCODING": "utf-8"}
    (kernel_dir / "kernel.json").write_text(json.dumps({"argv": [sys.executable, "-X", "utf8", "-m", "ipykernel_launcher", "-f", "{connection_file}"],
        "display_name": "GeoAI NB29", "language": "python", "env": env}), encoding="utf-8")
    manager = AsyncKernelManager(kernel_name="geoai_nb29", connection_file=str(runtime / "connection.json"),
        kernel_spec_manager=KernelSpecManager(kernel_dirs=[str(runtime / "kernels")]))
    def checkpoint(**kwargs):
        nbf.write(nb, path)
        print(f"Celda {kwargs.get('cell_index', '?')} ejecutada", flush=True)
    client = NotebookClient(nb, km=manager, timeout=7200, resources={"metadata": {"path": str(ROOT)}}, on_cell_executed=checkpoint)
    try:
        client.execute(cleanup_kc=True)
    except BaseException:
        nbf.write(nb, path)
        print("Ejecución interrumpida: checkpoints de notebook y ajustes completos conservados.", flush=True)
        raise
    nbf.write(nb, path)
    code_cells = [c for c in nb.cells if c.cell_type == "code"]
    errors = [o for c in code_cells for o in c.get("outputs", []) if o.output_type == "error"]
    if errors or any(c.execution_count is None for c in code_cells):
        raise AssertionError("Notebook incompleto o con errores.")
    sys.path.insert(0, str(ROOT / "src"))
    from geoau.geochemical_experiment import sha256, write_json
    write_json(ROOT / args.output / "notebook_execution.json", {"notebook": path.relative_to(ROOT).as_posix(),
        "sha256": sha256(path), "code_cells_executed": len(code_cells), "errors": len(errors), "python": sys.executable})
    print(f"NB29 ejecutado y guardado: {len(code_cells)} celdas de código, sin errores", flush=True)


if __name__ == "__main__":
    main()
