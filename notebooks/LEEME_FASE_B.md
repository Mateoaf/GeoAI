# Ejecutar 01_indicios_limpieza_etiquetas

Abre `01_indicios_limpieza_etiquetas.ipynb`, selecciona el mismo intérprete
`.venv-fase-a/Scripts/python.exe` del cuaderno 00 y pulsa **Ejecutar todo**.
La fase B no añade dependencias al entorno ya comprobado.

Desde la raíz del proyecto también puedes ejecutar:

```powershell
.\.venv-fase-a\Scripts\python.exe scripts/ejecutar_notebook_01.py
```

La configuración está en `config/labels.yaml`; la lógica reutilizable está en
`src/geoau/labels.py`. Las fuentes, el cuaderno 00 y sus resultados se conservan.

## Relación con la fase A

Se selecciona la última ejecución de fase A completada con hashes, o la ruta fijada
en `phase_a_run`. Se leen su manifiesto y snapshot de configuración. Antes y después
del procesamiento se verifica SHA-256 de las 93 fuentes de esa ejecución. Si han
cambiado, vuelve a ejecutar 00; no se reutiliza silenciosamente una auditoría obsoleta.

El notebook 01 no necesita variables del kernel de 00. Carga las tres bases de indicios
por sus rutas y conserva cada fuente por separado. Los maestros enriquecidos siguen
siendo derivados; no se concatenan con los indicios como nuevas observaciones.

## Qué hace cada paso

| Paso del plan | Implementación |
|---|---|
| 07 | Conciliación por código, diferencias de atributos/sustancias/X/Y y duplicados en cada copia |
| 08 | Normalización de texto y tokenización exacta de Oro/Au; conservación de `*_raw`, WKT, CRS y hash |
| 09 | QC de geometría, comparación condicional con X/Y, cuarentena y cruce opcional con máscara/límites |
| 10 | Coincidencias exactas y componentes geodésicas a 250/500/1.000 m, sin deducir depósitos independientes |
| 11 | Tipologías propuestas, revisión documentada y separación de etiquetas candidatas/revisadas |
| 12 | Representatividad por provincia, tipología y dominio declarado, disponibilidad puntual de rásteres y pendientes de distritos |

Los fallos básicos de geometría se excluyen de las posiciones utilizables. Los X/Y cuyo
CRS no está documentado no sustituyen la geometría. Las cajas amplias de plausibilidad
no equivalen a una máscara de España; los controles territoriales pendientes se explicitan.

## Resultados

Cada ejecución crea `reports/fase_b/<fecha-hora-UTC>/` con:

- `reconciliacion_indicios.csv`, duplicados y candidatos Au ausentes de la base canónica.
- `indicios_normalizados.csv` e `indicios_geometry_qc.gpkg` con trazabilidad y estados QC.
- `cuarentena_geometria.csv` y registro de correcciones/decisiones aplicadas.
- `etiquetas_au_candidatas.csv/.gpkg` y `plantilla_revision.csv`.
- Pares de proximidad, sensibilidad a radios, posiciones y correspondencias con grupos.
- Cobertura puntual del MDT y las nueve geoquímicas, tablas de representatividad y figura.
- Configuración, entradas, entorno, código utilizado y control final de integridad.

`etiquetas_au_revisadas.gpkg` solo se escribe si existen positivos con revisión
documentada de presencia y geometría, sin cuarentena ni código ambiguo. El modelo
por tipo exige además tipología revisada. Un conjunto candidato no está listo por
sí solo para entrenar; no hay negativos, rejilla ni particiones espaciales definitivas.

`deposit_id` y `district_id` quedan sin asignar hasta disponer de una revisión.
`proximity_group_*` no son IDs geológicos y las componentes conexas pueden extenderse
más que su radio de conexión. Los representantes de posición no son un inventario
deduplicado de depósitos; se conserva toda la relación con los registros originales.

## Incorporar decisiones de revisión

1. Copia la `plantilla_revision.csv` de una ejecución a `data/review/`.
2. Mantén `record_id` y las columnas. Rellena solo decisiones respaldadas por evidencia.
3. Indica la ruta relativa en `config/labels.yaml`, por ejemplo:

```yaml
review_file: data/review/revision_au.csv
```

4. Ejecuta nuevamente el notebook. Obtendrás una ejecución nueva y un registro de cambios.

| Columna | Valores / significado |
|---|---|
| `estado_presencia` | `confirmada`, `rechazada`, `pendiente` o vacío |
| `estado_geometria` | `validada`, `rechazada`, `pendiente` o vacío |
| `tipo_au_revisado` | `roca`, `aluvial`, `mixto`, `desconocido` o vacío |
| `deposit_id` / `district_id` | Identificadores geológicos revisados; no asumir que coinciden con provincia o grupo de proximidad |
| `lon_corregida` / `lat_corregida` | Ambas en EPSG:4326, punto decimal; solo cuando hay corrección documentada |
| `precision_m` | Incertidumbre de posición respaldada por fuente; no inventar precisión |
| `revisor`, `fecha_revision`, `evidencia`, `motivo` | Obligatorios para cada decisión; fecha ISO como `2026-09-06` |

Los IDs incluyen el hash del GPKG: una revisión de otra versión se rechaza. Revisa
fuentes documentales/cartografía antes de confirmar geometría; no basta con que esté
dentro de una ventana amplia. La ausencia de Oro en una copia o un rechazo del indicio
no se convierte en ausencia geológica. La morfología filoniana no acredita génesis orogénica.

Para el contraste territorial opcional, configura `territory_mask` y, si procede,
`territory_layer`. Para provincias/municipios, configura los límites y sus dos columnas.
Las entradas adicionales y componentes del shapefile quedan identificados por hash.

## Comprobar el código

```powershell
.\.venv-fase-a\Scripts\python.exe -m unittest discover -s tests -v
```

Las pruebas verifican tokens, preservación de códigos y originales, uniones sin
multiplicación, cuarentena, distancias/agrupaciones, requisitos de revisión y conservación
de los controles de fase A. No sustituyen la validación geológica.
