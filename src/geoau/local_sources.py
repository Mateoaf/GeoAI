"""Inventario y lectura local, sin descargas ni modificación de fuentes originales.

La inspección no certifica cobertura, validez geométrica o equivalencia geológica.
"""
from __future__ import annotations

from contextlib import closing
from datetime import datetime, timezone
from importlib import metadata
from pathlib import Path
import hashlib
import json
import platform
import re
import sqlite3
import sys
import warnings
import zipfile
import xml.etree.ElementTree as ET

import numpy as np
import pandas as pd
import pyogrio
import rasterio
from rasterio.enums import Resampling
from rasterio.windows import Window
from pyproj import Transformer
import yaml


def find_project_root(start=None):
    """Funciona desde la raíz del workspace, del proyecto o de notebooks/."""
    start = Path(start or Path.cwd()).resolve()
    if start.is_file():
        start = start.parent
    for parent in (start, *start.parents):
        for candidate in (parent, parent / 'Proyecto Con Luis'):
            if (candidate / 'config/project.yaml').is_file() and (candidate / 'src/geoau').is_dir():
                return candidate
    raise FileNotFoundError('No se encuentra config/project.yaml; indica la raíz local del proyecto.')


def local_path(root, relative):
    """Solo archivos dentro de la raíz declarada; rechaza URL y escapes de ruta."""
    if '://' in str(relative):
        raise ValueError('Este módulo solo permite archivos locales.')
    root = Path(root).resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        raise ValueError(f'Ruta fuera del proyecto: {relative}')
    return path


def load_config(root):
    with local_path(root, 'config/project.yaml').open(encoding='utf-8') as f:
        config = yaml.safe_load(f)
    if config.get('schema_version') != 1 or config.get('mode') != 'local_only':
        raise ValueError('Se requiere schema_version=1 y mode=local_only.')
    return config


def discover_sources(root, config):
    root = Path(root).resolve()
    spec = config['local_sources']
    files = list(root.iterdir()) if spec['root_files'] else []
    for directory in spec['recursive_directories']:
        folder = local_path(root, directory)
        if folder.is_dir():
            files.extend(folder.rglob('*'))
    allowed = set(spec['extensions'])
    return sorted({p.resolve() for p in files if p.is_file() and p.suffix.lower() in allowed
                   and p.resolve().is_relative_to(root)}, key=lambda p: p.as_posix().casefold())


def sha256_file(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as f:
        for block in iter(lambda: f.read(8 * 1024 * 1024), b''):
            digest.update(block)
    return digest.hexdigest()


def quote_identifier(name):
    return '"' + name.replace('"', '""') + '"'


def gpkg_info(path):
    """SQLite en modo lectura. COUNT(*) cuenta filas, no geometrías válidas."""
    with closing(sqlite3.connect(Path(path).resolve().as_uri() + '?mode=ro', uri=True)) as con:
        con.row_factory = sqlite3.Row
        geometries = {row['table_name']: dict(row) for row in con.execute('SELECT * FROM gpkg_geometry_columns')}
        layers = []
        for row in con.execute('SELECT * FROM gpkg_contents'):
            layer = dict(row)
            table = quote_identifier(layer['table_name'])
            layer['row_count'] = con.execute(f'SELECT COUNT(*) FROM {table}').fetchone()[0]
            layer['fields'] = [dict(x) for x in con.execute(f'PRAGMA table_info({table})')]
            layer['geometry'] = geometries.get(layer['table_name'])
            layers.append(layer)
    return layers


def read_table(path, nrows=5, *, sheet_name=0, encoding='utf-8-sig', sep=','):
    """Conserva todos los atributos como texto, incluso códigos con ceros iniciales.

    keep_default_na=False preserva textos como 'NA' y vacíos originales. La política
    de nulos y los tipos numéricos se decidirán en el notebook de limpieza.
    """
    path = Path(path)
    if nrows is not None and nrows <= 0:
        raise ValueError('nrows debe ser positivo o None para carga completa.')
    if path.suffix.lower() == '.csv':
        return pd.read_csv(path, nrows=nrows, dtype='string', keep_default_na=False,
                           encoding=encoding, sep=sep, on_bad_lines='error')
    if path.suffix.lower() == '.xlsx':
        return pd.read_excel(path, sheet_name=sheet_name, nrows=nrows,
                             dtype='string', keep_default_na=False, engine='openpyxl')
    raise ValueError(f'Formato tabular no admitido: {path.suffix}')


def iter_csv(path, chunksize=100000, *, encoding='utf-8-sig', sep=','):
    if chunksize <= 0:
        raise ValueError('chunksize debe ser positivo.')
    return pd.read_csv(path, dtype='string', keep_default_na=False, encoding=encoding,
                       sep=sep, chunksize=chunksize, on_bad_lines='error')


def read_vector(path, layer=None, *, max_features=1000, columns=None,
                read_geometry=True, bbox=None, bbox_crs=None,
                allow_curve_conversion=False, allow_full=False):
    """Lee una muestra por defecto; bbox siempre declara su CRS.

    La conversión que GDAL pueda hacer de curvas/Z/M se autoriza expresamente
    para una previsualización. No constituye la linealización validada de fase C.
    """
    path = Path(path)
    if max_features is None and not allow_full:
        raise ValueError('La carga completa requiere allow_full=True.')
    if max_features is not None and max_features <= 0:
        raise ValueError('max_features debe ser positivo, o None con allow_full=True.')
    if path.suffix.lower() == '.gpkg':
        layers = gpkg_info(path)
        if not layers:
            raise ValueError(f'{path.name} no contiene capas; no puede cargarse como vector.')
        if layer is None and len(layers) != 1:
            raise ValueError('Indica layer: el GeoPackage contiene varias capas.')
        layer = layer or layers[0]['table_name']
        selected = next((x for x in layers if x['table_name'] == layer), None)
        if selected is None:
            raise ValueError(f'Capa inexistente: {layer}')
        geometry = selected['geometry'] or {}
        curved = any(x in geometry.get('geometry_type_name', '') for x in ('CURVE', 'CIRCULAR', 'SURFACE'))
        if curved and read_geometry:
            if not allow_curve_conversion:
                raise ValueError('Geometría curva: usa read_geometry=False o allow_curve_conversion=True para vista previa.')
            warnings.warn('Vista previa de curvas: GDAL puede linealizar y alterar Z/M. No usar como capa armonizada.', UserWarning)
    options = {'layer': layer, 'columns': columns, 'read_geometry': read_geometry}
    if max_features is not None:
        options['max_features'] = max_features
    if bbox is not None:
        if bbox_crs is None:
            raise ValueError('bbox requiere bbox_crs explícito.')
        info = pyogrio.read_info(path, layer=layer)
        if not info['crs']:
            raise ValueError('La fuente no declara CRS; no se puede transformar bbox.')
        if len(bbox) != 4 or bbox[0] >= bbox[2] or bbox[1] >= bbox[3]:
            raise ValueError('bbox debe ser xmin, ymin, xmax, ymax con límites crecientes.')
        options['bbox'] = Transformer.from_crs(bbox_crs, info['crs'], always_xy=True).transform_bounds(*bbox)
    return pyogrio.read_dataframe(path, **options)


def read_raster_preview(path, band=1, side=256):
    """Vista reducida por vecino más próximo; no es una nueva capa analítica."""
    if side <= 0:
        raise ValueError('side debe ser positivo.')
    with rasterio.open(path) as src:
        scale = min(1, side / max(src.height, src.width))
        shape = (max(1, round(src.height * scale)), max(1, round(src.width * scale)))
        data = src.read(band, out_shape=shape, masked=True, resampling=Resampling.nearest)
        transform = src.transform * src.transform.scale(src.width / shape[1], src.height / shape[0])
        return data, {'crs': str(src.crs), 'transform': tuple(transform), 'bounds': tuple(src.bounds),
                      'band': band, 'description': src.descriptions[band-1], 'preview_only': True}


def read_raster_window(path, *, col_off, row_off, width, height, bands=(1,)):
    """Lectura a resolución nativa, conservando máscara y transformada del recorte."""
    values = (col_off, row_off, width, height)
    if any(not isinstance(v, int) for v in values) or min(col_off, row_off) < 0 or min(width, height) <= 0:
        raise ValueError('Ventana: offsets enteros no negativos y dimensiones enteras positivas.')
    with rasterio.open(path) as src:
        if col_off + width > src.width or row_off + height > src.height:
            raise ValueError('La ventana excede los límites del ráster.')
        window = Window(col_off, row_off, width, height)
        return src.read(list(bands), window=window, masked=True), {
            'crs': str(src.crs), 'transform': tuple(src.window_transform(window)), 'nodata': src.nodata}


def inspect_qgis(path):
    """Lee referencias del QGZ sin consultar los servicios remotos."""
    with zipfile.ZipFile(path) as z:
        doc = ET.fromstring(z.read(next(n for n in z.namelist() if n.endswith('.qgs'))))
    rows = []
    for element in doc.findall('.//projectlayers/maplayer'):
        source = element.findtext('datasource') or ''
        remote = '://' in source
        base = source.split('|', 1)[0]
        rows.append({'name': element.findtext('layername'), 'source': source,
                     'provider': element.findtext('provider'), 'remote': remote,
                     'local_exists': None if remote or not base else (Path(path).parent / base).is_file()})
    return rows


def classify(path, config):
    name = path.name
    suffix = path.suffix.lower()
    aliases = [key for key, value in config['canonical_candidates'].items() if value == name]
    if suffix in {'.qgz', '.qmd', '.xml', '.prj', '.shx', '.dbf', '.cpg'}:
        return 'metadatos_o_componente', aliases
    if suffix == '.zip':
        return 'archivo_comprimido_respaldo', aliases
    if '_RGB' in name:
        return 'visual', aliases
    if name.startswith('AtlasGeoquimico_'):
        return 'geoquimica_clasificada', aliases
    if name.startswith('Indicios_con_') or name.startswith('Indicios_Master_'):
        return 'derivado_indicios', aliases
    if name.startswith('geoquimica') or name in ('Au.gpkg', 'oro.gpkg'):
        return 'geoquimica_vectorial_derivada', aliases
    if name == 'IndiciosII.gpkg':
        return 'etiquetas_candidatas', aliases
    if name in ('IndiciosII.csv', 'Indicios.xlsx'):
        return 'contraste_indicios', aliases
    return ('vector_fuente' if suffix in ('.gpkg', '.shp') else
            'raster_relieve' if suffix in ('.tif', '.tiff') else 'tabla_auxiliar'), aliases


def inspect_source(path, root, config):
    stat = path.stat()
    role, aliases = classify(path, config)
    row = {'path': path.relative_to(root).as_posix(), 'format': path.suffix.lower(),
           'bytes': stat.st_size, 'mtime_ns': stat.st_mtime_ns,
           'file_modified_utc': datetime.fromtimestamp(stat.st_mtime, timezone.utc).isoformat(),
           'downloaded_at': None, 'license_verified': None, 'origin_verified': None,
           'role': role, 'canonical_aliases': aliases, 'sha256': None,
           'status': 'registrado', 'error': None, 'warnings': [], 'details': {}}
    n = config['inspection']['preview_rows']
    try:
        if config['inspection']['compute_sha256']:
            row['sha256'] = sha256_file(path)
        with warnings.catch_warnings(record=True) as caught:
            warnings.simplefilter('always')
            ext = path.suffix.lower()
            if ext == '.gpkg':
                layers = gpkg_info(path)
                row['details']['layers'] = layers
                row['row_count'] = sum(x['row_count'] for x in layers)
                row['status'] = 'requiere_revision' if row['row_count'] else 'sin_datos'
                for layer in layers:
                    # Atributos por defecto: no convertir curvas sin control.
                    table = quote_identifier(layer['table_name'])
                    geom = (layer['geometry'] or {}).get('column_name')
                    fields = [x['name'] for x in layer['fields'] if x['name'] != geom]
                    sql = f'SELECT {", ".join(map(quote_identifier, fields))} FROM {table} LIMIT {int(n)}'
                    with closing(sqlite3.connect(path.as_uri() + '?mode=ro', uri=True)) as con:
                        layer['preview'] = pd.read_sql_query(sql, con).to_dict('records')
            elif ext in ('.tif', '.tiff'):
                with rasterio.open(path) as src:
                    row['details'] = {'crs': str(src.crs), 'width': src.width, 'height': src.height,
                                      'count': src.count, 'dtypes': src.dtypes, 'nodata': src.nodata,
                                      'transform': tuple(src.transform), 'bounds': tuple(src.bounds),
                                      'resolution': src.res, 'descriptions': src.descriptions, 'tags': src.tags()}
                array, _ = read_raster_preview(path, side=config['inspection']['sample_raster_side'])
                vals = array.compressed()
                vals = vals[np.isfinite(vals)]
                row['details']['band1_preview'] = {'sample_shape': array.shape, 'valid_pixels': len(vals),
                    'min': float(vals.min()) if len(vals) else None,
                    'max': float(vals.max()) if len(vals) else None,
                    'unique_in_preview': np.unique(vals).tolist() if len(np.unique(vals)) < 30 else None,
                    'scope': 'muestra reducida; no certifica estadísticas ni cobertura completa'}
                row['status'] = 'visual' if role == 'visual' else 'requiere_revision'
            elif ext == '.csv':
                count = 0
                with iter_csv(path, encoding=config['inspection']['csv_encoding'],
                              sep=config['inspection']['csv_separator']) as chunks:
                    for chunk in chunks:
                        if count == 0:
                            row['details'] = {'columns': list(chunk.columns), 'preview': chunk.head(n).to_dict('records')}
                        count += len(chunk)
                row['row_count'] = count
                row['status'] = 'tabla_sin_geometria_verificada' if count else 'sin_datos'
            elif ext == '.xlsx':
                with pd.ExcelFile(path, engine='openpyxl') as book:
                    sheets = {}
                    for sheet in book.sheet_names:
                        data = pd.read_excel(book, sheet_name=sheet, dtype='string', keep_default_na=False)
                        sheets[sheet] = {'row_count': len(data), 'columns': list(data.columns), 'preview': data.head(n).to_dict('records')}
                row['details']['sheets'] = sheets
                row['row_count'] = sum(x['row_count'] for x in sheets.values())
                row['status'] = 'requiere_conciliacion'
            elif ext == '.shp':
                missing = [e for e in ('.dbf', '.shx', '.prj') if not path.with_suffix(e).is_file()]
                if missing:
                    raise ValueError(f'Shapefile incompleto: faltan {missing}')
                info = pyogrio.read_info(path)
                row['details'] = info
                row['row_count'] = int(info['features'])
                row['status'] = 'requiere_revision'
            elif ext == '.qgz':
                row['details']['references'] = inspect_qgis(path)
            elif ext == '.zip':
                with zipfile.ZipFile(path) as z:
                    row['details']['members'] = [{'path': x.filename, 'bytes': x.file_size, 'crc32': x.CRC} for x in z.infolist()]
                row['details']['content_extracted'] = False
            elif name_is_orphan_aux(path):
                row['status'] = 'auxiliar_sin_raster'
            row['warnings'] = [str(w.message) for w in caught]
        after = path.stat()
        if (stat.st_size, stat.st_mtime_ns) != (after.st_size, after.st_mtime_ns):
            raise RuntimeError('El archivo cambió durante la inspección; repetir inventario.')
    except Exception as exc:
        row['status'] = 'error'
        row['error'] = f'{type(exc).__name__}: {exc}'
    return row


def name_is_orphan_aux(path):
    return path.name.endswith('.aux.xml') and not Path(str(path)[:-8]).is_file()


def environment_info():
    names = ('pandas', 'geopandas', 'pyogrio', 'shapely', 'pyproj', 'rasterio',
             'openpyxl', 'PyYAML', 'nbformat', 'nbclient', 'ipykernel', 'matplotlib')
    return {'python': sys.version, 'executable': sys.executable, 'platform': platform.platform(),
            'packages': {name: metadata.version(name) for name in names},
            'gdal_pyogrio': pyogrio.__gdal_version_string__, 'gdal_rasterio': rasterio.__gdal_version__}


def json_safe(value):
    if isinstance(value, dict):
        return {str(k): json_safe(v) for k, v in value.items()}
    if isinstance(value, (list, tuple, np.ndarray)):
        return [json_safe(v) for v in value]
    if isinstance(value, np.generic):
        return json_safe(value.item())
    if value is None or value is pd.NA:
        return None
    if isinstance(value, float) and not np.isfinite(value):
        return None
    if isinstance(value, (str, int, float, bool)):
        return value
    return str(value)


def write_json(path, obj):
    Path(path).write_text(json.dumps(json_safe(obj), ensure_ascii=False, indent=2, allow_nan=False), encoding='utf-8')


def inventory(root, config, progress=print):
    rows = []
    paths = discover_sources(root, config)
    for i, path in enumerate(paths, 1):
        if progress:
            progress(f'[{i:02}/{len(paths)}] {path.name}')
        rows.append(inspect_source(path, root, config))
    return rows


def catalog_frame(rows):
    keys = ['path', 'format', 'bytes', 'role', 'status', 'row_count', 'sha256', 'error']
    return pd.DataFrame([{key: row.get(key) for key in keys} for row in rows])


def write_reports(root, config, rows):
    # Cada ejecución es independiente: no sobrescribe el manifiesto anterior.
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S_%fZ')
    output = local_path(root, config['reports_directory']) / stamp
    output.mkdir(parents=True, exist_ok=False)
    write_json(output / 'manifest.json', {'schema_version': 1, 'inspected_at_utc': stamp, 'sources': rows})
    catalog_frame(rows).to_csv(output / 'catalogo.csv', index=False, encoding='utf-8-sig')
    write_json(output / 'environment.json', environment_info())
    write_json(output / 'config_snapshot.json', config)
    pending = list(config['pending_sources'])
    pending += [{'name': row['path'], 'reason': row['status'], 'priority': 'revisar por familia'}
                for row in rows if row['status'] in ('sin_datos', 'error', 'auxiliar_sin_raster')]
    for alias, filename in config['canonical_candidates'].items():
        if not local_path(root, filename).is_file():
            pending.append({'name': filename, 'reason': f'Candidato canónico ausente: {alias}', 'priority': 'revisar'})
    write_json(output / 'pendientes.json', pending)
    qgis = [ref for row in rows for ref in row['details'].get('references', [])]
    write_json(output / 'referencias_qgis.json', qgis)
    # Fija TODAS las distribuciones de este entorno, incluidas las transitivas.
    packages = sorted({f'{dist.metadata["Name"]}=={dist.version}' for dist in metadata.distributions()})
    (output / 'environment.freeze.txt').write_text('\n'.join(packages) + '\n', encoding='utf-8')
    code = [local_path(root, p) for p in ('src/geoau/local_sources.py', 'notebooks/00_configuracion_y_fuentes.ipynb')]
    code_rows = []
    for path in code:
        if not path.is_file():
            continue
        if path.suffix == '.ipynb':
            notebook = json.loads(path.read_text(encoding='utf-8'))
            content = json.dumps([{'type': cell['cell_type'], 'source': cell['source']} for cell in notebook['cells']], ensure_ascii=False, sort_keys=True)
            digest = hashlib.sha256(content.encode('utf-8')).hexdigest()
            scope = 'tipo y fuente de celdas; excluye salidas y metadatos de ejecución'
        else:
            digest, scope = sha256_file(path), 'archivo completo'
        code_rows.append({'path': path.relative_to(root).as_posix(), 'sha256': digest, 'scope': scope})
    write_json(output / 'code_manifest.json', code_rows)
    return output


def verify_unchanged(root, rows, *, rehash=False):
    changes = []
    for row in rows:
        path = local_path(root, row['path'])
        if not path.is_file():
            changes.append({'path': row['path'], 'reason': 'ausente'})
            continue
        stat = path.stat()
        if stat.st_size != row['bytes'] or stat.st_mtime_ns != row['mtime_ns']:
            changes.append({'path': row['path'], 'reason': 'tamaño/fecha modificados'})
        elif rehash and row['sha256'] and sha256_file(path) != row['sha256']:
            changes.append({'path': row['path'], 'reason': 'SHA-256 diferente'})
    return changes
