"""Fase D: variables territoriales candidatas, sin entrenamiento ni imputación.

La ejecución consume C sellada. Los bloques son reejecutables dentro de una
ejecución D solo si sus salidas y entradas conservan sus hashes.
"""
from datetime import datetime, timezone
from pathlib import Path
import ast
import json
import shutil
import sqlite3
import unicodedata
import importlib.metadata

import geopandas as gpd
import numpy as np
import pandas as pd
import pyogrio
import rasterio
from scipy import ndimage
from scipy.signal import fftconvolve
import shapely
import yaml

from .local_sources import sha256_file, write_json, environment_info
from .territory import grid_spec, land_areas, aggregate_values, aggregate_sum, save_raster


def read_json(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def norm(value):
    if pd.isna(value):
        return ''
    return ' '.join(''.join(c for c in unicodedata.normalize('NFKD', str(value))
                            if not unicodedata.combining(c)).lower().split())


def structural_class(value):
    """Reglas textuales conservadoras; lo no reconocido queda excluido."""
    t = norm(value)
    if any(x in t for x in ('agua', 'borde', 'limite', 'escombr', 'corta', 'simbolo')):
        return 'excluido'
    certainty = 'supuesta' if any(x in t for x in ('supuest', 'ocult', 'inferid')) else 'cartografiada'
    if 'cabalg' in t:
        return 'cabalgamiento_' + certainty
    if 'falla' in t or 'cizalla' in t:
        return 'falla_' + certainty
    if 'contacto intrusivo' in t:
        return 'contacto_intrusivo_' + certainty
    return 'excluido'


LINE_GROUPS = [f'{a}_{b}' for a in ['falla', 'cabalgamiento', 'contacto_intrusivo']
               for b in ['cartografiada', 'supuesta']]


def verify_records(base, records, *, check_sha256=True):
    for item in records:
        p = base / item['path']
        if not p.is_file() or (check_sha256 and sha256_file(p) != item['sha256']):
            raise ValueError(f'Entrada/salida modificada o ausente: {p}')


def records(base, paths):
    return [{'path': p.relative_to(base).as_posix(), 'sha256': sha256_file(p),
             'size_bytes': p.stat().st_size} for p in paths]


def start_run(root, config_path=None, *, verify_phase_c_sha256=True):
    root = Path(root).resolve()
    config_path = Path(config_path or root / 'config/features.yaml')
    cfg = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    c = root / cfg['phase_c_run']
    if read_json(c / 'control_cierre.json')['estado_ejecucion'] != 'completada':
        raise ValueError('La fase C seleccionada no terminó.')
    # C selló sus productos: verificar antes de cualquier cálculo.
    verify_records(c, read_json(c / 'outputs_manifest.json'), check_sha256=verify_phase_c_sha256)
    if cfg['structural_source'] != 'contactos_geode':
        raise ValueError('V1 admite GEODE como única fuente estructural; no combina MAGNA.')
    spec = read_json(c / 'grid_spec.json')
    if not 0 < cfg['minimum_valid_fraction'] <= 1 or not 0 < cfg['terrain_minimum_neighborhood_fraction'] <= 1:
        raise ValueError('Fracciones fuera de (0,1].')
    if cfg['tile_cells'] <= 0 or cfg['distance_cap_m'] <= 0 or cfg['rgb_max_distance'] < 0:
        raise ValueError('Parámetros espaciales/color inválidos.')
    if max(cfg['density_radii_m'] + cfg['terrain_radii_m']) <= 0 or min(cfg['density_radii_m'] + cfg['terrain_radii_m']) <= 0:
        raise ValueError('Radios deben ser positivos.')
    if cfg['distance_cap_m'] > spec['vector_margin_m']:
        raise ValueError('Distancia de búsqueda mayor que el margen conservado por C.')
    external = [root / 'MDT_Espana_CNIG_500m.tif', config_path, Path(__file__).resolve(),
                root / 'src/geoau/territory.py', root / 'src/geoau/local_sources.py']
    external += sorted(root.glob('AtlasGeoquimico_*_Sedimentos_2012*.tif'))
    external += [root / n for n in PALETTE_SCRIPTS]
    # Las fuentes numéricas y el MDT deben ser los inventariados en A enlazada por C.
    a = root / read_json(c / 'inputs.json')['phase_a_run']
    source_hash = {r['path']: r.get('sha256') for r in read_json(a / 'manifest.json')['sources']}
    for p in external:
        if p.suffix == '.tif' and source_hash.get(p.name) != sha256_file(p):
            raise ValueError(f'Fuente distinta de A enlazada: {p.name}')
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    out = root / cfg['output_directory'] / stamp
    out.mkdir(parents=True)
    for name in ['rasters', 'dictionaries', 'blocks']:
        (out / name).mkdir()
    write_json(out / 'config_snapshot.json', cfg)
    write_json(out / 'inputs.json', {'phase_c_run': cfg['phase_c_run'],
        'verify_phase_c_sha256': verify_phase_c_sha256,
        'external': records(root, external),
        'c_manifest_sha256': sha256_file(c / 'outputs_manifest.json')})
    shutil.copy2(Path(__file__), out / 'features_source.py')
    env = environment_info()
    env['packages'].update({n: importlib.metadata.version(n) for n in ['numpy','scipy','pyarrow']})
    write_json(out / 'environment.json', env)
    write_json(out / 'control_cierre.json', {'estado_ejecucion': 'en_curso',
               'fase_d_cientifica_cerrada': False, 'prediction_allowed': False})
    write_json(root / cfg['output_directory'] / 'current_run.json', {'run': out.relative_to(root).as_posix()})
    print('Ejecución D:', out, flush=True)
    return out


def current_run(root):
    root = Path(root).resolve()
    cfg = yaml.safe_load((root / 'config/features.yaml').read_text(encoding='utf-8'))
    out = root / read_json(root / cfg['output_directory'] / 'current_run.json')['run']
    if read_json(out / 'config_snapshot.json') != cfg:
        raise ValueError('Cambió features.yaml: iniciar una nueva ejecución con el cuaderno 03.')
    return out


COMPUTE_FUNCTIONS = {
    'geology': ['geology','categorical_areas','clip_to_mask','cell_boxes','tiles','vector_read','meta'],
    'terrain': ['terrain','terrain_arrays','disk_kernel','raster_check','meta'],
    'geochemistry': ['geochemistry','color_quality','local_palettes','raster_check','meta'],
    'structural': ['lines','line_lengths','nearest_distances','disk_kernel','structural_class','norm','clip_to_mask','cell_boxes','tiles','vector_read','meta'],
    'hydrology': ['lines','line_lengths','nearest_distances','disk_kernel','structural_class','norm','clip_to_mask','cell_boxes','tiles','vector_read','meta'],
}
BLOCK_PARAMETERS = {
    'geology': ['tile_cells','minimum_valid_fraction'],
    'terrain': ['minimum_valid_fraction','terrain_radii_m','terrain_minimum_neighborhood_fraction'],
    'geochemistry': ['minimum_valid_fraction','rgb_max_distance','rgb_min_class_margin'],
    'structural': ['tile_cells','structural_source','distance_cap_m','density_radii_m'],
    'hydrology': ['tile_cells','distance_cap_m','density_radii_m'],
}


def compute_signature(source, block):
    tree=ast.parse(source)
    funcs={n.name:ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.FunctionDef)}
    constants=[ast.dump(n,include_attributes=False) for n in tree.body if isinstance(n,ast.Assign)
               and any(isinstance(t,ast.Name) and t.id in ('LINE_GROUPS','PALETTE_SCRIPTS') for t in n.targets)]
    # Constantes usadas en la extracción; las tablas de orquestación no son cálculo.
    return [funcs.get(n) for n in COMPUTE_FUNCTIONS[block]], constants


def reuse_verified_blocks(root,out):
    """Solo reutiliza productos sellados con cálculo, soporte e inputs equivalentes."""
    root,out=Path(root).resolve(),Path(out).resolve()
    config=read_json(out/'config_snapshot.json');inputs=read_json(out/'inputs.json')
    source=(out/'features_source.py').read_text(encoding='utf-8')
    audit=[]
    candidates=sorted([p for p in out.parent.iterdir() if p.is_dir() and p!=out],reverse=True)
    for block in BLOCKS:
        if (out/'blocks'/f'{block}_manifest.json').exists():continue
        for previous in candidates:
            seal=previous/'blocks'/f'{block}_manifest.json'
            if not seal.exists():continue
            try:
                oldconfig=read_json(previous/'config_snapshot.json');oldinputs=read_json(previous/'inputs.json')
                if oldinputs['c_manifest_sha256']!=inputs['c_manifest_sha256']:continue
                if oldinputs['phase_c_run']!=inputs['phase_c_run']:continue
                if any(oldconfig.get(k)!=config.get(k) for k in BLOCK_PARAMETERS[block]):continue
                oldsource=(previous/'features_source.py').read_text(encoding='utf-8')
                # Verificar que el snapshot pertenece realmente a la ejecución.
                code_record=next(r for r in oldinputs['external'] if r['path']=='src/geoau/features.py')
                if sha256_file(previous/'features_source.py')!=code_record['sha256']:continue
                if compute_signature(oldsource,block)!=compute_signature(source,block):continue
                other=[r for r in oldinputs['external'] if r['path'] not in ('src/geoau/features.py','config/features.yaml')]
                verify_records(root,other)
                entries=read_json(seal);verify_records(previous,entries)
                for item in entries:
                    dst=out/item['path'];dst.parent.mkdir(parents=True,exist_ok=True)
                    shutil.copy2(previous/item['path'],dst)
                shutil.copy2(seal,out/'blocks'/seal.name)
                shutil.copy2(previous/'features_source.py',out/f'reused_{block}_source.py')
                audit.append({'block':block,'source_run':previous.relative_to(root).as_posix(),
                    'source_code_sha256':code_record['sha256'],'source_manifest_sha256':sha256_file(seal),
                    'reason':'funciones AST, parámetros, entradas y soporte equivalentes; hashes verificados'})
                print('Recuperado',block,'desde',previous.name,flush=True)
                break
            except (ValueError,KeyError,FileNotFoundError,StopIteration) as error:
                audit.append({'block':block,'source_run':str(previous),'rejected':str(error)})
    write_json(out/'reuse_audit.json',audit)
    return audit


def ensure_run(root, *, verify_phase_c_sha256=False):
    """Reanuda una ejecución compatible; crea otra si código/configuración cambió."""
    try:
        out=current_run(root)
        source=read_json(out/'inputs.json')['external']
        entry=next(r for r in source if r['path']=='src/geoau/features.py')
        if entry['sha256']==sha256_file(Path(__file__)):
            return out
    except (FileNotFoundError,ValueError,StopIteration):
        pass
    out=start_run(root, verify_phase_c_sha256=verify_phase_c_sha256)
    reuse_verified_blocks(root,out)
    return out


def context(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    cfg = read_json(out / 'config_snapshot.json')
    inp = read_json(out / 'inputs.json')
    c = root / inp['phase_c_run']
    verify_records(root, inp['external'])
    if sha256_file(c / 'outputs_manifest.json') != inp['c_manifest_sha256']:
        raise ValueError('Cambió el manifiesto C.')
    verify_records(c, read_json(c / 'outputs_manifest.json'),
                   check_sha256=inp.get('verify_phase_c_sha256', True))
    spec = grid_spec(read_json(c / 'grid_spec.json'))
    grid = pd.read_csv(c / 'grid_1km.csv.gz')
    if not grid.cell_id.is_unique:
        raise ValueError('cell_id duplicado en C.')
    mask = gpd.read_file(c / 'coverage.gpkg', layer='mascara_peninsular').geometry.iloc[0]
    return cfg, c, spec, grid, mask


def tiles(grid, size):
    for _, block in grid.groupby([grid.row // size, grid.col // size], sort=True):
        yield block


def cell_boxes(grid, spec):
    x = spec['origin_x'] + grid.col.to_numpy() * spec['resolution_m']
    y = spec['origin_y'] - grid.row.to_numpy() * spec['resolution_m']
    return shapely.box(x, y-spec['resolution_m'], x+spec['resolution_m'], y)


def clip_to_mask(geometries, mask):
    """No recalcula intersecciones de entidades contenidas; resultado equivalente."""
    geometries = np.asarray(geometries,dtype=object).copy()
    shapely.prepare(mask)
    needs_clip = ~shapely.covers(mask,geometries)
    geometries[needs_clip] = shapely.intersection(geometries[needs_clip],mask)
    return geometries


def raster_check(src, spec, native=False):
    if (src.crs != rasterio.crs.CRS.from_user_input(spec['crs']) or
        src.shape != tuple(spec['native_shape'] if native else spec['shape']) or
        src.transform != spec['native_transform' if native else 'transform']):
        raise ValueError(f'Rejilla incompatible: {src.name}')


def vector_read(path, bbox, columns):
    frame = pyogrio.read_dataframe(path, bbox=bbox, columns=columns)
    if frame.crs is None or frame.crs.to_epsg() != 25830:
        raise ValueError(f'CRS vectorial inesperado: {path}')
    return frame


def finish_block(out, name, x, quality, metadata, extra_paths=()):
    if not x.cell_id.is_unique or not quality.cell_id.equals(x.cell_id):
        raise ValueError('Claves incompatibles dentro del bloque.')
    paths = []
    for suffix, frame in [('features', x), ('quality', quality)]:
        p = out / 'blocks' / f'{name}_{suffix}.parquet'
        frame.to_parquet(p, index=False); paths.append(p)
    p = out / 'blocks' / f'{name}_dictionary.json'
    write_json(p, metadata); paths.append(p)
    paths += list(extra_paths)
    write_json(out / 'blocks' / f'{name}_manifest.json', records(out, paths))
    return x, quality


def cached(out, name):
    p = out / 'blocks' / f'{name}_manifest.json'
    if not p.exists():
        return None
    verify_records(out, read_json(p))
    print('Bloque verificado:', name, flush=True)
    return (pd.read_parquet(out / 'blocks' / f'{name}_features.parquet'),
            pd.read_parquet(out / 'blocks' / f'{name}_quality.parquet'))


def meta(name, source, units, method, status='candidata', representation='numeric'):
    return dict(name=name, source=source, units=units, method=method,
                status=status, representation=representation, allowed_as_candidate=True,
                approved_for_training=False, missing='NaN; sin imputar', target='general; validar por proceso')


def categorical_areas(polygons, values, cells):
    """Intersecciones exactas; disuelve por categoría y audita cobertura/solape.

    Devuelve superficies por categoría y unión total. La unión por clase elimina
    solapes repetidos dentro de la misma clase sin sumar doble su superficie.
    """
    values = np.asarray(values, dtype=str)
    categories = sorted(set(values))
    dissolved = [shapely.union_all(polygons[values == v]) for v in categories]
    masses = np.zeros((len(cells), len(categories)))
    for k, geom in enumerate(dissolved):
        idx = np.where(shapely.intersects(cells, geom))[0]
        masses[idx, k] = shapely.area(shapely.intersection(cells[idx], geom))
    union = shapely.union_all(dissolved)
    area = shapely.area(shapely.intersection(cells, union))
    overlap = np.maximum(0, masses.sum(axis=1)-area)
    return categories, masses, area, overlap


def geology(root, out):
    cfg, c, spec, grid, mask = context(root, out)
    old = cached(out, 'geology')
    if old is not None: return old
    x, q, metadata, paths = grid[['cell_id']].copy(), grid[['cell_id']].copy(), [], []
    for alias, field in [('litologia', 'Litologia'), ('edades', 'SISTEMA')]:
        path = c / 'vectors' / f'{alias}.gpkg'
        raw = pyogrio.read_dataframe(path, columns=[field], read_geometry=False)[field]
        names = sorted(set(raw.map(lambda v: str(v).strip() if pd.notna(v) and str(v).strip() else 'SIN_ATRIBUTO')))
        ids = {v: f'{alias}_u{i:03d}' for i, v in enumerate(names)}
        dictionary = pd.DataFrame({'category_id': list(ids.values()), 'description': names})
        dictionary['interpretation'] = 'unidad original; mezcla interna no desagregada'
        p = out / 'dictionaries' / f'{alias}.csv'; dictionary.to_csv(p, index=False, encoding='utf-8-sig'); paths.append(p)
        fractions = np.full((len(grid),len(names)), np.nan, dtype='float32')
        cover, overlap, unknown = [np.zeros(len(grid)) for _ in range(3)]
        dominant = np.full(len(grid), None, dtype=object)
        for number, tile in enumerate(tiles(grid, cfg['tile_cells']), 1):
            cells = clip_to_mask(cell_boxes(tile, spec), mask)
            bounds = shapely.total_bounds(cells)
            frame = vector_read(path, tuple(bounds), [field])
            vals = frame[field].map(lambda v: str(v).strip() if pd.notna(v) and str(v).strip() else 'SIN_ATRIBUTO')
            # Recortar antes de disolver evita arrastrar partes ajenas a la tesela.
            polygons = shapely.intersection(frame.geometry.to_numpy(),shapely.box(*bounds))
            cats, masses, area, ov = categorical_areas(polygons, vals, cells)
            denom = shapely.area(cells)
            idx = tile.index.to_numpy()
            cover[idx], overlap[idx] = area/denom, ov/denom
            if 'SIN_ATRIBUTO' in cats: unknown[idx] = masses[:,cats.index('SIN_ATRIBUTO')]/denom
            valid = (cover[idx]-unknown[idx] >= cfg['minimum_valid_fraction']) & (ov <= np.maximum(1,denom*1e-6))
            fractions[idx[valid],:] = 0
            for k, cat in enumerate(cats):
                fractions[idx[valid],names.index(cat)] = (masses[valid,k]/denom[valid]).astype('float32')
            if cats:
                best = np.argmax(masses,axis=1)
                dominant[idx[valid]] = [ids[cats[k]] for k in best[valid]]
            if number % 10 == 0: print(alias, 'teselas', number, flush=True)
        x[f'{alias}_dominante'] = dominant
        metadata.append(meta(f'{alias}_dominante',alias,'categoria','mayor área terrestre; empate por texto ordenado',representation='categorical'))
        for i, name in enumerate(names):
            if name == 'SIN_ATRIBUTO': continue
            col = ids[name] + '_fraccion'
            x[col] = fractions[:,i]
            metadata.append(meta(col,alias,'m2/m2 terrestre','intersección exacta; fracción de unidad mixta, no de mineral'))
        q[f'{alias}_cobertura'] = cover
        q[f'{alias}_solape_fraccion'] = overlap
        q[f'{alias}_sin_atributo_fraccion'] = unknown
    return finish_block(out,'geology',x,q,metadata,paths)


def disk_kernel(radius, pixel, fractional=False):
    n = int(np.ceil(radius/pixel))
    yy, xx = np.mgrid[-n:n+1,-n:n+1]
    if not fractional:
        return ((xx*pixel)**2+(yy*pixel)**2 <= radius**2).astype(float)
    circle = shapely.Point(0,0).buffer(radius,quad_segs=128)
    boxes = shapely.box(xx*pixel-pixel/2, yy*pixel-pixel/2,xx*pixel+pixel/2, yy*pixel+pixel/2)
    return shapely.area(shapely.intersection(boxes,circle))/pixel**2


def nearest_distances(points, lines, cap):
    result = np.full(len(points), np.nan)
    if len(lines):
        pairs, distances = shapely.STRtree(lines).query_nearest(points,max_distance=cap,
                                                               return_distance=True,all_matches=False)
        result[pairs[0]] = distances
    return result


def line_lengths(lines, cells, outer_boundary=None):
    """Longitud por celda; media longitud sobre bordes compartidos (sin doble suma)."""
    result = np.zeros(len(cells))
    if not len(lines): return result
    if outer_boundary is None:
        outer_boundary=shapely.boundary(shapely.union_all(cells))
    # Nodar/disolver evita contar dos veces las trazas geométricamente coincidentes.
    lines = shapely.get_parts(shapely.union_all(lines))
    tree = shapely.STRtree(cells)
    for start in range(0,len(lines),2000):
        part = lines[start:start+2000]
        li, ci = tree.query(part,predicate='intersects')
        pieces = shapely.intersection(part[li],cells[ci])
        length = shapely.length(pieces)
        on_edge=shapely.intersection(pieces,shapely.boundary(cells[ci]))
        shared=shapely.length(on_edge)-shapely.length(shapely.intersection(on_edge,outer_boundary))
        length -= .5*np.maximum(0,shared)
        np.add.at(result,ci,length)
    return result


def lines(root, out, hydro=False):
    cfg,c,spec,grid,mask = context(root,out)
    name = 'hydrology' if hydro else 'structural'
    old = cached(out,name)
    if old is not None: return old
    alias = 'hidrografia' if hydro else cfg['structural_source']
    path = c/'vectors'/f'{alias}.gpkg'
    field = None if hydro else 'DESC_LINE'
    groups = ['cauce'] if hydro else LINE_GROUPS
    x,q = grid[['cell_id']].copy(),grid[['cell_id']].copy()
    metadata, extras = [], []
    distance = {g:np.full(len(grid),np.nan) for g in groups}
    length = {g:np.zeros(spec['shape']) for g in groups}
    if not hydro:
        raw = pyogrio.read_dataframe(path,columns=[field],read_geometry=False)[field].value_counts(dropna=False)
        d = pd.DataFrame({'description':raw.index,'entities':raw.values})
        d['group'] = d.description.map(structural_class); d['status']='regla textual candidata; revisar leyenda'
        p = out/'dictionaries/estructuras.csv';d.to_csv(p,index=False,encoding='utf-8-sig');extras.append(p)
    cap = cfg['distance_cap_m']
    outer_boundary=shapely.box(spec['origin_x'],spec['origin_y']-spec['height']*1000,
                             spec['origin_x']+spec['width']*1000,spec['origin_y']).boundary
    for number,tile in enumerate(tiles(grid,cfg['tile_cells']),1):
        cells = cell_boxes(tile,spec)
        bounds = shapely.total_bounds(cells)
        extent = shapely.box(*bounds)
        bbox = (bounds[0]-cap,bounds[1]-cap,bounds[2]+cap,bounds[3]+cap)
        frame = vector_read(path,bbox,[] if hydro else [field])
        classes = np.full(len(frame),'cauce') if hydro else frame[field].map(structural_class).to_numpy()
        points = shapely.points(tile.x_center,tile.y_center)
        for group in groups:
            geoms = frame.geometry.to_numpy()[classes==group]
            distance[group][tile.index] = nearest_distances(points,geoms,cap)
            selected = geoms[shapely.intersects(geoms,extent)]
            clipped = clip_to_mask(shapely.intersection(selected,extent),mask)
            length[group][tile.row,tile.col] = line_lengths(clipped,cells,outer_boundary)
        if number % 5 == 0: print(name,'teselas',number,flush=True)
    land = np.zeros(spec['shape']);land[grid.row,grid.col]=grid.land_area_m2
    for group in groups:
        col=f'dist_{group}_m'
        x[col] = distance[group].astype('float32')
        q[f'{group}_sin_traza_en_{cap}m'] = ~np.isfinite(distance[group])
        metadata.append(meta(col,alias,'m',f'centro a traza cartografiada; NaN sin traza dentro de {cap} m; cobertura no acreditada'))
        for radius in cfg['density_radii_m']:
            kernel=disk_kernel(radius,1000,fractional=True)
            numerator=np.maximum(0,fftconvolve(length[group],kernel,mode='same'))
            numerator[numerator<1e-7]=0  # ruido de redondeo FFT, metros de longitud
            denominator=np.maximum(0,fftconvolve(land,kernel,mode='same'))
            density=np.divide(numerator*1000,denominator,out=np.full_like(numerator,np.nan),where=denominator>1)
            col=f'dens_aprox_{group}_{radius}m_km_km2'
            x[col]=density[grid.row,grid.col].astype('float32')
            q[f'{name}_soporte_terrestre_{radius}m']=(denominator/(kernel.sum()*1e6))[grid.row,grid.col]
            metadata.append(meta(col,alias,'km/km2','longitud exacta por celda; ventana circular con reparto uniforme subcelda; no acredita ausencia',status='experimental_aproximacion_1km'))
    q[f'{name}_cobertura_levantamiento_acreditada']=False
    return finish_block(out,name,x,q,metadata,extras)


PALETTE_SCRIPTS = {'generar_mapa_geoquimica_oro.py':('Au','PALETTE_LAYER0'),
    'generar_mapa_geoquimica_arsenico.py':('As','PALETTE_LAYER0_AS'),
    'generar_mapa_geoquimica_antimonio.py':('Sb','PALETTE_LAYER0_SB'),
    'generar_mapa_geoquimica_bismuto.py':('Bi','PALETTE_LAYER0_BI'),
    'generar_mapas_geoquimica_batch.py':(None,'TARGET_ELEMENTS')}


def local_palettes(root):
    """Lee constantes con AST; nunca importa/ejecuta scripts de descarga históricos."""
    result={}
    for filename,(element,name) in PALETTE_SCRIPTS.items():
        tree=ast.parse((Path(root)/filename).read_text(encoding='utf-8-sig'))
        found=False
        for node in tree.body:
            if isinstance(node,ast.Assign) and any(isinstance(t,ast.Name) and t.id==name for t in node.targets):
                value=ast.literal_eval(node.value);found=True
                if element: result[element]=value
                else: result.update({k:v['clases'] for k,v in value.items()})
        if not found: raise ValueError(f'Paleta ausente: {filename}')
    return result


def color_quality(rgb, classes, valid, palette, threshold=0, minimum_margin=0):
    """Distancia al color de la clase declarada; evita matriz píxeles x clases."""
    colors=np.asarray([p[1] for p in palette],dtype=float)
    ok=valid & np.isfinite(classes) & (classes==np.floor(classes)) & (classes>=0) & (classes<len(colors))
    diff=np.full(classes.shape,np.nan)
    idx=np.where(ok)
    diff[idx]=np.linalg.norm(rgb[:,idx[0],idx[1]].T.astype(float)-colors[classes[idx].astype(int)],axis=1)
    accepted=ok & (diff<=threshold)
    if minimum_margin>0:
        # Comprobar solo los colores únicos, evitando píxeles x clases en memoria.
        ii=np.where(accepted);unique,inverse=np.unique(rgb[:,ii[0],ii[1]].T,axis=0,return_inverse=True)
        distances=np.linalg.norm(unique[:,None,:].astype(float)-colors[None,:,:],axis=2)
        order=np.argsort(distances,axis=1)
        margin=np.take_along_axis(distances,order[:,1:2],axis=1)[:,0]-np.take_along_axis(distances,order[:,:1],axis=1)[:,0]
        accepted[ii]=(order[inverse,0]==classes[ii]) & (margin[inverse]>=minimum_margin)
    return accepted,diff


def geochemistry(root,out):
    cfg,c,spec,grid,mask=context(root,out)
    old=cached(out,'geochemistry')
    if old is not None: return old
    land=land_areas(mask,spec['native_shape'],spec['native_transform'])
    x,q=grid[['cell_id']].copy(),grid[['cell_id']].copy()
    metadata,extras,audit,legend=[],[],[],[]
    for element,palette in local_palettes(root).items():
        print('RGB/geoquímica',element,flush=True)
        alias=f'geoquimica_{element.lower()}'
        with rasterio.open(Path(root)/f'AtlasGeoquimico_{element}_Sedimentos_2012.tif') as src:
            raster_check(src,spec,True);a=src.read(1,masked=True)
        with rasterio.open(Path(root)/f'AtlasGeoquimico_{element}_Sedimentos_2012_RGB.tif') as src:
            raster_check(src,spec,True);rgb=src.read([1,2,3]);visible=src.dataset_mask()>0
            if src.count>=4: visible &= src.read(4)==255
        original=~np.ma.getmaskarray(a) & np.isfinite(a.data)
        valid,difference=color_quality(rgb,a.data,original & visible,palette,cfg['rgb_max_distance'],cfg.get('rgb_min_class_margin',0))
        mode,frac,props=aggregate_values(a.data,valid,land,len(palette))
        accepted=(frac>=cfg['minimum_valid_fraction'])
        arrays=[mode,frac,*props]
        desc=['clase_modal','fraccion_valida_rgb']+[f'proporcion_clase_{k}' for k in range(len(palette))]
        p=out/'rasters'/f'{alias}_rgb_controlado_1km.tif'
        save_raster(p,arrays,desc,spec);extras.append(p)
        row,col=grid.row.to_numpy(),grid.col.to_numpy()
        name=f'{element.lower()}_clase_modal'
        x[name]=np.where(accepted[row,col],mode[row,col],np.nan).astype('float32')
        metadata.append(meta(name,alias,'clase ordinal','moda ponderada; empate clase menor; RGB coincidente; leyenda local pendiente',status='leyenda_local_no_validada',representation='ordinal'))
        for k,palette_row in enumerate(palette):
            name=f'{element.lower()}_proporcion_clase_{k}'
            x[name]=np.where(accepted[row,col],props[k,row,col],np.nan).astype('float32')
            metadata.append(meta(name,alias,'fraccion sobre area valida','proporciones alternativas a moda; no concentraciones',status='leyenda_local_no_validada'))
            legend.append({'element':element,'class':k,'rgb':str(palette_row[1]),'label_local':palette_row[2],
                           'lower_local':palette_row[3],'upper_local':palette_row[4],
                           'status':'extraída de script local; validar medio, extracción y unidades oficiales'})
        q[f'{alias}_valid_rgb']=frac[row,col]
        with rasterio.open(c/'rasters'/f'{alias}_1km.tif') as src:
            raster_check(src,spec); previous=src.read(1)
        both=(mode!=-9999)&(previous!=-9999)
        audit.append({'element':element,'valid_native_original_land':int((original&(land>0)).sum()),
            'accepted_native_land':int((valid&(land>0)).sum()),
            'rejected_native_land':int((original&~valid&(land>0)).sum()),
            'modal_changed_vs_C':int((both&(mode!=previous)&(aggregate_sum(land)>0)).sum()),
            'cells_sufficient_rgb':int(accepted[row,col].sum()),'official_legend_validated':False,
            'rgb_max_distance':cfg['rgb_max_distance'],
            'rgb_min_class_margin':cfg.get('rgb_min_class_margin',0),
            'pixels_exact_land':int((original&visible&(difference==0)&(land>0)).sum()),
            'pixels_within_2_land':int((original&visible&(difference<=2)&(land>0)).sum()),
            'pixels_within_8_land':int((original&visible&(difference<=8)&(land>0)).sum())})
    for filename,data in [('geoquimica_rgb_qc.csv',audit),('dictionaries/geoquimica_leyendas_locales.csv',legend)]:
        p=out/filename;pd.DataFrame(data).to_csv(p,index=False,encoding='utf-8-sig');extras.append(p)
    return finish_block(out,'geochemistry',x,q,metadata,extras)


def terrain_arrays(z,valid,pixel,radii,min_fraction):
    """Pendiente de diferencias centrales (cruz completa) y estadística circular."""
    z=np.where(valid,z,np.nan).astype(float)
    slope=np.full(z.shape,np.nan)
    dx=(z[1:-1,2:]-z[1:-1,:-2])/(2*pixel)
    dy=(z[2:,1:-1]-z[:-2,1:-1])/(2*pixel)
    slope[1:-1,1:-1]=np.degrees(np.arctan(np.hypot(dx,dy)))
    slope[~valid]=np.nan
    result={'pendiente_grados':slope}
    for radius in radii:
        kernel=disk_kernel(radius,pixel)
        count=ndimage.convolve(valid.astype(float),kernel,mode='constant',cval=0)
        total=ndimage.convolve(np.where(valid,z,0),kernel,mode='constant',cval=0)
        second=ndimage.convolve(np.where(valid,z*z,0),kernel,mode='constant',cval=0)
        mean=np.divide(total,count,out=np.zeros_like(total),where=count>0)
        variance=np.divide(second,count,out=np.zeros_like(total),where=count>0)-mean**2
        enough=valid & (count/kernel.sum()>=min_fraction)
        result[f'tpi_{radius}m_m']=np.where(enough,z-mean,np.nan)
        result[f'desv_elevacion_{radius}m_m']=np.where(enough,np.sqrt(np.maximum(0,variance)),np.nan)
    return result


def terrain(root,out):
    cfg,c,spec,grid,mask=context(root,out)
    old=cached(out,'terrain')
    if old is not None: return old
    land=land_areas(mask,spec['native_shape'],spec['native_transform'])
    with rasterio.open(Path(root)/'MDT_Espana_CNIG_500m.tif') as src:
        raster_check(src,spec,True);a=src.read(1,masked=True)
    valid=~np.ma.getmaskarray(a)&np.isfinite(a.data)&(land>0)
    result=terrain_arrays(a.data,valid,500,cfg['terrain_radii_m'],cfg['terrain_minimum_neighborhood_fraction'])
    result={'elevacion_media_m':np.where(valid,a.data,np.nan),**result}
    x,q=grid[['cell_id']].copy(),grid[['cell_id']].copy()
    metadata,extra=[],[]
    for name,values in result.items():
        mean,frac,_=aggregate_values(values,np.isfinite(values),land)
        row,col=grid.row.to_numpy(),grid.col.to_numpy()
        x[name]=np.where(frac[row,col]>=cfg['minimum_valid_fraction'],mean[row,col],np.nan).astype('float32')
        q[f'{name}_valid_fraction']=frac[row,col]
        p=out/'rasters'/f'{name}_1km.tif';save_raster(p,[mean,frac],[name,'valid_fraction'],spec);extra.append(p)
        metadata.append(meta(name,'MDT banda 1','grados' if name=='pendiente_grados' else 'm',
            'derivación nativa 500m; TPI z-media circular incluyendo centro; desviación poblacional; media terrestre a 1km'))
    return finish_block(out,'terrain',x,q,metadata,extra)


BLOCKS=['geology','structural','geochemistry','terrain','hydrology']


def geological_associations(x,out):
    """Agrupa unidades explícitas; ninguna fracción interna de roca se inventa."""
    d=pd.read_csv(out/'dictionaries/litologia.csv')
    rules={
        'unidades_granitoides_explicitos':['Granitoides de dos micas','Otros granitoides'],
        'unidades_mixtas_con_granitoides':['Migmatitas, mármoles y granitoides indiferenciados'],
        'unidades_volcanicas':['Vulcanitas y rocas volcanoclásticas'],
        'unidades_basicas_ultrabasicas':['Serpentinitas y peridotitas. Rocas básicas y ultrabásicas'],
        'unidades_con_gneisses':['Gneisses'],
        'unidades_con_gravas_arenas_limos':['Gravas, conglomerados, arenas y limos'],
    }
    lookup=dict(zip(d.description.map(norm),d.category_id))
    metadata=[];audit=[]
    for group,descriptions in rules.items():
        if not all(norm(desc) in lookup for desc in descriptions):
            raise ValueError(f'Revisar diccionario de asociación {group}: descripción ausente.')
        columns=[lookup[norm(desc)]+'_fraccion' for desc in descriptions]
        name=group+'_fraccion'
        x[name]=x[columns].sum(axis=1,min_count=len(columns)).astype('float32')
        metadata.append(meta(name,'litologia','fracción de área terrestre','suma de unidades explícitas; no proporción interna de roca',status='asociacion_textual_candidata'))
        audit.extend({'group':group,'description':desc,'category_id':lookup[norm(desc)],
                      'interpretation':'fracción de unidad cartográfica; no fracción mineral interna; grupos pueden solaparse'} for desc in descriptions)
    pd.DataFrame(audit).to_csv(out/'dictionaries/asociaciones_litologicas.csv',index=False,encoding='utf-8-sig')
    return x,metadata


def label_relations(root,c):
    labels=pd.read_csv(c/'indicios_celda_cobertura.csv',dtype={'Codigo_indicio':'string'})
    if not labels.record_id.is_unique or labels.record_id.isna().any():raise ValueError('record_id inválido en C.')
    if labels.positivo_revisado.isna().any() or not labels.positivo_revisado.isin([True,False]).all():
        raise ValueError('positivo_revisado debe contener booleanos no nulos.')
    inputs=read_json(c/'inputs.json');b=Path(root)/inputs['phase_b_run']
    path=b/'etiquetas_au_candidatas.gpkg'
    frozen=[r for r in inputs['frozen_inputs'] if r['path']==path.relative_to(root).as_posix() or Path(root)/r['path']==path]
    if len(frozen)!=1:raise ValueError('No se encuentra el sello B consumido por C.')
    verify_records(Path(root),frozen)
    fields=['record_id','tipo_au_final','tipologia_estado','deposit_id','district_id',
            'position_id','proximity_group_250m','proximity_group_500m','proximity_group_1000m',
            'elegible_general_revisada','elegible_roca_revisada','elegible_aluvial_revisada']
    detail=pyogrio.read_dataframe(path,columns=fields,read_geometry=False)
    if not detail.record_id.is_unique or set(labels.record_id)!=set(detail.record_id):
        raise ValueError('Los indicios de B y C no corresponden.')
    return labels.merge(detail,on='record_id',how='left',validate='one_to_one')


def validate_matrix(x,dictionary):
    allowed=[m['name'] for m in dictionary]
    if not x.cell_id.is_unique or x.cell_id.isna().any():raise ValueError('cell_id inválido.')
    if set(allowed)!=set(x.columns)-{'cell_id'} or len(set(allowed))!=len(allowed):
        raise ValueError('El diccionario no coincide con la lista de variables.')
    for col in x.select_dtypes(include='number'):
        v=x[col].dropna()
        if np.isinf(v).any():raise ValueError(f'Inf en {col}')
        if (col.endswith('_fraccion') or '_proporcion_clase_' in col) and not v.between(0,1+1e-6).all():
            raise ValueError(f'Fracción fuera de [0,1]: {col}')
        if col.startswith(('dist_','dens_aprox_')) and (v<0).any():raise ValueError(f'Negativo: {col}')
    if 'pendiente_grados' in x and not x.pendiente_grados.dropna().between(0,90).all():raise ValueError('Pendiente inválida.')
    for prefix in ('au','as','sb','bi','hg','cu','pb','zn','w'):
        props=x.filter(regex=f'^{prefix}_proporcion_clase_')
        if props.shape[1]:
            complete=props.notna().all(axis=1)
            if not complete.equals(props.notna().any(axis=1)) or not np.allclose(props.loc[complete].sum(axis=1),1,atol=1e-6):
                raise ValueError(f'Proporciones incompletas/no normalizadas: {prefix}')
    return allowed


def write_master(master,out):
    """Archivos deterministas y reemplazo atómico: reintentar no añade filas."""
    out=Path(out)
    temporary=out/'.Grid_Master_Au.parquet.tmp'
    master.to_parquet(temporary,index=False,row_group_size=50000)
    temporary.replace(out/'Grid_Master_Au.parquet')
    for partition,frame in master.groupby('partition_id',sort=True):
        folder=out/'Grid_Master_Au'/f'partition_id={int(partition)}'
        folder.mkdir(parents=True,exist_ok=True)
        temp=folder/'.part-00000.parquet.tmp'
        frame.drop(columns='partition_id').to_parquet(temp,index=False,row_group_size=50000)
        temp.replace(folder/'part-00000.parquet')


def assemble(root,out):
    root,out=Path(root).resolve(),Path(out).resolve()
    cfg,c,spec,grid,mask=context(root,out)
    if (out/'outputs_manifest.json').exists():
        verify_records(out,read_json(out/'outputs_manifest.json'))
        return (pd.read_parquet(out/'X_features.parquet'),pd.read_parquet(out/'calidad_y_soporte.parquet'),
                pd.read_parquet(out/'etiquetas_por_celda.parquet'))
    x,q=grid[['cell_id']].copy(),grid.copy()
    dictionary=[]
    for block in BLOCKS:
        pair=cached(out,block)
        if pair is None: raise ValueError(f'Ejecutar bloque pendiente: {block}')
        bx,bq=pair
        if set(bx.cell_id)!=set(grid.cell_id) or len(bx)!=len(grid):
            raise ValueError(f'Bloque {block} no cubre la misma rejilla.')
        if (set(x.columns)&set(bx.columns))-{'cell_id'} or (set(q.columns)&set(bq.columns))-{'cell_id'}:
            raise ValueError('Columnas duplicadas entre bloques.')
        x=x.merge(bx,on='cell_id',validate='one_to_one',how='left')
        q=q.merge(bq,on='cell_id',validate='one_to_one',how='left')
        dictionary.extend(read_json(out/'blocks'/f'{block}_dictionary.json'))
    x,associations=geological_associations(x,out);dictionary.extend(associations)
    allowed=validate_matrix(x,dictionary)
    # Coberturas heredadas: se etiquetan como auxiliares, nunca se añaden a X.
    coverage=pd.read_csv(c/'coverage_by_cell.csv.gz')
    if not coverage.cell_id.is_unique or set(coverage.cell_id)!=set(grid.cell_id):
        raise ValueError('Cobertura C y rejilla con claves distintas.')
    extra=[k for k in coverage if k not in q and k not in ('n_candidatos','n_positivos_revisados')]
    q=q.merge(coverage[['cell_id',*extra]].rename(columns={k:'fase_c_'+k for k in extra}),on='cell_id',how='left',validate='one_to_one')
    q['eligible_geology_terrain']=q.coastal_eligible & x[['litologia_dominante','edades_dominante','elevacion_media_m','pendiente_grados']].notna().all(axis=1)
    for label,elements in [('geo4',['au','as','sb','bi']),('geo9',['au','as','sb','bi','hg','cu','pb','zn','w'])]:
        q[f'eligible_{label}']=q.eligible_geology_terrain & x[[f'{e}_clase_modal' for e in elements]].notna().all(axis=1)
    q['prediction_allowed']=False
    labels=label_relations(root,c)
    assigned=labels[labels.cell_id.notna()].copy()
    labels.to_parquet(out/'relacion_indicios_celda.parquet',index=False)
    aggregated=assigned.groupby('cell_id').agg(n_candidatos=('record_id','size'),
                      n_positivos_revisados=('positivo_revisado','sum')).reset_index()
    y=grid[['cell_id']].merge(aggregated,on='cell_id',how='left',validate='one_to_one')
    y[['n_candidatos','n_positivos_revisados']]=y[['n_candidatos','n_positivos_revisados']].fillna(0).astype(int)
    y['estado_etiqueta']=np.where(y.n_positivos_revisados>0,'P_revisado',np.where(y.n_candidatos>0,'candidato_no_revisado','U'))
    if len(assigned) and not set(assigned.cell_id).issubset(set(grid.cell_id)):raise ValueError('Etiqueta fuera de la rejilla.')
    # X separada y maestro completo con roles explícitos para evitar fuga.
    x.to_parquet(out/'X_features.parquet',index=False,row_group_size=50000)
    q.to_parquet(out/'calidad_y_soporte.parquet',index=False)
    y.to_parquet(out/'etiquetas_por_celda.parquet',index=False)
    for id_column in ['deposit_id','district_id','proximity_group_500m']:
        relation=assigned[['cell_id',id_column]].dropna().drop_duplicates()
        relation=relation[relation[id_column].astype(str).str.strip().ne('')]
        relation.to_parquet(out/f'relacion_{id_column}_celda.parquet',index=False)
    master=q.merge(x,on='cell_id',validate='one_to_one').merge(y,on='cell_id',validate='one_to_one')
    master['partition_id']=(master.row//100).astype('int16')
    write_master(master,out)
    shutil.copy2(c/'grid_spec.json',out/'grid_spec.json')
    roles=[{'column':col,'role':'predictor_candidato' if col in allowed else 'etiqueta' if col in y and col!='cell_id' else 'clave' if col=='cell_id' else 'auxiliar_no_predictor'} for col in master]
    pd.DataFrame(roles).to_csv(out/'column_roles.csv',index=False,encoding='utf-8-sig')
    del master
    pd.DataFrame(dictionary).to_csv(out/'feature_dictionary.csv',index=False,encoding='utf-8-sig')
    write_json(out/'feature_allowlist.json',{'candidate_columns':allowed,'approved_training_columns':[],
        'exclude_all_other_columns':True,'reason':'revisión semántica y etiquetas pendientes',
        'alternative_representations':'comparar moda o proporciones geoquímicas; no duplicar evidencia por defecto'})
    qc=pd.DataFrame({'variable':allowed,'missing_fraction':[float(x[n].isna().mean()) for n in allowed],
                     'n_unique':[int(x[n].nunique()) for n in allowed]})
    qc.to_csv(out/'variables_qc.csv',index=False,encoding='utf-8-sig')
    write_json(out/'feature_sets.json',{
        'base_geologia_relieve_estructuras':[n for n in allowed if not any(n.startswith(e+'_') for e in ('au','as','sb','bi','hg','cu','pb','zn','w'))],
        'geoquimica_modal_4':[f'{e}_clase_modal' for e in ('au','as','sb','bi')],
        'geoquimica_modal_9':[f'{e}_clase_modal' for e in ('au','as','sb','bi','hg','cu','pb','zn','w')],
        'proporciones_alternativas':[n for n in allowed if '_proporcion_clase_' in n],
        'no_utilizables_sin_revision':qc.loc[qc.n_unique<=1,'variable'].tolist(),
        'nota':'Comparaciones candidatas; no particiones ni validación del modelo.'})
    support=[]
    for flag in ['eligible_geology_terrain','eligible_geo4','eligible_geo9']:
        support.append({'criterion':flag,'cells':int(q[flag].sum()),
            'land_area_km2':float(q.loc[q[flag],'land_area_m2'].sum()/1e6),
            'candidate_records':int(y.loc[q[flag],'n_candidatos'].sum()),
            'reviewed_positive_cells':int((y.loc[q[flag],'n_positivos_revisados']>0).sum())})
    pd.DataFrame(support).to_csv(out/'soporte_modelos.csv',index=False,encoding='utf-8-sig')
    write_json(out/'pending_extensions.json',{
        'geological_groups':'asociaciones explícitas implementadas; equivalencias metalogenéticas y mezclas internas pendientes',
        'geophysics':'gravimetría: unidades/campañas/soporte; vuelos/MT/petro no se interpolan como propiedades',
        'advanced_structures':'leyendas angulares, intersecciones y topología pendientes',
        'alluvial':'cuaternario genérico no distingue terrazas; MDT fino y cuencas pendientes',
        'geochemistry':'contraste RGB local ejecutado; leyendas oficiales, medio y extracción pendientes',
        'density':'aproximación por distribución uniforme de longitud dentro de celdas de 1km; validar sensibilidad',
        'territory':'máscara regional candidata y cobertura de levantamientos pendientes'})
    write_json(out/'control_cierre.json',{'estado_ejecucion':'completada','fase_d_cientifica_cerrada':False,
        'prediction_allowed':False,'cells':len(x),'candidate_features':len(allowed),
        'assigned_candidates':len(assigned),'occupied_candidate_cells':int((y.n_candidatos>0).sum()),
        'reviewed_positive_cells':int((y.n_positivos_revisados>0).sum()),
        'scope':spec['scope'],'grid_version':spec['grid_version'],
        'master_includes_auxiliary_and_labels':True,'predictors_file':'X_features.parquet',
        'partitioned_master':'Grid_Master_Au','partitions_are_validation_folds':False})
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='outputs_manifest.json')
    write_json(out/'outputs_manifest.json',records(out,files))
    print('Fase D terminada técnicamente:',len(x),'celdas;',len(allowed),'variables candidatas.',flush=True)
    return x,q,y
