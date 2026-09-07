"""Ejecuta el notebook con el Python actual y guarda sus salidas tras éxito.

Uso desde la raíz: .venv-fase-a/Scripts/python.exe scripts/ejecutar_notebook_02.py
"""
from pathlib import Path
import json
import sys
import tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

root = Path(__file__).resolve().parents[1]
path = root / 'notebooks/02_rejilla_armonizacion_cobertura.ipynb'
notebook = nbformat.read(path, as_version=4)
nbformat.validate(notebook)

def progress(cell, cell_index, **kwargs):
    if cell.cell_type == 'code':
        print(f'Ejecutando celda {cell_index + 1}/{len(notebook.cells)}', flush=True)

# Kernel temporal con intérprete explícito: no depende del PATH ni instala kernels globales.
with tempfile.TemporaryDirectory(prefix='geoau-kernel-') as directory:
    kernel_dir = Path(directory) / 'geoau-fase-a'
    kernel_dir.mkdir()
    (kernel_dir / 'kernel.json').write_text(json.dumps({
        'argv': [sys.executable, '-m', 'ipykernel_launcher', '-f', '{connection_file}'],
        'display_name': 'GeoAu fase A', 'language': 'python',
    }), encoding='utf-8')
    manager = KernelManager(kernel_name='geoau-fase-a',
                            kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]))
    client = NotebookClient(notebook, km=manager, timeout=7200,
                            resources={'metadata': {'path': str(root / 'notebooks')}},
                            on_cell_start=progress)
    try:
        client.execute()
    finally:
        if manager.has_kernel:
            manager.shutdown_kernel(now=True)
nbformat.validate(notebook)
nbformat.write(notebook, path)
print('Notebook ejecutado y guardado sin errores:', path, flush=True)
