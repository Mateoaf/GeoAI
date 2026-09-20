"""Ejecuta U1 y guarda el cuaderno con salidas usando este intérprete."""
import argparse
import json
from pathlib import Path
import sys
import tempfile

import nbformat
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

from crear_notebook_unidad1 import main as create_notebook
from ejecutar_notebooks_fase_f import StreamingNotebookClient

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT/'src'))
from geoau import neural_u1 as u1


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--nuevo', action='store_true', help='Entrena una nueva ejecución U1 antes de abrir el cuaderno.')
    args = parser.parse_args()
    if args.nuevo: u1.run_experiment(ROOT)
    create_notebook()
    path = ROOT/'notebooks/15_unidad1_redes_neuronales.ipynb'
    book = nbformat.read(path, as_version=4)
    with tempfile.TemporaryDirectory(prefix='geoau-u1-kernel-') as directory:
        folder = Path(directory)/'geoau-unidad1'; folder.mkdir()
        (folder/'kernel.json').write_text(json.dumps({'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
                 'display_name': 'GeoAu Unidad 1', 'language': 'python'}), encoding='utf-8')
        km = KernelManager(kernel_name='geoau-unidad1', kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]))
        def progress(cell, cell_index, **kwargs):
            if cell.cell_type == 'code': print('U1 celda', cell_index+1, flush=True)
        client = StreamingNotebookClient(book, km=km, timeout=7200,
            resources={'metadata': {'path': str(ROOT/'notebooks')}}, on_cell_start=progress)
        try:
            client.execute()
        except Exception:
            nbformat.write(book, path.with_suffix('.failed.ipynb')); raise
        finally:
            if km.has_kernel: km.shutdown_kernel(now=True)
    nbformat.validate(book); nbformat.write(book, path)
    print('Guardado:', path, flush=True)


if __name__ == '__main__': main()
