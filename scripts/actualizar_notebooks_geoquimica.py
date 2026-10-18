"""Construye y ejecuta los notebooks del flujo GeoAI de 64 predictores."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import shutil
import sys
import uuid

import nbformat as nbf
from nbclient import NotebookClient
from jupyter_client import KernelManager


ROOT = Path(__file__).resolve().parents[1]
NOTEBOOKS = ROOT / "notebooks"
TAG = "geoai-64-predictores"
BACKUP = ROOT / "reports/notebook_backups/geoai_integrado_20261017"
NAMES = {
    1: "01_indicios_limpieza_etiquetas.ipynb",
    6: "06_matriz_variables_control.ipynb",
    7: "07_particiones_espaciales.ipynb",
    9: "09_protocolo_PU_y_control.ipynb",
    16: "16_fase_g_evaluacion_holdout.ipynb",
    4: "04_variables_geoquimicas.ipynb",
    8: "08_muestreo_presencia_fondo.ipynb",
    10: "10_pipelines_y_contrato_entrenamiento.ipynb",
    11: "11_referencias_y_regresion_logistica.ipynb",
    12: "12_random_forest_espacial.ipynb",
    13: "13_comparacion_modelos.ipynb",
    14: "14_ablaciones_PU_y_cierre.ipynb",
    17: "17_fase_h_mapa_interpretabilidad.ipynb",
    18: "18_modelos_avanzados_pu_ebm_incertidumbre.ipynb",
}

SETUP = """from pathlib import Path
import sys, json
import pandas as pd
from IPython.display import display, Image
ROOT_GEO = next(p for p in [Path.cwd(), *Path.cwd().parents] if (p / 'src/geoau/geochemical_experiment.py').is_file())
if str(ROOT_GEO / 'src') not in sys.path:
    sys.path.insert(0, str(ROOT_GEO / 'src'))
RESULTS_GEO = ROOT_GEO / 'reports/geoquimica_20261017'
REPORT_GEO = ROOT_GEO / 'informes/geoquimica_20261017'
REENTRENAR_GEOQUIMICA = False  # True vuelve a ejecutar datos, CV, rotaciones, mapas e informe.
if REENTRENAR_GEOQUIMICA:
    from geoau.geochemical_experiment import run_experiment
    run_experiment(ROOT_GEO)
if not (RESULTS_GEO / 'control_ejecucion.json').is_file():
    raise FileNotFoundError('Ejecutar primero scripts/ejecutar_geoquimica.py con el entorno .venv-fase-a.')
control_geo = json.loads((RESULTS_GEO / 'control_ejecucion.json').read_text(encoding='utf-8'))
assert control_geo['status'] == 'complete' and control_geo['n_input_features'] == 64
print('Ejecución:', RESULTS_GEO)
print('GeoAI · 64 predictores · ocho variables geoquímicas · score relativo P/U')
"""


def md(source):
    cell = nbf.v4.new_markdown_cell(source)
    cell.metadata.tags = [TAG]
    return cell


def code(source):
    cell = nbf.v4.new_code_cell(source)
    cell.metadata.tags = [TAG]
    return cell


def backup(path):
    BACKUP.mkdir(parents=True, exist_ok=True)
    destination = BACKUP / path.name
    if path.is_file() and not destination.exists():
        shutil.copy2(path, destination)
        (BACKUP / (path.name + ".sha256")).write_text(hashlib.sha256(path.read_bytes()).hexdigest() + "\n", encoding="utf-8")



SECTIONS = {'datos': ('Inventario y unidad espacial de aprendizaje',
           'BDMIN contiene 790 registros: 190 confirmados, 597 pendientes y tres rechazados. Tras excluir rechazados y '
           'cruzar con el dominio, se obtienen 753 registros elegibles (175 confirmados y 578 pendientes), '
           'consolidados en 664 celdas P. Si coinciden varios estados en una celda se conserva el peso máximo: '
           'confirmada=1, pendiente=0,5. Depósitos y distritos organizan la evaluación, sin entrar como predictores.',
           "dataset = json.loads((RESULTS_GEO / 'dataset_summary.json').read_text(encoding='utf-8'))\n"
           "display(pd.DataFrame(list(dataset.items()), columns=['indicador','valor']))\n"
           "records = pd.read_csv(RESULTS_GEO / 'registros_elegibles.csv')\n"
           "display(records.estado_presencia.value_counts().to_frame('registros'))\n"
           'display(pd.read_csv(RESULTS_GEO / '
           "'celdas_positivas.csv').groupby('peso_confianza').size().to_frame('celdas'))"),
 'variables': ('Contrato de los 64 predictores',
               'Una fila representa una celda de un kilómetro EPSG:25830. Se integran 19 fracciones litológicas, 27 '
               'fracciones de edades, tres distancias estructurales, seis variables del relieve, una hidrológica y '
               'ocho geoquímicas. Identificadores, coordenadas, pesos y bloques no son covariables. El dominio se '
               'define por el soporte geológico y de relieve, conservando las ausencias geoquímicas.',
               "variables = pd.read_csv(RESULTS_GEO / 'variables_incluidas.csv')\n"
               'assert len(variables) == 64 and variables.variable.is_unique\n'
               "display(variables.groupby(['family','representation']).size().rename('variables').reset_index())\n"
               'display(variables)'),
 'geoquimica': ('Geoquímica: elementos, cobertura y leyendas',
                'Se incorporan arsénico (As), antimonio (Sb), bismuto (Bi), mercurio (Hg), cobre (Cu), plomo (Pb), '
                'zinc (Zn) y wolframio (W). Sus distribuciones aportan contexto químico que se interpreta con '
                'litología y estructuras. Una clase aislada no acredita presencia de oro. Au se excluye para reducir '
                'posible circularidad con el objetivo.\n'
                '\n'
                'Las capas del atlas geoquímico se integran recuperando clases mediante sus paletas RGB y agregando la '
                'clase modal por celda. La tabla de leyendas conserva códigos, colores e intervalos locales. Medio de '
                'muestreo, extracción y unidades requieren contraste con las fichas oficiales antes de interpretar los '
                'intervalos como concentraciones analíticas verificadas. El modelo usa categorías, sin asumir una '
                'distancia química entre códigos ni convertirlos en puntos medios de intervalos.\n'
                '\n'
                'La clase cero es válida. La ausencia se representa con -1 y se aplica one-hot, ajustado dentro del '
                'entrenamiento; handle_unknown=ignore gestiona categorías nuevas. Zn y W tienen menor cobertura. Se '
                'exporta el contador de elementos ausentes por celda. El número de columnas transformadas depende de '
                'las categorías aprendidas: 64 es el número de variables originales.',
                "coverage = pd.read_csv(RESULTS_GEO / 'cobertura_geoquimica.csv')\n"
                "coverage['coverage_percent'] = (1-coverage.missing_fraction)*100\n"
                'display(coverage.round(4))\n'
                "display(Image(filename=str(REPORT_GEO / 'figuras/cobertura_geoquimica.png')))\n"
                "display(pd.read_csv(RESULTS_GEO / 'leyendas_geoquimicas.csv'))"),
 'pipeline': ('Preprocesamiento dentro del entrenamiento',
              'Las variables numéricas se imputan con la mediana, añaden indicadores de ausencia cuando procede y se '
              'estandarizan. Las clases geoquímicas se imputan como categoría -1 y se codifican con one-hot. Cada '
              'algoritmo contiene estas transformaciones en un Pipeline ajustado exclusivamente con el entrenamiento '
              'de su partición. La aplicación territorial usa el pipeline ya aprendido.',
              'from geoau.geochemical_experiment import load_data, make_preprocessor\n'
              'data = load_data(ROOT_GEO)\n'
              "display(make_preprocessor(data.feature_columns, data.config['geochemical_columns']))\n"
              "print('Entradas:', len(data.feature_columns))\n"
              "print('Geoquímicas:', data.config['geochemical_columns'])"),
 'muestreo': ('Aprendizaje P/U y confianza del inventario',
              'Las celdas con indicios forman P y el territorio no inventariado es U, cuyo estado de mineralización se '
              'desconoce. Se muestrean hasta tres U por P con semillas fijadas. Las confirmadas reciben peso 1, las '
              'pendientes 0,5 y U peso 1. Las métricas se calculan sin ponderación. Bagging PU conserva P y remuestrea '
              'U dentro de cada ajuste; la ausencia de registros no se transforma en una ausencia geológica '
              'demostrada.',
              "sample = pd.read_parquet(RESULTS_GEO / 'partitions/benchmark_sample.parquet')\n"
              'assert sample.cell_id.is_unique\n'
              "display(sample.groupby(['label','peso_confianza']).size().rename('celdas').reset_index())\n"
              'display(pd.DataFrame([json.loads((RESULTS_GEO / '
              "'partitions/benchmark_design.json').read_text(encoding='utf-8'))]))"),
 'particiones': ('Validación espacial por bloques y buffer',
                 'Se utilizan cinco pliegues por bloques de 50 km. Los bloques de los distritos de reserva quedan '
                 'fuera del pool de evaluación de algoritmos. En cada pliegue se excluyen del entrenamiento las '
                 'muestras situadas a menos de 15 km de las muestras de validación. Cada muestra se predice fuera de '
                 'pliegue una vez. Se exportan pertenencias y hashes para comprobar la separación. Todos los '
                 'algoritmos utilizan las mismas 64 variables y particiones.',
                 "folds = pd.read_csv(RESULTS_GEO / 'benchmark_folds.csv')\n"
                 "assert folds.groupby('fold').training_ids_sha256.nunique().eq(1).all()\n"
                 "assert folds.groupby('fold').validation_ids_sha256.nunique().eq(1).all()\n"
                 "display(folds.loc[folds.model.eq('bagging_pu'),['fold','train_cells','validation_cells','buffer_excluded','roc_auc']].round(4))\n"
                 'display(pd.read_parquet(RESULTS_GEO / '
                 "'partitions/benchmark_memberships.parquet').groupby(['fold','role']).size().to_frame('celdas'))"),
 'modelos': ('Algoritmos y métricas fuera de pliegue',
             'Se evalúan logística L2, Random Forest, LightGBM y Bagging PU con las mismas 64 entradas. La logística '
             'representa relaciones aditivas regularizadas; los árboles modelan relaciones no lineales e '
             'interacciones. Bagging PU combina cinco miembros LightGBM de 100 árboles y hasta dos U por P dentro de '
             'cada muestra de entrenamiento.\n'
             '\n'
             'ROC-AUC y Average Precision se calculan sobre etiquetas P/U observadas. La recuperación de P de esta '
             'tabla cuenta celdas de la muestra, no depósitos ni superficie nacional. Las puntuaciones ordenan '
             'favorabilidad relativa. No se aplica una corrección Elkan–Noto ni se anuncian probabilidades físicas '
             'calibradas.',
             "benchmark = pd.read_csv(RESULTS_GEO / 'benchmark_summary.csv')\n"
             "display(benchmark[['model','n_input_features','roc_auc','average_precision','positive_cell_recovery_at_05','positive_cell_recovery_at_10']].round(4))\n"
             "display(Image(filename=str(REPORT_GEO / 'figuras/resultados_modelos.png')))"),
 'rotaciones': ('Transferencia por siete grupos de distritos',
                'Cada rotación reserva un grupo de distritos, sus bloques completos y un buffer de 15 km respecto a '
                'las celdas de esos bloques. También se excluyen del entrenamiento los indicios sin distrito situados '
                'en ese territorio. Se reentrenan logística, LightGBM y Bagging PU y se puntúan todas las celdas '
                'reservadas.\n'
                '\n'
                'Un depósito se recupera si alguna de sus celdas entra en el 1 %, 5 % o 10 % mejor puntuado del grupo. '
                'Los empates se resuelven por cell_id sin consultar etiquetas. Se evalúan 45 depósitos en siete '
                'grupos. Es una evaluación interna de transferencia con inventario conocido; una campaña nueva '
                'permitiría medir la utilidad prospectiva externa.\n'
                '\n'
                'La media uniforme y la fusión con pesos internos se evalúan sobre las mismas muestras y territorios. '
                'La media conserva pesos 0,25; los pesos aprendidos se seleccionan solo con el entrenamiento del grupo '
                'mediante tres pliegues internos con buffer.',
                "rotations = pd.read_csv(RESULTS_GEO / 'rotation_summary.csv')\n"
                'display(rotations.round(4))\n'
                "display(pd.read_csv(RESULTS_GEO / 'partitions/district_groups.csv'))\n"
                "rotation_folds = pd.read_csv(RESULTS_GEO / 'rotation_metrics.csv')\n"
                "assert rotation_folds.groupby('group').training_ids_sha256.nunique().eq(1).all()\n"
                "assert rotation_folds.groupby('group').held_ids_sha256.nunique().eq(1).all()\n"
                "display(rotation_folds[['model','group','n_deposits','n_held_cells','captured_deposits_at_10']])"),
 'mapas': ('Cartografía: favorabilidad, dispersión y novedad',
           'Después de evaluar se ajustan ocho miembros LightGBM de 150 árboles con las 664 celdas P y distintas '
           'muestras de hasta 1.992 U por miembro. Se guardan los ocho pipelines y se cartografían 478.443 celdas. '
           'Estos ajustes usan el inventario elegible completo y no son un test independiente. La evaluación de '
           'Bagging PU corresponde a cinco miembros de 100 árboles y su propio muestreo.\n'
           '\n'
           'La media resume favorabilidad relativa; la desviación describe variación entre miembros. La novedad es la '
           'distancia euclídea al centroide P en el espacio numérico estandarizado y geoquímico one-hot del primer '
           'miembro. Un centroide simplifica los contextos multimodales. La dispersión no cubre toda la incertidumbre '
           'geológica. Novedad alta usa el percentil 95, favorabilidad alta el percentil 90 y dispersión alta el '
           'percentil 75.\n'
           '\n'
           'Categorías: 1, novedad elevada; 2, favorabilidad alta y dispersión baja; 3, favorabilidad alta y '
           'dispersión alta; 4, favorabilidad menor y dispersión baja; 5, favorabilidad menor y dispersión elevada. '
           'Son umbrales relativos al dominio. Se exportan Parquet y GeoTIFF EPSG:25830 de score, dispersión, novedad '
           'y categoría.',
           "display(Image(filename=str(REPORT_GEO / 'figuras/mapa_geoquimica.png')))\n"
           "display(pd.read_csv(RESULTS_GEO / 'map_category_counts.csv').sort_values('category'))\n"
           "metadata = json.loads((RESULTS_GEO / 'models/GeoAI/metadata.json').read_text(encoding='utf-8'))\n"
           "display(pd.DataFrame([{'indicador':k,'valor':v} for k,v in metadata.items() if k not in "
           "['input_features','member_classifier_parameters']]))\n"
           "display(pd.DataFrame([{'producto':p.name,'MB':round(p.stat().st_size/1024**2,2)} for p in "
           "sorted((RESULTS_GEO / 'maps').iterdir())]))"),
 'consulta': ('Interpretación local de las evidencias',
              'La consulta reúne puntuación, estabilidad, novedad y los ocho elementos geoquímicos de cada celda. El '
              'contador de elementos ausentes acompaña la cartografía. Las clases deben interpretarse con sus leyendas '
              'y contexto geológico. La inspección permite formular hipótesis y preparar revisión de campo; las '
              'asociaciones no demuestran causalidad. Esta cadena no calcula SHAP ni EBM.',
              "national_map = pd.read_parquet(RESULTS_GEO / 'maps/GeoAI_national.parquet')\n"
              'from geoau.geochemical_experiment import load_data\n'
              'data = load_data(ROOT_GEO)\n'
              "chemistry = data.features[data.config['geochemical_columns']].reset_index()\n"
              "top = national_map.nlargest(12,'favorability_mean')\n"
              "display(top[['cell_id','favorability_mean','ensemble_std','novelty_distance','category','missing_geochemical_features']].merge(chemistry,on='cell_id').round(4))\n"
              'assert len(national_map) == 478443\n'
              "print('Celdas:',len(national_map))\n"
              "print('Miembros guardados:',len(list((RESULTS_GEO / 'models/GeoAI').glob('member_*.joblib'))))"),
 'reproduccion': ('Reproducción y uso',
                  'Configuración: config/geoquimica_20261017.yaml. Lógica: src/geoau/geochemical_experiment.py. '
                  'Ejecución: .venv-fase-a/Scripts/python.exe scripts/ejecutar_geoquimica.py. Se admiten etapas audit, '
                  'benchmark, diagnostics, rotations, maps, fusion y report. Para ejecutar todos los cuadernos: '
                  'scripts/actualizar_notebooks_geoquimica.py --execute. REENTRENAR_GEOQUIMICA=True en la primera '
                  'celda ejecuta la cadena completa antes de consultar resultados.\n'
                  '\n'
                  'Los manifiestos SHA-256 conservan entradas, código y salidas. Se exportan entorno, variables, '
                  'cobertura, leyendas, muestras, particiones, pesos y modelos. El notebook 18 reúne el sistema y el '
                  'informe desarrolla sus datos y resultados. Uso: priorización regional con revisión geológica. El '
                  'contraste de las leyendas y una campaña externa completan su evaluación.',
                  'display(pd.DataFrame([control_geo]))\n'
                  "print('Informe:',REPORT_GEO / 'INFORME_RESULTADOS_GEOQUIMICA.md')\n"
                  "print('Configuración:',ROOT_GEO / 'config/geoquimica_20261017.yaml')"),
 'propension': ('Factor de propensión c: estimación y reescalado',
                'El estimador de Elkan y Noto calcula c como la media del score de positivos reservados fuera del '
                'ajuste. El diagnóstico del catálogo usa las 664 celdas P elegibles y una muestra U, con reserva por '
                'bloques y buffer de 15 km. Cada uno de sus cinco miembros tiene un c propio. Se aplica '
                'q_b(x)=clip(g_b(x)/c_b,0,1) y después se promedian los miembros. La inversa de la media de c es una '
                'escala de referencia, no equivale exactamente al reescalado del ensamble con factores distintos y '
                'recorte.\n'
                '\n'
                'La lectura como probabilidad de registro depende del supuesto SCAR, la calibración y el diseño de '
                'muestreo. Con U muestreado y pesos de confianza lo presentamos como un factor aparente del '
                'experimento. No estima el porcentaje de oro conocido en España. El c del catálogo pertenece a su '
                'ensamble diagnóstico: la cartografía nacional mantiene sus ocho pipelines de scores relativos. En CV, '
                'cada c se estima dentro del entrenamiento del pliegue sin consultar la validación externa.',
                'propensity = json.loads((RESULTS_GEO / '
                "'propensity_catalog_summary.json').read_text(encoding='utf-8'))\n"
                'print(f"Factor c (Elkan y Noto) estimado en positivos reservados del catálogo: '
                '{propensity[\'c_mean\']:.4f}")\n'
                'print(f"Score medio aparente sobre esos positivos: {100*propensity[\'c_mean\']:.2f} %")\n'
                'print(f"Escala de referencia 1/c: {propensity[\'inverse_c_mean\']:.3f}×")\n'
                "print('Corrección por miembro: q_b = clip(g_b / c_b, 0, 1); ensamble = media de q_b.')\n"
                "display(pd.DataFrame({'miembro':range(len(propensity['c_members'])),'c':propensity['c_members'],'escala_1_c':[1/c "
                "for c in propensity['c_members']]}).round(5))\n"
                "display(pd.DataFrame([propensity]).drop(columns=['c_members','reference','scope']))\n"
                "display(pd.read_csv(RESULTS_GEO / 'propensity_catalog_score_examples.csv').head(12).round(5))"),
 'diagnosticos': ('Benchmark: tres estrategias CV y seis procedimientos con geoquímica',
                  'La tabla presenta 18 resultados del mismo conjunto de 64 predictores: logística L2, Random Forest, '
                  'LightGBM, Bagging PU + Elkan–Noto, fusión media uniforme y fusión con pesos internos, bajo Random '
                  'CV, Spatial Block CV sin buffer y Buffered Spatial CV de 15 km. Todos utilizan la misma muestra de '
                  '629 P y 1.887 U, con bloques de reserva excluidos. Las dos estrategias espaciales comparten sus '
                  'celdas de validación; el buffer cambia el entrenamiento.\n'
                  '\n'
                  'En Bagging PU + Elkan–Noto se reserva un pliegue interno para estimar c; el clasificador y su '
                  'preprocesamiento se ajustan sin esa reserva. Se reproduce el tipo de separación de cada estrategia. '
                  'La tabla muestra métricas de predicciones fuera de pliegue; c del nombre del modelo resume cinco '
                  'miembros y cinco pliegues.\n'
                  '\n'
                  'PR-AUC conserva la definición de la tabla solicitada: Average Precision. El área PR trapezoidal se '
                  'exporta en otra columna. Brier Loss es el error cuadrático frente a etiquetas P/U y no demuestra '
                  'calibración de mineralización real. Recovery usa un cupo exacto del 5 % o 10 % de las celdas de la '
                  'muestra, con desempate por cell_id independiente de etiquetas; representa porcentaje de P '
                  'recuperadas. El recorte en uno no amplía ese presupuesto. La recuperación de depósitos del apartado '
                  'territorial es otra unidad de evaluación.',
                  'from geoau.validation_diagnostics import display_benchmark\n'
                  "cv_results = pd.read_csv(RESULTS_GEO / 'benchmark_cv_summary.csv')\n"
                  'assert len(cv_results) == 18 and cv_results.n_input_features.eq(64).all()\n'
                  'display(display_benchmark(cv_results))\n'
                  "display(cv_results.loc[cv_results.model.eq('bagging_pu_elkan_noto'),['strategy','c_mean','c_std','fraction_score_one']].round(5))\n"
                  "display(cv_results[['strategy','model','average_precision','pr_auc_trapezoid']].round(5))\n"
                  "display(Image(filename=str(REPORT_GEO / 'figuras/validacion_tres_estrategias.png')))\n"
                  "print('Tabla CSV:',RESULTS_GEO / 'benchmark_cv_tabla.csv')\n"
                  "print('Particiones internas y externas:',RESULTS_GEO / 'partitions')"),
 'fusion': ('Fusión heterogénea: complementariedad y pesos mediante validación interna',
            'Se evalúan dos reglas de agregación sobre los mismos componentes: media uniforme con pesos fijos 0,25 y '
            'pesos aprendidos únicamente en la validación interna. La media uniforme permite comprobar si basta '
            'agregar señales sin ajustar otra capa de parámetros.\n'
            '\n'
            'La fusión combina logística L2, Random Forest, LightGBM y Bagging PU. Bagging agrega miembros de una '
            'familia; la fusión permite combinar estructuras de aprendizaje distintas. Todos los componentes utilizan '
            'las mismas 64 variables geológicas y geoquímicas y pesos de confianza. La correlación de sus scores OOF '
            'describe su complementariedad.\n'
            '\n'
            'El score es S(x)=Σ w_j s_j(x), con pesos no negativos que suman uno. En la regla de pesos aprendidos, '
            'cada entrenamiento externo genera predicciones OOF con tres pliegues internos. Se seleccionan los pesos '
            'maximizando Average Precision interna en una rejilla de paso 0,1, que incluye pesos cero y la media '
            'uniforme. Los empates favorecen pesos menos concentrados. Imputación, escalado y one-hot se aprenden '
            'dentro de cada ajuste interno. Después se reajustan los componentes sobre todo el entrenamiento externo y '
            'se predice el test con los pesos ya fijados. El test externo no interviene en la selección.\n'
            '\n'
            'Se evalúa el procedimiento en las tres estrategias CV y en siete rotaciones por grupos de distritos. Las '
            'métricas observadas permiten valorar si mejora AP, AUC o recuperación territorial; una mejora en una de '
            'ellas no implica superioridad en todas. Se fusionan scores P/U sin aplicar el c de otro modelo. No se '
            'estiman probabilidades físicas de depósito.\n'
            '\n'
            'La mejora se valora por métrica y presupuesto territorial. Una AP mayor no garantiza mayor AUC ni '
            'recuperar más depósitos al 10 %. Se incorpora la fusión como candidato evaluado y se conserva la '
            'referencia territorial cuando la evidencia no justifica sustituirla.',
            "fusion_summary = json.loads((RESULTS_GEO / 'fusion_summary.json').read_text(encoding='utf-8'))\n"
            "print('Criterio de selección:', fusion_summary['selection_metric'])\n"
            "print('¿Se utilizan etiquetas del test para los pesos?', "
            "fusion_summary['weight_selection_uses_outer_test'])\n"
            "fusion_weights = pd.read_csv(RESULTS_GEO / 'fusion_weights.csv')\n"
            "display(fusion_weights.loc[fusion_weights.scope.eq('cv')].groupby(['strategy','component']).weight.agg(['mean','std']).round(4))\n"
            "display(Image(filename=str(REPORT_GEO / 'figuras/fusion_complementariedad.png')))\n"
            "comparison = pd.read_csv(RESULTS_GEO / 'benchmark_summary.csv')\n"
            "display(comparison[['model','roc_auc','average_precision','positive_cell_recovery_at_05','positive_cell_recovery_at_10']].round(5))\n"
            "display(pd.read_csv(RESULTS_GEO / 'rotation_summary.csv').round(5))\n"
            "display(Image(filename=str(REPORT_GEO / 'figuras/fusion_resultados.png')))\n"
            "uniform = comparison.loc[comparison.model.eq('heterogeneous_uniform')].iloc[0]\n"
            "reference = comparison.loc[comparison.model.eq('bagging_pu')].iloc[0]\n"
            "print(f'Media uniforme: AP {uniform.average_precision:.4f}; Bagging PU: "
            "{reference.average_precision:.4f}.')\n"
            "print(f'AUC uniforme: {uniform.roc_auc:.4f}; Bagging PU: {reference.roc_auc:.4f}.')\n"
            "rot = pd.read_csv(RESULTS_GEO / 'rotation_summary.csv').set_index('model')\n"
            'for budget in [5,10]:\n'
            '    print(f"Depósitos al {budget}%: media uniforme '
            "{int(rot.loc['heterogeneous_uniform',f'captured_deposits_at_{budget:02d}'])}/45; Bagging PU "
            '{int(rot.loc[\'bagging_pu\',f\'captured_deposits_at_{budget:02d}\'])}/45.")'),
 'mapa_fusion': ('Modelo nacional y cartografía de la fusión',
                 'La media uniforme conserva pesos 0,25 para los cuatro componentes. La regla aprendida selecciona de '
                 'nuevo sus pesos mediante tres pliegues internos espaciales. Ambas utilizan una muestra nacional con '
                 '664 P y 1.992 U. Los cuatro pipelines se reajustan sobre esa muestra y se guardan junto con los '
                 'pesos. El mapa nacional es una aplicación posterior al ajuste, no un test independiente.\n'
                 '\n'
                 'Se exporta el score fusionado, los cuatro scores de componentes, novedad y desacuerdo ponderado: '
                 'raíz de Σ w_j(s_j−S)². Este desacuerdo mide diferencias entre familias. La dispersión del ensamble '
                 'de ocho LightGBM del apartado anterior mide variación entre remuestreos de esa familia. Son '
                 'diagnósticos distintos; ninguno cubre toda la incertidumbre geológica. Los mapas de la fusión se '
                 'guardan como GeoTIFF y Parquet y conservan el contador de elementos geoquímicos ausentes.',
                 'fusion_metadata = json.loads((RESULTS_GEO / '
                 "'models/fusion_uniform/metadata.json').read_text(encoding='utf-8'))\n"
                 "display(pd.DataFrame([fusion_metadata['weights']]).round(5))\n"
                 "display(Image(filename=str(REPORT_GEO / 'figuras/fusion_mapa.png')))\n"
                 "fusion_map = pd.read_parquet(RESULTS_GEO / 'maps/GeoAI_fusion_uniform_national.parquet')\n"
                 "display(fusion_map.nlargest(12,'favorability_mean')[['cell_id','favorability_mean','component_disagreement_std','novelty_distance','missing_geochemical_features']].round(5))\n"
                 "print('Modelo:',RESULTS_GEO / 'models/fusion_uniform/model.joblib')\n"
                 "print('Mapa:',RESULTS_GEO / 'maps/GeoAI_fusion_uniform_national.parquet')\n"
                 "print('Informe:',REPORT_GEO / 'INFORME_FUSION_MODELOS.md')")}

PLANS = {
    1: ('Inventario y etiquetas', ['datos','muestreo','reproduccion']),
    4: ('Variables geoquímicas', ['geoquimica','pipeline','consulta','reproduccion']),
    6: ('Matriz de variables y control', ['variables','geoquimica','pipeline','reproduccion']),
    7: ('Particiones espaciales', ['datos','particiones','rotaciones','reproduccion']),
    8: ('Muestreo de presencia y fondo', ['datos','muestreo','particiones','reproduccion']),
    9: ('Protocolo P/U', ['muestreo','pipeline','modelos','reproduccion']),
    10: ('Pipelines y contrato de entrenamiento', ['variables','pipeline','muestreo','particiones','reproduccion']),
    11: ('Regresión logística regularizada', ['pipeline','particiones','modelos','rotaciones','reproduccion']),
    12: ('Random Forest espacial', ['variables','pipeline','particiones','modelos','reproduccion']),
    13: ('Evaluación de algoritmos', ['variables','particiones','modelos','rotaciones','reproduccion']),
    14: ('Aprendizaje PU y cierre', ['muestreo','modelos','rotaciones','mapas','reproduccion']),
    16: ('Evaluación territorial reservada', ['particiones','rotaciones','reproduccion']),
    17: ('Mapa e interpretación', ['mapas','geoquimica','consulta','rotaciones','reproduccion']),
    18: ('GeoAI: prospectividad aurífera, PU, fusión e incertidumbre', ['datos','variables','geoquimica','pipeline','muestreo','particiones','propension','fusion','diagnosticos','rotaciones','mapas','mapa_fusion','consulta','reproduccion']),
}

def build_cells(number):
    title, sections = PLANS[number]
    cells = [md(f'# {number:02d} · {title}\n\nGeoAI integra **64 predictores**, incluidas ocho variables geoquímicas, sobre una malla de un kilómetro. Este cuaderno desarrolla su etapa utilizando la configuración común. El notebook 18 reúne el sistema completo. Las celdas de consulta leen resultados entrenados; el indicador de reentrenamiento permite regenerarlos.'), code(SETUP)]
    for index, name in enumerate(sections, 1):
        title, description, source = SECTIONS[name]
        if number == 18 and name == 'particiones':
            source = source.replace(",'roc_auc'", "")
        if name == 'geoquimica':
            description += '\n\nSe muestra también la importancia global por ganancia de los árboles, agregada por elemento sobre sus categorías one-hot. Es un diagnóstico del ajuste: correlaciones, número de categorías y ausencias pueden influir. No es una atribución causal ni mide la mejora predictiva debida a cada elemento.'
            source += "\ndisplay(pd.read_csv(RESULTS_GEO / 'importancia_geoquimica.csv').round(6))"
        cells += [md(f'## {index}. {title}\n\n{description}'), code(source)]
    return cells


def execute_cells(cells):
    notebook = nbf.v4.new_notebook(cells=cells)
    runtime = ROOT / "tmp/jupyter_geoquimica"
    runtime.mkdir(parents=True, exist_ok=True)
    environment = os.environ.copy()
    environment.update({"IPYTHONDIR": str(runtime / "ipython"), "JUPYTER_RUNTIME_DIR": str(runtime),
                        "MPLCONFIGDIR": str(runtime / "matplotlib"), "PYTHONUTF8": "1"})
    manager = KernelManager(kernel_name="python3", connection_file=str(runtime / f"kernel-{uuid.uuid4().hex}.json"))
    manager.kernel_spec.argv = [sys.executable, "-m", "ipykernel_launcher", "-f", "{connection_file}"]
    client = NotebookClient(notebook, timeout=600, km=manager, resources={"metadata": {"path": str(ROOT)}})
    try:
        client.execute(env=environment)
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
    return notebook.cells


def update_notebooks(numbers=None, execute=False):
    for number in numbers or list(NAMES):
        path = NOTEBOOKS / NAMES[number]
        backup(path)
        cells = build_cells(number)
        if execute:
            cells = execute_cells(cells)
        notebook = nbf.v4.new_notebook(cells=cells)
        notebook.metadata.kernelspec = {"display_name": "Python (GeoAI)", "language": "python", "name": "python3"}
        notebook.metadata.language_info = {"name": "python", "version": sys.version.split()[0]}
        notebook.metadata.geoai = {"pipeline": "geoai", "n_input_features": 64, "geochemical_features": 8}
        nbf.validate(notebook)
        nbf.write(notebook, path)
        print(f"Notebook {number:02d}: 64 predictores; ejecutado={execute}", flush=True)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--execute", action="store_true")
    parser.add_argument("--notebooks", nargs="+", type=int, choices=sorted(NAMES))
    args = parser.parse_args()
    update_notebooks(args.notebooks, args.execute)
