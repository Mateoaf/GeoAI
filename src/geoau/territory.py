"""Fase C: soporte territorial, armonización y diagnóstico, sin entrenar modelos.

La cobertura poligonal se estima a 500 m; las áreas terrestres se intersectan
exactamente con la máscara candidata en el CRS de trabajo. No se confunden.
"""
from datetime import datetime, timezone
from contextlib import closing
import ast
import hashlib
import json
from pathlib import Path
import sqlite3
import shutil
import warnings

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
from pyproj import CRS, Proj, Transformer
import rasterio
from rasterio.features import rasterize, shapes
from rasterio.transform import Affine
import shapely

from .local_sources import local_path, sha256_file, verify_unchanged, write_json, environment_info


def csv(path, frame):
    frame.to_csv(path, index=False, encoding='utf-8-sig')


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def start_run(root, config):
    """Usa la fase A enlazada por B, nunca otra ejecución más reciente."""
    b = local_path(root, config['phase_b_run'])
    control = read_json(b / 'control_cierre.json')
    if control.get('estado_ejecucion') != 'completada':
        raise ValueError('La ejecución B seleccionada no terminó íntegramente.')
    inputs_b = read_json(b / 'inputs.json')
    a = local_path(root, inputs_b['phase_a_run'])
    if sha256_file(a / 'manifest.json') != inputs_b['manifest_sha256']:
        raise ValueError('El manifiesto A enlazado por B ha cambiado.')
    manifest = read_json(a / 'manifest.json')
    changed = verify_unchanged(root, manifest['sources'], rehash=True)
    if changed:
        raise ValueError(f'Fuentes A modificadas: {changed}')
    for item in inputs_b['additional_inputs']:
        if sha256_file(local_path(root, item['path'])) != item['sha256']:
            raise ValueError(f'Entrada adicional B modificada: {item["path"]}')
    aliases = read_json(a / 'config_snapshot.json')['canonical_candidates']
    indexed = {r['path']: r for r in manifest['sources']}
    for alias, name in config.get('additional_vectors', {}).items():
        entry = indexed.get(name)
        if not entry or entry['status'] in ('error', 'sin_datos'):
            raise ValueError(f'{name}: actualizar fase A/B antes de incorporar una fuente no inventariada.')
        aliases[alias] = name
    paths = [b / n for n in ['control_cierre.json', 'inputs.json', 'config_snapshot.json',
             'etiquetas_au_candidatas.gpkg', 'cobertura_en_indicios_au.csv']]
    paths += [local_path(root, config['mask_path']), local_path(root, config['mask_metadata']),
              root / 'config/grid.yaml', root / 'src/geoau/territory.py',
              root / 'src/geoau/labels.py',
              root / 'src/geoau/additional_layers.py',
              root / 'src/geoau/local_sources.py', a / 'config_snapshot.json']
    frozen = [{'path': p.relative_to(root).as_posix(), 'sha256': sha256_file(p)} for p in paths]
    provenance = read_json(local_path(root, config['mask_metadata']))
    if sha256_file(local_path(root, config['mask_path'])) != provenance['sha256']:
        raise ValueError('Máscara distinta de su registro de procedencia.')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = local_path(root, config['output_directory']) / stamp
    out.mkdir(parents=True, exist_ok=False)
    (out / 'vectors').mkdir()
    (out / 'rasters').mkdir()
    write_json(out / 'config_snapshot.json', config)
    write_json(out / 'inputs.json', {'phase_a_run': str(a.relative_to(root)),
               'phase_b_run': str(b.relative_to(root)), 'frozen_inputs': frozen,
               'phase_b_output_hashes_note': 'B no selló sus salidas con hashes; se congelan al iniciar C.'})
    write_json(out / 'environment.json', environment_info())
    (out / 'territory_source.py').write_bytes((root / 'src/geoau/territory.py').read_bytes())
    write_json(out / 'control_cierre.json', {'estado_ejecucion': 'en_curso', 'fase_c_cientifica_cerrada': False})
    return out, aliases, manifest, frozen, gpd.read_file(b / 'etiquetas_au_candidatas.gpkg')


def grid_spec(config):
    s = dict(config)
    if CRS(s['crs']).to_epsg() != 25830 or s['scope'] != 'peninsula_componente_principal':
        raise ValueError('Esta versión solo implementa el ámbito peninsular en EPSG:25830.')
    if s['resolution_m'] != 1000 or s['native_resolution_m'] != 500:
        raise ValueError('Esta versión implementa agregación anidada 500 m a 1 km.')
    for k in ['width', 'height', 'vector_batch_size']:
        if not isinstance(s[k], int) or s[k] <= 0:
            raise ValueError(k)
    for k in ['coastal_min_land_fraction', 'minimum_valid_land_fraction']:
        if not 0 < s[k] <= 1:
            raise ValueError(k)
    if s['vector_margin_m'] < 10000:
        raise ValueError('El margen debe cubrir al menos la ventana prevista de 10 km.')
    s['transform'] = Affine(s['resolution_m'], 0, s['origin_x'], 0, -s['resolution_m'], s['origin_y'])
    s['native_transform'] = s['transform'] * Affine.scale(.5)
    s['shape'] = (s['height'], s['width'])
    s['native_shape'] = (s['height'] * 2, s['width'] * 2)
    return s


def load_mask(root, config, out):
    raw = gpd.read_file(local_path(root, config['mask_path']))
    if raw.crs is None or set(raw.CNTR_ID) != {'ES'} or not raw.geometry.is_valid.all():
        raise ValueError('La máscara necesita CRS, país ES y geometrías válidas.')
    parts = gpd.GeoDataFrame(geometry=list(shapely.get_parts(raw.geometry.union_all())), crs=raw.crs)
    # Elegir por superficie métrica en proyección equivalente, no por grados cuadrados.
    areas = parts.to_crs(3035).area
    main = areas.idxmax()
    parts['ambito'] = ['peninsula' if i == main else 'fuera_ambito_v1' for i in parts.index]
    parts['area_km2_epsg3035'] = areas / 1e6
    parts.to_file(out / 'coverage.gpkg', layer='ambitos_espana', driver='GPKG')
    csv(out / 'ambitos_espana.csv', parts.drop(columns='geometry'))
    mask = parts.loc[[main]].to_crs(config['crs']).geometry.iloc[0]
    gpd.GeoDataFrame({'estado': [config['mask_status']]}, geometry=[mask], crs=config['crs']).to_file(
        out / 'coverage.gpkg', layer='mascara_peninsular', driver='GPKG')
    return mask


def land_areas(mask, shape, transform):
    """Área de intersección por píxel; solo los píxeles de borde necesitan overlay."""
    if not mask.is_valid or mask.is_empty:
        raise ValueError('Máscara inválida/vacía.')
    h, w = shape
    extent = shapely.box(transform.c, transform.f + h * transform.e,
                         transform.c + w * transform.a, transform.f)
    if mask.difference(extent).area > 1:
        raise ValueError('La rejilla no contiene la máscara completa.')
    result = rasterize([(mask, 1)], out_shape=shape, transform=transform, dtype='uint8').astype('float64')
    result *= abs(transform.a * transform.e)
    edge = rasterize([(mask.boundary, 1)], out_shape=shape, transform=transform,
                     all_touched=True, dtype='uint8')
    rr, cc = np.where(edge)
    for start in range(0, len(rr), 2000):
        r, c = rr[start:start+2000], cc[start:start+2000]
        x, y = transform.c + c * transform.a, transform.f + r * transform.e
        boxes = shapely.box(x, y + transform.e, x + transform.a, y)
        result[r, c] = shapely.area(shapely.intersection(boxes, mask))
    if not np.isclose(result.sum(), mask.area, rtol=1e-9, atol=1):
        raise AssertionError('La suma de áreas no conserva la máscara.')
    return result


def aggregate_sum(array):
    h, w = array.shape
    if h % 2 or w % 2:
        raise ValueError('La matriz no es divisible en bloques 2x2.')
    return array.reshape(h//2, 2, w//2, 2).sum(axis=(1, 3))


def aggregate_values(values, valid, land, class_count=None):
    """Soporte terrestre idéntico para P/U; moda ponderada y empate a clase menor."""
    if values.shape != valid.shape or values.shape != land.shape:
        raise ValueError('Formas incompatibles.')
    valid = valid & np.isfinite(values)
    if class_count is not None:
        v = values[valid]
        if np.any((v != np.floor(v)) | (v < 0) | (v >= class_count)):
            raise ValueError('Códigos de clase fraccionarios o fuera de leyenda.')
    weights = np.where(valid, land, 0)
    area = aggregate_sum(weights)
    total = aggregate_sum(land)
    frac = np.divide(area, total, out=np.zeros_like(area), where=total > 0)
    if class_count is None:
        weighted = aggregate_sum(np.where(valid, values, 0) * weights)
        mean = np.divide(weighted, area, out=np.full_like(area, -9999.), where=area > 0)
        return mean, frac, None
    masses = np.stack([aggregate_sum(np.where(valid & (values == k), land, 0)) for k in range(class_count)])
    proportions = np.divide(masses, area, out=np.zeros_like(masses), where=area > 0)
    mode = np.argmax(masses, axis=0).astype('float64')
    mode[area == 0] = -9999
    proportions[:, area == 0] = -9999
    if not np.allclose(proportions[:, area > 0].sum(axis=0), 1):
        raise AssertionError('Proporciones de clases incoherentes.')
    return mode, frac, proportions


def save_raster(path, arrays, descriptions, spec):
    data = np.asarray(arrays, dtype='float32')
    if data.ndim == 2:
        data = data[None, ...]
    if data.shape[1:] != spec['shape']:
        raise ValueError('Forma de salida incompatible con rejilla.')
    with rasterio.open(path, 'w', driver='GTiff', width=spec['width'], height=spec['height'],
                       count=len(data), crs=spec['crs'], transform=spec['transform'], dtype='float32',
                       nodata=-9999, tiled=True, compress='deflate') as dst:
        dst.write(data)
        for i, name in enumerate(descriptions, 1):
            dst.set_band_description(i, name)
        dst.update_tags(grid_version=spec['grid_version'], support='area_terrestre_mascara_candidata')
    with rasterio.open(path) as check:
        assert check.transform == spec['transform'] and check.shape == spec['shape']
        assert check.crs == CRS(spec['crs']) and check.nodata == -9999


def make_grid(land, spec, out):
    area = aggregate_sum(land)
    r, c = np.where(area > 0)
    grid = pd.DataFrame({'row': r, 'col': c})
    grid['cell_id'] = [f'{spec["grid_version"]}_r{y:04d}_c{x:04d}' for y, x in zip(r, c)]
    grid['x_center'] = spec['origin_x'] + (c + .5) * 1000
    grid['y_center'] = spec['origin_y'] - (r + .5) * 1000
    grid['land_area_m2'] = area[r, c]
    grid['land_fraction'] = grid.land_area_m2 / 1e6
    grid['coastal_eligible'] = grid.land_fraction >= spec['coastal_min_land_fraction']
    grid['diagnostic_block'] = ('b' + (grid.row * 1000 // spec['diagnostic_block_m']).astype(str)
                                + '_' + (grid.col * 1000 // spec['diagnostic_block_m']).astype(str))
    assert grid.cell_id.is_unique
    csv(out / 'grid_1km.csv.gz', grid)
    serial = {k: v for k, v in spec.items() if k not in ('transform', 'native_transform')}
    serial.update(transform_gdal=list(spec['transform'].to_gdal()),
                  bounds=list(rasterio.transform.array_bounds(*spec['shape'], spec['transform'])),
                  coastal_policy='Todas las intersecciones positivas se conservan; elegibilidad >= fracción configurada.',
                  point_boundary_policy='Intervalos semiabiertos: borde E/S pasa a celda adyacente; E/S exterior queda fuera.',
                  area_units='m2 proyectados EPSG:25830; distorsión cuantificada aparte')
    write_json(out / 'grid_spec.json', serial)
    save_raster(out / 'rasters/land_fraction.tif', np.where(area > 0, area / 1e6, -9999), ['land_fraction'], spec)
    # Diagnóstico sistemático cada ~20 km, incluyendo los extremos de todas las celdas terrestres.
    sample = grid.iloc[::400]
    idx = set(sample.index) | {grid.x_center.idxmin(), grid.x_center.idxmax(), grid.y_center.idxmin(), grid.y_center.idxmax()}
    sample = grid.loc[sorted(idx), ['cell_id', 'x_center', 'y_center']].copy()
    lon, lat = Transformer.from_crs(spec['crs'], 4326, always_xy=True).transform(sample.x_center, sample.y_center)
    factors = Proj(spec['crs']).get_factors(lon, lat)
    sample['linear_scale_error_pct'] = (np.asarray(factors.meridional_scale) - 1) * 100
    sample['area_scale_error_pct'] = (np.asarray(factors.areal_scale) - 1) * 100
    csv(out / 'distorsion_crs.csv', sample)
    return grid


def align_rasters(root, aliases, land, spec, out):
    reports, fractions = [], {}
    for alias, name in aliases.items():
        if not (alias.startswith('geoquimica_') or alias == 'relieve'):
            continue
        print('Alineando', alias, flush=True)
        nclasses = (7 if alias in ('geoquimica_au', 'geoquimica_w') else 8) if alias.startswith('geoquimica_') else None
        with rasterio.open(local_path(root, name)) as src:
            # Evita remuestreo implícito si cambian las entradas; hay que revisar el nuevo soporte.
            if src.crs != CRS(spec['crs']) or src.transform != spec['native_transform'] or src.shape != spec['native_shape']:
                raise ValueError(f'{alias}: rejilla fuente no anidada exactamente; requiere política explícita nueva.')
            values = np.empty(src.shape, dtype='float32')
            valid = np.empty(src.shape, dtype=bool)
            for _, win in src.block_windows(1):
                block = src.read(1, window=win, masked=True)
                rs, cs = win.toslices()
                values[rs, cs] = block.data
                valid[rs, cs] = ~np.ma.getmaskarray(block) & np.isfinite(block.data)
            value, fraction, proportions = aggregate_values(values, valid, land, nclasses)
            descriptions = ['clase_modal' if nclasses else 'elevacion_media_m', 'valid_land_fraction']
            arrays = [value, np.where(aggregate_sum(land) > 0, fraction, -9999)]
            if nclasses:
                arrays.extend(proportions)
                descriptions.extend([f'proporcion_clase_{k}_sobre_area_valida' for k in range(nclasses)])
            save_raster(out / f'rasters/{alias}_1km.tif', arrays, descriptions, spec)
            fractions[alias] = fraction
            reports.append({'fuente': alias, 'banda_fuente': 1, 'descripcion_original': src.descriptions[0],
                'crs_origen': str(src.crs), 'nodata_origen': src.nodata, 'pixel_coincidente': True,
                'metodo': 'moda_y_proporciones_ponderadas_area_terrestre' if nclasses else 'media_ponderada_area_terrestre',
                'clase_0_valida': bool(nclasses), 'celdas_con_dato': int((fraction > 0).sum()),
                'area_valida_km2': float(aggregate_sum(np.where(valid, land, 0)).sum()/1e6)})
    csv(out / 'raster_alignment.csv', pd.DataFrame(reports))
    return fractions


def clean_geometries(frame, target_crs):
    """No elimina atributos; audita reparación en unidades del CRS métrico destino."""
    if frame.crs is None:
        raise ValueError('CRS vectorial ausente.')
    projected = frame.to_crs(target_crs)
    before = shapely.force_2d(projected.geometry.array)
    invalid = ~shapely.is_valid(before)
    after = before.copy()
    after[invalid] = shapely.make_valid(before[invalid])
    ok = ~shapely.is_missing(after) & ~shapely.is_empty(after) & shapely.is_valid(after)
    metrics = pd.DataFrame({'source_fid': frame.index,
        'invalid_before': invalid, 'accepted_geometry': ok,
        'type_before': shapely.get_type_id(before), 'type_after': shapely.get_type_id(after),
        'area_before_m2': shapely.area(before), 'area_after_m2': shapely.area(after),
        'length_before_m': shapely.length(before), 'length_after_m': shapely.length(after)})
    projected.geometry = after
    projected['source_fid'] = frame.index
    return projected, metrics


def _harmonize_vectors_uncached(root, aliases, mask, land, spec, out):
    """Paginación por FID (sin OFFSET creciente), conserva vecindarios sin recortar trazas."""
    fractions, summary = {}, []
    buffer = mask.buffer(spec['vector_margin_m'])
    shapely.prepare(buffer)
    old_step = pyogrio.get_gdal_config_option('OGR_ARC_STEPSIZE')
    pyogrio.set_gdal_config_options({'OGR_ARC_STEPSIZE': spec['curve_step_degrees']})
    try:
        for alias in spec['vector_families']:
            path = local_path(root, aliases[alias])
            info = pyogrio.read_info(path)
            layer, fid = info['layer_name'], info['fid_column']
            if not fid or not info['crs']:
                raise ValueError(f'{alias}: faltan FID/CRS.')
            is_polygon = 'Polygon' in info['geometry_type']
            count = np.zeros(spec['native_shape'], dtype='uint32')
            bbox = Transformer.from_crs(spec['crs'], info['crs'], always_xy=True).transform_bounds(*buffer.bounds)
            qlayer, qfid = layer.replace('"', '""'), fid.replace('"', '""')
            rtree = f'rtree_{layer}_{info["geometry_name"]}'.replace('"', '""')
            spatial_where = (f'"{qfid}" IN (SELECT id FROM "{rtree}" WHERE '
                             f'minx <= {bbox[2]} AND maxx >= {bbox[0]} AND '
                             f'miny <= {bbox[3]} AND maxy >= {bbox[1]})')
            with closing(sqlite3.connect(f'{path.resolve().as_uri()}?mode=ro', uri=True)) as db:
                expected_count = db.execute(f'SELECT count(*) FROM "{qlayer}" WHERE {spatial_where}').fetchone()[0]
            last, read_n, kept_n, invalid_n, discarded_n, changed_types = -1, 0, 0, 0, 0, 0
            metric_parts, warning_texts = [], set()
            output_path = out / f'vectors/{alias}.gpkg'
            print('Saneando', alias, 'filas fuente', info['features'], flush=True)
            curve_check = None
            # Comparación empírica de dos tolerancias en muestra de lectura; no es garantía global.
            if alias == 'contactos_geode':
                first = pyogrio.read_dataframe(path, layer=layer, max_features=spec['curve_check_sample'], fid_as_index=True)
                pyogrio.set_gdal_config_options({'OGR_ARC_STEPSIZE': spec['curve_check_step_degrees']})
                second = pyogrio.read_dataframe(path, layer=layer, max_features=spec['curve_check_sample'], fid_as_index=True)
                pyogrio.set_gdal_config_options({'OGR_ARC_STEPSIZE': spec['curve_step_degrees']})
                distance = shapely.hausdorff_distance(first.to_crs(spec['crs']).geometry.array,
                                                     second.to_crs(spec['crs']).geometry.array)
                curve_check = float(np.nanmax(distance))
                if curve_check > spec['curve_max_hausdorff_m']:
                    raise ValueError('Sensibilidad de linealización mayor que tolerancia configurada.')
            while True:
                with warnings.catch_warnings(record=True) as caught:
                    warnings.simplefilter('always')
                    # SQL ordenado + filtro espacial OGR; identificadores internos escapados.
                    frame = pyogrio.read_dataframe(path,
                        sql=f'SELECT * FROM "{qlayer}" WHERE "{qfid}" > {last} AND {spatial_where} ORDER BY "{qfid}" LIMIT {spec["vector_batch_size"]}',
                        sql_dialect='SQLITE', fid_as_index=True)
                    warning_texts.update(str(w.message) for w in caught)
                if frame.empty:
                    break
                if not frame.index.is_unique or frame.index.min() <= last:
                    raise AssertionError('Paginación FID no monótona.')
                last = int(frame.index.max())
                read_n += len(frame)
                clean, metrics = clean_geometries(frame, spec['crs'])
                # GeometryCollections de make_valid se conservan si son de dimensión prevista.
                expected = [3, 6] if is_polygon else [1, 5]
                compatible = np.isin(shapely.get_type_id(clean.geometry.array), expected)
                usable = metrics.accepted_geometry.to_numpy() & compatible
                metrics['compatible_family'] = compatible
                invalid_n += int(metrics.invalid_before.sum())
                discarded_n += int((~usable).sum())
                changed_types += int((metrics.type_before != metrics.type_after).sum())
                metric_parts.append(metrics.loc[metrics.invalid_before | ~metrics.accepted_geometry | ~compatible | (metrics.type_before != metrics.type_after)])
                clean = clean.loc[usable].copy()
                clean = clean.loc[shapely.intersects(buffer, clean.geometry.array)]
                if len(clean):
                    # El primer lote sustituye la capa de un intento anterior;
                    # solo se anexan los lotes de esta invocación.
                    pyogrio.write_dataframe(clean, output_path, layer=alias, driver='GPKG',
                                            append=kept_n > 0, promote_to_multi=True)
                    kept_n += len(clean)
                    # Polígonos: multiplicidad en centros de 500 m. Líneas: presencia local, NO cobertura de levantamiento.
                    burn = rasterize(((g, 1) for g in clean.geometry), out_shape=spec['native_shape'],
                                     transform=spec['native_transform'], dtype='uint32',
                                     merge_alg=rasterio.enums.MergeAlg.add, all_touched=not is_polygon)
                    count += burn
                print(alias, 'leídas', read_n, 'conservadas', kept_n, flush=True)
            # Recuento independiente del filtro rectangular; detectar truncación del lector.
            if read_n != expected_count:
                raise AssertionError(f'{alias}: paginación incompleta/duplicada: {read_n} != {expected_count}.')
            if kept_n == 0:
                # Publicar una capa vacía con su esquema, sin conservar filas previas.
                empty = pyogrio.read_dataframe(path, layer=layer, max_features=1,
                                               fid_as_index=True).iloc[:0]
                empty, _ = clean_geometries(empty, spec['crs'])
                pyogrio.write_dataframe(empty, output_path, layer=alias, driver='GPKG',
                                        append=False, promote_to_multi=True)
            written_n = pyogrio.read_info(output_path, layer=alias)['features']
            if written_n != kept_n:
                raise AssertionError(
                    f'{alias}: recuento de salida incorrecto en {output_path}: '
                    f'{written_n} entidades escritas != {kept_n} conservadas.')
            metric_frame = pd.concat(metric_parts, ignore_index=True) if metric_parts else pd.DataFrame()
            csv(out / f'vectors/{alias}_geometry_changes.csv', metric_frame)
            valid_area = aggregate_sum(np.where(count > 0, land, 0))
            total = aggregate_sum(land)
            fraction = np.divide(valid_area, total, out=np.zeros_like(total), where=total > 0)
            if is_polygon:
                fractions[alias] = fraction
            save_raster(out / f'rasters/{alias}_support_1km.tif', np.where(total > 0, fraction, -9999),
                        ['fraccion_soporte_estimado_500m' if is_polygon else 'fraccion_con_traza_NO_cobertura'], spec)
            summary.append({'familia': alias, 'source_features': info['features'], 'read_bbox': read_n,
                'expected_bbox': expected_count, 'pagination_complete': read_n == expected_count,
                'kept_with_margin': kept_n, 'invalid_before': invalid_n, 'quarantine_count': discarded_n,
                'changed_geometry_types': changed_types, 'crs_source': info['crs'], 'crs_target': spec['crs'],
                'area_support_km2_estimated': float(valid_area.sum()/1e6) if is_polygon else None,
                'area_overlap_km2_estimated': float(land[count > 1].sum()/1e6) if is_polygon else None,
                'coverage_status': 'estimada_centros_500m' if is_polygon else 'desconocida_sin_huella_de_levantamiento',
                'curve_sample_hausdorff_m': curve_check, 'reader_warnings': ' | '.join(sorted(warning_texts)),
                'z_m_policy': 'Z/M no usados; conservar originales; GDAL descarta M y force_2d elimina Z',
                'semantic_status': 'pendiente_fase_D; no deduplicación entre GEODE y MAGNA'})
            csv(out / 'vector_harmonization.csv', pd.DataFrame(summary))
    finally:
        pyogrio.set_gdal_config_options({'OGR_ARC_STEPSIZE': old_step})
    return fractions, pd.DataFrame(summary)


def vector_fingerprints(source):
    names = {'harmonize_vectors', '_harmonize_vectors_uncached', 'clean_geometries', 'aggregate_sum', 'save_raster'}
    result = {}
    for node in ast.parse(source).body:
        if isinstance(node, ast.FunctionDef) and node.name in names:
            name = node.name
            if name == 'harmonize_vectors' and 'def _harmonize_vectors_uncached' in source:
                continue
            if name in ('harmonize_vectors', '_harmonize_vectors_uncached'):
                name = 'vector_implementation'
            node.name = name
            result[name] = hashlib.sha256(ast.dump(node, include_attributes=False).encode()).hexdigest()
    return result


def base_vector_config(config):
    # Las etiquetas y las capas adicionales no intervienen en el saneamiento base.
    return {k:v for k,v in config.items() if k not in ('vector_cache_run', 'phase_b_run', 'additional_vectors')}


def base_source_hashes(root, out):
    inputs = read_json(out / 'inputs.json')
    a = local_path(root, inputs['phase_a_run'])
    manifest = read_json(a / 'manifest.json')
    aliases = read_json(a / 'config_snapshot.json')['canonical_candidates']
    config = read_json(out / 'config_snapshot.json')
    indexed = {r['path']:r['sha256'] for r in manifest['sources']}
    return {name: indexed[aliases[name]] for name in config['vector_families']}


def seal_vector_checkpoint(root, out):
    """Sella el paso 15 completo, independiente de que el resto del cuaderno termine."""
    config = read_json(out / 'config_snapshot.json')
    summary = pd.read_csv(out / 'vector_harmonization.csv')
    if set(summary.familia) != set(config['vector_families']) or not summary.pagination_complete.all():
        raise ValueError('El paso vectorial no está completo.')
    source_copy = out / 'territory_source.py'
    inputs = read_json(out / 'inputs.json')
    expected = next(x['sha256'] for x in inputs['frozen_inputs'] if x['path'] == 'src/geoau/territory.py')
    if sha256_file(source_copy) != expected:
        raise ValueError('Snapshot de código distinto del usado para generar vectores.')
    files = [out / 'vector_harmonization.csv']
    files += [out / f'vectors/{name}{suffix}' for name in config['vector_families']
              for suffix in ('.gpkg', '_geometry_changes.csv')]
    files += [out / f'rasters/{name}_support_1km.tif' for name in config['vector_families']]
    for row in summary.itertuples():
        if pyogrio.read_info(out / f'vectors/{row.familia}.gpkg')['features'] != row.kept_with_margin:
            raise ValueError('Recuento de producto vectorial distinto del informe.')
    checkpoint = {'stage': '15_complete', 'config': base_vector_config(config),
        'base_source_hashes': base_source_hashes(root, out),
        'source_manifest_sha256': sha256_file(local_path(root, inputs['phase_a_run']) / 'manifest.json'),
        'mask_sha256': sha256_file(local_path(root, config['mask_path'])),
        'function_fingerprints': vector_fingerprints(source_copy.read_text(encoding='utf-8')),
        'files': [{'path': p.relative_to(out).as_posix(), 'sha256': sha256_file(p)} for p in files if p.is_file()]}
    write_json(out / 'vector_checkpoint.json', checkpoint)
    return checkpoint


def harmonize_vectors(root, aliases, mask, land, spec, out):
    cache_name = spec.get('vector_cache_run')
    if not cache_name:
        result = _harmonize_vectors_uncached(root, aliases, mask, land, spec, out)
        seal_vector_checkpoint(root, out)
        # Igual precisión canónica con/sin caché: la publicada en los TIFF float32.
        return {k: v.astype('float32').astype('float64') for k,v in result[0].items()}, result[1]
    cache = local_path(root, cache_name)
    checkpoint = read_json(cache / 'vector_checkpoint.json')
    current_config = read_json(out / 'config_snapshot.json')
    if checkpoint['stage'] != '15_complete' or checkpoint['config'] != base_vector_config(current_config):
        raise ValueError('Caché vectorial incompatible con configuración; desactiva vector_cache_run.')
    inputs = read_json(out / 'inputs.json')
    if checkpoint.get('base_source_hashes') != base_source_hashes(root, out):
        raise ValueError('Caché de otras fuentes vectoriales base; desactiva vector_cache_run.')
    if checkpoint['mask_sha256'] != sha256_file(local_path(root, current_config['mask_path'])):
        raise ValueError('Caché de otra máscara territorial.')
    if checkpoint['function_fingerprints'] != vector_fingerprints((root / 'src/geoau/territory.py').read_text(encoding='utf-8')):
        raise ValueError('Ha cambiado el algoritmo vectorial; desactiva vector_cache_run.')
    print('Verificando y copiando paso vectorial completo:', cache, flush=True)
    for row in checkpoint['files']:
        source = local_path(cache, row['path'])
        if sha256_file(source) != row['sha256']:
            raise ValueError(f'Caché modificada: {source}')
        destination = local_path(out, row['path'])
        shutil.copy2(source, destination)
        if sha256_file(destination) != row['sha256']:
            raise ValueError('Copia vectorial no íntegra.')
    summary = pd.read_csv(out / 'vector_harmonization.csv')
    fractions = {}
    for name in ('litologia', 'edades', 'recintos'):
        with rasterio.open(out / f'rasters/{name}_support_1km.tif') as src:
            if src.transform != spec['transform'] or src.shape != spec['shape'] or src.crs != CRS(spec['crs']):
                raise ValueError('Soporte de caché distinto de la rejilla.')
            fractions[name] = src.read(1, masked=True).filled(0).astype('float64')
    write_json(out / 'vector_cache_used.json', {'run': cache_name,
        'checkpoint_sha256': sha256_file(cache / 'vector_checkpoint.json'),
        'policy': 'Mismo código vectorial, parámetros, máscara y fuentes; copias verificadas SHA-256.'})
    seal_vector_checkpoint(root, out)
    return fractions, summary


def feature_dictionary(out):
    rows = [
        ('litologia_fracciones_dominante', 'litologia/recintos', 'interseccion_poligonal/area_terrestre', 'fraccion/categoria', 'fase_D'),
        ('edad_fracciones_dominante', 'edades/recintos', 'interseccion_poligonal/area_terrestre', 'fraccion/categoria', 'fase_D'),
        ('distancia_estructuras', 'contactos_geode/estructuras_magna', 'centro_geometrico_fijo_de_celda_a_linea_clasificada', 'm', 'fase_D'),
        ('densidad_estructuras', 'contactos_geode/estructuras_magna', 'longitud_en_circulo_1_5_10km/area_soporte_valido', 'km/km2', 'fase_D'),
        ('distancia_cauce', 'hidrografia', 'centro_geometrico_fijo_de_celda_a_red', 'm', 'fase_D'),
        ('elevacion_media', 'relieve_banda_1', 'media_ponderada_por_area_terrestre_valida', 'm', 'armonizada_C'),
        ('pendiente_TPI_rugosidad', 'relieve_banda_1', 'ventana_y_formula_a_fijar_en_D_con_NoData_y_margen', 'segun_variable', 'fase_D'),
    ]
    for el in ['au', 'as', 'sb', 'bi', 'hg', 'cu', 'pb', 'zn', 'w']:
        rows.append((f'{el}_clase', f'geoquimica_{el}_banda_1', 'moda_area_valida; empate_clase_menor; proporciones_alternativas', 'clase_ordinal', 'armonizada_C_leyenda_pendiente_D'))
    frame = pd.DataFrame(rows, columns=['feature', 'source', 'support', 'units', 'status'])
    frame['same_for_P_U_inference'] = True
    frame['missing_policy'] = 'NoData; no rellenar con 0; imputacion solo dentro de entrenamiento'
    frame['predictor_policy'] = 'una representacion por elemento; no incluir IDs, coordenadas ni etiquetas'
    csv(out / 'feature_dictionary.csv', frame)
    return frame


def assign_points(points, mask, grid, spec):
    projected = points.to_crs(spec['crs'])
    rows = []
    ids = grid.set_index(['row', 'col']).cell_id
    for i, point in projected.iterrows():
        g = point.geometry
        state, cell = 'geometria_no_utilizable', None
        if g is not None and g.geom_type == 'Point' and g.is_valid and not g.is_empty and not bool(point.geo_cuarentena):
            if not mask.covers(g):
                state = 'fuera_mascara_candidata'
            else:
                c = int(np.floor((g.x - spec['origin_x'])/spec['resolution_m']))
                r = int(np.floor((spec['origin_y'] - g.y)/spec['resolution_m']))
                cell = ids.get((r, c))
                state = 'asignado' if cell is not None else 'fuera_rejilla'
        rows.append({'record_id': point.record_id, 'Codigo_indicio': point.Codigo_indicio,
                     'cell_id': cell, 'estado_territorial': state,
                     'positivo_revisado': bool(point.elegible_general_revisada),
                     'Provincia_declarada': point.Provincia})
    result = pd.DataFrame(rows)
    assert len(result) == len(points) and result.record_id.is_unique
    return result


def coverage_products(root, grid, fractions, points, mask, spec, out):
    grid = grid.copy()
    rr, cc = grid.row.to_numpy(), grid.col.to_numpy()
    for name, array in fractions.items():
        grid[f'valid_{name}'] = array[rr, cc]
    chemical = [f'valid_{k}' for k in fractions if k.startswith('geoquimica_')]
    threshold = spec['minimum_valid_land_fraction']
    required = ['valid_litologia', 'valid_edades', 'valid_relieve']
    if len(chemical) != 9 or not set(required).issubset(grid.columns):
        raise ValueError('Faltan familias del diagnóstico básico.')
    geo_relief = grid[required].ge(threshold).all(axis=1)
    all_chem = grid[chemical].ge(threshold).all(axis=1)
    grid['coverage_code'] = np.select([
        ~grid.coastal_eligible, geo_relief & all_chem, geo_relief], [1, 2, 3], default=4).astype('uint8')
    meanings = {1: 'costera_baja_fraccion', 2: 'soporte_basico_candidato',
                3: 'candidato_reducido_sin_geoquimica_completa', 4: 'soporte_insuficiente'}
    grid['coverage_decision'] = grid.coverage_code.map(meanings)
    grid['prediction_allowed'] = False
    linked = assign_points(points, mask, grid, spec).merge(
        grid[['cell_id', 'coverage_decision'] + [c for c in grid if c.startswith('valid_')]],
        on='cell_id', how='left', validate='many_to_one')
    csv(out / 'indicios_celda_cobertura.csv', linked)
    counts = linked.loc[linked.cell_id.notna()].groupby('cell_id').agg(
        n_candidatos=('record_id', 'size'), n_positivos_revisados=('positivo_revisado', 'sum'))
    grid = grid.merge(counts, left_on='cell_id', right_index=True, how='left', validate='one_to_one')
    grid[['n_candidatos', 'n_positivos_revisados']] = grid[['n_candidatos', 'n_positivos_revisados']].fillna(0).astype(int)
    csv(out / 'coverage_by_cell.csv.gz', grid)
    summaries = []
    for name in fractions:
        for scope, part in [('peninsula', grid)] + list(grid.groupby('diagnostic_block')):
            area = part.land_area_m2.sum()
            summaries.append({'ambito': scope, 'familia': name, 'area_terrestre_km2': area / 1e6,
                 'area_valida_km2': (part.land_area_m2 * part[f'valid_{name}']).sum() / 1e6,
                 'area_hueco_km2': (part.land_area_m2 * (1-part[f'valid_{name}'])).sum() / 1e6,
                 'candidatos_total': int(part.n_candidatos.sum()),
                 'candidatos_celda_cubierta': int(part.loc[part[f'valid_{name}'] >= threshold, 'n_candidatos'].sum()),
                 'revisados_celda_cubierta': int(part.loc[part[f'valid_{name}'] >= threshold, 'n_positivos_revisados'].sum()),
                 'metodo': 'estimacion_centros_500m' if name in ('litologia','edades','recintos') else 'area_pixeles_validos_intersectada_con_mascara'})
    coverage = pd.DataFrame(summaries)
    coverage['porcentaje_area_valida'] = coverage.area_valida_km2 / coverage.area_terrestre_km2 * 100
    csv(out / 'coverage_by_scope_family.csv', coverage)
    decisions = grid.groupby('coverage_decision').agg(celdas=('cell_id','size'), area_km2=('land_area_m2','sum'),
        candidatos=('n_candidatos','sum'), revisados=('n_positivos_revisados','sum')).reset_index()
    decisions['area_km2'] /= 1e6
    decisions['prediction_allowed'] = False
    decisions['motivo'] = 'Faltan validacion semantica, huellas estructurales, revision de etiquetas y modelo validado.'
    csv(out / 'coverage_decisions.csv', decisions)
    status = np.zeros(spec['shape'], dtype='uint8')
    status[rr, cc] = grid.coverage_code
    save_raster(out / 'rasters/coverage_status.tif', np.where(status > 0, status.astype('float32'), -9999.), ['coverage_code'], spec)
    polygons = [(shapely.intersection(shapely.geometry.shape(g), mask), int(v))
                for g, v in shapes(status, mask=status > 0, transform=spec['transform'])]
    spatial = gpd.GeoDataFrame({'coverage_code': [v for _, v in polygons]},
                              geometry=[g for g, _ in polygons], crs=spec['crs'])
    spatial = spatial.loc[~spatial.geometry.is_empty & (spatial.area > 0)]
    spatial['decision'] = spatial.coverage_code.map(meanings)
    spatial['prediction_allowed'] = False
    spatial.to_file(out / 'coverage.gpkg', layer='estados_cobertura', driver='GPKG')
    # Los casos sin dato puntual se vuelven a muestrear; no se rellenan por tener vecino válido.
    from .labels import coverage_at_points
    aliases = read_json(local_path(root, read_json(out / 'inputs.json')['phase_a_run']) / 'config_snapshot.json')['canonical_candidates']
    sample = coverage_at_points(points, {k: local_path(root,v) for k,v in aliases.items()
                                         if k.startswith('geoquimica_') or k == 'relieve'})
    csv(out / 'cobertura_puntual_recomprobada.csv', sample)
    missing = sample[sample.fuente.str.startswith('geoquimica_') & sample.estado.ne('valor_valido')]
    issues = missing.merge(linked, on='record_id', how='left', validate='many_to_one', suffixes=('_punto','_celda'))
    issues['decision'] = 'Conservar indicio; dato puntual sigue ausente; revisar RGB/leyenda y borde. No imputar cero.'
    csv(out / 'revision_au_sin_geoquimica.csv', issues)
    old = pd.read_csv(local_path(root, spec['phase_b_run']) / 'cobertura_en_indicios_au.csv', dtype={'record_id': str})
    contrast = old[['record_id','fuente','estado']].merge(sample[['record_id','fuente','estado']],
        on=['record_id','fuente'], how='outer', suffixes=('_B','_C'), validate='one_to_one', indicator=True)
    csv(out / 'contraste_cobertura_puntual_B_C.csv', contrast)
    if spec.get('additional_vectors'):
        from .additional_layers import additional_coverage_products
        additional_coverage_products(root, grid, points, spec, out)
    return grid, coverage, decisions, linked, status


def finish_run(root, out, manifest, frozen, grid, linked, vectors):
    config = read_json(out / 'config_snapshot.json')
    additions = None
    if config.get('additional_vectors'):
        additions = pd.read_csv(out / 'additional_vector_harmonization.csv')
        if set(additions.familia) != set(config['additional_vectors']) or not additions.pagination_complete.all():
            raise AssertionError('No se han completado todas las capas adicionales.')
    changed = verify_unchanged(root, manifest['sources'], rehash=True)
    extra = [r['path'] for r in frozen if sha256_file(local_path(root, r['path'])) != r['sha256']]
    control = {'estado_ejecucion': 'completada' if not changed and not extra else 'error_integridad',
       'fase_c_cientifica_cerrada': False, 'celdas_terrestres': len(grid),
       'area_terrestre_km2_epsg25830': float(grid.land_area_m2.sum()/1e6),
       'candidatos_asignados': int(linked.cell_id.notna().sum()),
       'candidatos_fuera_mascara_o_no_utilizables': int(linked.cell_id.isna().sum()),
       'positivos_revisados_asignados': int(grid.n_positivos_revisados.sum()),
       'capas_adicionales_procesadas': [] if additions is None else additions.familia.tolist(),
       'fuentes_modificadas': changed, 'entradas_adicionales_modificadas': extra,
       'pendientes': ['Validar máscara generalizada y sensibilidad de costa/frontera con cartografía más detallada.',
          'Cobertura poligonal estimada a 500 m; verificar huecos, solapes y discontinuidades por hoja/dominio.',
          'Linealización contrastada en muestra; completar certificación geométrica y revisar cuarentenas.',
          'Sin huellas de levantamiento de líneas: ausencia de trazas no demuestra cobertura.',
          'Clasificación estructural, equivalencia GEODE/MAGNA y leyendas corresponden a fase D.',
          'Etiquetas, depósitos, distritos y piloto siguen pendientes de revisión.',
          'Islas, Ceuta, Melilla y otras componentes fuera de ámbito; no extrapolar resultados peninsulares.']}
    write_json(out / 'control_cierre.json', control)
    # Sella productos, incluyendo capas grandes, para reutilización verificable.
    write_json(out / 'outputs_manifest.json', [{'path': p.relative_to(out).as_posix(), 'sha256': sha256_file(p),
                    'size_bytes': p.stat().st_size} for p in sorted(out.rglob('*')) if p.is_file() and p.name != 'outputs_manifest.json'])
    if changed or extra:
        raise AssertionError('Entradas modificadas durante la ejecución.')
    return control
