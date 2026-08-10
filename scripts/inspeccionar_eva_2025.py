"""Inspecciona el archivo EVA 2019-2025 para verificar compatibilidad."""
from pathlib import Path
import pandas as pd


def main():
    path = Path("data/external/eva_2019_2025_valle_del_cauca.xlsx")
    
    if not path.exists():
        print(f"[ERROR] Archivo no encontrado: {path}")
        print("Cópialo primero con:")
        print('  copy "C:\\Users\\Usuario\\Downloads\\20260526_BaseAgricola20192025.xlsx" "data\\external\\eva_2019_2025_valle_del_cauca.xlsx"')
        return
    
    print(f"Archivo: {path}")
    print(f"Tamaño: {path.stat().st_size / 1024 / 1024:.1f} MB")
    print()
    
    # Leer archivo
    print("Leyendo archivo...")
    df = pd.read_excel(path)
    
    print(f"\n{'='*60}")
    print(f"INSPECCIÓN DEL ARCHIVO")
    print(f"{'='*60}")
    print(f"Filas: {len(df):,}")
    print(f"Columnas: {len(df.columns)}")
    
    print(f"\n{'='*60}")
    print(f"COLUMNAS DISPONIBLES")
    print(f"{'='*60}")
    for i, col in enumerate(df.columns, 1):
        print(f"{i:2d}. {col}")
    
    print(f"\n{'='*60}")
    print(f"ANÁLISIS DE AÑOS")
    print(f"{'='*60}")
    # Buscar columna de año
    anio_cols = [c for c in df.columns if 'año' in c.lower() or 'anio' in c.lower() or 'year' in c.lower()]
    if anio_cols:
        anio_col = anio_cols[0]
        print(f"Columna de año: {anio_col}")
        print(f"Rango de años: {df[anio_col].min()} - {df[anio_col].max()}")
        print(f"Años únicos: {sorted(df[anio_col].unique())}")
    else:
        print("[AVISO] No se encontró columna de año")
    
    print(f"\n{'='*60}")
    print(f"ANÁLISIS DE DEPARTAMENTOS")
    print(f"{'='*60}")
    dpto_cols = [c for c in df.columns if 'departamento' in c.lower() or 'dpto' in c.lower()]
    if dpto_cols:
        dpto_col = dpto_cols[0]
        print(f"Columna de departamento: {dpto_col}")
        departamentos = df[dpto_col].unique()
        print(f"Departamentos: {len(departamentos)}")
        if 'VALLE DEL CAUCA' in [str(d).upper() for d in departamentos]:
            print("✓ Contiene Valle del Cauca")
        else:
            print("✗ NO contiene Valle del Cauca")
        print(f"\nPrimeros 10 departamentos:")
        for d in sorted(departamentos)[:10]:
            print(f"  - {d}")
    else:
        print("[AVISO] No se encontró columna de departamento")
    
    print(f"\n{'='*60}")
    print(f"ANÁLISIS DE MUNICIPIOS")
    print(f"{'='*60}")
    mun_cols = [c for c in df.columns if 'municipio' in c.lower()]
    if mun_cols:
        mun_col = mun_cols[0]
        print(f"Columna de municipio: {mun_col}")
        municipios = df[mun_col].unique()
        print(f"Municipios únicos: {len(municipios)}")
        
        # Filtrar Valle del Cauca si existe
        if dpto_cols:
            df_valle = df[df[dpto_col].str.upper().str.contains('VALLE', na=False)]
            mun_valle = df_valle[mun_col].unique()
            print(f"Municipios en Valle del Cauca: {len(mun_valle)}")
            print(f"\nPrimeros 10 municipios del Valle:")
            for m in sorted(mun_valle)[:10]:
                print(f"  - {m}")
    else:
        print("[AVISO] No se encontró columna de municipio")
    
    print(f"\n{'='*60}")
    print(f"MUESTRA DE DATOS (primeras 5 filas)")
    print(f"{'='*60}")
    print(df.head())
    
    print(f"\n{'='*60}")
    print(f"CONCLUSIÓN")
    print(f"{'='*60}")
    print("Si el archivo contiene Valle del Cauca y tiene columnas similares a:")
    print("  - Año/Año")
    print("  - Departamento")
    print("  - Municipio")
    print("  - Cultivo")
    print("  - Producción")
    print("  - Área sembrada/cosechada")
    print("\nEntonces es COMPATIBLE y podemos integrarlo.")


if __name__ == "__main__":
    main()