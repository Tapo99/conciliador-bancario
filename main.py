import streamlit as st
import pandas as pd
import io

# Configuración visual
st.set_page_config(page_title="Conciliación Caja de Crédito", layout="wide")

st.title("🏦 Conciliador: Nueva Concepción vs Banco")
st.markdown("Busca automáticamente movimientos no liquidados usando la lógica de **Llaves Invertidas**.")

# 1. CARGA DE ARCHIVOS
col1, col2 = st.columns(2)
with col1:
    file_e = st.file_uploader("📂 Subir archivo de la EMPRESA", type=["xlsx"])
with col2:
    file_b = st.file_uploader("📂 Subir archivo del BANCO", type=["xlsx"])

if file_e and file_b:
    if st.button("🚀 CONCILIAR AHORA"):
        try:
            # Leer archivos (Empresa salta 6 filas, Banco salta 4)
            df_e = pd.read_excel(file_e, skiprows=6)
            df_b = pd.read_excel(file_b, skiprows=4)

            # Limpiar nombres de columnas (quita saltos de línea molestos)
            df_e.columns = df_e.columns.str.replace('\n', ' ').str.strip()
            df_b.columns = df_b.columns.str.replace('\n', ' ').str.strip()

            # Función para convertir texto a número limpio
            def limpiar_monto(val):
                if pd.isna(val) or val == "": return 0.0
                if isinstance(val, (int, float)): return float(val)
                return float(str(val).replace(',', '').strip())

            # --- CREACIÓN DE LLAVES INVERTIDAS ---
            def crear_llave_empresa(row):
                # En Empresa: CARGO es NA | ABONO es NC
                c = limpiar_monto(row.get('VALOR CARGOS', 0))
                a = limpiar_monto(row.get('VALOR ABONOS', 0))
                if a > 0: return f"NC{round(a, 2)}"
                if c > 0: return f"NA{round(c, 2)}"
                return "SKIP"

            def crear_llave_banco(row):
                # En Banco: Cargo es NC | Abono es NA
                c = limpiar_monto(row.get('Cargo (US$)', 0))
                a = limpiar_monto(row.get('Abono (US$)', 0))
                if c > 0: return f"NC{round(c, 2)}"
                if a > 0: return f"NA{round(a, 2)}"
                return "SKIP"

            df_e['LLAVE'] = df_e.apply(crear_llave_empresa, axis=1)
            df_b['LLAVE'] = df_b.apply(crear_llave_banco, axis=1)

            # --- FILTRAR SOLO LOS QUE NO TIENEN PAREJA ---
            pendientes_e = df_e[~df_e['LLAVE'].isin(df_b['LLAVE']) & (df_e['LLAVE'] != "SKIP")]
            pendientes_b = df_b[~df_b['LLAVE'].isin(df_e['LLAVE']) & (df_b['LLAVE'] != "SKIP")]

            # --- RESULTADO ---
            st.success(f"✅ ¡Hecho! Quedan {len(pendientes_e)} filas en Empresa y {len(pendientes_b)} en Banco sin liquidar.")

            # Crear el Excel de descarga
            output = io.BytesIO()
            with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
                pendientes_e.drop(columns=['LLAVE']).to_excel(writer, sheet_name='SOLO_EN_EMPRESA', index=False)
                pendientes_b.drop(columns=['LLAVE']).to_excel(writer, sheet_name='SOLO_EN_BANCO', index=False)
            
            st.download_button(
                label="📥 DESCARGAR EXCEL DE PENDIENTES",
                data=output.getvalue(),
                file_name="Pendientes_Conciliacion.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

        except Exception as e:
            st.error(f"Hubo un problema con el formato: {e}")
