# Ejecutar 00_configuracion_y_fuentes

Abre `00_configuracion_y_fuentes.ipynb` y selecciona el intérprete
`.venv-fase-a/Scripts/python.exe` de este proyecto. Pulsa **Ejecutar todo**.
El notebook ya incluye salidas de una ejecución completa con las fuentes locales.

El entorno se ha comprobado en Windows con Python 3.14.7. En otra instalación compatible:

```powershell
python -m venv .venv-fase-a
.\.venv-fase-a\Scripts\python.exe -m pip install -r requirements-fase-a.lock.txt
```

Ejecuta esos comandos desde la raíz `Proyecto Con Luis`. El archivo
`requirements-fase-a.txt` contiene los rangos de dependencias; el archivo `.lock.txt`
fija las versiones del entorno comprobado. Si cambias de Python o sistema operativo,
verifica de nuevo compatibilidad y pruebas. No se instala boosting para cargar datos.

Para ejecutar y actualizar las salidas del notebook desde PowerShell:

```powershell
.\.venv-fase-a\Scripts\python.exe scripts/ejecutar_notebook_00.py
```

Para ejecutar los controles de los lectores:

```powershell
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -v
```

El código reutilizable está en `src/geoau/local_sources.py`. Las decisiones y alias de
fuentes se editan en `config/project.yaml`. Las rutas se resuelven desde la raíz y no
dependen del nombre del usuario de Windows. No es necesario activar PowerShell ni
alterar su política de ejecución: se llama directamente al ejecutable del entorno.

## Qué queda disponible en memoria

| Variable | Contenido |
|---|---|
| `fuentes` | Rutas de fuentes canónicas candidatas |
| `registros`, `catalogo` | Metadatos, hashes, capas internas, estados y recuentos |
| `indicios` | GeoDataFrame completo de IndiciosII.gpkg |
| `tablas` | CSV y Excel de indicios completos, separados y con códigos como texto |
| `vectores` | Indicios, litología y edades completos |
| `muestras_vectores` | Atributos de cada capa interna de los GPKG con datos |
| `muestras_tablas` | Cinco filas de cada CSV/Excel |
| `rasters` | Rutas de los 20 TIFF para lectura por bandas/ventanas |
| `muestras_shp` | Vista previa de los shapefiles locales |
| `referencias_qgis` | Referencias locales/remotas y rutas locales ausentes |
| `RUN_DIR` | Directorio de resultados de esta ejecución |

## Qué se escribe

En `reports/fase_a/<fecha-hora-UTC>/`: manifiesto SHA-256, catálogo CSV, metadatos de
bandas, fuentes canónicas, pendientes, versiones del entorno, configuración utilizada,
resumen de indicios, vista previa de rásteres y control final de integridad.
Cada ejecución conserva su propio directorio; no sobrescribe las fuentes descargadas.

El notebook inventaría **93 archivos de datos y componentes** en la copia comprobada,
incluidos **nueve GPKG sin datos**. Los documentos y scripts de informes no son fuentes
geoespaciales de entrenamiento y se excluyen de este catálogo. Los recuentos pueden
cambiar cuando añadas o sustituyas archivos locales.

La carga no resuelve las diferencias entre GPKG/CSV/Excel, ni limpia geometrías, ni
armoniza CRS, ni genera etiquetas definitivas. Los rásteres RGB son visuales; los otros
TIFF geoquímicos siguen siendo clases cartográficas. La recuperación de datos remotos
del paso 06 queda como lista de pendientes, conforme al alcance local solicitado.

Para el siguiente cuaderno, utiliza `config/project.yaml` y el manifiesto de una ejecución
con `control_cierre.json` satisfactorio. Comprueba sus hashes antes de reutilizar datos.
No dependas de que este kernel siga abierto ni unas maestros derivados como observaciones nuevas.
