"""Informe descriptivo reproducible. Solo lee productos D y escribe esta carpeta."""
from pathlib import Path
import ast
import csv
import hashlib
import html
import json
import re
import sys
import importlib.util
import pandas as pd
import numpy as np
import pyarrow.parquet as pq

BASE = Path(__file__).resolve().parent
ROOT = BASE.parents[1]
RUN = ROOT / 'reports/fase_d/20260923T211448_267684Z'
STEM = 'INFORME_VARIABLES_GRID_MASTER_AU'


def read_json(p):
    return json.loads(p.read_text(encoding='utf-8'))


def read_csv(p):
    return pd.read_csv(p, encoding='utf-8-sig')


def table(headers, rows):
    def esc(v):
        return str(v).replace('|', '/').replace('\n', ' ')
    return '\n'.join(['| ' + ' | '.join(headers) + ' |', '|' + '|'.join(['---']*len(headers)) + '|'] + ['| ' + ' | '.join(esc(v) for v in row) + ' |' for row in rows])


LITH_REASON = {
    0: 'Describe una mezcla sedimentaria: permeabilidad y reactividad pueden condicionar circulación y precipitación; su amplitud impide asignarle favorabilidad fija.',
    1: 'Combina encajantes siliciclásticos y carbonatados; sus contrastes mecánicos y químicos pueden localizar mineralización si hay fluidos y estructuras apropiadas.',
    2: 'Contexto sedimentario carbonatado y detrítico. Puede distinguir cuencas, cobertura y encajantes reactivos; señal principalmente contextual.',
    3: 'Carbonatos potencialmente reactivos junto con materiales detríticos; hipótesis de control del encajante, sin evidencia de alteración en esta variable.',
    4: 'Contexto detrítico con conglomerados. Puede señalar ambientes de transporte o encajantes, pero no identifica paleoplaceres auríferos por sí solo.',
    5: 'Mezcla sedimentaria y evaporítica; diferencia dominios y cobertura. No hay una relación positiva universal con Au.',
    6: 'Unidad sedimentaria heterogénea con yesos; aporta contexto de cuenca y posibles contrastes de permeabilidad, no una señal aurífera directa.',
    7: 'Encajantes detríticos y pizarrosos, carbonatos y carbón. Sugiere contrastes mecánicos y químicos, sin medir materia reductora ni sulfuros efectivamente presentes.',
    8: 'Contrastes entre cuarcitas, pizarras y carbonatos pueden condicionar fracturación, circulación y reacción con fluidos; requiere estructuras favorables.',
    9: 'Carbonatos y materiales detríticos: contexto de encajante reactivo y permeabilidad; no basta para inferir un sistema mineralizado.',
    10: 'Representa basamento metamórfico; puede contextualizar zonas de cizalla y vetas, pero gneiss no equivale a roca aurífera.',
    11: 'Contexto granítico para evaluar sistemas relacionados con intrusiones; necesita edad, fertilidad y geoquímica compatibles.',
    12: 'Hipótesis de transporte y acumulación detrítica de Au; la unidad incluye depósitos no auríferos y no distingue terrazas de otros sedimentos.',
    13: 'Encajantes metamórficos y carbonatados con contrastes mecánicos y químicos; posible contexto de vetas y reacción roca-fluido.',
    14: 'Unidad mixta de basamento y granitoides; puede aportar contexto térmico e intrusivo, pero no cuantifica cuánto granito contiene.',
    15: 'Contexto intrusivo genérico; útil para contrastar hipótesis relacionadas con magmatismo, sin asumir que cualquier granitoide es fértil.',
    16: 'Encajantes siliciclásticos/metasedimentarios: posible contexto de vetas y cizallas; necesita estructura, cronología y señal geoquímica.',
    18: 'Contexto máfico y ultramáfico; permite probar controles del encajante y contrastes litológicos sin asumir asociación universal con Au.',
    19: 'Contexto volcánico/volcanoclástico donde se pueden probar hipótesis hidrotermales; no informa sobre alteración ni fertilidad.',
}
ELEMENTS = {
    'au': ('oro', 'Señal del propio elemento objetivo en sedimentos; puede reflejar una fuente aurífera en la cuenca aportante. No localiza necesariamente el yacimiento en la celda y puede reflejar actividad minera previa.'),
    'as': ('arsénico', 'Elemento guía de ciertos sistemas auríferos hidrotermales; una asociación As-Au coherente con el contexto puede aportar evidencia indirecta. También existen anomalías de As sin Au.'),
    'sb': ('antimonio', 'Elemento guía en determinadas asociaciones hidrotermales con Au; su combinación con As y estructuras es una hipótesis más específica que Sb aislado.'),
    'bi': ('bismuto', 'Puede ayudar a reconocer asociaciones de Au vinculadas a intrusiones; su utilidad depende del tipo de sistema y del contexto geológico.'),
    'hg': ('mercurio', 'Puede aportar evidencia de determinados sistemas epitermales; deben distinguirse anomalías naturales de aportes mineros o ambientales.'),
    'cu': ('cobre', 'Permite probar asociaciones hidrotermales Cu-Au; muchas anomalías de Cu responden a otros procesos y no implican oro.'),
    'pb': ('plomo', 'Contexto de asociaciones polimetálicas que en ciertos sistemas acompañan Au; señal menos específica, sensible al fondo litológico y a actividad humana.'),
    'zn': ('zinc', 'Contexto de asociaciones polimetálicas; puede añadir información conjunta, aunque Zn elevado por sí solo no acredita Au.'),
    'w': ('wolframio', 'Puede acompañar sistemas hidrotermales relacionados con intrusiones; su asociación espacial con Au no exige correlación de concentraciones.'),
}


def main():
    pf = pq.ParquetFile(RUN/'Grid_Master_Au.parquet')
    columns = pf.schema_arrow.names
    pasted_paths = [Path('C:/Users/Lenovo/.codex/attachments/bea8ae25-585c-4a9d-a149-79f22e128f4d/Pasted text.txt'), Path('C:/Users/Lenovo/.codex/attachments/f89ed837-bbc9-4ce4-b57c-7c8af5972264/Pasted text.txt')]
    pasted = [ast.literal_eval(p.read_text(encoding='utf-8-sig')) for p in pasted_paths]
    xcols = pq.ParquetFile(RUN/'X_features.parquet').schema_arrow.names
    assert pasted[0] == columns, 'El primer listado no coincide con el maestro.'
    assert pasted[1] == xcols, 'El segundo listado no coincide con X.'
    roles = read_csv(RUN/'column_roles.csv').set_index('column').role.to_dict()
    metadata = read_csv(RUN/'feature_dictionary.csv').set_index('name').to_dict('index')
    allow = read_json(RUN/'feature_allowlist.json')
    assert set(metadata) == set(allow['candidate_columns']) == set(xcols)-{'cell_id'}
    lith = read_csv(RUN/'dictionaries/litologia.csv').set_index('category_id').description.to_dict()
    ages = read_csv(RUN/'dictionaries/edades.csv').set_index('category_id').description.to_dict()
    legends = read_csv(RUN/'dictionaries/geoquimica_leyendas_locales.csv')
    associations = read_csv(RUN/'dictionaries/asociaciones_litologicas.csv')
    qc = read_csv(RUN/'variables_qc.csv').set_index('variable')
    profiles = {}
    for start in range(0, len(columns), 12):
        frame = pf.read(columns=columns[start:start+12]).to_pandas()
        for col in frame:
            s = frame[col]
            valid = s.dropna()
            item = {'tipo': str(s.dtype), 'n_faltantes': int(s.isna().sum()), 'faltantes_pct': float(s.isna().mean()*100), 'n_distintos': int(valid.nunique())}
            if pd.api.types.is_numeric_dtype(s) or pd.api.types.is_bool_dtype(s):
                item['rango_o_ejemplos'] = f'{valid.min()} … {valid.max()}' if len(valid) else 'sin valores válidos'
            else:
                counts = s.value_counts(dropna=False).head(4)
                item['rango_o_ejemplos'] = '; '.join(f'{k}: {int(v):,}' for k,v in counts.items())
            if col in qc.index:
                assert abs(s.isna().mean()-qc.loc[col, 'missing_fraction']) < 1e-10
                assert valid.nunique() == qc.loc[col, 'n_unique']
            profiles[col] = item
        print(f'Perfiladas {min(start+12,len(columns))}/{len(columns)} columnas', flush=True)

    duplicate_checks = []
    for group, entries in associations.groupby('group', sort=False):
        derived = group+'_fraccion'
        inputs = [v+'_fraccion' for v in entries.category_id]
        f = pf.read(columns=[derived,*inputs]).to_pandas()
        expected = f[inputs].sum(axis=1, min_count=len(inputs)).astype('float32')
        assert f[derived].equals(expected)
        duplicate_checks.append({'derivada': derived, 'formula': ' + '.join(inputs), 'identidad_verificada': True, 'duplicado_simple':len(inputs)==1})
    f = pf.read(columns=['litologia_u012_fraccion','edades_u004_fraccion']).to_pandas()
    cross_duplicate = f.iloc[:,0].equals(f.iloc[:,1])
    constants = [c for c in xcols if c != 'cell_id' and profiles[c]['n_distintos'] <= 1]
    assert constants == ['zn_proporcion_clase_3', 'w_proporcion_clase_2']
    for col in constants:
        assert pf.read(columns=[col]).to_pandas()[col].dropna().eq(0).all()

    entries = []
    def add(c, family, meaning, units, rationale, caution, use=None, source=None):
        candidate = roles[c] == 'predictor_candidato'
        entries.append(dict(variable=c, familia=family, rol=roles[c], uso=use or ('Candidata; no aprobada' if candidate else 'Excluir de X'), significado=meaning, unidades=units, fundamento_predictivo=rationale, limitaciones=caution, fuente=source or (metadata[c]['source'] if candidate else 'Fases C/D; código y configuración'), metodo=metadata[c]['method'] if candidate else '', **profiles[c]))

    base = {
        'row': ('Índice de fila desde 0; aumenta hacia el sur.', 'índice', 'Permite reconstruir la rejilla; puede memorizar localización.'),
        'col': ('Índice de columna desde 0; aumenta hacia el este.', 'índice', 'Localiza la celda en la matriz; no representa un proceso geológico.'),
        'cell_id': ('Identificador único formado por versión de rejilla, fila y columna.', 'texto', 'Clave de unión y trazabilidad; nunca una magnitud geológica.'),
        'x_center': ('Coordenada este del centro: -50000 + (col + 0,5) × 1000.', 'm; EPSG:25830', 'Localización espacial; usar para mapas y evaluación espacial, no como predictor autorizado.'),
        'y_center': ('Coordenada norte del centro: 4860000 - (row + 0,5) × 1000.', 'm; EPSG:25830', 'Localización espacial; no es latitud y puede codificar provincias de exploración.'),
        'land_area_m2': ('Superficie terrestre de la celda según la máscara candidata.', 'm²', 'Denominador para agregaciones; mide soporte territorial.'),
        'land_fraction': ('land_area_m2 / 1000000; fracción terrestre del cuadrado de 1 km.', 'fracción 0–1', 'Describe costa y bordes de la máscara, no fertilidad.'),
        'coastal_eligible': ('Verdadero cuando land_fraction ≥ 0,5.', 'booleano', 'Filtro de soporte mínimo costero; no una probabilidad de oro.'),
        'diagnostic_block': ('Bloque de diagnóstico de 50 × 50 km, construido con fila y columna.', 'categoría espacial', 'Agrupa diagnósticos de cobertura; no es automáticamente un fold de validación.'),
        'partition_id': ('División entera row // 100; organiza franjas de 100 filas en el Parquet particionado.', 'entero', 'Partición de almacenamiento, sin significado metalogenético ni función de validación por sí misma.'),
    }
    for c in columns:
        if c in base:
            meaning,unit,note = base[c]
            add(c,'Identificación y soporte territorial',meaning,unit,'No se propone como predictor geológico.',note)
        elif c in ('n_candidatos','n_positivos_revisados','estado_etiqueta'):
            meanings = {'n_candidatos':'Número de registros de indicios candidatos asignados a la celda; puede haber varios del mismo depósito.', 'n_positivos_revisados':'Número de registros con positivo_revisado verdadero asignados a la celda.', 'estado_etiqueta':'P_revisado si n_positivos_revisados > 0; candidato_no_revisado si solo hay candidatos; U si no hay registros candidatos.'}
            add(c,'Etiquetas',meanings[c],'conteo' if c != 'estado_etiqueta' else 'categoría','Sirve para construir y auditar la respuesta objetivo, no para explicarla.','Incluirla en X filtra información de la etiqueta. U significa no etiquetado, no ausencia de oro.')
        elif c.startswith(('litologia_', 'edades_')) and roles[c] != 'predictor_candidato':
            family, suffix = c.split('_',1)
            meaning = {'cobertura':'Área de unión de polígonos de la familia / área terrestre de la celda.', 'solape_fraccion':'Exceso de suma de áreas de categorías sobre área de unión, dividido por área terrestre; detecta conflicto entre categorías.', 'sin_atributo_fraccion':'Área de polígonos SIN_ATRIBUTO / área terrestre.'}[suffix]
            add(c,'Calidad geológica',meaning,'m²/m² terrestre','Controla si la extracción es utilizable.','No interpreta litología ni edad; filtrar/auditar fuera de X. El exceso de solape no tiene garantizado el límite 1 en cualquier conjunto de datos.')
        elif c in ('litologia_dominante','edades_dominante'):
            is_lith = c.startswith('litologia')
            add(c,'Litología' if is_lith else 'Edades','Código de la unidad con mayor área terrestre; empate resuelto por orden textual de categoría.','categoría nominal','Resume el encajante y dominio geológico.' if is_lith else 'Resume el dominio cronoestratigráfico cartografiado; permite contrastar asociaciones con historia geológica.','Los códigos uNNN no son rangos de favorabilidad ni edades numéricas. Pierde mezclas minoritarias; la edad de la roca no fecha la mineralización.')
        elif re.fullmatch(r'(litologia|edades)_u\d{3}_fraccion',c):
            key = c.removesuffix('_fraccion')
            is_lith = c.startswith('litologia')
            desc = (lith if is_lith else ages)[key]
            reason = LITH_REASON[int(key[-3:])] if is_lith else 'Distingue dominios y episodios de la historia geológica; su asociación con Au es una hipótesis contextual, no una relación monotónica con antigüedad.'
            if key == 'edades_u004': reason = 'Contexto cuaternario útil para plantear transporte, depósito y cobertura superficial; no identifica por sí solo un placer aurífero.'
            if key == 'edades_u008': reason = 'La leyenda vincula la unidad al plutonismo hercínico; permite probar contexto intrusivo, sin fechar el oro ni acreditar fertilidad.'
            add(c,'Litología' if is_lith else 'Edades',f'Fracción de área terrestre ocupada por la unidad «{desc}».','fracción 0–1',reason,'Intersección exacta con polígonos. Unidad cartográfica completa, no proporción de cada roca interna; NaN si falla cobertura/conflicto. Los intervalos de edad mixtos no se desagregan.')
        elif c.startswith('unidades_'):
            d = next(x for x in duplicate_checks if x['derivada']==c)
            relevant = associations[associations.group == c.removesuffix('_fraccion')]
            ids = list(relevant.category_id)
            add(c,'Asociaciones litológicas','Suma de fracciones de unidades: '+'; '.join(relevant.description)+'. Fórmula: '+d['formula']+'.','fracción 0–1',LITH_REASON[int(ids[0][-3:])],('Duplicado exacto de una fracción original; elegir una representación.' if d['duplicado_simple'] else 'Combinación determinista de fracciones existentes; no añade una medición independiente.')+' No estima el porcentaje interno de cada roca.')
        elif c.startswith('dist_') or c.startswith('dens_aprox_'):
            distance = c.startswith('dist_')
            group = c[5:-2] if distance else re.match(r'dens_aprox_(.+)_\d+m_km_km2', c)[1]
            hydro = group == 'cauce'
            kind = 'cauce' if hydro else ('contacto intrusivo' if group.startswith('contacto') else 'cabalgamiento' if group.startswith('cabalgamiento') else 'falla/cizalla')
            certainty = '' if hydro else (' supuesta/oculta' if group.endswith('supuesta') else ' cartografiada sin marcador textual de supuesta')
            reason = {'cauce':'Contextualiza transporte y acumulación detrítica; para Au aluvial importan además fuente aguas arriba, conectividad y trampas sedimentarias.', 'falla/cizalla':'Las fracturas y cizallas pueden conducir fluidos y localizar trampas estructurales para mineralización hidrotermal.', 'cabalgamiento':'Puede representar zonas de deformación y contactos que canalizan fluidos; la cronología respecto al oro es decisiva.', 'contacto intrusivo':'Puede aproximar interfaces entre intrusión y encajante asociadas a circulación hidrotermal y reacción roca-fluido.'}[kind]
            if distance:
                meaning = f'Distancia euclídea del centro de celda a la traza más próxima de {kind}{certainty}, buscada hasta 10000 m.'
                units = 'm'
                caution = 'NaN si no se encuentra traza en 10 km; no es distancia cero ni ausencia geológica. No se calcula desde el borde de la celda; la cobertura del levantamiento no está acreditada.'
            else:
                radius = re.search(r'_(\d+)m_km_km2$',c)[1]
                meaning = f'Longitud aproximada de {kind}{certainty} por superficie terrestre en una ventana de radio {radius} m.'
                units = 'km/km²'
                caution = 'Longitud exacta por celda de 1 km redistribuida uniformemente para la ventana circular; aproximación, especialmente sensible a 1 km. Cero significa sin longitud registrada, no ausencia acreditada.'
                reason += ' La densidad describe intensidad de la red a esa escala; no cuenta intersecciones ni conectividad.'
            add(c,'Hidrografía' if hydro else 'Estructuras',meaning,units,reason,caution)
        elif re.fullmatch(r'(au|as|sb|bi|hg|cu|pb|zn|w)_(clase_modal|proporcion_clase_\d+)',c):
            el = c.split('_')[0]
            name,reason = ELEMENTS[el]
            if c.endswith('clase_modal'):
                meaning = f'Clase de {name} con mayor área válida en la celda; empate a la clase menor. Códigos según la leyenda local reproducida en este informe.'
                units = 'índice de clase'
            else:
                k = int(c.rsplit('_',1)[1])
                leg = legends[(legends.element.str.lower()==el) & (legends['class']==k)].iloc[0]
                meaning = f'Fracción del área válida asignada a clase {k} de {name}; etiqueta local «{leg.label_local}». No son unidades de concentración verificadas.'
                units = 'fracción 0–1 del área válida'
            caution = 'Mapa clasificado a partir de RGB; leyenda, medio, extracción y unidades pendientes de validación en D. Exige ≥95 % de área válida. No es concentración puntual ni ley del mineral; clase 0 es válida.'
            use = None
            if c in constants:
                caution += ' En esta ejecución es 0 en todas las celdas no nulas: no discrimina valores; revisar paleta/rechazo RGB.'
                use = 'Candidata en lista; descartar como señal de valor constante'
            add(c,'Geoquímica',meaning,units,reason,caution,use)
        elif c in ('elevacion_media_m','pendiente_grados','tpi_1000m_m','tpi_5000m_m','desv_elevacion_1000m_m','desv_elevacion_5000m_m'):
            if c == 'elevacion_media_m':
                meaning = 'Media de elevación del MDT nativo de 500 m, ponderada por área terrestre válida dentro de la celda de 1 km.'
                reason = 'Contextualiza posición geomorfológica, exposición y nivel erosivo; puede también capturar diferencias regionales ajenas a mineralización.'
            elif c == 'pendiente_grados':
                meaning = 'Media terrestre de pendientes calculadas a 500 m con diferencias centrales: atan(raíz(dx²+dy²)), convertida a grados.'
                reason = 'Aproxima inclinación y procesos de erosión/transporte; puede ayudar en modelos aluviales junto con otras variables. No mide pendiente de cauce.'
            else:
                radius = re.search(r'_(\d+)m_m$',c)[1]
                tpi = c.startswith('tpi')
                meaning = (f'Elevación menos media de vecinos en radio {radius} m, incluyendo el centro; luego media terrestre a 1 km. Positivo: alto relativo; negativo: bajo relativo.' if tpi else f'Desviación estándar poblacional de elevaciones en radio {radius} m; luego media terrestre a 1 km. Mide variabilidad del relieve; no es error del MDT ni TRI.')
                reason = 'Describe posición relativa en laderas, valles y divisorias; posible contexto de transporte y acumulación.' if tpi else 'Resume contraste topográfico a esta escala; puede contextualizar erosión y relieve de cuenca sin identificar directamente Au.'
            add(c,'Relieve',meaning,'grados' if c=='pendiente_grados' else 'm',reason,'Soporte regional: derivados nativos de 500 m promediados a 1 km. TPI/desviación requieren ≥95 % de vecinos válidos; sin relación universal creciente con Au.')
        elif c.endswith('_sin_traza_en_10000m'):
            group = c.removesuffix('_sin_traza_en_10000m')
            add(c,'Calidad de trazas',f'Verdadero cuando no hay distancia finita a {group} dentro de 10000 m.','booleano','Indicador de búsqueda sin resultado; ayuda a interpretar el NaN de distancia.','No demuestra ausencia de estructura/cauce ni que la zona haya sido levantada. Excluido de la lista de predictores.')
        elif '_soporte_terrestre_' in c:
            radius = re.search(r'_(\d+)m$',c)[1]
            add(c,'Soporte de vecindario',f'Área terrestre ponderada de la ventana de radio {radius} m dividida por el área de la ventana discretizada usada en densidades.','fracción ≈0–1','Controla el denominador efectivo junto a costas y límites.','No mide porcentaje de estructuras/cauces observados ni cobertura de campaña; pequeñas desviaciones numéricas pueden deberse a la convolución.')
        elif c.endswith('_cobertura_levantamiento_acreditada'):
            add(c,'Calidad de levantamiento','Bandera de acreditación de cobertura del levantamiento estructural o hidrográfico; el código la fija en falso.','booleano','Control científico de disponibilidad, sin señal geológica.','Falso no significa territorio sin fallas/cauces. Es constante en esta ejecución.')
        elif c.startswith('geoquimica_') and c.endswith('_valid_rgb'):
            el = c.split('_')[1]
            add(c,'Calidad geoquímica',f'Fracción del área terrestre con clase y RGB aceptados para {ELEMENTS[el][0]}.','fracción 0–1','Determina si puede conservarse la variable geoquímica.','RGB compatible no prueba leyenda correcta. Tolerancia euclídea 2 y margen mínimo 10 frente al segundo color; umbral de área 0,95.')
        elif c.endswith('_valid_fraction'):
            name = c.removesuffix('_valid_fraction')
            add(c,'Calidad de relieve',f'Área terrestre con valor finito de {name} / área terrestre total de la celda.','fracción 0–1','Controla la aceptación del agregado de relieve.','No es relieve, pendiente ni rugosidad; exige ≥0,95 para conservar el predictor.')
        elif c.startswith('fase_c_valid_'):
            alias = c.removeprefix('fase_c_valid_')
            polygon = alias in ('litologia','edades','recintos')
            meaning = f'Fracción de soporte de {alias} heredada de C: '+('ocupación por polígonos estimada a 500 m y ponderada por tierra.' if polygon else 'área terrestre con píxeles considerados válidos en la armonización de C.')
            add(c,'Cobertura heredada de C',meaning,'fracción 0–1','Diagnóstico de cobertura previo a la extracción de predictores en D.','No es booleano pese a valid_. No incorpora todos los controles posteriores de D; en geoquímica no sustituye valid_rgb; en geología no sustituye intersecciones exactas y conflictos.')
        elif c == 'fase_c_coverage_code':
            add(c,'Cobertura heredada de C','Código: 1 costera con tierra <50 %; 2 geología, relieve y los nueve elementos con soporte ≥95 %; 3 geología y relieve suficientes sin los nueve elementos completos; 4 soporte insuficiente.','código 1–4','Resume reglas de soporte para diagnóstico.','Categoría administrativa de cobertura, no orden de probabilidad de oro. La regla costera tiene prioridad; recintos no interviene en este código.')
        elif c == 'fase_c_coverage_decision':
            add(c,'Cobertura heredada de C','Texto equivalente al código C: costera_baja_fraccion, soporte_basico_candidato, candidato_reducido_sin_geoquimica_completa o soporte_insuficiente.','categoría','Facilita interpretar decisiones de soporte.','Redundante con fase_c_coverage_code; excluir de X.')
        elif c in ('fase_c_prediction_allowed','prediction_allowed'):
            add(c,'Estado de validación','Bandera de permiso científico de predicción; heredada de C.' if c.startswith('fase_c') else 'Bandera final de permiso científico de predicción de D, fijada en falso.','booleano','Expresa el estado del proceso de revisión.','No es probabilidad ni resultado del modelo. En la ejecución examinada todas las celdas tienen falso.')
        elif c.startswith('fase_c_entity_present_'):
            layer = c.removeprefix('fase_c_entity_present_')
            add(c,'Capas adicionales: presencia',f'Indica si hay alguna entidad de {layer} en la celda rasterizada; valores 0/1.','indicador 0/1','Inventario de disponibilidad, no propiedad física.','No mide campo magnético, radiactividad, resistividad, densidad, buzamiento ni petrofísica; no acredita cobertura total. Puede reproducir sesgo de campañas.')
        elif c.startswith('fase_c_footprint_'):
            layer = c.removeprefix('fase_c_footprint_')
            add(c,'Capas adicionales: huella',f'Fracción estimada de área terrestre cubierta por polígonos de {layer}, rasterizados a 500 m.','fracción 0–1','Diagnóstico espacial de huella de una capa.','No codifica la edad/tipología específica de depósitos cuaternarios ni la identidad de zona GEODE; no es cobertura acreditada de investigación.')
        elif c.startswith('eligible_'):
            meaning = 'coastal_eligible y valores no nulos de litologia_dominante, edades_dominante, elevacion_media_m y pendiente_grados.'
            if c != 'eligible_geology_terrain': meaning += ' Además, clases modales no nulas de '+('Au, As, Sb y Bi.' if c=='eligible_geo4' else 'Au, As, Sb, Bi, Hg, Cu, Pb, Zn y W.')
            add(c,'Elegibilidad técnica',meaning,'booleano','Selecciona celdas con soporte para un conjunto concreto.','No significa favorable para Au ni valida entrenamiento. No garantiza disponibilidad de TPI, desviaciones ni distancias estructurales.')
        else:
            raise ValueError('Columna sin explicar: '+c)

    assert [e['variable'] for e in entries] == columns
    assert len(entries) == len(set(columns)) == 245
    pd.DataFrame(entries).to_csv(BASE/'diccionario_245_variables.csv', index=False, encoding='utf-8-sig')
    pd.DataFrame(duplicate_checks).to_csv(BASE/'redundancias_verificadas.csv', index=False, encoding='utf-8-sig')

    overview = (BASE/'contenido.md').read_text(encoding='utf-8')
    family_counts = pd.DataFrame(entries).groupby(['familia','rol'],sort=False).size()
    overview = overview.replace('{{FAMILIAS}}',table(['Familia','Rol','Columnas'],[(a,b,n) for (a,b),n in family_counts.items()]))
    support = read_csv(RUN/'soporte_modelos.csv')
    overview = overview.replace('{{SOPORTE}}',table(['Criterio','Celdas','% del maestro','Registros candidatos'],[(r.criterion,f'{r.cells:,}',f'{100*r.cells/pf.metadata.num_rows:.2f} %',r.candidate_records) for r in support.itertuples()]))
    overview = overview.replace('{{REDUNDANCIAS}}',table(['Variable derivada','Identidad comprobada'],[(r['derivada'],r['formula']) for r in duplicate_checks]))
    overview = overview.replace('{{DUPLICADO_CRUZADO}}','También se ha comprobado igualdad exacta, incluidos los nulos, entre `edades_u004_fraccion` (CUATERNARIO) y `litologia_u012_fraccion` (Gravas, conglomerados, arenas y limos).' if cross_duplicate else 'La fracción de Cuaternario y la de gravas no son exactamente iguales en todas las celdas; no deben declararse duplicadas.')
    overview = overview.replace('{{LEYENDAS}}',table(['Elemento','Clase','Etiqueta local (unidades no validadas)'],[(r.element,r._1,r.label_local) for r in legends.itertuples(index=False)]))
    groups = list(dict.fromkeys(e['familia'] for e in entries))
    dictionary_md = []
    for family in groups:
        dictionary_md.append('## '+family+' — diccionario completo\n')
        for e in (entry for entry in entries if entry['familia'] == family):
            dictionary_md.append(f"### `{e['variable']}`\n\n**Rol y uso:** {e['rol']}; {e['uso']}.\n\n**Qué significa:** {e['significado']}\n\n**Unidades:** {e['unidades']}.\n\n**Por qué puede predecir o por qué se excluye:** {e['fundamento_predictivo']}\n\n**Límites:** {e['limitaciones']}\n\n**Datos observados:** {e['faltantes_pct']:.2f} % nulos; {e['n_distintos']:,} valores distintos no nulos. Rango o valores más frecuentes: {e['rango_o_ejemplos']}.\n\n**Procedencia:** {e['fuente']}." + (f" Método registrado: {e['metodo']}." if e['metodo'] else '')+'\n')
    content = overview.replace('{{DICCIONARIO}}','\n'.join(dictionary_md))
    assert '{{' not in content
    (BASE/(STEM+'.md')).write_text(content,encoding='utf-8')
    # Reutiliza únicamente el lector Markdown local, sin ejecutar su main ni modificarlo.
    spec = importlib.util.spec_from_file_location('report_renderer',ROOT/'informes/analisis_codigo_20260910/generar_informe.py')
    renderer = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(renderer)
    page = renderer.render_html(content)
    page = page.replace('GeoAI — Informe de código y notebooks','GeoAI — Variables de Grid Master Au').replace('GeoAI · revisión técnica','GeoAI · Grid Master Au')
    toolbar = '<div class="toolbar"><button onclick="window.print()">Imprimir / guardar PDF</button><input id="variable-search" type="search" placeholder="Buscar una variable o concepto…" aria-label="Buscar en el diccionario"><span id="search-count" aria-live="polite"></span></div>'
    page = re.sub(r'<div class="toolbar">.*?</div><p class="hint">.*?</p>',toolbar+'<p class="hint">245 columnas · 168 candidatas · 496.855 celdas. Informe local, sin conexión. El buscador filtra las fichas del diccionario.</p>',page,count=1)
    # Agrupa cada ficha en una sección para filtrado. Las secciones generales permanecen visibles.
    page = re.sub(r'(<h3 id="[^"]+"><code>.*?)(?=<h[23] |</main>)',r'<section class="variable-card">\1</section>',page,flags=re.S)
    script = '''<script>
const cards=[...document.querySelectorAll('.variable-card')];
const search=document.getElementById('variable-search');
const norm=s=>s.normalize('NFD').replace(/[\u0300-\u036f]/g,'').toLowerCase();
function filterCards(){const q=norm(search.value);let n=0;for(const c of cards){c.hidden=!norm(c.textContent).includes(q);if(!c.hidden)n++;}document.getElementById('search-count').textContent=n+' / '+cards.length+' fichas';}
search.addEventListener('input',filterCards);filterCards();
window.addEventListener('beforeprint',()=>cards.forEach(c=>c.hidden=false));
window.addEventListener('afterprint',filterCards);
</script><style>.variable-card{border-bottom:1px solid #d8e3df;padding:4px 0 20px}input[type=search]{padding:10px;min-width:290px;max-width:100%;border:1px solid #9ebbb1;border-radius:5px}#search-count{font-size:13px;align-self:center}h3{scroll-margin-top:20px}@media print{.variable-card{break-inside:auto}h3{break-after:avoid}.variable-card p{orphans:3;widows:3}}</style>'''
    page = page.replace('</body>',script+'</body>')
    assert page.count('class="variable-card"') == 245
    (BASE/(STEM+'.html')).write_text(page,encoding='utf-8')
    used_files = [RUN/name for name in ['Grid_Master_Au.parquet','X_features.parquet','column_roles.csv','feature_dictionary.csv','feature_allowlist.json','variables_qc.csv','soporte_modelos.csv','control_cierre.json','config_snapshot.json','grid_spec.json','features_source.py','dictionaries/litologia.csv','dictionaries/edades.csv','dictionaries/geoquimica_leyendas_locales.csv','dictionaries/asociaciones_litologicas.csv']]
    used_files += [ROOT/p for p in ['src/geoau/territory.py','src/geoau/additional_layers.py','src/geoau/features.py','src/geoau/training.py']]
    hashes=[]
    for p in used_files:
        digest=hashlib.file_digest(p.open('rb'),'sha256').hexdigest()
        hashes.append({'path':p.relative_to(ROOT).as_posix(),'bytes':p.stat().st_size,'sha256':digest})
    control={'run':RUN.relative_to(ROOT).as_posix(),'fecha_informe':'2026-09-25','filas':pf.metadata.num_rows,'columnas':len(columns),'candidatas':len(metadata),'aprobadas':len(allow['approved_training_columns']),'roles':pd.Series(roles).value_counts().to_dict(),'listados_usuario_coinciden_en_orden':True,'columnas_explicadas':len(entries),'qc_recalculado_coincide':True,'constantes_candidatas':constants,'identidades_derivadas_verificadas':duplicate_checks,'duplicado_cuaternario_gravas':cross_duplicate,'fuentes':hashes,'alcance':'Descripción y perfilado; sin entrenar, medir importancia predictiva ni auditar todos los archivos del manifiesto D.'}
    (BASE/'control_informe.json').write_text(json.dumps(control,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps({k:v for k,v in control.items() if k not in ('fuentes','identidades_derivadas_verificadas')},ensure_ascii=False,indent=2))


if __name__ == '__main__':
    main()
