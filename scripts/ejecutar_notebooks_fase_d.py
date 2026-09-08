"""Ejecuta 03–06 con este intérprete. --desde 4 permite continuar el run actual."""
import argparse
import json
from pathlib import Path
import sys
import tempfile
import nbformat
from nbclient import NotebookClient
from jupyter_client import KernelManager
from jupyter_client.kernelspec import KernelSpecManager

class StreamingNotebookClient(NotebookClient):
    def process_message(self,msg,cell,cell_index):
        if msg.get('msg_type')=='stream':
            print(msg['content'].get('text',''),end='',flush=True)
        return super().process_message(msg,cell,cell_index)

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--desde',type=int,choices=range(3,7),default=3)
    parser.add_argument('--hasta',type=int,choices=range(3,7),default=6)
    args=parser.parse_args()
    if args.desde>args.hasta: parser.error('--desde debe ser <= --hasta')
    root=Path(__file__).resolve().parents[1]
    for number in range(args.desde,args.hasta+1):
        candidates=[p for p in (root/'notebooks').glob(f'{number:02d}_*.ipynb') if not p.name.endswith('.failed.ipynb')]
        if len(candidates)!=1:
            raise ValueError(f'Se esperaba un único notebook {number:02d}, encontrados: {candidates}')
        path=candidates[0]
        notebook=nbformat.read(path,as_version=4)
        with tempfile.TemporaryDirectory(prefix='geoau-d-kernel-') as directory:
            folder=Path(directory)/'geoau-fase-a';folder.mkdir()
            (folder/'kernel.json').write_text(json.dumps({'argv':[sys.executable,'-m','ipykernel_launcher','-f','{connection_file}'],
                'display_name':'GeoAu fase D','language':'python'}),encoding='utf-8')
            km=KernelManager(kernel_name='geoau-fase-a',kernel_spec_manager=KernelSpecManager(kernel_dirs=[directory]))
            def progress(cell,cell_index,**kwargs):
                if cell.cell_type=='code': print(path.name,'celda',cell_index+1,flush=True)
            client=StreamingNotebookClient(notebook,km=km,timeout=14400,resources={'metadata':{'path':str(root/'notebooks')}},on_cell_start=progress)
            try:
                client.execute()
            except Exception:
                # Mantiene el cuaderno original; copia de diagnóstico con el error.
                nbformat.write(notebook,path.with_suffix('.failed.ipynb'))
                raise
            finally:
                if km.has_kernel: km.shutdown_kernel(now=True)
        nbformat.validate(notebook);nbformat.write(notebook,path)
        print('Guardado:',path.name,flush=True)

if __name__=='__main__': main()
