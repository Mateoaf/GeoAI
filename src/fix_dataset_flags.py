"""
Actualiza las columnas de flags de commodities (Au, Cu, Ag, Pb) en ml_dataset_real_v2.csv
utilizando la tabla enriquecida oficial OxREP_Hispania_Enriched.csv.
"""
import os
import sys
from pathlib import Path
import pandas as pd
import geopandas as gpd
from shapely.geometry import Point

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

PROJECT_ROOT = Path(__file__).resolve().parent.parent
PROCESSED_DIR = PROJECT_ROOT / "data" / "processed"

mines_csv = PROCESSED_DIR / "OxREP_Hispania_Enriched.csv"
df_mines = pd.read_csv(mines_csv)

csv_v2 = PROCESSED_DIR / "ml_dataset_real_v2.csv"
df_v2 = pd.read_csv(csv_v2)

print(f"📊 Total en dataset v2: {len(df_v2)} (Positivos: {sum(df_v2['target_class']==1)}, Background: {sum(df_v2['target_class']==0)})")

def parse_flag(val):
    if pd.isna(val):
        return 0
    s = str(val).strip().lower()
    return 1 if (s in ['1', '1.0', 'true', 'confirmado', 'hipotetico'] or 'confirmado' in s or 'hipotetico' in s) else 0

# Mapear flags de las primeras 993 filas
for i in range(min(len(df_mines), 993)):
    row_m = df_mines.iloc[i]
    df_v2.at[i, 'flag_Au'] = parse_flag(row_m.get('Flag_Au_Oro', row_m.get('metalMinedGold', 0)))
    df_v2.at[i, 'flag_Cu'] = parse_flag(row_m.get('Flag_Cu_Cobre', row_m.get('metalMinedCopper', 0)))
    df_v2.at[i, 'flag_Ag'] = parse_flag(row_m.get('Flag_Ag_Plata', row_m.get('metalMinedSilver', 0)))
    df_v2.at[i, 'flag_Pb'] = parse_flag(row_m.get('Flag_Pb_Plomo', row_m.get('metalMinedLead', 0)))

# Backgrounds tienen 0 en todos los flags
df_v2.loc[df_v2['target_class'] == 0, ['flag_Au', 'flag_Cu', 'flag_Ag', 'flag_Pb']] = 0

print("\n📈 Conteo de positivos por commodity:")
print(f"   • Oro (Au):   {int(df_v2['flag_Au'].sum()):,} yacimientos positivos")
print(f"   • Cobre (Cu): {int(df_v2['flag_Cu'].sum()):,} yacimientos positivos")
print(f"   • Plata (Ag): {int(df_v2['flag_Ag'].sum()):,} yacimientos positivos")
print(f"   • Plomo (Pb): {int(df_v2['flag_Pb'].sum()):,} yacimientos positivos")

# Guardar CSV y GPKG
df_v2.to_csv(csv_v2, index=False, encoding='utf-8-sig')

gdf_v2 = gpd.GeoDataFrame(
    df_v2,
    geometry=[Point(xy) for xy in zip(df_v2['Coord_X'], df_v2['Coord_Y'])],
    crs="EPSG:25830"
)
gpkg_v2 = PROCESSED_DIR / "ml_dataset_real_v2.gpkg"
gdf_v2.to_file(gpkg_v2, layer="ml_dataset_real_v2", driver="GPKG")

print(f"\n✅ Dataset v2 actualizado en {csv_v2} y {gpkg_v2}")
