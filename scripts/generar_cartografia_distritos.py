#!/usr/bin/env python3
"""Generador y validador de la cartografía territorial de distritos metalogenéticos (Paso 4).

Construye un mapa reproducible cell_id -> district_id para la rejilla de 1 km de Fase D:
- Incorpora las 137 celdas con labores/indicios confirmados de los 32 distritos (Paso 3B).
- Utiliza límites geológicos/metalogenéticos documentados de GEODE (recintos.gpkg) para
  formaciones huésped locales bien acotadas (plutones, complejos volcánicos, abanicos aluviales,
  estructuras locales <= 100 km²).
- Mantiene en estado 'pendiente_delimitacion_regional' las formaciones regionales difusas
  (> 100 km² como Serie de los Cabos, Domo Extremeño o pizarras regionales), acotando el
  distrito estrictamente a las celdas confirmadas para evitar polígonos arbitrarios.
- Genera data/review/territorial_groups.csv con las 496.855 celdas de la rejilla.
- Valida compatibilidad estricta con el contrato de evaluation.py de Fase D.
"""
from pathlib import Path
import json
import numpy as np
import pandas as pd
import geopandas as gpd
import pyogrio

def build_territorial_cartography():
    ROOT = Path(__file__).resolve().parents[1]
    
    # 1. Cargar rejilla maestra de 1 km (Fase D)
    d_run = ROOT / 'reports/fase_d/20260926T212039_928615Z'
    grid_path = d_run / 'Grid_Master_Au.parquet'
    print(f"Cargando rejilla maestra desde {grid_path}...")
    grid = pd.read_parquet(grid_path, columns=['cell_id', 'row', 'col', 'x_center', 'y_center', 'eligible_geo4'])
    n_total_cells = len(grid)
    print(f"Total celdas en la rejilla: {n_total_cells:,}")
    assert grid.cell_id.is_unique, "Error: claves cell_id duplicadas en la rejilla."

    # 2. Cargar indicios revisados de Fase B (Paso 3B) y correspondencia con celdas (Fase C)
    c_run = ROOT / 'reports/fase_c/20260926T175114_459406Z'
    df_c = pd.read_csv(c_run / 'indicios_celda_cobertura.csv', dtype=str)
    
    rev_path = ROOT / 'data/review/revision_au_fase_b.csv'
    print(f"Cargando auditoría geológica de Fase B desde {rev_path}...")
    rev = pd.read_csv(rev_path, dtype=str, keep_default_na=False)
    conf = rev[rev.estado_presencia == 'confirmada'].copy()
    print(f"Total registros confirmados en B: {len(conf)}")
    print(f"Total depósitos confirmados: {conf.deposit_id.nunique()}")
    print(f"Total distritos metalogenéticos: {conf.district_id.nunique()}")

    conf = conf.merge(df_c[['record_id', 'cell_id']], on='record_id', how='left')
    assert conf.cell_id.notna().all(), "Error: hay indicios confirmados sin cell_id asignada."

    # Celdas confirmadas por depósito y distrito
    conf_cells = conf[['district_id', 'deposit_id', 'cell_id']].drop_duplicates()
    conf_cells = conf_cells.merge(grid[['cell_id', 'x_center', 'y_center']], on='cell_id', how='left')
    n_conf_cells = conf_cells.cell_id.nunique()
    print(f"Celdas únicas con indicios confirmados: {n_conf_cells}")

    # Verificar que no hay celdas compartidas entre distintos distritos
    cell_to_dist = conf_cells.groupby('cell_id')['district_id'].unique()
    multidist = cell_to_dist[cell_to_dist.apply(len) > 1]
    assert len(multidist) == 0, f"Error: celdas con más de un distrito: {multidist}"

    # 3. Intersección con recintos geológicos documentados (GEODE)
    recintos_path = c_run / 'vectors/recintos.gpkg'
    print(f"Consultando recintos geológicos documentados desde {recintos_path}...")

    # Mapeo de celdas por distrito
    district_cells = {}
    district_metadata = []

    for dist, grp in conf_cells.groupby('district_id'):
        xs, ys = grp.x_center, grp.y_center
        margin = 6000  # margen de búsqueda en metros
        bbox = (xs.min() - margin, ys.min() - margin, xs.max() + margin, ys.max() + margin)
        
        # Leer recintos en la caja envolvente
        rec = pyogrio.read_dataframe(recintos_path, bbox=bbox)
        pt_geoms = gpd.points_from_xy(grp.x_center, grp.y_center, crs='EPSG:25830')
        pts_union = pt_geoms.union_all()
        matching_polys = rec[rec.intersects(pts_union)].copy()

        # Separar polígonos locales documentados (<= 100 km²) de formaciones regionales difusas (> 100 km²)
        matching_polys['area_km2'] = matching_polys.geometry.area / 1e6
        doc_polys = matching_polys[matching_polys.area_km2 <= 100.0]
        regional_polys = matching_polys[matching_polys.area_km2 > 100.0]

        cells_in_dist = set(grp.cell_id)  # Siempre incluye las celdas directamente confirmadas
        poly_objectids = []
        poly_descs = []
        poly_area_total = 0.0

        if len(doc_polys) > 0:
            grid_sub = grid[(grid.x_center >= bbox[0]) & (grid.x_center <= bbox[2]) & 
                            (grid.y_center >= bbox[1]) & (grid.y_center <= bbox[3])].copy()
            gdf_grid_sub = gpd.GeoDataFrame(grid_sub, geometry=gpd.points_from_xy(grid_sub.x_center, grid_sub.y_center), crs='EPSG:25830')
            joined = gpd.sjoin(gdf_grid_sub, doc_polys, how='inner', predicate='intersects')
            cells_in_dist |= set(joined.cell_id)
            poly_objectids = doc_polys.OBJECTID.tolist()
            poly_descs = [f"[{r.CODE_UNIO}] ({r.NAME_EDA1}) {str(r.DESC_UNIT)[:50]}" for _, r in doc_polys.iterrows()]
            poly_area_total = float(doc_polys.area_km2.sum())

        if len(doc_polys) > 0 and len(regional_polys) == 0:
            metodo = 'delimitacion_geologica_recintos_documentados'
            estado = 'delimitado_geologico'
        elif len(doc_polys) > 0 and len(regional_polys) > 0:
            metodo = 'delimitacion_mixta_recintos_locales_y_pendiente_regional'
            estado = 'parcialmente_delimitado_pendiente_regional'
        else:
            metodo = 'acotado_a_celdas_confirmadas_pendiente_delimitacion_regional'
            estado = 'pendiente_delimitacion_regional'

        district_cells[dist] = {
            'cells': cells_in_dist,
            'metodo': metodo,
            'estado': estado
        }

        district_metadata.append({
            'district_id': dist,
            'n_depositos': grp.deposit_id.nunique(),
            'depositos': ', '.join(sorted(grp.deposit_id.unique())),
            'celdas_confirmadas': len(grp),
            'celdas_totales': len(cells_in_dist),
            'area_recintos_km2': round(poly_area_total, 2),
            'n_recintos_documentados': len(doc_polys),
            'n_recintos_regionales_excluidos': len(regional_polys),
            'metodo_delimitacion': metodo,
            'estado_delimitacion': estado,
            'recintos_documentados': '; '.join(poly_descs[:3]) if poly_descs else 'Sin recintos locales <= 100 km²'
        })

    # 4. Comprobar solapamientos entre distritos
    assigned_cells = {}
    for dist, data in district_cells.items():
        for c in data['cells']:
            if c in assigned_cells:
                raise ValueError(f"Conflicto de distrito en celda {c}: {assigned_cells[c]} vs {dist}")
            assigned_cells[c] = (dist, data['metodo'], data['estado'])

    print(f"Total celdas asignadas a los 32 distritos: {len(assigned_cells)}")
    print(f"Total celdas de fondo no asignadas: {n_total_cells - len(assigned_cells):,}")

    # 5. Construir DataFrame territorial completo (496.855 filas)
    records = []
    for c in grid.cell_id:
        if c in assigned_cells:
            dist, metodo, estado = assigned_cells[c]
            records.append({
                'cell_id': c,
                'district_id': dist,
                'metodo_delimitacion': metodo,
                'estado_delimitacion': estado
            })
        else:
            records.append({
                'cell_id': c,
                'district_id': '',
                'metodo_delimitacion': 'fondo_territorial',
                'estado_delimitacion': 'fondo_no_asignado'
            })

    df_territorial = pd.DataFrame(records)
    assert len(df_territorial) == n_total_cells, "Error en número total de celdas."
    assert set(df_territorial.cell_id) == set(grid.cell_id), "Error: celdas no coinciden con la rejilla de Fase D."

    # Guardar territorial_groups.csv
    out_csv = ROOT / 'data/review/territorial_groups.csv'
    print(f"Guardando cartografía territorial en {out_csv}...")
    df_territorial.to_csv(out_csv, index=False, encoding='utf-8')

    # Guardar metadatos de los distritos
    df_meta = pd.DataFrame(district_metadata)
    meta_csv = ROOT / 'data/review/inventario_distritos_metalogeneticos.csv'
    print(f"Guardando inventario de distritos en {meta_csv}...")
    df_meta.to_csv(meta_csv, index=False, encoding='utf-8-sig')

    # 6. Verificación de concordancia estricta con indicios confirmados (contrato evaluation.py)
    reviewed_cells = conf[['cell_id', 'district_id']].drop_duplicates()
    mapped = reviewed_cells.merge(df_territorial[['cell_id', 'district_id']], on='cell_id', suffixes=('_record', '_map'))
    discordances = mapped[mapped.district_id_record.fillna('') != mapped.district_id_map.fillna('')]
    assert len(discordances) == 0, f"Error: discordancia entre indicios y mapa territorial:\n{discordances}"
    print("Validación de concordancia indicios-cartografía: 100% satisfactoria (0 discordancias).")

    return df_territorial, df_meta

if __name__ == '__main__':
    build_territorial_cartography()
