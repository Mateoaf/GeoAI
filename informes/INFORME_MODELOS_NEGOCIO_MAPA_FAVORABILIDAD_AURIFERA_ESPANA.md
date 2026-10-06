# Informe de modelos de negocio para un mapa de favorabilidad aurífera de España

**Fecha:** 1 de octubre de 2026  
**Supuesto de trabajo:** el equipo ya dispone de un modelo operativo que genera una superficie nacional de favorabilidad aurífera. Este informe estudia cómo convertirla en una oferta comercial; no presupone que una puntuación de favorabilidad equivalga a un descubrimiento, recurso o reserva.

## 1. Resumen ejecutivo

El activo vendible no es solo el raster nacional. Es una combinación de conocimiento geológico codificado, priorización espacial, explicación de cada objetivo, datos preparados, flujo de actualización y apoyo para decidir dónde invertir la siguiente jornada de exploración. El cliente paga cuando esa combinación reduce el coste o el tiempo de descartar terreno y concentra mejor el presupuesto de campo.

La oportunidad comercial más realista empieza con **servicios de evaluación de áreas y estudios de objetivos para empresas de exploración**, con un alcance acotado y revisión de un geólogo. Esa modalidad permite aprender qué entregables usan los clientes y qué evidencias consideran suficientes antes de invertir en una plataforma completa. En paralelo, conviene desarrollar una **licencia anual empresarial** para clientes con actividad recurrente. Una API o suscripción autoservicio puede escalar después, cuando la cobertura, la estabilidad de las puntuaciones, la documentación y la actualización estén automatizadas.

No recomiendo iniciar el negocio con un pago por éxito, una promesa de descubrimiento o la adquisición de derechos mineros como modelo principal. Los resultados dependen de campañas costosas y largas, de permisos, geología local y factores que un mapa regional no observa. Si se desean conservar derechos económicos sobre objetivos, deberían ser una opción separada, revisada legalmente y financiada con capital específico.

### Orden recomendado de lanzamiento

1. **Estudio de cartera o de área bajo contrato**, vendido a exploradoras y consultoras.
2. **Licencia empresarial anual** con mapas, fichas, acceso GIS y actualizaciones.
3. **Campañas de validación y refinamiento local** como servicio adicional, con socios de campo.
4. **API y licencia de datos** para integrar scores en software de terceros.
5. **Consorcios y contratos públicos/académicos** para proyectos regionales y metodológicos.
6. **Opción, joint venture o participación en derechos de exploración** solo para objetivos seleccionados y bajo una estructura independiente.

## 2. Qué estamos vendiendo y qué no

El proyecto técnico describe un mapa continuo nacional, inicialmente pensado a una malla de 1 km, derivado de indicios BDMIN y de variables geocientíficas. También contempla distinguir oro primario de oro aluvial, expresar incertidumbre y comprobar el rendimiento con separación espacial. El propio diseño reconoce que la falta de un indicio registrado no es una ausencia probada. Estas propiedades deben reflejarse en el producto y en el contrato.

**Propuesta de valor:** ayudar a un equipo de exploración a ordenar áreas amplias, priorizar revisión geológica y diseñar dónde adquirir evidencia nueva. El mapa puede contestar «¿qué zonas merecen una revisión más detallada, dado el modelo y los datos disponibles?». Por sí solo no contesta «¿hay una mina?», «¿qué ley o tonelaje tiene?» ni «¿será rentable o autorizable?».

El registro público BDMIN del IGME reúne información geológico-minera de indicios y explotaciones; sus servicios incluyen geometrías y atributos como sustancia, morfología y asociación mineral. Por tanto, una parte sustancial de las fuentes es pública. La ventaja defendible debe residir en el tratamiento, la selección de features, la validación, la experiencia geológica, las mejoras con datos autorizados del cliente y la calidad de la decisión entregada, no en afirmar exclusividad sobre datos públicos. [Catálogo BDMIN del IGME](https://info.igme.es/catalogo/Resource.aspx?catalog=1&dlang=eng&lang=spa&master=datosgobes&resource=23), [servicio de indicios BDMIN](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_BDMIN_Indicios/MapServer/1)

### Unidad de valor comercial

La unidad inicial debería ser **una decisión de exploración**, por ejemplo:

- comparar una cartera de bloques o permisos;
- identificar las áreas que conviene descartar, retener o estudiar primero;
- seleccionar objetivos de reconocimiento de campo;
- evaluar un área antes de presentar una oferta, adquirir un permiso o asignar presupuesto;
- actualizar una cartera tras incorporar nueva cartografía, geoquímica o resultados de campo.

Entregar solo un archivo raster facilita que el cliente lo use mal o no lo use. Cada zona priorizada debería tener una ficha con score relativo, tipología (primario/aluvial cuando aplique), estabilidad entre ejecuciones, calidad/cobertura de datos, controles geológicos que contribuyen, factores que reducen confianza, restricciones cartográficas que requieren revisión y siguientes pasos sugeridos.

## 3. Clientes, problemas y disposición a pagar

| Segmento | Necesidad | Oferta de entrada | Barrera comercial |
|---|---|---|---|
| Exploradoras junior y compañías privadas | Decidir qué permisos o distritos merecen presupuesto limitado | Evaluación de área o cartera, objetivos priorizados | Presupuesto limitado; exigirán confidencialidad y una recomendación accionable |
| Productores y compañías medianas/grandes | Añadir objetivos regionales o revisar cinturones poco explorados | Licencia empresarial, análisis de cartera, integración con GIS | Due diligence técnica, seguridad, auditoría y validación geológica más exigentes |
| Consultoras geológicas y geofísicas | Acelerar selección de áreas y enriquecer entregables a clientes | Licencia profesional o marca blanca; API más adelante | Pueden ser canal y competidor; aclarar propiedad de entregables y uso de datos de clientes |
| Fondos, bancos, compradores de proyectos y asesores de M&A | Evaluar si una tesis de exploración merece diligencia técnica | Informe de cribado preliminar con límites claros | No sustituye una due diligence de recursos, títulos o permisos; alto riesgo de sobreinterpretación |
| Administraciones, servicios geológicos, universidades | Cartografía prospectiva, planificación de campañas, investigación | Proyecto regional, contrato de análisis, licencia institucional | Contratación pública más lenta; requisitos de publicación y reutilización |
| Empresas de software geoespacial/minero | Incorporar una capa de favorabilidad a su producto | Licencia de datos/API o integración OEM | Dependencia de cobertura, SLA, derechos de redistribución y actualización |

### Cliente inicial recomendado

Priorizar de 5 a 10 entrevistas con exploradoras activas en España, consultoras con clientes mineros y equipos de exploración de metales base que también valoren oro como coproducto. Las juniors pueden facilitar pilotos y feedback rápido; una consultora puede aportar distribución y conocimiento local. Los productores grandes ofrecen mayor valor contractual, pero probablemente pedirán evidencia, protección de datos y procesos de compra más largos.

La existencia de proyectos y permisos de exploración activos confirma que hay actores que toman decisiones de exploración en España. Por ejemplo, Pan Global presenta proyectos de exploración metálica en España y Ormonde comunicó la renovación de permisos de investigación en Zamora en 2025. Son señales de mercado, no una estimación del tamaño ni de la demanda específicamente por mapas de oro. [Pan Global, proyectos](https://www.panglobalresources.com/projects-overview), [actualización pública de permisos de Ormonde](https://www.investegate.co.uk/announcement/rns/shearwater-group--swg/update-re-spanish-gold-licences/8728275)

## 4. Modelos de negocio posibles

### A. Estudios de área y priorización como servicio

**Qué se entrega:** análisis de un distrito, permiso o cartera; polígonos objetivo; ranking; fichas; proyecto QGIS/COG; explicación de factores; reunión técnica y plan recomendado de validación.

**Cómo se cobra:** precio fijo por área/paquete y complejidad, con hitos de pago. Extras por integración de datos del cliente, revisión de archivos, análisis de sensibilidad, talleres o refinamiento de alta resolución. El precio se determina por valor de la decisión, tiempo de especialistas y alcance; no por número de píxeles.

**Ventajas:** es el camino más rápido al ingreso; hace explícito el valor; no exige plataforma madura; revela qué formato y evidencia son útiles.

**Riesgos:** ingresos ligados a horas; posibilidad de personalización sin límite; riesgo de entregar un análisis que el cliente trate como diligencia completa.

**Control recomendado:** contrato con área y preguntas definidas, número máximo de iteraciones, fecha de corte de datos, usos permitidos, exclusión expresa de garantía de descubrimiento y aceptación por entregables verificables. No afirmar que se han inspeccionado permisos, restricciones, accesos ni títulos salvo que ese análisis figure en el alcance.

### B. Licencia empresarial anual del producto

**Qué se licencia:** acceso a mapas y fichas para España o regiones pactadas, descargas GIS, versiones históricas, actualizaciones, documentación, soporte y número definido de usuarios/entidades afiliadas.

**Cómo se cobra:** cuota anual por organización, ámbito territorial, módulos y nivel de soporte. Puede combinarse con una cuota inicial de incorporación e integración. Las opciones de licencia deben distinguir uso interno, uso para asesorar a terceros, redistribución y productos derivados.

**Ventajas:** recurrencia; integra el producto en el ciclo anual de planificación; crea una base para actualizaciones y feedback.

**Riesgos:** el cliente puede usar el mapa una sola vez y no renovar; una actualización sin cambios relevantes debilita la renovación; la licencia se vuelve difícil de hacer cumplir si la salida es un raster sin control de distribución.

**Mitigación:** vender el servicio recurrente (nuevas fuentes, objetivos, comparativas, API/GIS y asistencia) y no solo el archivo. Ofrecer un paquete de evaluación corto que pueda convertirse en licencia anual.

### C. Suscripción autoservicio / SaaS geoespacial

**Qué incluye:** visualizador web con capas, búsqueda por coordenadas o polígono, exportación controlada, capas explicativas, historial de versiones y gestión de usuarios.

**Ingresos:** suscripción por asiento, organización, región o cuota de análisis; niveles individual, profesional y corporativo. El autoservicio nacional no debería ser el primer producto de pago sin confirmar que el usuario puede interpretar las salidas y sin controles de seguridad adecuados.

**Ventajas:** puede escalar y servir a equipos distribuidos; reduce fricción para probar un área.

**Riesgos:** inversión de producto/infraestructura; soporte y onboarding; divulgación de objetivos sensibles; expectativas de disponibilidad y precisión; posibilidad de que usuarios ocasionales confundan scores con probabilidades calibradas.

**Momento recomendado:** después de pilotos pagados que demuestren tareas repetibles y un flujo GIS/API mantenible. Antes, se puede usar un portal privado sencillo como interfaz de entrega, sin prometer un SaaS completo.

### D. API y licencia de datos para terceros

**Qué se ofrece:** consultas por coordenada/polígono, score y metadatos de versión, estabilidad, cobertura y dominio de aplicabilidad; o licencia de COG/tiles para integrar en una plataforma minera.

**Cobro:** licencia anual de integración más límites de uso, o tarifa por volumen de consultas/territorio. Si se permite redistribuir la puntuación, la tarifa debe reflejar el alcance y el número de clientes finales.

**Ventajas:** distribución mediante plataformas existentes; posible escala mayor y uso integrado en workflows de exploración.

**Riesgos:** una salida de score desnuda pierde contexto; el cliente puede combinarla con sistemas y presentarla como dato propio; dependencia técnica/SLA; exposición del modelo y los datos.

**Requisitos mínimos:** versionado inmutable, límites y términos de redistribución, bitácora de consultas, documentación de score y NoData, monitorización, controles de acceso y plan de retirada/corrección de una versión defectuosa.

### E. Consultoría de exploración potenciada por el mapa

La empresa podría vender equipos geológicos que combinen el mapa con interpretación de distrito, datos de cliente, mapas de campo, geoquímica de campaña, geofísica y muestreo. El mapa inicia y organiza el trabajo; el informe profesional y la recomendación de siguiente fase constituyen el producto.

Es una ruta de margen potencialmente mayor y fomenta relaciones de largo plazo. También requiere geólogos competentes, gestión de conflictos de interés y delimitación clara entre screening, diseño de campaña y trabajo de recursos/reservas. Recomiendo asociarse con consultores de campo para trabajos que exijan presencia regional o disciplinas que el equipo no tenga.

### F. Validación de campo y refinamiento bajo contrato

**Qué se ofrece:** convertir objetivos seleccionados en un programa de adquisición de datos: reconocimiento, muestreo, cartografía, revisión de históricos, geofísica de detalle o teledetección. La ejecución puede correr a cargo del cliente o de un socio acreditado.

**Ingresos:** honorarios de diseño/gestión y margen transparente sobre servicios subcontratados, o tarifa por campaña. Los resultados de campo regresan al modelo solo si existe permiso contractual para reutilizarlos; por defecto, deben ser confidenciales.

**Ventaja clave:** cierra el ciclo entre priorización y evidencia nueva, mejora el producto y demuestra valor de decisión.

**Riesgos:** logística, seguridad, permisos de acceso, clima, muestreo sesgado y atribución errónea de hallazgos al modelo. Una campaña sin descubrimiento no demuestra por sí sola que el modelo haya fallado, igual que un hallazgo aislado no demuestra causalidad.

### G. Marca blanca, OEM y alianzas con consultoras

Se licencia el motor, las capas o las fichas para que un tercero las incorpore a su marca. Puede acelerar ventas y dar acceso a clientes sin crear toda la fuerza comercial propia.

Negociar territorio, sector, duración, exclusividad limitada, nivel de soporte, publicación de resultados, uso de datos de campo, atribución y derechos sobre mejoras. Evitar exclusividad nacional perpetua antes de medir el potencial de venta directa. Se puede acordar exclusividad por región o sector, con mínimos de ingresos y caducidad si no se cumplen.

### H. Consorcios de investigación y contratos públicos

Financiarían mejoras metodológicas, validación independiente, ampliación de datos y generación de mapas regionales. La contraprestación puede incluir entregables abiertos, acceso institucional o derechos de publicación.

Es útil para costear I+D y aportar credibilidad, pero el ciclo de contratación puede ser largo y la obligación de publicar puede reducir la ventaja comercial. Separar desde el contrato el conocimiento metodológico, los datos públicos, el código reusable y los entregables financiados que deban difundirse.

### I. Opciones sobre terrenos, earn-in o participación en proyectos

La empresa puede identificar un objetivo, obtener una opción o colaborar con el titular de derechos, y monetizar mediante pago de opción, participación, royalties o venta posterior. Es el modelo de mayor potencial por objetivo y de mayor riesgo financiero y legal.

No confundir un área de alto score con un activo minero probado. Antes de perseguirlo hacen falta título/permiso verificable, revisión ambiental y social, geología de detalle, trabajo de campo, capital de riesgo, gestión de conflictos y asesoría jurídica. Mantener separado el negocio de datos/consultoría del vehículo que posea derechos, declarar los conflictos al cliente y no recomendar de forma independiente terrenos en los que la empresa tenga interés económico.

### J. Informes de cribado para inversión o transacciones

Un informe puede ayudar a compradores, inversores o financiadores a decidir si encargan una diligencia técnica más profunda. Su alcance debe ser una señal de cribado geoespacial, nunca una opinión de recursos, reservas, valoración económica, legalidad del título o probabilidad de permiso.

Tiene potencial de venta puntual, pero demanda control de calidad, seguro profesional y lenguaje contractual prudente. La forma más segura de entrar es a través de consultoras de diligencia técnica que integren el análisis en su alcance global.

## 5. Arquitectura de precios a validar

No hay una fuente pública fiable que establezca el precio de mercado para un mapa propietario de favorabilidad aurífera nacional en España. Por ello, no sería riguroso inventar tarifas como si fueran tarifas observadas. Se recomienda probar precios mediante propuestas reales y registrar tasa de aceptación, días de trabajo y valor del contrato.

| Oferta | Base de precio inicial | Variables que justifican niveles |
|---|---|---|
| Evaluación rápida de área | Precio fijo por paquete de polígono(s) y entrega | Superficie, tipología, urgencia, número de zonas y capas del cliente |
| Estudio de objetivos | Precio por distrito/permiso más hitos | Revisión geológica, trabajo GIS, fichas, reuniones y análisis de sensibilidad |
| Licencia empresarial | Suscripción anual por entidad y ámbito | Territorio, usuarios, actualizaciones, soporte, exportación y redistribución |
| API/OEM | Cuota anual más tramo de uso o clientes finales | Volumen, disponibilidad, integración, soporte y sublicencias |
| Campaña/refinamiento | Honorarios de diseño y gestión más costes de ejecución | Logística, muestreo, disciplinas, número de sitios y permisos de acceso |
| Contrato público/consorcio | Presupuesto por hitos y entregables | Alcance, publicación, datos abiertos, validación y participación de socios |

### Pruebas de precio prácticas

1. Ofrecer tres alcances comparables: cribado, estudio con fichas y estudio con plan de validación.
2. Cotizar al menos dos opciones contractuales: proyecto puntual y licencia con crédito parcial del importe hacia la suscripción anual.
3. Preguntar qué decisión y partida presupuestaria financiarían el trabajo, quién aprueba la compra y qué evidencia necesitan antes de pagar.
4. Medir margen bruto incluyendo geólogo, GIS, soporte, adquisición de fuentes, infraestructura, seguros y ventas.
5. No descontar el piloto a cambio de acceso irrestricto a datos del cliente. Acordar por escrito si se permite usar resultados agregados o anonimizados para mejorar el modelo.

## 6. Diferenciación y ventaja defendible

La fuente de datos pública no basta para crear una barrera. La diferenciación debería acumularse en:

- separación geológica y tratamiento específico de oro primario y placer;
- geometrías y etiquetas depuradas con trazabilidad de origen y fecha;
- validación espacial por distritos y evaluación de recuperación de objetivos frente a área priorizada;
- estabilidad ante distintas muestras de fondo, particiones y fuentes;
- capa de aplicabilidad: indicar dónde el territorio no se parece a los datos usados;
- fichas que explican evidencia y vacíos, con revisión geológica;
- nuevos datos de campo bajo licencia expresa y retroalimentación acumulada;
- actualización de fuentes, detección de cambios y comparación entre versiones;
- facilidad de uso en QGIS y otros flujos de exploración.

La validación debe seguir siendo una demostración de priorización, no una garantía de descubrimiento. Asegurar que el cliente entiende la diferencia entre score relativo, probabilidad calibrada, ley, tonelaje y viabilidad económica.

## 7. Riesgos comerciales, técnicos y regulatorios

### Riesgo de validez y reputación

Si el modelo aprende dónde se han buscado minerales o dónde se concentra el inventario, podría repetir sesgos de exploración en vez de generalizar a zonas nuevas. La documentación interna reconoce positivos y fondo no etiquetado, posibles duplicados, heterogeneidad de etiquetas y la necesidad de validación espacial. Antes de vender un ranking como validado, cerrar esas pruebas, publicar limitaciones y fijar una versión del modelo. En el proyecto actual, los documentos revisados también presentan la validación final y el mapa de entrega como fases por completar; el supuesto de este informe prevalece solo para el análisis de negocio.

### Riesgo de derechos y licencias de datos

Registrar para cada fuente procedencia, licencia, atribución, fecha y derechos de transformación y redistribución. Que un servicio cartográfico sea consultable no significa automáticamente que todas sus capas puedan redistribuirse comercialmente en cualquier formato. El BDMIN es una fuente institucional útil y sus metadatos deben acompañar cualquier uso. Obtener permiso para datos de clientes, resultados de campo y datos comprados antes de incorporarlos a una versión común.

### Riesgo de permisos y medio ambiente

Un mapa de favorabilidad no concede derechos de investigación ni explotación. La Ley de Minas prevé permisos y concesiones para las actividades correspondientes; su tramitación debe comprobarse con la autoridad minera competente y en la comunidad autónoma aplicable. Los proyectos mineros están sujetos al marco de evaluación ambiental, y los proyectos que puedan afectar de forma apreciable a Red Natura 2000 requieren evaluación adecuada conforme al marco aplicable. Un futuro módulo de restricciones debe ser una capa de cribado con fuentes/fecha y revisión humana, no una afirmación de que un terreno es autorizable o está libre. [Ley 22/1973, de Minas](https://www.boe.es/buscar/act.php?id=BOE-A-1973-1018), [Ley 21/2013, de evaluación ambiental](https://boe.es/buscar/act.php?id=BOE-A-2013-12913), [evaluación de afecciones a Red Natura 2000](https://www.miteco.gob.es/ca/biodiversidad/temas/espacios-protegidos/red-natura-2000/rn_cons_evaluacion_afecciones.html)

### Riesgo de propuesta de valor asociada al CRMA

El Reglamento europeo de materias primas fundamentales (CRMA) promueve seguridad de suministro y enumera materias primas estratégicas y fundamentales. El oro no figura en las listas de los anexos I y II del Reglamento 2024/1252. Por tanto, no se debe vender el proyecto aurífero como beneficiario directo de la etiqueta CRMA o de sus objetivos de proyectos estratégicos. Puede haber valor geológico o industrial en otros metales asociados, pero necesitaría un producto multimetal y evidencia propia. [Reglamento (UE) 2024/1252, texto en español](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=OJ%3AL_202401252)

### Riesgo de conflicto de interés

Vender análisis a un cliente y tener derechos económicos sobre un objetivo que afecta a su decisión crea un conflicto. Crear política de revelación, separación de equipos/vehículos, registro de áreas bajo opción y revisión independiente. Para los primeros años, mantener ingresos principales en licencias y servicios reduce ese conflicto.

## 8. Plan comercial de 12 meses

### Meses 0–2: empaquetado y evidencia

- Definir una versión del mapa y su fecha de corte.
- Preparar un ejemplo de ficha de objetivo y un área demostrativa no sensible.
- Escribir un resumen técnico breve de validación, incertidumbre, limitaciones y aplicabilidad.
- Revisar derechos de fuentes, marcas, código y resultados de terceros.
- Construir una lista de 20 cuentas objetivo y realizar entrevistas de problema sin presentar cifras de mercado no verificadas.

### Meses 2–5: pilotos pagados

- Vender entre 3 y 5 estudios acotados, idealmente a perfiles diferentes.
- Acordar con el cliente una pregunta y una medida de éxito antes de analizar el área.
- Recoger feedback sobre formato, confianza, facilidad GIS, uso en presupuesto y disposición a renovar.
- Si hay datos nuevos del cliente, firmar autorización y reglas de confidencialidad antes de recibirlos.

### Meses 5–8: recurrencia y canal

- Convertir pilotos adecuados en licencias anuales o evaluaciones periódicas de cartera.
- Cerrar al menos una alianza no exclusiva con consultora o plataforma GIS/minera.
- Automatizar versionado, entrega de mapas, trazabilidad y fichas repetibles.
- Definir una oferta de refinamiento de campo con socios y precios separados.

### Meses 8–12: producto escalable

- Decidir, en función de renovaciones, si lanzar portal privado/API.
- Publicar política de versiones y tiempos de actualización.
- Analizar la posibilidad de extender a otros metales solo tras confirmar que el pipeline y las etiquetas son adecuados para cada sistema mineral.
- Mantener los objetivos con potencial de derechos mineros en una cartera aparte y someterlos a una revisión de conflicto de interés.

### Métricas de negocio

- Conversión de entrevista a piloto pagado y de piloto a licencia anual.
- Ingreso recurrente y renovación anual.
- Margen bruto por tipo de oferta y días de especialista por entrega.
- Tiempo desde primer contacto a contrato y coste de adquisición del cliente.
- Porcentaje de entregas que producen una decisión documentada del cliente.
- Uso real: descargas, consultas, reuniones de revisión y solicitudes de actualización.
- Para medir valor geológico: protocolos acordados de antemano, área examinada, resultados de campo y resultados no concluyentes, sin atribuir causalidad por un solo caso.

## 9. Recomendación final

Construir un negocio **B2B de inteligencia geológica de exploración**, no una simple tienda de mapas. Empezar con estudios de área pagados que conviertan el score en una decisión documentada, cobrar por alcance y revisión experta, y usar esos proyectos para validar el formato de una licencia anual. Mantener una vía de consultoras como canal y reservar API/SaaS para cuando la entrega se repita con poca personalización.

La mejor combinación inicial es:

1. **Ingreso hoy:** estudios de área y ranking de cartera.
2. **Recurrencia:** licencia empresarial anual con soporte y actualización.
3. **Aumento de valor y aprendizaje:** validación/refinamiento de campo con socios, bajo contrato claro sobre los datos.
4. **Escala posterior:** API/OEM o portal privado.

El activo debe describirse como herramienta de cribado y priorización. La confianza comercial vendrá de mostrar dónde funciona, dónde no hay datos suficientes, qué controles lo explican y cómo una nueva campaña puede comprobar un objetivo. Hasta que esas condiciones estén medidas y documentadas, vendería el análisis como apoyo geológico con revisión humana, sin prometer hallazgos ni rentabilidad.

## 10. Fuentes y documentos internos consultados

### Fuentes externas

- IGME, [Base de Datos de Recursos Minerales BDMIN](https://info.igme.es/catalogo/Resource.aspx?catalog=1&dlang=eng&lang=spa&master=datosgobes&resource=23).
- IGME, [servicio cartográfico BDMIN de indicios](https://mapas.igme.es/gis/rest/services/BasesDatos/IGME_BDMIN_Indicios/MapServer/1).
- BOE, [Ley 22/1973, de Minas](https://www.boe.es/buscar/act.php?id=BOE-A-1973-1018).
- BOE, [Ley 21/2013, de evaluación ambiental](https://boe.es/buscar/act.php?id=BOE-A-2013-12913).
- MITECO, [evaluación de afecciones a Red Natura 2000](https://www.miteco.gob.es/ca/biodiversidad/temas/espacios-protegidos/red-natura-2000/rn_cons_evaluacion_afecciones.html).
- Unión Europea, [Reglamento (UE) 2024/1252 sobre materias primas fundamentales](https://eur-lex.europa.eu/legal-content/ES/TXT/?uri=OJ%3AL_202401252).
- Pan Global Resources, [resumen de proyectos en España](https://www.panglobalresources.com/projects-overview).
- Ormonde Mining, [anuncio de renovación de permisos en España, 2025](https://www.investegate.co.uk/announcement/rns/shearwater-group--swg/update-re-spanish-gold-licences/8728275).

### Documentos internos

- `informes/auditoria_2026-09-05/Informe_Modelo_Prospectividad_Aurifera_BDMIN.txt`.
- `informes/PLAN_PROSPECTIVIDAD_AURIFERA_ESPANA.md`.
- `informes/auditoria_2026-09-05/Ideas_reunion_proyecto_oro_7_septiembre_2026-1 (1).txt`.

Las recomendaciones comerciales, la secuencia de lanzamiento y las estructuras de cobro son hipótesis de diseño para validar con compradores; no representan precios de mercado observados ni asesoramiento jurídico o de permisos.
