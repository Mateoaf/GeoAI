# Auditoría reproducible de OxREP 3.0 y subconjunto España

## Alcance y fuente

Se auditó programáticamente el libro `oxrep-mines-3.0-20250408.xlsx` (SHA-256 `802e35d0abef469fb7683b3b82b1638224db059f19919a2e245ce44ec757815a`), sin modificarlo. La hoja analítica contiene 1,399 registros y 47 campos; la segunda hoja está vacía. OxREP indica que la versión 3.0 es una base de minas del mundo romano y advierte que la cobertura de hierro no es sistemática y que la datación es difícil para la mayoría de los sitios.

Fuente institucional: https://oxrep.web.ox.ac.uk/mines-database (consulta: 2026-08-14).

## Criterio exacto para España actual

1. Se normalizó únicamente espacio exterior y mayúsculas/minúsculas de `country`. `country == Spain` produjo 929 registros.
2. Se añadió mediante override explícito `mineID=132` (Lanz), cuyo `country` crudo es `Navarra`, coordenadas 42.99640694, -1.621914721 y hoja española 115. Se conserva `country=Navarra` y `flag_country_override=true`.
3. Total curado: 930 registros (1 override). Todos los demás países quedan excluidos. El campo romano `province` no se usa para el filtro porque incluye sitios fuera de la España actual, especialmente Portugal.
4. Las coordenadas se someten solo a un control amplio de plausibilidad. La validación administrativa point-in-polygon queda pendiente hasta incorporar un límite oficial reproducible.

La tabla completa de inclusión/exclusión por registro está en `reports/audit/spain_selection_decisions.csv`.

## Integridad del libro

- Hojas: OxREP Mines 3 0 - 20250408, Sheet1.
- La hoja principal es una tabla Excel A1:AU1400; no contiene fórmulas.
- `mineID`: 1,399 informados, 1,399 únicos, rango 1-1780. Los huecos de la secuencia son identificadores no presentes y no se imputan.
- Duplicados exactos de fila: 0; duplicados de `mineID`: 0.
- No existe hoja de diccionario de datos ni campos de CRS/unidad para Lambert o `coordinateAccuracy`; la auditoría no inventa EPSG ni unidades.
- Advertencia de lector: el render/importador de hojas puede mostrar `53` en celdas que en el XLSX son shared strings vacíos. El pipeline analítico usa pandas/openpyxl, que resuelven correctamente esas celdas; `53` no se incorpora a los datos.

## Esquema y nulos

Los 47 campos, tipos observados, nulos, cardinalidades y ejemplos están en `reports/audit/column_audit.csv`; todas las categorías y sus frecuencias, no solo el top-N, están en `reports/audit/value_counts_all_columns.csv`. Aspectos centrales:

- Coordenadas completas: 923/930; faltan 7.
- Geología informada: 449/930; tipo de depósito: 717; explotación: 522.
- Alguna cronología: 38; sin cronología: 892.
- Los indicadores mezclan texto (`TRUE/FALSE/?`), booleanos o 0/1 y nulos. El pipeline los normaliza a booleano nullable más un estado explícito: present, absent, unknown, missing o invalid.

## Commodities

| Código | Campo OxREP | Presente | Ausente | Desconocido | No informado |
|---|---|---:|---:|---:|---:|
| Au | `metalMinedGold` | 598 | 329 | 3 | 0 |
| Ag | `metalMinedSilver` | 174 | 756 | 0 | 0 |
| Pb | `metalMinedLead` | 169 | 761 | 0 | 0 |
| Cu | `metalMinedCopper` | 169 | 759 | 0 | 2 |
| Sn | `metalMinedTin` | 9 | 921 | 0 | 0 |
| Fe | `metalMinedIron` | 15 | 915 | 0 | 0 |
| Hg | `metalMinedMercuryCinnabar` | 5 | 925 | 0 | 0 |
| Zn | `metalMinedZinc` | 3 | 927 | 0 | 0 |
| Other | `metalMinedOther` | 0 | 930 | 0 | 0 |

Combinaciones principales (multi-label, no categorías exclusivas):

| Combinación | Registros |
|---|---:|
| Au | 596 |
| Ag+Pb | 131 |
| Cu | 128 |
| Ag+Pb+Cu | 31 |
| Fe | 12 |
| Sn | 7 |
| Ag+Cu | 7 |
| Hg | 5 |
| Pb+Zn | 3 |
| Pb | 3 |
| Ag | 2 |
| Au+Ag | 1 |
| Au+Sn | 1 |
| Ag+Cu+Fe | 1 |
| Ag+Pb+Cu+Sn+Fe | 1 |

Registros multimetálicos (>1 commodity confirmada): 177. La estructura real respalda una formulación multi-label. Las clases Fe, Sn, Hg y Zn son muy pequeñas para estimar modelos commodity-específicos robustos sin más etiquetas.

## Técnicas

| Técnica | Campo OxREP | Presente | Ausente | Desconocido/no informado |
|---|---|---:|---:|---:|
| Opencast / surface | `techniqueOpencast` | 420 | 153 | 357 |
| Underground | `techniqueUnderground` | 139 | 436 | 355 |
| Hydraulic | `techniqueHydraulic` | 426 | 342 | 162 |
| Hushing | `techniqueHushing` | 67 | 459 | 404 |
| Ground sluicing | `techniqueGroundSluicing` | 55 | 477 | 398 |
| Ruina montium | `techniqueRuinaMontium` | 6 | 540 | 384 |
| Rake / comb | `techniqueRakeComb` | 72 | 468 | 390 |
| Gold washing | `techniqueGoldWashing` | 1 | 542 | 387 |
| Other | `techniqueOther` | 2 | 343 | 585 |

No tienen ninguna técnica confirmada 354 registros; esto no significa ausencia de técnica porque la ficha puede estar incompleta.

## Coordenadas y precisión

- Latitud observada: 36.54648941 a 43.56532899; longitud: -8.93707518 a 2.70304220.
- `coordinateAccuracy` no informado: 8; valor cero: 76; >1000: 23.
- Cero no se interpreta como precisión perfecta: aparece incluso junto a fuentes descritas como estimadas. La unidad y semántica no están codificadas en el libro.
- La salida GeoJSON usa OGC:CRS84, orden longitud/latitud, porque los campos decimales son inequívocamente geográficos; no se transforma Lambert por falta de CRS documentado.

## Depósitos, geología, explotación y cronología

Las tablas completas están en `reports/tables/`. `geology` mezcla materiales, ambientes y narraciones; no se fuerza una taxonomía geológica. `depositType` contiene principal/secundario y valores inesperados; `exploitationType` contiene selectivo/extensivo y al menos un patrón compatible con desplazamiento de columnas. Se conservan los valores crudos y se añaden normalizaciones solo para vocabularios inequívocos.

Los cuatro límites cronológicos son números de año, no fechas Excel. Los valores negativos se conservan sin reetiquetarlos como a. C. porque esa semántica no está formalizada en el libro. No se fabrican intervalos cuando faltan límites.

## Distribución espacial

| Región OxREP | Registros |
|---|---:|
| León | 304 |
| Oviedo | 168 |
| Córdoba | 82 |
| Lugo | 61 |
| Badajoz | 52 |
| Huelva | 50 |
| Orense | 45 |
| Ciudad Real | 37 |
| Jaén | 30 |
| Sevilla | 12 |
| Pontevedra | 10 |
| Murcia | 9 |

La fuerte concentración en el noroeste y varios distritos del sur combina señal histórica, geología, intensidad de explotación e historia de investigación. No debe interpretarse como muestra espacial aleatoria; condiciona background y validación.

## Duplicados y casos problemáticos

- Duplicados de mineID en el subconjunto: 0 filas.
- Registros con coordenadas exactas compartidas: 4; con nombre normalizado repetido: 20; con algún vecino <=100 m: 6.
- Se generaron 13 pares candidatos en `reports/audit/duplicate_candidates.csv`. Todos se retienen pendientes de revisión; cercanía o nombre repetido no demuestra identidad.
- Artefacto de texto detectado en 6 registros; posible desplazamiento categorial en 2.

## Política de limpieza

- No se modifica ni sobrescribe el libro original.
- Se conserva cada campo OxREP crudo, `mineID`, fila Excel, hoja, hash del fichero y hash determinista de la fila.
- No se elimina ningún registro problemático. Cada problema se expresa mediante flags booleanos documentados en `data/processed/quality_flag_definitions.csv`.
- Nulo/desconocido no se convierte en cero. Esto es especialmente importante en commodities y técnicas.
- Las categorías se normalizan solo en columnas derivadas; el valor original permanece.

## Límites de esta fase

OxREP documenta minas romanas y no es un inventario exhaustivo de mineralización. El Excel no permite inferir ley, tonelaje, rentabilidad, continuidad del cuerpo mineral, ausencia de mineralización ni etiquetas modernas de materias críticas. Tampoco permite validar relaciones geológicas causales sin integrar fuentes oficiales adicionales.
