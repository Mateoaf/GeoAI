"""Capas recuperadas: geometría, soporte observado y revisión semántica explícita."""
import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.features import rasterize
import shapely

from .local_sources import local_path, sha256_file, write_json
from .territory import clean_geometries, aggregate_sum, save_raster, csv


POLYGONS = {'cuaternariorecintos', 'zonasgeode'}
POINTS = {'magnetotelurico', 'petrofisica', 'buzamientos', 'gravimetria'}
ROLES = {
    'cuaternariorecintos': 'huella_materiales_cuaternarios; no acredita cobertura del levantamiento ni ausencia fuera',
    'zonasgeode': 'zonas_cartograficas_GEODE; no distritos ni dominios metalogeneticos validados',
    'gravimetria': 'observaciones_con_VALU_BOU267; unidades, correcciones y centinelas pendientes',
    'magnetometriaradiometria': 'lineas_de_vuelo; VALU_LINE es identificador, no anomalia magnetica',
    'magnetotelurico': 'sitios_y_referencias_EDI; sin modelo resistivo ni profundidad en atributos',
    'petrofisica': 'localizaciones_documentales; sin propiedades fisicas cuantitativas en atributos',
    'buzamientos': 'simbolos_puntuales; ROTATION y STRING requieren convenciones de leyenda',
    'medidasestructurales': 'simbolos_lineales_con_angulos; longitud no equivale a estructura geologica',
}


def attribute_checks(frame, alias):
    rows = []
    fields = {'gravimetria': ['VALU_BOU267'], 'medidasestructurales': ['DIRECCION','BUZAMIENTO'],
              'buzamientos': ['ROTATION','STRING']}.get(alias, [])
    for field in fields:
        raw = frame[field]
        numeric = pd.to_numeric(raw, errors='coerce')
        finite = numeric.notna() & np.isfinite(numeric)
        low, high = (0, 90) if field in ('BUZAMIENTO','STRING') else (0, 360)
        # Rangos son diagnóstico, no traducción automática de simbología.
        out_of_range = finite & ~numeric.between(low, high) if alias != 'gravimetria' else pd.Series(False, index=frame.index)
        rows.append({'familia': alias, 'campo': field, 'filas': len(frame),
            'nulos_o_no_numericos': int(numeric.isna().sum()), 'no_finitos': int((numeric.notna() & ~finite).sum()),
            'fuera_rango_angular_candidato': int(out_of_range.sum()),
            'minimo_observado': numeric[finite].min(), 'maximo_observado': numeric[finite].max(),
            'interpretacion': 'no filtrar ni imputar automaticamente; requiere metadatos'})
    return rows


def harmonize_additional(root, aliases, mask, land, spec, out):
    summaries, attributes = [], []
    total = aggregate_sum(land)
    buffer = mask.buffer(spec['vector_margin_m'])
    shapely.prepare(buffer)
    for alias in spec.get('additional_vectors', {}):
        path = local_path(root, aliases[alias])
        layers = pyogrio.list_layers(path)
        if len(layers) != 1:
            raise ValueError(f'{alias}: se necesita una capa inequívoca.')
        info = pyogrio.read_info(path, layer=layers[0,0])
        expected = [3,6] if alias in POLYGONS else [0,4] if alias in POINTS else [1,5]
        count = np.zeros(spec['native_shape'], dtype='uint32')
        read_n = kept = invalid = rejected = outside = 0
        changes = []
        target = out / f'vectors/{alias}.gpkg'
        if target.exists():
            raise ValueError(f'No añadir duplicados a un producto existente: {target}')
        while read_n < info['features']:
            frame = pyogrio.read_dataframe(path, layer=layers[0,0], skip_features=read_n,
                    max_features=spec['vector_batch_size'], fid_as_index=True)
            if frame.empty:
                raise ValueError(f'{alias}: lector truncado antes del recuento esperado.')
            read_n += len(frame)
            attributes.extend(attribute_checks(frame, alias))
            clean, metrics = clean_geometries(frame, spec['crs'])
            if alias in POINTS and frame.geometry.has_z.any():
                clean['z_original'] = shapely.get_z(frame.geometry.array)
            compatible = np.isin(shapely.get_type_id(clean.geometry.array), expected)
            usable = metrics.accepted_geometry.to_numpy() & compatible
            intersects = np.zeros(len(frame), dtype=bool)
            intersects[usable] = shapely.intersects(buffer, clean.geometry.array[usable])
            metrics['compatible_family'] = compatible
            metrics['outside_scope_margin'] = usable & ~intersects
            changes.append(metrics.loc[metrics.invalid_before | ~usable | metrics.outside_scope_margin])
            invalid += int(metrics.invalid_before.sum())
            rejected += int((~usable).sum())
            outside += int((usable & ~intersects).sum())
            clean = clean.loc[usable & intersects].copy()
            if len(clean):
                pyogrio.write_dataframe(clean, target, layer=alias, driver='GPKG',
                                        append=target.exists(), promote_to_multi=True)
                kept += len(clean)
                count += rasterize(((g,1) for g in clean.geometry), out_shape=spec['native_shape'],
                    transform=spec['native_transform'], dtype='uint32',
                    merge_alg=rasterio.enums.MergeAlg.add, all_touched=alias not in POLYGONS)
            print(alias, read_n, '/', info['features'], flush=True)
        if read_n != info['features'] or kept + rejected + outside != read_n:
            raise AssertionError('Recuentos de saneamiento no conservados.')
        if kept and pyogrio.read_info(target)['features'] != kept:
            raise AssertionError('Recuento exportado incoherente.')
        csv(out / f'vectors/{alias}_geometry_changes.csv', pd.concat(changes, ignore_index=True))
        # Solo los polígonos tienen área de huella; puntos y líneas tienen ocupación de celdas.
        fraction = np.divide(aggregate_sum(np.where(count > 0, land, 0)), total,
                             out=np.zeros_like(total), where=total > 0)
        occupied = aggregate_sum(count) > 0
        support = fraction if alias in POLYGONS else occupied.astype('float64')
        label = 'fraccion_huella_estimada_500m_NO_cobertura' if alias in POLYGONS else 'celda_con_entidad_NO_cobertura'
        save_raster(out / f'rasters/{alias}_support_1km.tif', np.where(total > 0, support, -9999.), [label], spec)
        summaries.append({'familia': alias, 'source_features': info['features'], 'read_features': read_n,
            'kept_with_margin': kept, 'invalid_before': invalid, 'quarantine_count': rejected,
            'outside_scope_margin': outside, 'pagination_complete': True, 'crs_source': info['crs'],
            'geometry_source': info['geometry_type'], 'source_sha256': sha256_file(path),
            'support_role': ROLES[alias], 'coverage_of_survey': 'no_acreditada',
            'prediction_allowed': False})
    result = pd.DataFrame(summaries)
    csv(out / 'additional_vector_harmonization.csv', result)
    csv(out / 'additional_attribute_qc.csv', pd.DataFrame(attributes))
    dictionary = pd.read_csv(out / 'feature_dictionary.csv')
    extra = pd.DataFrame([{'feature': name, 'source': name, 'support': role,
        'units': 'pendientes_metadatos', 'status': 'diagnostico_C; predictor_pendiente_D',
        'same_for_P_U_inference': True, 'missing_policy': 'desconocido; no rellenar con cero',
        'predictor_policy': 'referencias y simbologia no son propiedades cuantitativas'} for name,role in ROLES.items()
        if name in spec['additional_vectors']])
    csv(out / 'feature_dictionary.csv', pd.concat([dictionary, extra], ignore_index=True))
    return result


def additional_coverage_products(root, grid, points, spec, out):
    diagnostic = grid[['cell_id','row','col','diagnostic_block','land_area_m2','n_candidatos','n_positivos_revisados']].copy()
    rr, cc = diagnostic.row.to_numpy(), diagnostic.col.to_numpy()
    summary, point_rows = [], []
    for alias in spec['additional_vectors']:
        with rasterio.open(out / f'rasters/{alias}_support_1km.tif') as src:
            data = src.read(1, masked=True).filled(0)
        column = f'footprint_{alias}' if alias in POLYGONS else f'entity_present_{alias}'
        diagnostic[column] = data[rr, cc]
        for scope, part in [('peninsula',diagnostic)] + list(diagnostic.groupby('diagnostic_block')):
            present = part[column] > 0
            summary.append({'ambito':scope,'familia':alias,'celdas_con_entidad_o_huella':int(present.sum()),
                'area_huella_km2_estimada': float((part.land_area_m2*part[column]).sum()/1e6) if alias in POLYGONS else None,
                'candidatos_en_celda_con_entidad_o_huella':int(part.loc[present,'n_candidatos'].sum()),
                'revisados_en_celda_con_entidad_o_huella':int(part.loc[present,'n_positivos_revisados'].sum()),
                'cobertura_levantamiento':'desconocida; no inferir ausencias', 'rol': ROLES[alias]})
        path = out / f'vectors/{alias}.gpkg'
        if alias in POLYGONS and path.exists():
            polygons = pyogrio.read_dataframe(path)
            polygons.to_file(out / 'coverage.gpkg', layer=f'huella_{alias}', driver='GPKG')
            # Relación exacta punto-polígono, conserva solapes; no fuerza una única zona.
            usable = points.loc[~points.geo_cuarentena, ['record_id','geometry']].to_crs(spec['crs'])
            fields = ['source_fid'] + ([c for c in ['CODE_ZONE','DESC_ZONE'] if c in polygons] if alias == 'zonasgeode' else ['CODE_UNIO','DESC_UNIT'])
            joined = gpd.sjoin(usable, polygons[fields+['geometry']], how='left', predicate='intersects')
            joined['familia'] = alias
            joined['estado'] = np.where(joined.index_right.notna(), 'interseccion_geometrica', 'sin_interseccion_NO_ausencia')
            point_rows.append(joined.drop(columns=['geometry','index_right']))
    csv(out / 'additional_support_by_cell.csv.gz', diagnostic)
    csv(out / 'additional_support_by_scope.csv', pd.DataFrame(summary))
    if point_rows:
        csv(out / 'indicios_zonas_cuaternario.csv', pd.concat(point_rows, ignore_index=True))
    # Añadir diagnósticos sin cambiar las decisiones del conjunto básico.
    merged = grid.merge(diagnostic[['cell_id']+[c for c in diagnostic if c.startswith(('footprint_','entity_present_'))]],
                        on='cell_id', validate='one_to_one')
    csv(out / 'coverage_by_cell.csv.gz', merged)
    write_json(out / 'additional_layers_decisions.json', {'required_for_basic_model': False,
        'layers': ROLES, 'interpolation_performed': False,
        'pending': ['Unidades/correcciones/centinelas de VALU_BOU267',
                    'Convenciones angulares y equivalencias GEODE/MAGNA',
                    'Leyenda cuaternaria: auxiliares no equivalen a terrazas aluviales',
                    'Datos físicos externos de vuelos, EDI y petrofísica; no inferidos desde referencias']})
