"""Fase B: conciliación auditable, QC y etiquetas candidatas/revisadas.

No deduce depósitos independientes ni ausencias a partir de proximidad o de omisión de Au.
"""
from __future__ import annotations
from datetime import datetime, timezone
from pathlib import Path
from itertools import combinations
import hashlib
import json
import re
import unicodedata

import geopandas as gpd
import numpy as np
import pandas as pd
from pyproj import Geod
from shapely.geometry import Point
import rasterio
import yaml

from .local_sources import (local_path, read_table, read_vector, verify_unchanged,
                           sha256_file, write_json, environment_info)

GEOD = Geod(ellps='WGS84')
REVIEW_FIELDS = ['record_id', 'estado_presencia', 'estado_geometria', 'tipo_au_revisado',
                 'deposit_id', 'district_id', 'lon_corregida', 'lat_corregida',
                 'precision_m', 'revisor', 'fecha_revision', 'evidencia', 'motivo']


def normalize(value, null_tokens=('', 'null', 'none', 'nan', 's/d', 'sin datos')):
    if value is None or pd.isna(value):
        return None
    text = re.sub(r'\s+', ' ', unicodedata.normalize('NFKC', str(value))).strip()
    return None if text.casefold() in null_tokens else text


def key(value):
    value = normalize(value)
    if value is None:
        return ''
    return ''.join(c for c in unicodedata.normalize('NFKD', value.casefold()) if not unicodedata.combining(c))


def substance_tokens(value):
    # No divide '/', que forma parte de descripciones como 'Tierras raras / Monacita'.
    return sorted({key(v) for v in re.split(r'[,;|]', normalize(value) or '') if key(v)})


def load_phase_a(root, config):
    base = local_path(root, 'reports/fase_a')
    if config['phase_a_run']:
        candidates = [local_path(root, config['phase_a_run'])]
    else:
        candidates = sorted(base.glob('*'), reverse=True)
    for run in candidates:
        control = run / 'control_cierre.json'
        if not control.is_file():
            continue
        status = json.loads(control.read_text(encoding='utf-8'))
        if status.get('estado') == 'carga_local_completada' and status.get('hashes_completos'):
            break
    else:
        raise RuntimeError('Ejecuta primero 00: no hay una fase A satisfactoria con hashes.')
    manifest = json.loads((run / 'manifest.json').read_text(encoding='utf-8'))
    snapshot = json.loads((run / 'config_snapshot.json').read_text(encoding='utf-8'))
    # Se verifican todas las fuentes de la fase A, no solo la fecha del archivo.
    changes = verify_unchanged(root, manifest['sources'], rehash=True)
    if changes:
        raise RuntimeError(f'Fuentes cambiadas desde fase A; ejecutar 00 de nuevo: {changes}')
    expected = [snapshot['canonical_candidates']['indicios'], 'IndiciosII.csv', 'Indicios.xlsx']
    indexed = {row['path']: row for row in manifest['sources']}
    for path in expected:
        if path not in indexed or indexed[path]['status'] in ('error', 'sin_datos'):
            raise RuntimeError(f'Fuente requerida ausente o no válida en manifiesto: {path}')
    layers = indexed[expected[0]]['details']['layers']
    if len(layers) != 1:
        raise ValueError('La base de indicios requiere una capa inequívoca en fase A.')
    frames = {
        'gpkg': read_vector(local_path(root, expected[0]), layer=layers[0]['table_name'], max_features=None, allow_full=True),
        'csv': read_table(local_path(root, expected[1]), nrows=None),
        'excel': read_table(local_path(root, expected[2]), nrows=None),
    }
    for name, frame in frames.items():
        needed = {'Codigo_indicio', 'Sustancia', 'X', 'Y', 'Morfologia', 'Nombre_mina', 'Provincia', 'Municipio'}
        if not needed.issubset(frame.columns):
            raise ValueError(f'{name}: faltan {needed - set(frame.columns)}')
    return run, manifest, snapshot, frames


def reconcile(frames, gold_tokens=('oro', 'au')):
    """Una fila por código; compara conjuntos sin multiplicar registros por joins."""
    indices, duplicates = {}, []
    for source, frame in frames.items():
        data = pd.DataFrame(frame.drop(columns='geometry', errors='ignore')).copy()
        data['code'] = data['Codigo_indicio'].map(normalize)
        indices[source] = {}
        for code, group in data.groupby('code', dropna=False, sort=False):
            if pd.isna(code):
                code = '__CODIGO_AUSENTE__'
            indices[source][code] = group
            if len(group) > 1:
                for idx, record in group.iterrows():
                    duplicates.append({'source': source, 'source_row': int(idx), 'code': code,
                                       'Sustancia': record['Sustancia'], 'X': record['X'], 'Y': record['Y']})
    result = []
    codes = sorted(set().union(*(set(x) for x in indices.values())))
    for code in codes:
        row = {'Codigo_indicio': code}
        values = {}
        gold_states = set()
        for source, groups in indices.items():
            group = groups.get(code)
            row[f'n_{source}'] = 0 if group is None else len(group)
            if group is None:
                continue
            values[source] = {}
            for field in ('Sustancia', 'Nombre_mina', 'Provincia', 'Municipio', 'Morfologia', 'X', 'Y'):
                vals = sorted({('|'.join(substance_tokens(v)) if field == 'Sustancia' else key(v)) for v in group[field]})
                values[source][field] = vals
                row[f'{field}_{source}'] = json.dumps(vals, ensure_ascii=False)
            source_states = {bool(set(substance_tokens(v)) & set(gold_tokens)) for v in group.Sustancia}
            gold_states.update(source_states)
            row[f'au_{source}'] = any(source_states)
            row[f'au_mixto_{source}'] = len(source_states) > 1
        row['solo_en'] = next(iter(values)) if len(values) == 1 else ''
        row['fuentes_presentes'] = '|'.join(values)
        for field in ('Sustancia', 'Nombre_mina', 'Provincia', 'Municipio', 'Morfologia', 'X', 'Y'):
            row[f'difiere_{field}'] = len({tuple(v[field]) for v in values.values()}) > 1
        # Ausencia de Au en una copia NO prueba ausencia real de oro.
        row['conflicto_au'] = len(gold_states) > 1
        row['duplicado_codigo'] = any(row[f'n_{src}'] > 1 for src in indices)
        result.append(row)
    return pd.DataFrame(result), pd.DataFrame(duplicates, columns=['source','source_row','code','Sustancia','X','Y'])


def normalize_indicios(gdf, config):
    if gdf.crs is None:
        raise ValueError('No se pueden validar coordenadas sin CRS de origen.')
    # Conserva atributos originales y WKT antes de cualquier transformación/corrección.
    raw = gdf.rename(columns={c: c + '_raw' for c in gdf.columns if c != gdf.geometry.name}).copy()
    raw['geometry_wkt_raw'] = gdf.geometry.to_wkt()
    raw['source_crs'] = str(gdf.crs)
    raw = raw.to_crs(4326).reset_index(drop=True)
    raw['source_row'] = np.arange(len(raw))
    fingerprint = config.get('source_sha256')
    if not fingerprint:
        raise ValueError('Indica source_sha256 del manifiesto fase A para vincular IDs y revisiones a esta copia.')
    raw['source_sha256'] = fingerprint
    raw['record_id'] = ['gpkg:' + fingerprint + ':' + str(i) for i in raw.source_row]
    for field in ('Codigo_indicio', 'Sustancia', 'Morfologia', 'Nombre_mina', 'Provincia', 'Municipio', 'Zona_Geode'):
        source = raw.get(field + '_raw', pd.Series(None, index=raw.index))
        raw[field] = source.map(lambda v: normalize(v, config['null_tokens']))
    raw['codigo_duplicado'] = raw.Codigo_indicio.duplicated(keep=False) | raw.Codigo_indicio.isna()
    raw['sustancias_tokens'] = raw.Sustancia.map(lambda v: '|'.join(substance_tokens(v)))
    raw['au_observado'] = raw.Sustancia.map(lambda v: bool(set(substance_tokens(v)) & set(config['gold_tokens'])))
    raw['label_observada'] = np.where(raw.au_observado, 'P', 'U')
    raw['au_unica_sustancia'] = raw.Sustancia.map(lambda v: bool(substance_tokens(v)) and set(substance_tokens(v)).issubset(config['gold_tokens']))
    raw['rol_au_principal'] = 'no_determinado'  # el orden de Sustancia no acredita prioridad
    raw['tipo_au_propuesto'] = raw.Morfologia.map(lambda v: {'aluvionar': 'aluvial', 'filoniana': 'roca'}.get(key(v), 'desconocido'))
    raw.loc[~raw.au_observado, 'tipo_au_propuesto'] = 'no_aplica'
    raw['sistema_mineral'] = 'no_determinado'  # filoniano no equivale a orogénico
    return raw


def apply_reviews(gdf, review=None):
    out = gdf.copy()
    for field in REVIEW_FIELDS[1:]:
        out[field] = ''
    if review is None or review.empty:
        return out, pd.DataFrame(columns=['record_id', 'campo', 'valor_anterior', 'valor_nuevo', 'evidencia'])
    if not set(REVIEW_FIELDS).issubset(review.columns):
        raise ValueError('El CSV de revisión debe conservar todas las columnas de la plantilla.')
    if review.record_id.duplicated().any() or not set(review.record_id).issubset(out.record_id):
        raise ValueError('IDs de revisión duplicados o no pertenecientes a esta versión de indicios.')
    changes = []
    allowed = {'estado_presencia': {'', 'confirmada', 'rechazada', 'pendiente'},
               'estado_geometria': {'', 'validada', 'rechazada', 'pendiente'},
               'tipo_au_revisado': {'', 'roca', 'aluvial', 'mixto', 'desconocido'}}
    by_id = out.set_index('record_id').index
    for record in review.to_dict('records'):
        record = {k: normalize(v) or '' for k, v in record.items()}
        substantive = any(record[f] for f in REVIEW_FIELDS[1:] if f not in ('revisor','fecha_revision','evidencia','motivo'))
        if not substantive:
            continue
        for field, choices in allowed.items():
            if record[field] not in choices:
                raise ValueError(f'{record["record_id"]}: valor no permitido en {field}.')
        if not all(record[f] for f in ('revisor', 'fecha_revision', 'evidencia', 'motivo')):
            raise ValueError('Una decisión requiere revisor, fecha, evidencia y motivo.')
        datetime.fromisoformat(record['fecha_revision'])
        idx = by_id.get_loc(record['record_id'])
        lon, lat = record['lon_corregida'], record['lat_corregida']
        if bool(lon) != bool(lat):
            raise ValueError('Las coordenadas corregidas requieren longitud Y latitud.')
        if lon:
            x, y = float(lon), float(lat)
            if not np.isfinite([x, y]).all() or not (-180 <= x <= 180 and -90 <= y <= 90):
                raise ValueError('Coordenadas corregidas fuera de rango.')
            if record['estado_geometria'] != 'validada':
                raise ValueError('Una corrección necesita estado_geometria=validada y evidencia.')
            changes.append({'record_id': record['record_id'], 'campo': 'geometry',
                            'valor_anterior': out.geometry.iloc[idx].wkt if out.geometry.iloc[idx] is not None else None,
                            'valor_nuevo': Point(x, y).wkt, 'evidencia': record['evidencia']})
            out.at[idx, 'geometry'] = Point(x, y)
        if record['precision_m']:
            precision = float(record['precision_m'])
            if not np.isfinite(precision) or precision < 0:
                raise ValueError('precision_m debe ser finita y no negativa.')
        for field in REVIEW_FIELDS[1:]:
            out.at[idx, field] = record[field]
            if record[field]:
                changes.append({'record_id': record['record_id'], 'campo': field, 'valor_anterior': '',
                                'valor_nuevo': record[field], 'evidencia': record['evidencia']})
    return out, pd.DataFrame(changes, columns=['record_id','campo','valor_anterior','valor_nuevo','evidencia'])


def geometry_qc(gdf, config, mask=None, admin=None):
    out = gdf.copy()
    point = out.geometry.notna() & ~out.geometry.is_empty & out.geometry.is_valid & out.geom_type.eq('Point')
    out['lon'] = np.nan
    out['lat'] = np.nan
    out.loc[point, 'lon'] = out.loc[point].geometry.x
    out.loc[point, 'lat'] = out.loc[point].geometry.y
    finite = np.isfinite(out.lon) & np.isfinite(out.lat) & out.lon.between(-180,180) & out.lat.between(-90,90)
    plausible = pd.Series(False, index=out.index)
    for xmin, ymin, xmax, ymax in config['plausibility_boxes_lonlat']:
        plausible |= out.lon.between(xmin,xmax) & out.lat.between(ymin,ymax)
    out['geometria_basica_ok'] = point & finite & plausible
    out['territorio_estado'] = 'pendiente_mascara'
    if mask is not None:
        if mask.empty or mask.crs is None or not mask.geom_type.isin(['Polygon','MultiPolygon']).all() or not mask.is_valid.all():
            raise ValueError('La máscara debe contener polígonos válidos con CRS.')
        hits = gpd.sjoin(out.loc[point, ['geometry']], mask.to_crs(4326)[['geometry']], predicate='intersects', how='inner')
        out['territorio_estado'] = np.where(out.index.isin(hits.index), 'dentro_mascara', 'fuera_mascara')
    out['provincia_estado'] = 'pendiente_limites'
    out['municipio_estado'] = 'pendiente_limites'
    if admin is not None:
        if admin.crs is None or admin.empty or not admin.geom_type.isin(['Polygon','MultiPolygon']).all() or not admin.is_valid.all():
            raise ValueError('Los límites administrativos requieren polígonos válidos con CRS.')
        fields = [config['admin_province_column'], config['admin_municipality_column']]
        if any(not f or f not in admin for f in fields):
            raise ValueError('Configura columnas de provincia y municipio existentes.')
        renamed = admin[fields + ['geometry']].rename(columns={fields[0]: 'prov_ref', fields[1]: 'mun_ref'}).to_crs(4326)
        hits = gpd.sjoin(out.loc[point, ['geometry']], renamed, predicate='intersects', how='left')
        for idx, group in hits.groupby(level=0):
            for original, reference, output in [('Provincia','prov_ref','provincia_estado'), ('Municipio','mun_ref','municipio_estado')]:
                options = {key(v) for v in group[reference] if key(v)}
                out.at[idx, output] = ('sin_cobertura' if not options else 'ambiguo_limite' if len(options)>1
                    else 'sin_atributo' if not key(out.at[idx, original]) else 'coincide' if key(out.at[idx, original]) in options else 'discrepa')
    x = pd.to_numeric(out['X_raw'], errors='coerce')
    y = pd.to_numeric(out['Y_raw'], errors='coerce')
    comparable = x.between(-180,180) & y.between(-90,90) & point & finite
    out['xy_estado'] = np.where(x.isna() | y.isna(), 'faltante_no_numerico', 'crs_tabular_desconocido')
    out['xy_distancia_m_si_lonlat'] = np.nan
    ids = out.index[comparable]
    if len(ids):
        _, _, distances = GEOD.inv(x.loc[ids].to_numpy(), y.loc[ids].to_numpy(), out.loc[ids, 'lon'].to_numpy(), out.loc[ids, 'lat'].to_numpy())
        out.loc[ids, 'xy_distancia_m_si_lonlat'] = distances
        out.loc[ids, 'xy_estado'] = np.where(np.asarray(distances) > config['xy_discrepancy_m'], 'discrepa_si_lonlat', 'coincide_si_lonlat')
    out['geo_cuarentena'] = ~out.geometria_basica_ok | out.territorio_estado.eq('fuera_mascara') | out.estado_geometria.eq('rechazada')
    out['motivo_geo'] = np.select([~point, ~finite, ~plausible, out.territorio_estado.eq('fuera_mascara'), out.estado_geometria.eq('rechazada')],
                                  ['geometria_nula_vacia_invalida_no_punto', 'coordenada_no_finita_o_fuera_rango', 'fuera_ventanas_plausibles', 'fuera_mascara', 'rechazada_por_revisor'],
                                  default='sin_fallo_basico; contrastes territoriales según estado')
    # No se corrige la geometría por discrepancias con X/Y: su CRS no está acreditado.
    return out


def short_id(prefix, members):
    return prefix + hashlib.sha256('|'.join(sorted(members)).encode()).hexdigest()[:16]


def group_candidates(au, radii=(250,500,1000)):
    """Componentes conexas geodésicas. Una cadena puede superar el radio extremo a extremo."""
    out = au.copy()
    valid = out.geometria_basica_ok & ~out.geo_cuarentena & ~out.estado_presencia.eq('rechazada')
    out['position_id'] = None
    for idx in out.index[valid]:
        out.at[idx, 'position_id'] = short_id('pos_', [float(out.at[idx,'lon']).hex(), float(out.at[idx,'lat']).hex()])
    data = out.loc[valid].sort_values('record_id')
    ids = data.record_id.tolist()
    edges = []
    lon, lat = data.lon.to_numpy(), data.lat.to_numpy()
    for i in range(len(data)-1):
        n = len(data)-i-1
        _, _, distance = GEOD.inv(np.full(n,lon[i]), np.full(n,lat[i]), lon[i+1:], lat[i+1:])
        for off in np.flatnonzero(np.asarray(distance) <= max(radii)):
            edges.append((i, i+1+int(off), float(distance[off])))
    summaries = []
    for radius in radii:
        parent = list(range(len(ids)))
        def find(i):
            while parent[i] != i:
                parent[i] = parent[parent[i]]
                i = parent[i]
            return i
        for i,j,d in edges:
            if d <= radius:
                parent[find(j)] = find(i)
        groups = {}
        for i, rid in enumerate(ids):
            groups.setdefault(find(i), []).append(rid)
        mapping = {rid: short_id(f'prox{radius}_', members) for members in groups.values() for rid in members}
        out[f'proximity_group_{radius}m'] = out.record_id.map(mapping)
        summaries.append({'radio_m': radius, 'registros_localizables': len(data), 'componentes_proximidad': len(groups),
                          'componente_mayor_registros': max(map(len, groups.values()), default=0), 'depositos_confirmados': None})
    pairs = pd.DataFrame([{'record_a': ids[i], 'record_b': ids[j], 'distance_m': d} for i,j,d in edges],
                         columns=['record_a','record_b','distance_m'])
    return out, pairs, pd.DataFrame(summaries)


def define_labels(au):
    out = au.copy()
    out['tipo_au_final'] = out.tipo_au_revisado.where(out.tipo_au_revisado.ne(''), out.tipo_au_propuesto)
    out['tipologia_estado'] = np.where(out.tipo_au_revisado.ne(''), 'revisada', 'propuesta_desde_morfologia')
    out['confianza_presencia'] = np.where(out.estado_presencia.eq('confirmada'), 'confirmada_documentalmente', 'inventario_sin_revision_individual')
    geo = out.geometria_basica_ok & ~out.geo_cuarentena & out.estado_geometria.eq('validada')
    confirmed = geo & out.estado_presencia.eq('confirmada') & ~out.codigo_duplicado
    out['elegible_general_revisada'] = confirmed
    out['elegible_roca_revisada'] = confirmed & out.tipo_au_revisado.eq('roca')
    out['elegible_aluvial_revisada'] = confirmed & out.tipo_au_revisado.eq('aluvial')
    out['label_au_final'] = np.where(confirmed, 'P', 'pendiente')
    out.loc[out.estado_presencia.eq('rechazada'), 'label_au_final'] = 'excluida_no_equivale_ausencia'
    # IDs de depósito/distrito provienen exclusivamente de revisión, no de clustering.
    out['deposit_id'] = out.deposit_id.replace('', None)
    out['district_id'] = out.district_id.replace('', None)
    return out


def coverage_at_points(au, raster_paths):
    rows = []
    usable = au.geometria_basica_ok & ~au.geo_cuarentena
    for alias, path in raster_paths.items():
        with rasterio.open(path) as src:
            if src.crs is None:
                raise ValueError(f'Ráster sin CRS: {path}')
            points = au.loc[usable].to_crs(src.crs)
            coords = list(zip(points.geometry.x, points.geometry.y))
            vals = list(src.sample(coords, indexes=1, masked=True))
            for idx, coord, value in zip(points.index, coords, vals):
                pixel_row, pixel_col = src.index(*coord)
                inside = 0 <= pixel_row < src.height and 0 <= pixel_col < src.width
                valid = inside and not bool(np.ma.getmaskarray(value)[0]) and bool(np.isfinite(value[0]))
                rows.append({'record_id': au.at[idx,'record_id'], 'fuente': alias,
                             'estado': 'valor_valido' if valid else 'nodata' if inside else 'fuera_extension'})
            for rid in au.loc[~usable, 'record_id']:
                rows.append({'record_id': rid, 'fuente': alias, 'estado': 'no_muestreada_geometria'})
    return pd.DataFrame(rows, columns=['record_id','fuente','estado'])


def review_template(au):
    template = au[['record_id','Codigo_indicio','Nombre_mina','Provincia','Municipio','Morfologia',
                   'tipo_au_propuesto','lon','lat','geo_cuarentena','xy_estado',
                   'position_id']].copy()
    for field in REVIEW_FIELDS[1:]:
        template[field] = au[field].fillna('') if field in au else ''
    return template


def export_phase_b(root, config, phase_a_run, manifest, normalized, au, reconciliation,
                   duplicates, changes, pairs, sensitivity, coverage, extra_inputs=None):
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    output = local_path(root, config['output_directory']) / stamp
    output.mkdir(parents=True, exist_ok=False)
    def csv(name, frame):
        frame.to_csv(output / name, index=False, encoding='utf-8-sig')
    def vector(name, frame, layer):
        if len(frame):
            serial = frame.copy()
            # GeoPackage no admite tipos Pandas StringDtype/nullable en todos los builds.
            for col in serial.columns.difference([serial.geometry.name]):
                if isinstance(serial[col].dtype, pd.StringDtype):
                    serial[col] = serial[col].astype(object).where(serial[col].notna(), None)
            serial.to_file(output / name, layer=layer, driver='GPKG', engine='pyogrio', index=False)
    csv('reconciliacion_indicios.csv', reconciliation)
    csv('duplicados_por_codigo_fuentes.csv', duplicates)
    csv('correcciones_coordenadas.csv', changes[changes.campo.eq('geometry')] if len(changes) else changes)
    csv('registro_decisiones_revision.csv', changes)
    csv('pares_proximidad_au.csv', pairs)
    csv('sensibilidad_agrupacion.csv', sensitivity)
    csv('cobertura_en_indicios_au.csv', coverage)
    csv('plantilla_revision.csv', review_template(au))
    csv('correspondencia_registros_grupos.csv', au[['record_id','Codigo_indicio','position_id','deposit_id','district_id'] + [c for c in au if c.startswith('proximity_group_')]])
    csv('indicios_normalizados.csv', normalized.drop(columns='geometry'))
    csv('etiquetas_au_candidatas.csv', au.drop(columns='geometry'))
    csv('cuarentena_geometria.csv', normalized.loc[normalized.geo_cuarentena].drop(columns='geometry'))
    vector('indicios_geometry_qc.gpkg', normalized, 'indicios_qc')
    vector('etiquetas_au_candidatas.gpkg', au, 'au_candidatas')
    reviewed = au[au.elegible_general_revisada]
    vector('etiquetas_au_revisadas.gpkg', reviewed, 'au_revisadas')
    province = au.groupby('Provincia', dropna=False).agg(registros=('record_id','size'), posiciones=('position_id','nunique'),
        grupos_proximidad=(f'proximity_group_{config["proposal_cluster_m"]}m','nunique'), depositos_con_id_revisado=('deposit_id','nunique')).reset_index()
    province['porcentaje_registros'] = province.registros / max(1,len(au)) * 100
    csv('representatividad_provincia.csv', province.sort_values('registros',ascending=False))
    csv('representatividad_tipologia.csv', au.groupby(['tipo_au_propuesto','tipologia_estado'],dropna=False).size().reset_index(name='registros'))
    csv('representatividad_distrito.csv', au.groupby('district_id',dropna=False).size().reset_index(name='registros'))
    csv('dominio_declarado_indicio.csv', au.groupby('Zona_Geode',dropna=False).size().reset_index(name='registros'))
    write_json(output / 'config_snapshot.json', config)
    write_json(output / 'environment.json', environment_info())
    write_json(output / 'inputs.json', {'phase_a_run': str(phase_a_run.relative_to(root)),
        'manifest_sha256': sha256_file(phase_a_run/'manifest.json'), 'additional_inputs': extra_inputs or [],
        'source_policy': 'GPKG canónico candidato según snapshot fase A; CSV y Excel solo contraste, sin concatenación'})
    write_json(output / 'code_manifest.json', [{'path': str(p.relative_to(root)), 'sha256': sha256_file(p)}
        for p in [local_path(root,'src/geoau/labels.py'), local_path(root,'src/geoau/local_sources.py')]])
    control = {'estado_ejecucion': 'pendiente_integridad_final', 'fase_b_cientifica_cerrada': False,
               'registros_base': len(normalized), 'registros_au_observados': int(normalized.au_observado.sum()),
               'registros_candidatos_incluyendo_confirmaciones': len(au),
               'posiciones_au_localizables': int(au.position_id.nunique()),
               'cuarentena_geometria_base': int(normalized.geo_cuarentena.sum()),
               'au_en_cuarentena': int(au.geo_cuarentena.sum()), 'positivos_revisados': len(reviewed),
               'depositos_con_id_revisado': int(au.deposit_id.nunique()),
               'celdas_positivas': None,
               'pendientes': ['Máscara y contraste administrativo según disponibilidad', 'Revisión documental de presencia, geometría y tipología',
                              'Agrupación geológica de depósitos y distritos', 'Celdas positivas: requieren rejilla de fase C',
                              'Reservas espaciales: definir tras agrupar depósitos; no se fijan por provincia']}
    write_json(output/'control_cierre.json', control)
    return output, control
