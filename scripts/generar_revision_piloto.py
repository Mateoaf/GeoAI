#!/usr/bin/env python3
"""Generador auditado del lote piloto de revisión geológica formal de indicios de oro (Paso 3A).

Audita los 72 registros y 9 depósitos iniciales:
- Verifica la presencia real de Au documentalmente contrastada.
- Valida la geometría o segrega discrepancias espaciales a estado pendiente.
- Asigna la tipología defendible (roca vs aluvial).
- Segrega depósitos distintos evitando agrupaciones espurias por mera proximidad regional:
    * Mina Santa Josefa (filoniana baja sulfuración) separada de Cerro del Cinto (alta sulfuración).
    * Terrazas del río Cabrera separadas del abanico mioceno de Las Médulas de Carucedo.
    * Corcoesto Hoja 43 (discrepancia 4.5 km W) pasado a pendiente.
    * Labores periféricas o no contrastadas de El Valle-Boinás, Rodalquilar y Cabrera pasadas a pendiente.
- Incorpora referencias bibliográficas resolubles (DOI, URL de memorias MAGNA 50 del IGME, informes técnicos).
"""
from pathlib import Path
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]

def build_audited_pilot_reviews():
    plantillas = sorted(ROOT.glob('reports/fase_b/*/plantilla_revision.csv'))
    if not plantillas:
        raise FileNotFoundError("No se encontró ninguna plantilla_revision.csv en reports/fase_b/")
    plantilla_path = plantillas[-1]
    print(f"Cargando plantilla base: {plantilla_path}")
    
    df = pd.read_csv(plantilla_path, dtype='string', keep_default_na=False, encoding='utf-8-sig')
    print(f"Total registros en plantilla: {len(df)}")
    
    review_cols = [
        'estado_presencia', 'estado_geometria', 'tipo_au_revisado',
        'deposit_id', 'district_id', 'lon_corregida', 'lat_corregida',
        'precision_m', 'revisor', 'fecha_revision', 'evidencia', 'motivo'
    ]
    for col in review_cols:
        if col not in df.columns:
            df[col] = ''
        else:
            df[col] = df[col].fillna('')

    audit_specs = [
        # =========================================================================
        # 1. SALAVE (Tapia de Casariego, Asturias) - 2 confirmados
        # =========================================================================
        {
            'indices': [5, 6],
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_salave',
            'district_id': 'dist_occidente_asturiano',
            'precision_m': '25',
            'evidencia': 'Harris, M. (1980) Trans. Inst. Min. Metall. B89:B181-B188; Martín-Izard et al. (2000) J. Geochem. Explor. 71:89-101 (DOI:10.1016/S0375-6742(00)00146-2); IGME MAGNA 50 Hoja 10 (Tapia de Casariego) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0010.pdf',
            'motivo': 'Yacimiento hidrotermal intragranítico mayor en granodiorita varisca; corta romana de Llagos de Salave y filón Dos Amigos contrastados con sondeos modernos'
        },

        # =========================================================================
        # 2. CARLÉS (Salas / Belmonte, Asturias) - 4 confirmados
        # =========================================================================
        {
            'indices': [66, 67, 68, 69],
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_carles',
            'district_id': 'dist_cinturon_narcea',
            'precision_m': '25',
            'evidencia': 'Cepedal, A. et al. (2000) J. Geochem. Explor. 71(2):273-289 (DOI:10.1016/S0375-6742(00)00156-5); IGME MAGNA 50 Hoja 27 (Tineo/Salas) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0027.pdf',
            'motivo': 'Yacimiento de Au-Cu tipo skarn proximal en la aureola de la granodiorita de Carlés; labores Norte (Carlés), Este (Bandanaso), Sur (Mina del Cura) y Mouro unificadas en el mismo cuerpo intrusivo'
        },

        # =========================================================================
        # 3. EL VALLE - BOINÁS (Belmonte de Miranda, Asturias) - 4 confirmados, 2 pendientes
        # =========================================================================
        {
            'indices': [97, 98, 99, 102], # Boinás, Peniellas, El Valle-Lacanal, Begega
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_el_valle_boinas',
            'district_id': 'dist_cinturon_narcea',
            'precision_m': '25',
            'evidencia': 'Martín-Izard et al. (2000) J. Geochem. Explor. 71:173-190 (DOI:10.1016/S0375-6742(00)00150-4); Cepedal et al. (2008) Miner. Deposita 43:555-573 (DOI:10.1007/s00126-008-0182-3); IGME MAGNA 50 Hoja 51 (Belmonte) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0051.pdf',
            'motivo': 'Complejo minero industrial activo El Valle-Boinás-Begega (Orvana/Río Narcea); mineralización orogénica de skarn y jasperoides auríferos en carbonatos cámbricos'
        },
        {
            'indices': [100], # Cod 0051017: BELMONTE
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_el_valle_boinas',
            'district_id': 'dist_cinturon_narcea',
            'precision_m': '100',
            'evidencia': 'IGME MAGNA 50 Hoja 51 (Belmonte de Miranda) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0051.pdf',
            'motivo': 'Registro genérico próximo al casco de Belmonte de Miranda con morfología desconocida; no se confirma laboreo directo sin documentación de sondeos u obras mineras'
        },
        {
            'indices': [101], # Cod 0051019: COLLADO DAS ESTACAS
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'desconocido',
            'deposit_id': '',
            'district_id': 'dist_cinturon_narcea',
            'precision_m': '',
            'evidencia': 'IGME BDMIN inventario indicios Hoja 51; IGME MAGNA 50 Hoja 51 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0051.pdf',
            'motivo': 'Situado a 2 km al este de la huella minera en morfología desconocida; segregado de dep_el_valle_boinas para evitar agrupación espuria por proximidad'
        },

        # =========================================================================
        # 4. RODALQUILAR (Níjar, Almería) - 6 Cinto conf., 1 Santa Josefa conf., 2 pendientes
        # =========================================================================
        {
            'indices': [780, 781, 782, 783, 784, 785], # Canteras Cinto, SE1, SE2, E, Madrigueras
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_rodalquilar_cinto',
            'district_id': 'dist_cabo_de_gata',
            'precision_m': '25',
            'evidencia': 'Arribas et al. (1995) Econ. Geol. 90:795-822 (DOI:10.2113/gsecongeo.90.4.795); Hernández et al. (1989) Bol. Geol. Min. 100:755-776; IGME MAGNA 50 Hoja 1046 (Carboneras/Rodalquilar) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna1046.pdf',
            'motivo': 'Yacimiento epitermal de alta sulfuración en caldera volcánica neógena de Rodalquilar; pipas de brecha hidrotermal y canteras de cuarzo oquerosa (vuggy silica) en el Cerro del Cinto y Madrigueras'
        },
        {
            'indices': [778], # Cod 1046018: MINA SANTA JOSEFA
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_rodalquilar_santa_josefa',
            'district_id': 'dist_cabo_de_gata',
            'precision_m': '25',
            'evidencia': 'Arribas et al. (1995) Econ. Geol. 90:795-822 (DOI:10.2113/gsecongeo.90.4.795); IGME MAGNA 50 Hoja 1046 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna1046.pdf',
            'motivo': 'Yacimiento filoniano histórico independiente en el Barranco del Cestillar (descubierto en 1883); filones de cuarzo-oro de sulfuración intermedia segregados del cuerpo diseminado de Cerro del Cinto'
        },
        {
            'indices': [779], # Cod 1046022: LABORES MERIDIONALES DE RODALQUILAR
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_rodalquilar_cinto',
            'district_id': 'dist_cabo_de_gata',
            'precision_m': '100',
            'evidencia': 'Hernández et al. (1989) Bol. Geol. Min. 100:755-776; IGME Hoja 1046 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna1046.pdf',
            'motivo': 'Labores periféricas sur a 1.3 km del Cinto; pendiente de asignación precisa entre filón 340 y Consulta'
        },
        {
            'indices': [786], # Cod 1046047: POZOS DE LA MOLATA
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'desconocido',
            'deposit_id': '',
            'district_id': 'dist_cabo_de_gata',
            'precision_m': '',
            'evidencia': 'IGME BDMIN Hoja 1046; IGME MAGNA 50 Hoja 1046 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna1046.pdf',
            'motivo': 'Estructura volcánica costera de La Molata situada a 3.8 km al este de Rodalquilar; segregada de Cerro del Cinto por discontinuidad estructural y falta de laboreo aurífero probado'
        },

        # =========================================================================
        # 5. PINO DEL ORO (Pino, Zamora) - 23 confirmados
        # =========================================================================
        {
            'indices': [586, 587, 588] + list(range(590, 610)),
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_pino_del_oro',
            'district_id': 'dist_zamora_duero',
            'precision_m': '50',
            'evidencia': 'Currás, B.X. & Sánchez-Palencia, F.J. (2008) Arqueología en Castilla y León 18:1-185; Sánchez-García, T. et al. (2008) Geotemas 10:1515-1518; IGME MAGNA 50 Hoja 368 (Carbajales de Alba) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0368.pdf',
            'motivo': 'Enjambre filoniano de cuarzo aurífero y cortas romanas a cielo abierto (El Facho, Ladrón, Gibrero y trincheras numeradas) en el batolito granodiorítico de Pino del Oro; sistema mineral continuo delimitado por CSIC/Junta de CyL'
        },

        # =========================================================================
        # 6. LA CODOSERA (La Codosera, Badajoz) - 16 confirmados (15 roca, 1 aluvial)
        # =========================================================================
        {
            'indices': [i for i in list(range(695, 710)) + [715] if i != 702],
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_la_codosera',
            'district_id': 'dist_la_codosera',
            'precision_m': '50',
            'evidencia': 'IGME (1988) Informe Investigación de oro en el Cerro de los Algarbes y el Chirriato, La Codosera, 42 pp https://info.igme.es/sid/; Gumiel, P. & Arribas, A. (1987) Geol. Rundsch. 76:305-325; IGME MAGNA 50 Hoja 726 (Pino de Valencia) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0726.pdf',
            'motivo': 'Cinturón orogénico de cizalla Varisco en cuarcitas armoricanas y pizarras del Sinclinal de La Codosera; filones de cuarzo y saddle-reefs de Monteviejo (Bandas N, S, W), La Breña, La Perla de Aníbal, Matasiete y La Centena'
        },
        {
            'indices': [702], # Cod 0726012: Barrancones (Labor Romana Aluvial)
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_la_codosera',
            'district_id': 'dist_la_codosera',
            'precision_m': '50',
            'evidencia': 'IGME (1988) Investigación de oro en Cerro de los Algarbes y Chirriato, La Codosera https://info.igme.es/sid/; IGME MAGNA 50 Hoja 726 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0726.pdf',
            'motivo': 'Labor romana aluvial/eluvial encajada directamente en la vaguada que drena la banda mineralizada de Monteviejo; mineralización aluvial genéticamente co-espacial al yacimiento primario de La Codosera'
        },

        # =========================================================================
        # 7. CORCOESTO (Cabana de Bergantiños, A Coruña) - 1 confirmado, 1 pendiente
        # =========================================================================
        {
            'indices': [73], # Cod 0044002: CORCOESTO (Hoja 44, Carballo)
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_corcoesto',
            'district_id': 'dist_galicia_costa_da_morte',
            'precision_m': '25',
            'evidencia': 'Castroviejo, R. (1990) Chron. Rech. Min. 500:25-46; IGME MAGNA 50 Hoja 44 (Carballo) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0044.pdf',
            'motivo': 'Yacimiento filoniano orogénico de oro y arsenopirita en la Cizalla Malpica-Tui; labores mineras históricas y sondeos en Pozo Petaca, Monte Cotiño y Mina Emilita'
        },
        {
            'indices': [72], # Cod 0043009: Corcoesto (Hoja 43, Lage)
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'roca',
            'deposit_id': 'dep_corcoesto',
            'district_id': 'dist_galicia_costa_da_morte',
            'precision_m': '',
            'evidencia': 'IGME BDMIN Hoja 43; IGME MAGNA 50 Hoja 43 (Lage) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0043.pdf',
            'motivo': 'Discrepancia geométrica de 4.5 km al oeste respecto al yacimiento real de Corcoesto (Hoja 44); probable artefacto de digitalización en límite de hoja cartográfica. Se mantiene pendiente hasta verificar el expediente'
        },

        # =========================================================================
        # 8. TELENO (Truchas / Lucillo, León) - 3 confirmados
        # =========================================================================
        {
            'indices': [431, 433, 451], # Cod 0192001, 0192003, 0192027
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_teleno',
            'district_id': 'dist_leon_maragateria',
            'precision_m': '100',
            'evidencia': 'Pérez García, L.C., Sánchez-Palencia, F.J. & Torres Ruiz, J. (2000) J. Geochem. Explor. 71(2):225-240 (DOI:10.1016/S0375-6742(00)00153-X); Sánchez-Palencia, F.J. (2000) Las Médulas (León): un paisaje cultural en la "Asturia Augustana", CSIC; IGME MAGNA 50 Hoja 192 (Lucillo) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0192.pdf',
            'motivo': 'Complejo de minería hidráulica romana de montaña en las laderas y crestas del Macizo del Teleno; depósitos morrénicos y derrubios de vertiente auríferos retrabajados'
        },

        # =========================================================================
        # 9. LAS MÉDULAS Y TERRAZAS DEL CABRERA (León) - 5 confirmados (2 Médulas, 3 Cabrera), 2 pendientes
        # =========================================================================
        {
            'indices': [408, 414], # Cod 0191006 (LAS MEDULAS), Cod 0191017 (CARUCEDO)
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_las_medulas_carucedo',
            'district_id': 'dist_leon_bierzo',
            'precision_m': '50',
            'evidencia': 'Sánchez-Palencia, F.J. et al. (2000) Las Médulas (León): un paisaje cultural en la "Asturia Augustana", CSIC, 280 pp; Pérez García et al. (2000) J. Geochem. Explor. 71:225-240 (DOI:10.1016/S0375-6742(00)00153-X); IGME MAGNA 50 Hoja 191 (Ponferrada) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0191.pdf',
            'motivo': 'Mayor explotación aurífera a cielo abierto de la Hispania romana (Patrimonio de la Humanidad UNESCO); abanicos aluviales miocenos de la Formación Las Médulas/Santalla explotados mediante ruina montium'
        },
        {
            'indices': [412, 416, 417], # Cod 0191011 (RIO CABRERA), 0191019 (LOS CABORCOS), 0191020 (EL BOQUEIRON)
            'estado_presencia': 'confirmada',
            'estado_geometria': 'validada',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_rio_cabrera_terrazas',
            'district_id': 'dist_leon_cabrera',
            'precision_m': '100',
            'evidencia': 'Sánchez-Palencia, F.J. et al. (2000) Las Médulas (León), CSIC; Pérez García et al. (2000) J. Geochem. Explor. 71:225-240; IGME MAGNA 50 Hoja 191 (Ponferrada) https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0191.pdf',
            'motivo': 'Placeres fluviales cuaternarios y terrazas del curso bajo del río Cabrera en Puente de Domingo Flórez; segregados del abanico mioceno de Las Médulas por constituir un sistema sedimentario fluvial independiente'
        },
        {
            'indices': [413], # Cod 0191015: EL BURACO-BARREIRIN
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_rio_cabrera_terrazas',
            'district_id': 'dist_leon_cabrera',
            'precision_m': '100',
            'evidencia': 'IGME LIG CI002 Sucesión Ordovícico-Silúrico en Salas de la Ribera; Sánchez-Palencia et al. (2000) Canales romanos de Las Médulas https://info.igme.es/sid/',
            'motivo': 'Corresponde al túnel de conducción de agua del canal romano ("Buraco de Valellos") y a un paraje estratigráfico/paleontológico (Barreirín), no a un frente de arranque contrastado de mineral de oro'
        },
        {
            'indices': [415], # Cod 0191018: AÍBALEN-RIO SIL
            'estado_presencia': 'pendiente',
            'estado_geometria': 'pendiente',
            'tipo_au_revisado': 'aluvial',
            'deposit_id': 'dep_las_medulas_carucedo',
            'district_id': 'dist_leon_bierzo',
            'precision_m': '100',
            'evidencia': 'IGME BDMIN Hoja 191; IGME MAGNA 50 Hoja 191 https://info.igme.es/cartografiadigital/datos/magna50/memorias/MMagna0191.pdf',
            'motivo': 'Topónimo no contrastado en fuentes arqueológicas ni geológicas sobre la cuenca del Sil en Carucedo; mantenido en estado pendiente de verificación documental'
        },
    ]

    total_confirmed = 0
    total_pending = 0

    for spec in audit_specs:
        idxs = spec['indices']
        is_conf = spec['estado_presencia'] == 'confirmada'
        if is_conf:
            total_confirmed += len(idxs)
        else:
            total_pending += len(idxs)

        for idx in idxs:
            df.at[idx, 'estado_presencia'] = spec['estado_presencia']
            df.at[idx, 'estado_geometria'] = spec['estado_geometria']
            df.at[idx, 'tipo_au_revisado'] = spec['tipo_au_revisado']
            df.at[idx, 'deposit_id'] = spec['deposit_id']
            df.at[idx, 'district_id'] = spec['district_id']
            df.at[idx, 'precision_m'] = spec['precision_m']
            df.at[idx, 'revisor'] = 'auditoria_geologica_u3'
            df.at[idx, 'fecha_revision'] = '2026-09-27'
            df.at[idx, 'evidencia'] = spec['evidencia']
            df.at[idx, 'motivo'] = spec['motivo']
            df.at[idx, 'lon_corregida'] = ''
            df.at[idx, 'lat_corregida'] = ''

    out_dir = ROOT / 'data' / 'review'
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / 'revision_au_fase_b.csv'
    df.to_csv(out_path, index=False, encoding='utf-8-sig')
    print(f"Guardado exitoso en {out_path}")
    print(f"Balance auditoría: {total_confirmed} confirmados, {total_pending} pendientes, 0 rechazados.")
    print(f"Total registros auditados en el lote piloto: {total_confirmed + total_pending}")

if __name__ == '__main__':
    build_audited_pilot_reviews()
