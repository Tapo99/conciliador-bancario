import streamlit as st
import pandas as pd
import io

st.set_page_config(page_title="Conciliador Bancario", layout="wide")

st.title("🏦 Sistema de Conciliación - Nueva Concepción")
st.markdown("Carga tus archivos para identificar movimientos no liquidados.")

col1, col2 = st.columns(2)
with col1:
    file_e = st.file_uploader("📂 Archivo EMPRESA", type=["xlsx"])
with col2:
    file_b = st.file_uploader("📂 Archivo BANCO", type=["xlsx"])

if file_e and file_b:
    if st.button("🚀 EJECUTAR CONCILIACIÓN"):
        try:
            df_e = pd.read_excel(file_e, skiprows=6)
            df_b = pd.read_excel(file_b, skiprows=4)

            # Limpiar nombres de columnas
            df_e.columns = df_e.columns.str.replace('\n', ' ').str.strip()
            df_b.columns = df_b.columns.str.replace('\n', ' ').str.strip()

            def clean_val(val):
                if pd.isna(val) or val == "": return 0.0
                if isinstance(val, (int, float)): return float(val)
                return float(str(val).replace(',', '').strip())

            def crear_llave_e(row):
                c = clean_val(row.get('VALOR CARGOS', 0))
                a = clean_val(row.get('VALOR ABONOS', 0))
                if a > 0: return f"NC{round(a, 2)}"
                if c > 0: return f"NA{round(c, 2)}"
                return "SKIP"

            def crear_llave_b(row):
                c = clean_val(row.get('Cargo (US$)', 0))
                a = clean_val(row.get('Abono (US$)', 0))
                if c > 0: return f"NC{round(c, 2)}"
                if a > 0: return f"NA{round(a, 2)}"
                return "SKIP"

            df_e['LLAVE'] = df_e.apply(crear_llave_e, axis=1)
            df_b['LLAVE'] = df_b.apply(crear_llave_b, axis=1)

            solo_en_empresa = df_e[~df_e['LLAVE'].isin(df_b['LLAVE']) & (df_e['LLAVE'] != "SKIP")]
            solo_en_banco = df_b[~df_b['LLAVE'].isin(df_e['LLAVE']) & (df_b['LLAVE'] != "SKIP")]

            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                solo_en_empresa.drop(columns=['LLAVE']).to_excel(writer, sheet_name='PENDIENTES_EMPRESA', index=False)
                solo_en_banco.drop(columns=['LLAVE']).to_excel(writer, sheet_name='PENDIENTES_BANCO', index=False)
            
            st.success(f"✅ Proceso terminado. Pendientes: Empresa ({len(solo_en_empresa)}) | Banco ({len(solo_en_banco)})")
            st.download_button(label="📥 DESCARGAR REPORTE", data=output.getvalue(), file_name="Pendientes.xlsx")

        except Exception as e:
            st.error(f"Error: {e}")
