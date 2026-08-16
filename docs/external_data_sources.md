# Fuentes externas oficiales para GeoAI de prospectividad mineral en España

**Fecha de consulta:** 2026-08-14  
**Ámbito:** fuentes primarias de organismos públicos españoles y, de forma complementaria, infraestructuras oficiales europeas. No se incluyen agregadores comerciales ni copias de terceros.

## 1. Criterios de selección

La lista distingue tres niveles:

- **P0 — imprescindible:** bloquea o condiciona la construcción reproducible de variables geológicas, etiquetas modernas o máscaras espaciales.
- **P1 — alta prioridad:** aporta señal predictiva o permite controlar sesgos importantes, pero puede incorporarse después del núcleo P0.
- **P2 — complementaria:** útil para contraste, armonización europea, cobertura transfronteriza o análisis piloto; no debe sustituir a la fuente nacional de mayor detalle.

También se distingue el papel previsto de cada fuente:

- **X:** variable predictora geológica, geoquímica, geofísica o geomorfológica.
- **Y:** posible fuente de etiquetas positivas modernas.
- **MASK:** delimitación del dominio analítico o máscara de observabilidad.
- **BIAS/AUDIT:** control de sesgos, cobertura, actividad administrativa o QA contextual; no equivale a validación espacial independiente.
- **QA:** contraste cartográfico o semántico.

Una ausencia en un inventario no se interpreta como ausencia de mineralización. Los inventarios modernos se utilizarán como presencia o positivo-no-etiquetado, no como mapas exhaustivos de verdaderos negativos.

## 2. Geología, litología, edad, contactos y estructuras

### P0 — GEODE, Mapa Geológico Digital Continuo de España 1:50.000

- **Organismo:** Instituto Geológico y Minero de España, IGME-CSIC.
- **Fuente oficial:** [GEODE](https://info.igme.es/cartografiadigital/geologica/Geode.aspx?language=es).
- **Cobertura y detalle:** España, organizada en 19 zonas geológicas. Integra y armoniza la cartografía MAGNA; escala de referencia 1:50.000, con el detalle especial de las series insulares y territoriales de MAGNA donde procede.
- **Contenido útil:** unidades geológicas con litología y edad, contactos, fallas y otras estructuras, además de leyendas y relaciones cartográficas regionales.
- **Acceso y formato:** la página oficial permite consulta cartográfica. El propio IGME indica que el suministro vectorial oficial se solicita a cartografiadigital@igme.es; el producto se entrega en ESRI Shapefile con leyenda y documentación auxiliar, sujeto a las condiciones y tarifas que indique el organismo.
- **Licencia:** deben aplicarse las condiciones específicas entregadas con el producto. La [licencia general del IGME](https://www.igme.es/condiciones-de-uso/) solo se aplicará cuando no exista una condición particular.
- **Papel:** X principal para litología, edad, distancia a contactos, fallas, pliegues y unidades favorables.
- **Riesgos y limitaciones:** hereda campañas, criterios y fechas distintas de MAGNA; las leyendas regionales no son idénticas. Antes de armonizar deben conservarse el código original, zona GEODE, unidad, edad, fuente y versión. No debe asumirse que la visualización web equivale a una descarga vectorial libre. La [especificación vectorial GEODE](https://info.igme.es/cartografiadigital/datos/geode/docs/GEODE_FORM.pdf) documenta una capa `MPMIN` de indicios mineros: queda excluida de X si replica o deriva del inventario que define Y. Solo se usarán litología, edad, contactos y estructuras cuya procedencia sea independiente del target.

### P0 — Mapa litoestratigráfico continuo de España 1:200.000

- **Organismo:** IGME-CSIC.
- **Fuente oficial:** [ficha del mapa litoestratigráfico 1:200.000](https://info.igme.es/cartografiadigital/geologica/mapa.aspx?Id=15&parent=%2Ftematica%2Ftematicossingulares.aspx), [servicio WMS](https://mapas.igme.es/gis/services/Cartografia_Tematica/IGME_Litoestratigrafico_200/MapServer/WMSServer) y [servicio REST](https://mapas.igme.es/gis/rest/services/Cartografia_Tematica/IGME_Litoestratigrafico_200/MapServer).
- **Cobertura y escala:** cobertura nacional continua; escala 1:200.000.
- **Contenido útil:** capas oficiales de litoestratigrafía, estructuras, contactos y fracturas; distingue, entre otros, contactos normales, discordantes e intrusivos, fallas, cabalgamientos y ejes de pliegue.
- **Acceso y formato:** WMS para visualización interoperable; REST para consulta en JSON o GeoJSON, con límites de registros que obligan a paginar. La ficha oficial remite al IGME para el suministro vectorial completo en ESRI Shapefile.
- **Licencia:** [condiciones de uso del IGME](https://www.igme.es/condiciones-de-uso/), salvo condición específica del suministro.
- **Papel:** X nacional inmediato y homogéneo mientras se tramita y armoniza GEODE.
- **Riesgos y limitaciones:** demasiado general para objetivos de detalle local; la densidad de información no es uniforme. Los límites del servicio REST no deben convertirse en pérdidas silenciosas de registros.

### P1 — MAGNA 1:50.000, segunda y tercera series

- **Organismo:** IGME-CSIC.
- **Fuentes oficiales:** [MAGNA, segunda serie](https://info.igme.es/cartografiadigital/geologica/Magna50.aspx?Intranet=false) y [MAGNA, tercera serie](https://info.igme.es/cartografiadigital/geologica/Magna3S.aspx).
- **Cobertura y escala:** la segunda serie comprende 1.143 hojas elaboradas entre 1972 y 2003; referencia 1:50.000, con escalas más detalladas en Canarias, Baleares y ciudades autónomas según la serie. La tercera serie actualiza solo las hojas ya publicadas.
- **Contenido útil:** mapas, memorias, unidades litológicas y cronoestratigráficas, estructuras; la tercera serie puede añadir geomorfología y procesos activos.
- **Acceso y formato:** consulta y descarga por hoja desde el portal; el formato disponible varía según la hoja y la edición. Para una cobertura vectorial oficial coherente se seguirá la vía indicada por IGME.
- **Licencia:** condiciones de uso del IGME y las condiciones particulares de cada producto.
- **Papel:** X y QA local; las memorias son especialmente útiles para interpretar unidades y estructuras.
- **Riesgos y limitaciones:** cambios de criterio entre hojas, discontinuidades de borde y distinta antigüedad. No se mezclarán códigos de leyenda entre hojas sin tabla de correspondencias documentada.

### P1 — QAFI, base de datos de fallas activas del Cuaternario de Iberia, versión 4

- **Organismos:** IGME-CSIC y colaboradores científicos de la base QAFI.
- **Fuentes oficiales:** [catálogo QAFI](https://info.igme.es/catalogo/resource.aspx?catalog=3&ctt=1&dlang=eng&lang=eng&llt=dropdown&master=infoigme&portal=1&resource=35&shcd=true&shdi=true&shgc=true&shke=true&shla=true&shli=true&shpd=true&shpu=true&shrd=true&shto=true&shuf=true), [aplicación](https://info.igme.es/qafi/), [descargas](https://info.igme.es/qafi/Download.aspx) y [servicio REST de QAFI v4](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_QAFI_v4/MapServer).
- **Cobertura:** península ibérica; fallas con evidencia de actividad durante los últimos 2,6 Ma.
- **Acceso y formato:** descarga oficial en MDB, SHP, XLS y KMZ, además de servicios WMS y REST. La página de descarga identifica la versión 4 y su documentación.
- **Licencia:** acceso gratuito sujeto al descargo de responsabilidad específico de QAFI.
- **Papel:** X estructural complementaria y QA.
- **Riesgos y limitaciones:** una falla cuaternaria activa no equivale a una estructura mineralizante y QAFI no representa todas las fallas antiguas relevantes. Deben preservarse el estado de aceptación y los conjuntos de fallas activas, debatidas y descartadas.

### P2 — Geología armonizada europea 1:1.000.000

- **Organismo:** European Geological Data Infrastructure, EGDI, y servicios geológicos nacionales participantes.
- **Fuentes oficiales:** [tema Basic Geology de EGDI](https://www.europe-geology.eu/scientific-themes/basic-geology/), [registro de metadatos del conjunto armonizado](https://egdi.geology.cz/record/basic/5729ffdf-2558-48fc-a5d2-645a0a010855) y [visor EGDI](https://maps.europe-geology.eu/?mapname=egdi_new_structure).
- **Cobertura y escala:** paneuropea, edad y litología armonizadas a escala aproximada 1:1.000.000.
- **Acceso y formato:** servicios interoperables europeos, alimentados por WFS nacionales y vocabularios INSPIRE/OneGeology.
- **Licencia:** el registro oficial declara CC BY 4.0.
- **Papel:** QA, vocabulario y continuidad transfronteriza.
- **Riesgos y limitaciones:** escala muy gruesa, posibles huecos y heterogeneidad entre proveedores. No sustituye a GEODE ni a MAGNA.

## 3. Inventarios modernos de indicios, yacimientos, explotaciones y recursos

### P0 — BDMIN, Base de Datos de Recursos Minerales

- **Organismo:** IGME-CSIC.
- **Fuentes oficiales:** [ficha de BDMIN](https://info.igme.es/catalogo/resource.aspx?catalog=3&ctt=1&dlang=en&lang=spa&llt=dropdown&master=infoigme&portal=1&resource=23), [portal de servicios cartográficos IGME](https://mapas.igme.es/), [REST de indicios metalogenéticos](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_BDMIN_Indicios/MapServer) y [REST de rocas y minerales industriales](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_BDMIN_Explotaciones/MapServer).
- **Cobertura y geometría:** nacional; entidades puntuales en EPSG:4326 en los servicios consultados.
- **Contenido útil:** código e identificación del indicio o mina, sustancia, localización administrativa y coordenadas; según la capa también aparecen edades, asociación mineral, morfología, tamaño y relación con zonas geológicas.
- **Acceso y formato:** consulta web, WMS y REST. REST permite JSON o GeoJSON y requiere paginación por el límite de entidades del servicio.
- **Licencia:** [condiciones de uso del IGME](https://www.igme.es/condiciones-de-uso/), salvo condiciones particulares indicadas en los metadatos.
- **Papel:** Y, fuente principal de etiquetas positivas modernas por commodity y tipo de recurso.
- **Riesgos y limitaciones:** no es un censo exhaustivo de mineralización; la ausencia de punto no es un negativo. La página de servicios indica una revisión antigua y el catálogo no ofrece un historial de versiones suficientemente granular, por lo que cada extracción debe quedar congelada con fecha, recuento y hash. Deben auditarse precisión espacial, duplicados, estado, vocabulario de sustancias y posibles registros históricos. Si un atributo de BDMIN define Y, ese atributo y sus derivados no pueden entrar en X.

### P1 — Catastro Minero

- **Organismo:** Ministerio para la Transición Ecológica y el Reto Demográfico, MITECO.
- **Fuentes oficiales:** [Catastro Minero](https://www.miteco.gob.es/es/energia/mineria-explosivos/catastro.html), [visor oficial](https://geoportal.minetur.gob.es/CatastroMinero), [descarga nacional CSV](https://geoportal.minetur.gob.es/CatastroMinero/api/reportDerechosMineros?idCCAA=&idProv=&idMuni=&geometria&extension=CSV) y [servicio WMS](https://geoportal.minetur.gob.es/cgi-bin/mapservcm?request=GetCapabilities&service=WMS).
- **Cobertura:** territorio nacional, mar territorial y plataforma continental.
- **Contenido útil:** derechos mineros y su estado administrativo: permisos de exploración e investigación, concesiones de explotación y autorizaciones según las secciones de la legislación minera.
- **Acceso y formato:** visor, API de informes CSV o XLS y WMS.
- **Licencia:** condiciones de reutilización de la [sede del Ministerio de Industria y Turismo](https://sede.serviciosmin.gob.es/es-ES/Paginas/aviso.aspx#Reutilizacion), incluida la cita de la fuente y la fecha de actualización.
- **Papel:** BIAS/AUDIT para actividad administrativa, accesibilidad histórica y presión de exploración; posible estratificación de validación.
- **Riesgos y limitaciones:** un derecho minero no demuestra una mineralización, un yacimiento ni una explotación activa. Tampoco su ausencia constituye evidencia geológica negativa. La frecuencia declarada de actualización y la fecha observable en catálogos no siempre coinciden; se registrará la fecha efectiva de extracción.

### P1 — Estadística Minera de España y Panorama Minero

- **Organismos:** MITECO e IGME-CSIC.
- **Fuentes oficiales:** [consulta de Estadística Minera](https://www.miteco.gob.es/es/energia/mineria-explosivos/estadistica/consulta.html), [Estadística Minera de España 2024](https://www.miteco.gob.es/content/dam/miteco/es/energia/files-1/mineria/Estadistica/DatosBibliotecaConsumer/ESTADISTICA%20MINERA%202024-1.pdf) y [Panorama Minero de IGME](https://info.igme.es/catalogo/resource.aspx?catalog=1&ctt=1&dlang=eng&lang=spa&llt=dropdown&master=datosgobes&portal=1&resource=32).
- **Cobertura:** nacional; la Estadística Minera ofrece series anuales de producción y estructura del sector, y Panorama Minero documenta producción, recursos, reservas, comercio y contexto por sustancia.
- **Acceso y formato:** publicaciones y tablas oficiales, principalmente PDF y consulta web.
- **Licencia:** condiciones de reutilización del organismo responsable y atribución de la edición concreta.
- **Papel:** QA contextual de órdenes de magnitud, actividad y relevancia económica; no valida espacialmente el modelo.
- **Riesgos y limitaciones:** no se ha confirmado una capa nacional abierta, geocodificada y homogénea de tonelajes de recursos o reservas. Las cifras no deben convertirse automáticamente en etiquetas espaciales. Toda cifra extraída requiere sustancia, unidad, clase de recurso o reserva, fecha, fuente y localización explícitas.

### P2 — Cartografía metalogenética 1:200.000

- **Organismo:** IGME-CSIC.
- **Fuente oficial:** [Mapa Metalogenético de España 1:200.000](https://info.igme.es/cartografiadigital/tematica/metalogenetico200.aspx?language=es) y [serie histórica 1973–1974](https://info.igme.es/cartografiadigital/tematica/metalogeneticoA200.aspx?language=es).
- **Cobertura:** la serie moderna publicada solo cubre nueve hojas; no constituye cobertura nacional continua.
- **Contenido útil:** indicios y yacimientos, sustancia, morfología, volumen o recursos y controles geológicos representados en las hojas disponibles.
- **Acceso y formato:** cartografía y documentación por hoja desde IGME.
- **Licencia:** condiciones de uso del IGME y de cada edición.
- **Papel:** QA regional e hipótesis metalogenéticas.
- **Riesgos y limitaciones:** cobertura incompleta y posible dependencia de las mismas fuentes que BDMIN; no es un conjunto de validación independiente.

### P2 — MIN4EU

- **Organismo:** EGDI y servicios geológicos nacionales participantes.
- **Fuentes oficiales:** [registro de MIN4EU](https://egdi.geology.cz/record/basic/5f8008e9-7928-4ef3-a0d2-42e70a010833), [metadatos del WFS](https://egdi.geology.cz/record/basic/60c74fbf-b934-4f5a-9e55-7cd40a010833) y [servicio WFS de EGDI](https://maps.europe-geology.eu/wfs/).
- **Cobertura:** ocurrencias y minas de Europa en tierra firme, integradas desde proveedores geológicos nacionales.
- **Acceso y formato:** datos vectoriales mediante servicios interoperables.
- **Licencia:** el registro oficial declara CC BY 4.0 para el conjunto general y recoge excepciones de proveedor; deben conservarse los derechos por entidad.
- **Papel:** armonización de commodities, ontología y QA transfronteriza.
- **Riesgos y limitaciones:** la parte española puede proceder de BDMIN u otra fuente nacional y, por tanto, no es validación independiente. Hay heterogeneidad temporal, semántica y de licencias entre proveedores.

## 4. Geoquímica

### P0 — Base de Datos de Geoquímica del IGME

- **Organismo:** IGME-CSIC.
- **Fuentes oficiales:** [ficha de la Base de Datos de Geoquímica](https://info.igme.es/catalogo/resource.aspx?catalog=3&ctt=1&dlang=eng&lang=spa&llt=dropdown&master=infoigme&portal=1&resource=20), [aplicación de consulta](https://info.igme.es/Geoquimica/) y [servicio REST de muestras](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_MuestrasGeoquimica/MapServer).
- **Cobertura:** campañas geoquímicas del IGME en España; la cobertura y densidad dependen de la campaña.
- **Acceso y formato:** aplicación web y REST, con respuesta JSON o GeoJSON y paginación cuando se alcance el límite del servicio.
- **Licencia:** condiciones de uso del IGME, comprobando los metadatos de cada campaña.
- **Papel:** X geoquímica primaria.
- **Riesgos y limitaciones:** no debe tratarse como una campaña homogénea. Hay que preservar campaña, medio de muestreo, profundidad o fracción, preparación, digestión, método analítico, laboratorio, unidades, límite de detección, censura, fecha y precisión de coordenadas. Las interpolaciones deberán ajustarse dentro de cada pliegue de validación espacial para evitar fuga de información.

### P1 — Atlas Geoquímico de España 2012

- **Organismo:** IGME-CSIC.
- **Fuentes oficiales:** [ficha del Atlas Geoquímico](https://info.igme.es/catalogo/resource.aspx?catalog=3&ctt=1&dlang=eng&lang=spa&llt=dropdown&master=infoi&portal=1&resource=8309), [carpeta REST del Atlas](https://mapas.igme.es/gis/rest/services/AtlasGeoquimico), [muestras del Atlas](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_MuestrasGeoquimica2012/MapServer) y, como ejemplo de superficie elemental, [isovalores de Au](https://mapas.igme.es/gis/rest/services/AtlasGeoquimico/IGME_MapaIsovalores2012_Au/MapServer).
- **Cobertura y resolución:** España peninsular e islas. La publicación documenta 14.864 muestras de sedimento de corriente, 13.505 de suelo superficial de 0–20 cm y 7.682 de suelo de 20–40 cm. Las superficies publicadas se interpolaron por inverso de la distancia al cuadrado sobre malla de 1.000 m.
- **Acceso y formato:** puntos y superficies mediante servicios REST/WMS y productos cartográficos por elemento.
- **Licencia:** condiciones de uso del IGME.
- **Papel:** X derivada y referencia nacional.
- **Riesgos y limitaciones:** la digestión total con cuatro ácidos y la digestión parcial con agua regia no son intercambiables. Las superficies publicadas suavizan los datos y trasladan el diseño de muestreo y posibles señales antrópicas. Se preferirán los puntos crudos; una superficie derivada no se usará para evaluar puntos que participaron en su interpolación sin control de fuga espacial.

### P2 — GEMAS

- **Organismo:** EuroGeoSurveys/EGDI y servicios geológicos europeos participantes.
- **Fuentes oficiales:** [registro de metadatos GEMAS](https://metadata.europe-geology.eu/record/full/399663a7-0941-45a3-8952-28bbae54a5b6), [servicio REST oficial](https://gsi.geodata.gov.ie/server/rest/services/Geochemistry/IE_GSI_GEMAS_Geochemistry_Agricultural_Grazing_Land_Soil_EU_WGS84/MapServer) y [visor EGDI](https://maps.europe-geology.eu/#baslay=baseMapGEUS&layers=gemas_ap_aquaregiaxrf).
- **Cobertura y detalle:** Europa; muestreo de 2008–2009, aproximadamente una muestra por 2.500 km². Suelos agrícolas de 0–20 cm y de pastizal de 0–10 cm; análisis multielemental por agua regia y XRF.
- **Acceso y formato:** puntos mediante REST/WMS y descarga vectorial; el registro indica escala equivalente aproximada 1:1.000.000.
- **Licencia:** CC BY 4.0 según el registro oficial.
- **Papel:** QA transfronteriza y normalización de rangos.
- **Riesgos y limitaciones:** densidad demasiado baja para prospectividad local y fuerte condicionamiento por uso del suelo y horizonte muestreado.

## 5. Magnetometría, gravimetría, radiometría y otros métodos geofísicos

### P0 — SIGEOF, Sistema de Información Geofísica del IGME

- **Organismo:** IGME-CSIC.
- **Fuentes oficiales:** [ficha SIGEOF](https://info.igme.es/catalogo/resource.aspx?catalog=3&ctt=1&dlang=eng&lang=spa&llt=dropdown&master=infoigme&portal=1&resource=65), [aplicación SIGEOF](https://info.igme.es/SIGEOF/), [WMS](https://mapas.igme.es/gis/services/BasesDatos/IGME_SIGEOF/MapServer/WMSServer?request=getcapabilities&service=wms&version=1.3.0), [REST](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_SIGEOF/MapServer) y [guía de formatos SIGEOF, versión 25.0 de mayo de 2024](https://info.igme.es/sigeof/doc/SIGEOF_INFO.pdf).
- **Cobertura y resolución:** campañas heterogéneas en España. El IGME indica expresamente que la aeromagnetometría y radiometría cubren solo parte del territorio nacional; no existe una resolución nacional única.
- **Contenido útil:** gravimetría, aeromagnetometría, radiometría gamma, métodos eléctricos, TDEM, magnetotelúrica, resonancia magnética, sísmica, diagrafías y petrofísica. Los productos aerotransportados pueden incluir líneas, puntos de vuelo y mallas; la radiometría puede aportar K, Th, U y cuentas totales según campaña.
- **Acceso y formato:** según método, consulta web, WMS/REST, portapapeles, Excel, CSV y SHP; también formatos especializados como SEG-Y, TIFF, LAS o ASCII. La guía documenta CRS y límites de consulta por colección.
- **Licencia:** condiciones de uso del IGME y derechos específicos de cada estudio, especialmente cuando el origen no sea exclusivamente IGME.
- **Papel:** X geofísica principal.
- **Riesgos y limitaciones:** deben conservarse campaña, fecha, método, sensor, espaciado de líneas, altura, nivelado, datum, correcciones, densidad usada en Bouguer, tamaño de celda y procedencia. No se deben mosaicar valores de campañas distintas sin armonización y evaluación de solapes. Se generará una máscara de disponibilidad por método; la falta de dato geofísico no es un valor geológico. Los productos transformados, como reducción al polo o gradientes, se distinguirán de las observaciones.

## 6. DEM, geomorfología, drenaje y observación de la superficie

### P0 — MDT05, primera cobertura

- **Organismo:** Instituto Geográfico Nacional/Centro Nacional de Información Geográfica, IGN-CNIG.
- **Fuente oficial:** [Modelo Digital del Terreno MDT05](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=MDT05).
- **Cobertura y resolución:** nacional, paso de malla de 5 m. Derivado de la clase terreno de la primera cobertura LiDAR PNOA; Ceuta, Melilla y Alborán presentan la excepción fotogramétrica indicada por CNIG.
- **Acceso y formato:** Cloud Optimized GeoTIFF por hojas MTN50; ETRS89 o REGCAN95 en proyección UTM; altitudes ortométricas.
- **Licencia:** [política de datos de IGN-CNIG](https://www.ign.es/web/politica-datos), compatible con CC BY 4.0 con atribución.
- **Papel:** X para cota, pendiente, orientación, curvaturas, relieve relativo, TPI, TRI y métricas de red de drenaje calculadas a ventanas declaradas.
- **Riesgos y limitaciones:** las fechas de captura varían por hoja y las masas de agua han sido interpoladas o editadas, por lo que allí la precisión es menor. Toda derivada debe registrar algoritmo, ventana, tratamiento de bordes y versión del mosaico.

### P1 — MDT02, segunda cobertura

- **Organismo:** IGN-CNIG.
- **Fuente oficial:** [MDT02, segunda cobertura](https://centrodedescargas.cnig.es/CentroDescargas/modelo-digital-terreno-mdt02-segunda-cobertura).
- **Cobertura y resolución:** malla de 2 m, procedente de la segunda cobertura LiDAR 2015–2021; el propio producto advierte que la cobertura disponible no es completa.
- **Acceso y formato:** COG por hojas MTN25, ETRS89 o REGCAN95 UTM.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** X para pilotos regionales y análisis de microrelieve o labores antiguas.
- **Riesgos y limitaciones:** cobertura incompleta y distinta fecha/resolución respecto de MDT05. No se mezclarán sin una máscara explícita de procedencia y una resolución analítica común.

### P2 — Tercera cobertura LiDAR PNOA

- **Organismo:** IGN-CNIG.
- **Fuentes oficiales:** [especificaciones PNOA LiDAR](https://pnoa.ign.es/pnoa-lidar/especificaciones-tecnicas) y [descarga de tercera cobertura](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=LIDA3).
- **Cobertura y resolución:** adquisición 2022–2025, densidad mínima indicada de 5 puntos/m²; teselas LAZ de 1 km por 1 km.
- **Acceso y formato:** nubes de puntos clasificadas en LAZ.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** X o QA en pilotos de detalle.
- **Riesgos y limitaciones:** publicación y clasificación progresivas, gran volumen y heterogeneidad temporal; no es todavía una base nacional estable para el primer experimento.

### P1 — Información Geográfica de Referencia de Hidrografía

- **Organismo:** IGN-CNIG.
- **Fuente oficial:** [Hidrografía de referencia](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=HIDRO).
- **Cobertura y escala:** nacional, escala de referencia 1:5.000; distribuida por demarcación hidrográfica.
- **Acceso y formato:** GeoPackage y Shapefile.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** X para distancia a cauces, orden de red, densidad de drenaje y contexto de depósitos aluviales; también QA de redes derivadas del DEM.
- **Riesgos y limitaciones:** integra masas de agua del ciclo de planificación 2021–2027 y elementos obtenidos del LiDAR de 2 m; parte de los elementos ajenos al ámbito de planificación sigue en validación. Se guardará versión y tipo de entidad, sin confundir red cartográfica con paleodrenaje.

## 7. Teledetección y cobertura del suelo

### P1 — Sentinel-2 Level-2A

- **Organismo:** Programa Copernicus de la Unión Europea y ESA; distribución mediante Copernicus Data Space Ecosystem.
- **Fuentes oficiales:** [documentación Sentinel-2](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel2.html), [Copernicus Browser](https://browser.dataspace.copernicus.eu/) y [API STAC](https://documentation.dataspace.copernicus.eu/APIs/STAC.html).
- **Cobertura y resolución:** global; reflectancia de superficie corregida atmosféricamente. Bandas a 10, 20 y 60 m, con productos de aproximadamente 110 por 110 km sobre teselas UTM de 100 km.
- **Acceso y formato:** Browser y APIs oficiales, incluido STAC; la descarga de observación de la Tierra requiere registro y está sujeta a cuotas operativas.
- **Licencia:** [términos de Copernicus Data Space](https://dataspace.copernicus.eu/terms-and-conditions); datos Sentinel con acceso completo, gratuito y abierto conforme al aviso legal del producto.
- **Papel:** X para composiciones estacionales, índices de óxidos de hierro, arcillas de banda ancha, suelo desnudo y contexto de alteración superficial.
- **Riesgos y limitaciones:** solo dispone de dos bandas SWIR amplias y no permite identificación mineral hiperespectral. Nubes, sombras, vegetación, humedad, fenología y cambios de línea base de procesamiento pueden dominar la señal. Se fijarán fechas, baseline, máscara SCL y reglas de composición; los índices se interpretarán como proxies.

El antecedente de Rodalquilar demuestra la utilidad potencial de una cadena hiperespectral con QA, MNF/PPI/MTMF y abundancias minerales en un distrito concreto. No se equiparará esa información Hyperion con Sentinel-2 ni se asumirá una cobertura hiperespectral nacional homogénea. Una fuente hiperespectral futura será P2/piloto hasta verificar misión, cobertura, resolución, licencia, corrección atmosférica, suelo expuesto y mecanismo geológico.

### P1 — Sentinel-1 GRD o RTC

- **Organismo:** Copernicus/ESA.
- **Fuentes oficiales:** [documentación Sentinel-1](https://documentation.dataspace.copernicus.eu/Data/SentinelMissions/Sentinel1.html) y [descripción oficial de productos Sentinel-1](https://sentiwiki.copernicus.eu/web/s1-products).
- **Cobertura y resolución:** global desde 2014. En modo IW, el producto GRD de alta resolución usado habitualmente en tierra tiene resolución aproximada de 20 por 22 m y espaciado de píxel de 10 m; las polarizaciones dependen de la adquisición.
- **Acceso y formato:** productos SAFE y variantes preparadas para análisis, incluido COG_SAFE o RTC cuando estén disponibles en el catálogo oficial.
- **Licencia:** términos de Copernicus Data Space y política de datos Sentinel.
- **Papel:** X para rugosidad, humedad superficial, lineamientos y estructura geomorfológica.
- **Riesgos y limitaciones:** moteado, sombras y layover, dependencia del ángulo de incidencia, órbita y polarización. Se usará RTC o una cadena explícita de calibración y corrección topográfica; ascendente y descendente no se fusionarán sin control. Los lineamientos inferidos necesitan validación geológica y pueden ser antrópicos.

### P1 — SIOSE

- **Organismo:** IGN-CNIG y administraciones participantes.
- **Fuentes oficiales:** [SIOSE nacional](https://centrodedescargas.cnig.es/CentroDescargas/siose) y [actualizaciones SIOSE de Alta Resolución](https://centrodedescargas.cnig.es/CentroDescargas/novedades?codSerie=SIOAR).
- **Cobertura y detalle:** SIOSE 1:25.000 dispone de ediciones nacionales 2005, 2009, 2011 y 2014; SIOSE AR ofrece ediciones y actualizaciones autonómicas posteriores con estado de publicación variable.
- **Acceso y formato:** GeoPackage o geodatabase por comunidad autónoma, según edición.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** MASK y BIAS/AUDIT para vegetación, urbanización, agricultura, suelo expuesto y detectabilidad de señales remotas.
- **Riesgos y limitaciones:** es cobertura/ocupación del suelo, no geología. Se elegirá una edición temporal coherente o se incluirán año y máscara de cobertura; no se mezclarán actualizaciones autonómicas como si fueran simultáneas.

### P1 — PNOA, ortofoto de máxima actualidad

- **Organismo:** IGN-CNIG y administraciones participantes.
- **Fuente oficial:** [PNOA máxima actualidad](https://centrodedescargas.cnig.es/CentroDescargas/catalogo.do?Serie=02211).
- **Cobertura y resolución:** nacional; el mosaico toma la ortofoto más reciente de cada zona. La resolución y fecha varían espacialmente; CNIG distribuye la huella con ambos atributos.
- **Acceso y formato:** COG por hoja MTN25, shapefile de fechas y resoluciones, y metadatos XML; ETRS89 o REGCAN95.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** QA visual y cartografía local de labores, drenaje y exposición.
- **Riesgos y limitaciones:** no es un predictor nacional temporalmente homogéneo. La iluminación, vegetación, resolución y fecha cambian por zona. Digitalizar rasgos alrededor de las minas romanas conocidas y usarlos para predecir esas mismas etiquetas produciría fuga de información.

### P2 — Copernicus DEM GLO-30

- **Organismo:** Copernicus.
- **Fuentes oficiales:** [documentación DEM en Copernicus Data Space](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM.html), [catálogo CCM](https://documentation.dataspace.copernicus.eu/Data/Others/CCM.html) y [licencia específica COP-DEM GLO-30](https://documentation.dataspace.copernicus.eu/APIs/SentinelHub/Data/DEM/resources/license/License-COPDEM-30.pdf).
- **Cobertura y resolución:** global, 30 m. Es un modelo digital de superficie, no un modelo de terreno desnudo.
- **Acceso y formato:** Browser y APIs oficiales, incluida distribución por servicios de objetos y catálogos; requiere registro.
- **Licencia:** acceso completo, gratuito y abierto bajo la licencia específica del producto.
- **Papel:** QA transfronteriza o respaldo fuera de la cobertura nacional.
- **Riesgos y limitaciones:** vegetación y edificios forman parte de la superficie; CNIG MDT05 es preferible dentro de España.

## 8. Límites, costa y dominio de análisis

### P0 — Límites administrativos

- **Organismo:** IGN-CNIG.
- **Fuente oficial:** [límites municipales, provinciales y autonómicos](https://centrodedescargas.cnig.es/CentroDescargas/limites-municipales-provinciales-autonomicos).
- **Cobertura y escala:** nacional, escala de referencia 1:25.000; ETRS89 o REGCAN95 en coordenadas geográficas.
- **Acceso y formato:** Shapefile, GeoPackage y GML; el portal publica ediciones vigentes con fecha.
- **Licencia:** política de datos IGN-CNIG compatible con CC BY 4.0.
- **Papel:** MASK, agregación de resultados y definición de bloques espaciales; nunca predictor geológico.
- **Riesgos y limitaciones:** algunas líneas son provisionales y el CNIG advierte incertidumbres del orden de decenas de metros en límites procedentes de mediciones históricas. Se fijará una edición y no se usarán fronteras administrativas como X.

### P0 — Línea de costa del Instituto Hidrográfico de la Marina

- **Organismos:** Instituto Hidrográfico de la Marina, IHM, con distribución por CNIG.
- **Fuentes oficiales:** [Información Geográfica de Referencia](https://centrodedescargas.cnig.es/CentroDescargas/informacion-geografica-referencia) y [detalle de la línea de costa](https://centrodedescargas.cnig.es/CentroDescargas/index.jsp%2821/05/detalleArchivo?sec=9000006).
- **Cobertura y geometría:** costa de España, incluidas islas; líneas de pleamar y bajamar, en ETRS89 o REGCAN95.
- **Acceso y formato:** Shapefile nacional.
- **Licencia:** descarga gratuita con atribución al Instituto Hidrográfico de la Marina; la ficha ofrece fórmulas compatibles con CC BY 4.0.
- **Papel:** MASK tierra-mar y control de celdas costeras; nunca X geológica por sí sola.
- **Riesgos y limitaciones:** la posición depende de la definición de pleamar o bajamar, fecha y topología insular. Debe declararse qué línea se usa para el dominio.

## 9. Fuente opcional para sesgos climáticos

### P2 — AEMET OpenData

- **Organismo:** Agencia Estatal de Meteorología, AEMET.
- **Fuentes oficiales:** [información de AEMET OpenData](https://opendata.aemet.es/centrodedescargas/info), [documentación de la API](https://opendata.aemet.es/dist/) y [valores climatológicos](https://www.aemet.es/es/serviciosclimaticos/datosclimatologicos/valoresclimatologicos).
- **Cobertura:** estaciones y productos climatológicos oficiales para España. No se confirma una resolución única aplicable a todos los productos.
- **Acceso y formato:** API REST gratuita con clave y productos de consulta o descarga.
- **Licencia:** reutilización con cita de AEMET y de la fecha o producto, conforme a sus condiciones.
- **Papel:** BIAS/AUDIT para meteorización, vegetación, erosión y detectabilidad de la superficie; no fuente geológica primaria.
- **Riesgos y limitaciones:** las superficies climáticas son interpolaciones de estaciones y pueden diferir de los valores observados. La densidad de estaciones y el periodo climatológico deben conservarse.

## 10. Decisiones metodológicas y prevención de fuga de información

1. **Jerarquía geológica.** GEODE 1:50.000 será la fuente objetivo. El mapa continuo 1:200.000 permitirá iniciar una cobertura nacional reproducible. MAGNA se conservará para trazabilidad, detalle y control de calidad; EGDI 1:1.000.000 solo para armonización.
2. **Etiquetas modernas.** BDMIN generará etiquetas positivas modernas. No se crearán negativos a partir de zonas sin registros. Catastro Minero, Estadística Minera, Panorama Minero y MIN4EU servirán para auditoría o contexto, no como equivalentes automáticos de una ocurrencia.
3. **Recursos y reservas.** No se ha verificado una base abierta nacional, geocodificada y homogénea con tonelajes y clases de recursos/reservas. Si el experimento requiere esas magnitudes, se solicitará al IGME/MITECO una fuente estructurada o se extraerán de publicaciones oficiales con doble revisión y trazabilidad documental.
4. **Geoquímica.** Los puntos se modelarán por campaña y método. Cualquier imputación, transformación o interpolación que use observaciones deberá ajustarse solo con el conjunto de entrenamiento de cada partición espacial.
5. **Geofísica.** Se mantendrá la huella de cada levantamiento. La cobertura de campaña no se codificará como cero y las mallas se armonizarán solo después de evaluar nivelado, datum, resolución y solapes.
6. **Teledetección.** Sentinel-2 y Sentinel-1 aportarán proxies superficiales, no identificaciones directas de mena. Las máscaras de nube, vegetación, suelo expuesto, órbita y cobertura serán parte de la reproducibilidad.
7. **Máscaras y variables de sesgo.** Límites administrativos, costa, derechos mineros, cobertura cartográfica y uso del suelo no se incorporarán como predictores geológicos salvo que exista una hipótesis explícita y se evalúe su riesgo de aprender historia de búsqueda, accesibilidad o administración.
8. **Leakage de proximidad.** No se usarán como X distancias o densidades calculadas desde BDMIN, OxREP, MIN4EU o una cartografía digitalizada alrededor de los propios positivos cuando la misma fuente contribuya a Y. La señal romana solo entrará en el Modelo B del experimento incremental y se calculará dentro de cada partición espacial cuando corresponda.
9. **Escalas.** Una capa 1:200.000 o 1:1.000.000 no gana precisión por remuestrearla a 100 m o 1 km. La resolución nominal, escala de compilación y tamaño de celda analítico se guardarán por separado.
10. **WMS.** Los WMS se usarán para inspección y QA. No se entrenará con capturas ni colores de estilos cartográficos; para variables se obtendrá el dato vectorial o ráster y su metadato oficial.

## 11. Protocolo reproducible de adquisición

Para cada recurso se guardará un manifiesto con:

- organismo, nombre oficial, URL, identificador de capa o producto y fecha/hora UTC de consulta;
- edición o fecha de datos, fecha de metadatos, licencia y texto de atribución;
- parámetros de API, consulta, filtros, campos, CRS de origen y transformación;
- tamaño, recuento de entidades o celdas, extensión espacial y hash SHA-256 del archivo recibido;
- cabeceras ETag y Last-Modified cuando existan;
- cobertura, resolución, escala de compilación, unidad, valor sin dato y precisión conocida;
- registro de paginación y comparación entre recuento declarado, descargado y válido;
- inventario de geometrías vacías, inválidas, duplicadas o fuera del dominio, sin eliminarlas silenciosamente.
- `upstream_dataset_id`, organismo y campaña original, fechas de observación e ingestión y relaciones de derivación entre BDMIN, MIN4EU, mapas metalogenéticos, GEODE y OxREP;
- indicador `independent_of_target` con evidencia y responsable de la decisión, para no tratar como validación independiente la misma ocurrencia redistribuida por varios portales.

Las descargas REST se paginarán mediante un identificador estable cuando el servicio lo permita y se comprobarán contra el recuento del servicio. Para GEODE y el mapa litoestratigráfico vectorial se documentará la solicitud formal y se archivarán las condiciones de suministro; no se reconstruirá el producto a partir de teselas de visualización.

## 12. Orden recomendado de incorporación

| Orden | Fuente | Resultado esperado |
|---:|---|---|
| 1 | GEODE y mapa litoestratigráfico 1:200.000 | Litología, edad, contactos y estructuras con trazabilidad |
| 2 | BDMIN | Etiquetas positivas modernas congeladas por fecha y commodity |
| 3 | Base de Geoquímica IGME y puntos del Atlas 2012 | Variables multielementales con campaña y método |
| 4 | SIGEOF | Huellas, puntos y mallas de magnetometría, gravimetría y radiometría |
| 5 | MDT05, Hidrografía, límites y costa | Dominio, geomorfometría, drenaje y máscaras |
| 6 | Sentinel-2 y Sentinel-1 | Proxies superficiales multitemporales con máscaras de calidad |
| 7 | QAFI, SIOSE, Catastro y publicaciones mineras | Estructuras complementarias y auditoría de sesgos |
| 8 | MAGNA/PNOA/MDT02 por zonas piloto | Interpretación local y control de calidad |
| 9 | EGDI, MIN4EU, GEMAS, COP-DEM y AEMET | Armonización, frontera y análisis complementarios |

## 13. Condiciones de reutilización que deben archivarse

- **IGME-CSIC:** [condiciones de uso](https://www.igme.es/condiciones-de-uso/) y [licencia genérica de reutilización](https://info.igme.es/media/Pdfs/LicUsoIGME_GENERICA_2022.pdf). La licencia genérica permite reutilización comercial y no comercial con la atribución «Origen de los datos: ©Instituto Geológico y Minero de España (IGME)», además de la cita de autoría y actualización que figure en los metadatos; una condición específica del conjunto prevalece.
- **IGN-CNIG:** [política de datos](https://www.ign.es/web/politica-datos). Las fichas citadas declaran licencia compatible con CC BY 4.0 y especifican la atribución.
- **Copernicus:** [términos y condiciones de Copernicus Data Space](https://dataspace.copernicus.eu/terms-and-conditions), además de la licencia particular cuando el producto no sea Sentinel.
- **MITECO/Ministerio de Industria y Turismo:** [aviso de reutilización](https://sede.serviciosmin.gob.es/es-ES/Paginas/aviso.aspx#Reutilizacion), con cita de fuente y fecha de actualización.

La licencia y atribución se fijarán por archivo, no solo por portal, porque algunos servicios contienen datos aportados por terceros o productos con condiciones particulares.
