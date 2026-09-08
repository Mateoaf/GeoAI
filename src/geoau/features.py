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


def verify_records(base, records):
    for item in records:
        p = base / item['path']
        if not p.is_file() or sha256_file(p) != item['sha256']:
            raise ValueError(f'Entrada/salida modificada o ausente: {p}')


def records(base, paths):
    return [{'path': p.relative_to(base).as_posix(), 'sha256': sha256_file(p),
             'size_bytes': p.stat().st_size} for p in paths]


def start_run(root, config_path=None):
    root = Path(root).resolve()
    config_path = Path(config_path or root / 'config/features.yaml')
    cfg = yaml.safe_load(config_path.read_text(encoding='utf-8'))
    c = root / cfg['phase_c_run']
    if read_json(c / 'control_cierre.json')['estado_ejecucion'] != 'completada':
        raise ValueError('La fase C seleccionada no terminó.')
    # C selló sus productos: verificar antes de cualquier cálculo.
    verify_records(c, read_json(c / 'outputs_manifest.json'))
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
        'external': records(root, external),
        'c_manifest_sha256': sha256_file(c / 'outputs_manifest.json')})
    shutil.copy2(Path(__file__), out / 'features_source.py')
    write_json(out / 'environment.json', environment_info())
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


def context(root, out):
    root, out = Path(root).resolve(), Path(out).resolve()
    cfg = read_json(out / 'config_snapshot.json')
    inp = read_json(out / 'inputs.json')
    c = root / inp['phase_c_run']
    verify_records(root, inp['external'])
    if sha256_file(c / 'outputs_manifest.json') != inp['c_manifest_sha256']:
        raise ValueError('Cambió el manifiesto C.')
    verify_records(c, read_json(c / 'outputs_manifest.json'))
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


def line_lengths(lines, cells):
    """Longitud por celda; media longitud sobre bordes compartidos (sin doble suma)."""
    result = np.zeros(len(cells))
    if not len(lines): return result
    # Nodar/disolver evita contar dos veces las trazas geométricamente coincidentes.
    lines = shapely.get_parts(shapely.union_all(lines))
    tree = shapely.STRtree(cells)
    for start in range(0,len(lines),2000):
        part = lines[start:start+2000]
        li, ci = tree.query(part,predicate='intersects')
        pieces = shapely.intersection(part[li],cells[ci])
        length = shapely.length(pieces)
        length -= .5*shapely.length(shapely.intersection(pieces,shapely.boundary(cells[ci])))
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
            length[group][tile.row,tile.col] = line_lengths(clipped,cells)
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


def color_quality(rgb, classes, valid, palette, threshold=0):
    """Distancia al color de la clase declarada; evita matriz píxeles x clases."""
    colors=np.asarray([p[1] for p in palette],dtype=float)
    ok=valid & np.isfinite(classes) & (classes==np.floor(classes)) & (classes>=0) & (classes<len(colors))
    diff=np.full(classes.shape,np.nan)
    idx=np.where(ok)
    diff[idx]=np.linalg.norm(rgb[:,idx[0],idx[1]].T.astype(float)-colors[classes[idx].astype(int)],axis=1)
    return ok & (diff<=threshold),diff


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
        valid,difference=color_quality(rgb,a.data,original & visible,palette,cfg['rgb_max_distance'])
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
            'cells_sufficient_rgb':int(accepted[row,col].sum()),'official_legend_validated':False})
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


def assemble(root,out):
    cfg,c,spec,grid,mask=context(root,out)
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
    allowed=[m['name'] for m in dictionary]
    if set(allowed)!=set(x.columns)-{'cell_id'} or len(set(allowed))!=len(allowed):
        raise ValueError('El diccionario no coincide con la lista de variables.')
    for col in x.select_dtypes(include='number'):
        if np.isinf(x[col]).any(): raise ValueError(f'Inf en {col}')
    labels=pd.read_csv(c/'indicios_celda_cobertura.csv',dtype={'Codigo_indicio':'string'})
    if not labels.record_id.is_unique: raise ValueError('record_id duplicado.')
    assigned=labels[labels.cell_id.notna()].copy()
    labels.to_parquet(out/'relacion_indicios_celda.parquet',index=False)
    aggregated=assigned.groupby('cell_id').agg(n_candidatos=('record_id','size'),
                      n_positivos_revisados=('positivo_revisado','sum')).reset_index()
    y=grid[['cell_id']].merge(aggregated,on='cell_id',how='left',validate='one_to_one')
    y[['n_candidatos','n_positivos_revisados']]=y[['n_candidatos','n_positivos_revisados']].fillna(0).astype(int)
    y['estado_etiqueta']=np.where(y.n_positivos_revisados>0,'P_revisado',np.where(y.n_candidatos>0,'candidato_no_revisado','U'))
    # Sin y=0 ni entrenamiento. El maestro contiene solo X y cell_id.
    x.to_parquet(out/'Grid_Master_Au.parquet',index=False,row_group_size=50000)
    q.to_parquet(out/'calidad_y_soporte.parquet',index=False)
    y.to_parquet(out/'etiquetas_por_celda.parquet',index=False)
    pd.DataFrame(dictionary).to_csv(out/'feature_dictionary.csv',index=False,encoding='utf-8-sig')
    write_json(out/'feature_allowlist.json',{'candidate_columns':allowed,'approved_training_columns':[],
        'exclude_all_other_columns':True,'reason':'revisión semántica y etiquetas pendientes',
        'alternative_representations':'comparar moda o proporciones geoquímicas; no duplicar evidencia por defecto'})
    qc=pd.DataFrame({'variable':allowed,'missing_fraction':[float(x[n].isna().mean()) for n in allowed],
                     'n_unique':[int(x[n].nunique()) for n in allowed]})
    qc.to_csv(out/'variables_qc.csv',index=False,encoding='utf-8-sig')
    write_json(out/'pending_extensions.json',{
        'geological_groups':'revisión de unidades mixtas y equivalencias; fracciones actuales son unidades originales',
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
        'scope':spec['scope'],'grid_version':spec['grid_version']})
    files=sorted(p for p in out.rglob('*') if p.is_file() and p.name!='outputs_manifest.json')
    write_json(out/'outputs_manifest.json',records(out,files))
    print('Fase D terminada técnicamente:',len(x),'celdas;',len(allowed),'variables candidatas.',flush=True)
    return x,q,y
