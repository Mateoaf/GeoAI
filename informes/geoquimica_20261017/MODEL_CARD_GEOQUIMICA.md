# GeoAI · Model card

Modelo de prospectividad regional con 64 entradas: 56 variables numéricas y ocho clases geoquímicas (As, Sb, Bi, Hg, Cu, Pb, Zn y W). One-hot distingue clases y ausencias; las entradas no son concentraciones analíticas verificadas. Au y los identificadores quedan fuera de los predictores.

Bagging PU obtiene ROC-AUC 0.8866 y Average Precision 0.7119 en predicciones fuera de pliegue. En siete rotaciones territoriales recupera 5 de 45 depósitos al 5 % de celdas y 9 al 10 %.

Se utilizan 753 registros elegibles consolidados en 664 celdas P. Confirmadas tienen peso 1 y pendientes 0,5. Se evalúa mediante cinco pliegues espaciales y siete rotaciones territoriales con bloques de 50 km y buffer de 15 km. Las métricas se refieren a etiquetas P/U conocidas y a esos protocolos.

La cartografía contiene 8 miembros LightGBM de 150 árboles ajustados sobre todo el dominio elegible. Modelos y parámetros: reports/geoquimica_20261017/models/GeoAI/. La evaluación de Bagging PU emplea cinco miembros de 100 árboles; la cartografía posterior al ajuste no constituye un conjunto de evaluación independiente.

Salidas: score relativo P/U, dispersión, novedad y categorías. No se estima probabilidad física de mineralización. La cobertura desigual, especialmente Zn y W, la revisión pendiente de leyendas y el sesgo del inventario condicionan su interpretación. Uso previsto: priorización regional con revisión experta y contraste de campo. Detalles y tablas: informes/geoquimica_20261017/INFORME_RESULTADOS_GEOQUIMICA.md.
