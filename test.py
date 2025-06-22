import pandas as pd

# Cargar archivos
archivo_consolidado = r"C:\Users\Usuario\OneDrive - FRUTTO FOODS\scriptspython\ssr\data\reportSalesFrutto_2025-06-20.csv"
archivo_tx = r"C:\Users\Usuario\Downloads\sales-by-item-report-Fri, 20 Jun 2025 14_55_46 GMT.csv"
archivo_fl = r"C:\Users\Usuario\Downloads\sales-by-item-report-Fri, 20 Jun 2025 14_55_20 GMT.csv"

# Leer CSVs
df_consolidado = pd.read_csv(archivo_consolidado)
df_tx = pd.read_csv(archivo_tx)
df_fl = pd.read_csv(archivo_fl)

# Limpiar nombres de columnas
df_consolidado.columns = df_consolidado.columns.str.strip()
df_tx.columns = df_tx.columns.str.strip()
df_fl.columns = df_fl.columns.str.strip()

# Unir archivos fuente
df_fuentes = pd.concat([df_tx, df_fl], ignore_index=True)

# Ordenar columnas y registros para comparar bien
df_consolidado_sorted = df_consolidado.sort_values(by=df_consolidado.columns.tolist()).reset_index(drop=True)
df_fuentes_sorted = df_fuentes.sort_values(by=df_fuentes.columns.tolist()).reset_index(drop=True)

# Comprobar si tienen las mismas columnas
if set(df_consolidado.columns) != set(df_fuentes.columns):
    print("⚠️ Las columnas no coinciden entre el consolidado y la unión de fuentes.")
    print("Consolidado tiene:", df_consolidado.columns.tolist())
    print("Fuentes tienen:", df_fuentes.columns.tolist())
else:
    print("✅ Las columnas coinciden.")

# Igualar orden de columnas
df_fuentes_sorted = df_fuentes_sorted[df_consolidado_sorted.columns]

# Comparar dimensión
if len(df_consolidado_sorted) != len(df_fuentes_sorted):
    print(f"❌ Diferente número de registros:")
    print(f"- Consolidado: {len(df_consolidado_sorted)}")
    print(f"- Unión fuentes: {len(df_fuentes_sorted)}")
else:
    print(f"✅ El número de registros coincide: {len(df_consolidado_sorted)}")

# Comparar contenido exacto
diferencias = df_consolidado_sorted.compare(df_fuentes_sorted)

if diferencias.empty:
    print("🎯 Los archivos coinciden perfectamente. La unión es correcta.")
else:
    print("❌ Los archivos no son iguales. Hay diferencias.")
    print(f"Diferencias detectadas: {len(diferencias)} celdas distintas.")
    diferencias.to_csv("diferencias_union.csv")
    print("📝 Se guardó un archivo 'diferencias_union.csv' con los detalles.")
