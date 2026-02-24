import streamlit as st
import pandas as pd
import io

# Configuración de la interfaz
st.set_page_config(page_title="Conciliador Bancario", layout="wide")

st.title("🏦 Sistema de Conciliación - Caja de Crédito")
st.markdown("""
Esta herramienta cruza los datos de **Empresa** y **Banco** usando la lógica de llaves invertidas:
- **Empresa:** Cargo → `NA+Monto` | Abono → `NC+Monto`
- **Banco:** Cargo → `NC+Monto` | Abono → `NA+Monto`
""")

# 1. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1:
    file_e = st.file_uploader("📂 Archivo EMPRESA (xlsx)", type=["xlsx"])
with col2:
    file_b = st.file_uploader("📂 Archivo BANCO (xlsx)", type=["xlsx"])

if file_e and file_b:
    if st.button("🚀 EJECUTAR CONCILIACIÓN"):
        try:
            # Leer archivos (Empresa fila 7, Banco fila 5)
            df_e = pd.read_excel(file_e, skiprows=6)
            df_b = pd.read_excel(file_b, skiprows=4)

            # LIMPIEZA CRÍTICA: Quitar saltos de línea (\n) de los nombres de columnas
            df_e.columns = df_e.columns.str.replace('\n', ' ').str.replace('  ', ' ').str.strip()
            df_b.columns = df_b.columns.str.replace('\n', ' ').str.replace('  ', ' ').str.strip()

            # Función para limpiar montos (por si vienen como texto con comas)
            def clean_val(val):
                if pd.isna(val) or val == "": return 0.0
                if isinstance(val, (int, float)): return float(val)
                return float(str(val).replace(',', '').strip())

            # --- CREACIÓN DE LLAVES ---
            def crear_llave_e(row):
                # Empresa: Cargo -> NA | Abono -> NC
                c = clean_val(row.get('VALOR CARGOS', 0))
                a = clean_val(row.get('VALOR ABONOS', 0))
                if a > 0: return f"NC{round(a, 2)}"
                if c > 0: return f"NA{round(c, 2)}"
                return "SKIP"

            def crear_llave_b(row):
                # Banco: Cargo -> NC | Abono -> NA
                c = clean_val(row.get('Cargo (US$)', 0))
                a = clean_val(row.get('Abono (US$)', 0))
                if c > 0: return f"NC{round(c, 2)}"
                if a > 0: return f"NA{round(a, 2)}"
                return "SKIP"

            df_e['LLAVE'] = df_e.apply(crear_llave_e, axis=1)
            df_b['LLAVE'] = df_b.apply(crear_llave_b, axis=1)

            # --- FILTRADO (SOLO PENDIENTES) ---
            # Dejamos fuera los que SI tienen pareja
            solo_en_empresa = df_e[~df_e['LLAVE'].isin(df_b['LLAVE']) & (df_e['LLAVE'] != "SKIP")]
            solo_en_banco = df_b[~df_b['LLAVE'].isin(df_e['LLAVE']) & (df_b['LLAVE'] != "SKIP")]

            # --- PREPARAR EXCEL DE DESCARGA ---
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                # Mantenemos todas las columnas originales pero sin la columna auxiliar LLAVE
                solo_en_empresa.drop(columns=['LLAVE']).to_excel(writer, sheet_name='PENDIENTES_EMPRESA', index=False)
                solo_en_banco.drop(columns=['LLAVE']).to_excel(writer, sheet_name='PENDIENTES_BANCO', index=False)
            
            st.success(f"✅ Proceso terminado. Se encontraron {len(solo_en_empresa)} pendientes en empresa y {len(solo_en_banco)} en banco.")

            st.download_button(
                label="📥 DESCARGAR REPORTE DE PENDIENTES",
                data=output.getvalue(),
                file_name="Pendientes_Conciliacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Error al procesar: {e}")
            st.info("Asegúrate de que los archivos tienen el formato correcto.")
