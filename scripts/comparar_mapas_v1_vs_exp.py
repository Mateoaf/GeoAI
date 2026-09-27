#!/usr/bin/env python3
"""
Genera una figura comparativa de mapas entre v1.0 oficial y el modelo experimental de 787 indicios.
"""
from pathlib import Path
import numpy as np
import matplotlib.pyplot as plt
import rasterio

ROOT = Path(__file__).resolve().parents[1]

def main():
    path_v1 = ROOT / 'reports/fase_h/20260927T142549_961719Z/maps/mapa_nacional_favorabilidad_score.tif'
    path_exp = ROOT / 'reports/experimento_600_indicios/maps/mapa_nacional_favorabilidad_score_rf.tif'
    
    with rasterio.open(path_v1) as src:
        arr_v1 = src.read(1)
        arr_v1 = np.where(arr_v1 != src.nodata, arr_v1, np.nan)
        
    with rasterio.open(path_exp) as src:
        arr_exp = src.read(1)
        arr_exp = np.where(arr_exp != src.nodata, arr_exp, np.nan)
        
    fig, axes = plt.subplots(1, 2, figsize=(16, 7.5))
    
    im1 = axes[0].imshow(arr_v1, cmap='viridis', vmin=0, vmax=1)
    axes[0].set_title('A. Modelo Oficial v1.0 (190 Confirmados / 131 celdas P)\nSpatial ROC-AUC: 0.74 | Folds Externos', fontsize=12, fontweight='bold', pad=10)
    axes[0].axis('off')
    cbar1 = fig.colorbar(im1, ax=axes[0], orientation='horizontal', fraction=0.046, pad=0.04)
    cbar1.set_label('Prospectivity Score (0 a 1)', fontweight='bold')
    
    im2 = axes[1].imshow(arr_exp, cmap='viridis', vmin=0, vmax=1)
    axes[1].set_title('B. Modelo Experimental (787 Indicios / 664 celdas P)\nSpatial ROC-AUC: 0.86 | Random K-Fold ROC-AUC: 0.91', fontsize=12, fontweight='bold', pad=10)
    axes[1].axis('off')
    cbar2 = fig.colorbar(im2, ax=axes[1], orientation='horizontal', fraction=0.046, pad=0.04)
    cbar2.set_label('Prospectivity Score (0 a 1)', fontweight='bold')
    
    plt.suptitle('Comparativa Territorial: Modelo Oficial v1.0 vs Modelo Experimental con ~600 Indicios Adicionales', fontsize=15, fontweight='bold', y=0.98)
    plt.tight_layout()
    
    out_png = ROOT / 'reports/experimento_600_indicios/comparativa_mapa_v1_vs_experimental.png'
    plt.savefig(out_png, dpi=200, bbox_inches='tight')
    plt.close()
    print(f"Figura comparativa guardada en: {out_png.relative_to(ROOT)}")

if __name__ == '__main__':
    main()
