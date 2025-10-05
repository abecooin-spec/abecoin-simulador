# simulador_web.py
# Simulador Web para Abecoin (Streamlit)
# Requisitos: streamlit, pandas, openpyxl
# Ejecutar: streamlit run simulador_web.py

import streamlit as st
import pandas as pd
import math
from datetime import datetime, timedelta
from io import BytesIO

# --------------------------
# CONFIG
# --------------------------
st.set_page_config(page_title="Abecoin - Simulador", page_icon="🐝", layout="wide")

# Ruta del logo (poner el archivo en la misma carpeta)
LOGO_PATH = "abecoin_logo.png"  # <- cambia si tu imagen tiene otro nombre

# Colores institucionales
AZUL = "#062a6f"    # fondo header
AMARILLO = "#FFD166"  # acento amarillo del logo
TEXTO_HEADER = "#FFFFFF"

# --------------------------
# FUNCIONES DE TASAS / DEGRAVAMEN
# --------------------------
def obtener_tasa_semanal(capital, cuotas):
    """
    Retorna la tasa semanal en decimal basada en la tabla que proporcionaste.
    Asume cuotas = número de letras (2,3,4). Si es otro número, toma la opción más cercana.
    """
    # Normalizar cuotas a 2/3/4 si fuera distinto (elige el más cercano entre 2,3,4)
    opciones = [2, 3, 4]
    cuotas_closest = min(opciones, key=lambda x: abs(x - cuotas))
    if 10 < capital <= 200:
        if cuotas_closest == 2: return 0.04   # 4%
        if cuotas_closest == 3: return 0.03   # 3%
        if cuotas_closest == 4: return 0.025  # 2.5%
    elif 200 < capital <= 400:
        if cuotas_closest == 2: return 0.02   # 2%
        if cuotas_closest == 3: return 0.0167 # 1.67%
        if cuotas_closest == 4: return 0.015  # 1.5%
    elif 400 < capital <= 600:
        if cuotas_closest == 2: return 0.025  # 2.5%
        if cuotas_closest == 3: return 0.02   # 2%
        if cuotas_closest == 4: return 0.0175 # 1.75%
    # Default fallback
    return 0.03

def obtener_porcentaje_degravamen(capital):
    """Retorna porcentaje decimal del degravamen según intervalos."""
    if capital <= 200:
        return 0.008   # 0.8%
    elif capital <= 400:
        return 0.01    # 1%
    else:
        return 0.015   # 1.5%

# --------------------------
# LÓGICA DEL CRONOGRAMA
# --------------------------
def generar_cronograma(nombre, dni, direccion, capital, cuotas, degrav_mode="prorated"):
    """
    Genera DataFrame del cronograma:
    degrav_mode: 'prorated' or 'upfront'
    """
    tasa = obtener_tasa_semanal(capital, cuotas)
    amortizacion = round(capital / cuotas, 2)
    interes_semanal = round(capital * tasa, 2)
    interes_total = round(interes_semanal * cuotas, 2)

    # Degravamen total y prorrateo o upfront
    pct_degrav = obtener_porcentaje_degravamen(capital)
    degrav_total = round(capital * pct_degrav, 2)

    if degrav_mode == "prorated":
        # repartir en cuotas y ajustar la última
        base_prorr = math.floor((degrav_total / cuotas) * 100) / 100
        prorrateos = [base_prorr] * cuotas
        diff = round(degrav_total - sum(prorrateos), 2)
        prorrateos[-1] = round(prorrateos[-1] + diff, 2)
    else:  # upfront
        prorrateos = [0.0] * cuotas
        if cuotas >= 1:
            prorrateos[0] = degrav_total

    hoy = datetime.today()
    saldo = capital
    filas = []
for i in range(1, cuotas + 1):
    degrav = prorrateos[i-1]
    cuota_base = round(amortizacion + interes_semanal, 2)
    cuota_final = round(cuota_base + degrav, 2)
    vencimiento = (hoy + timedelta(weeks=i)).strftime("%d/%m/%Y")
    estado = "PENDIENTE"
    filas.append({
        "N° Cuota": i,
        "Fecha Venc.": vencimiento,
        "Saldo Capital": round(saldo, 2),
        "Amortización": amortizacion,
        "Interés": interes_semanal,
        "Cuota Base": cuota_base,
        "Degravamen": degrav,
        "Cuota Final": cuota_final,
        "Estado": estado
    })

    saldo = round(saldo - amortizacion, 2)

df = pd.DataFrame(filas)
resumen = {
        "Nombre": nombre,
        "DNI": dni,
        "Dirección": direccion,
        "Capital Inicial (S/)": capital,
        "Tasa semanal (%)": round(tasa * 100, 3),
        "N° Cuotas": cuotas,
        "Interés Total (S/)": interes_total,
        "Degravamen Total (S/)": degrav_total,
        "Total a Pagar (S/)": round(capital + interes_total + degrav_total, 2)
    }
    return df, resumen

# --------------------------
# UTIL: EXPORTAR A XLSX EN MEMORIA
# --------------------------
def to_excel_bytes(df, resumen, filename="cronograma.xlsx"):
    """Genera un XLSX en memoria y lo devuelve como bytes"""
    output = BytesIO()
    with pd.ExcelWriter(output, engine="openpyxl") as writer:
        # Hoja cronograma
        df.to_excel(writer, index=False, sheet_name="Cronograma")
        # Hoja resumen
        res_df = pd.DataFrame(list(resumen.items()), columns=["Concepto", "Valor"])
        res_df.to_excel(writer, index=False, sheet_name="Resumen")
        writer.close()
    processed_data = output.getvalue()
    return processed_data

# --------------------------
# STYLES: HEADER / LAYOUT
# --------------------------
def header():
    st.markdown(
        f"""
        <style>
        .abecoin-header {{
            background: linear-gradient(90deg, {AZUL}, {AZUL});
            padding: 18px;
            border-radius: 8px;
            color: {TEXTO_HEADER};
            display: flex;
            align-items: center;
            gap: 20px;
        }}
        .abecoin-logo {{
            height: 70px;
            width: auto;
            border-radius: 6px;
        }}
        .abecoin-title {{
            font-size:32px;
            font-weight:700;
            margin:0;
        }}
        .card {{
            background: white;
            padding: 12px;
            border-radius: 8px;
            box-shadow: 0 1px 3px rgba(0,0,0,0.08);
        }}
        </style>
        <div class="abecoin-header">
            <img src="data:image/png;base64,{_get_logo_base64()}" class="abecoin-logo"/>
            <div>
                <p class="abecoin-title">ABECOIN</p>
                <div style="font-size:14px;">Simulador de préstamos — Cooperativa Abecoin</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )

def _get_logo_base64():
    """Intenta leer el logo y devolver base64 para embebido (evita problemas con rutas relativas)."""
    import base64, os
    if os.path.exists(LOGO_PATH):
        with open(LOGO_PATH, "rb") as f:
            data = f.read()
        return base64.b64encode(data).decode("utf-8")
    else:
        # Si no existe logo, devuelve imagen 1x1 transparente (no rompe la interfaz)
        return "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAQAAAC1HAwCAAAAC0lEQVR4nGNgYAAAAAMAASsJTYQAAAAASUVORK5CYII="

# --------------------------
# INTERFAZ PRINCIPAL
# --------------------------
header()

col1, col2 = st.columns([2, 3])

with col1:
    st.markdown("### 📋 Datos del socio", unsafe_allow_html=True)
    with st.form("datos_form"):
        nombre = st.text_input("Nombre completo")
        dni = st.text_input("DNI")
        direccion = st.text_input("Dirección")
        col_a, col_b = st.columns(2)
        with col_a:
            capital = st.number_input("Monto del préstamo (S/)", min_value=10.0, step=10.0, value=200.0)
        with col_b:
            cuotas = st.number_input("N° de cuotas (semanas)", min_value=1, step=1, value=3)
        degrav_mode = st.selectbox("Cómo cobrar Degravamen?", ("prorated", "upfront"),
                                  help="prorated = repartido en cuotas, upfront = todo al inicio (cuota 1)")
        submitted = st.form_submit_button("Calcular Cronograma")

    st.markdown("---")
    st.markdown("#### 🧾 Vista previa")
    if submitted and nombre and dni:
        df_preview, resumen_preview = generar_cronograma(nombre, dni, direccion, capital, int(cuotas), degrav_mode)
        st.metric("Total a pagar (S/)", f"{resumen_preview['Total a Pagar (S/)']}")
        st.write(f"Interés total (S/): {resumen_preview['Interés Total (S/)']}")
        st.write(f"Degravamen total (S/): {resumen_preview['Degravamen Total (S/)']}")
    else:
        st.info("Complete el formulario y presione 'Calcular Cronograma' para ver resultados.")

with col2:
    st.markdown("### 📅 Cronograma")
    if submitted and nombre and dni:
        df, resumen = generar_cronograma(nombre, dni, direccion, capital, int(cuotas), degrav_mode)
        st.dataframe(df, use_container_width=True)

        # Botones de descarga
        csv = df.to_csv(index=False).encode('utf-8')
        st.download_button("⬇ Descargar CSV", data=csv, file_name=f"cronograma_{dni}.csv", mime="text/csv")

        xlsx_bytes = to_excel_bytes(df, resumen, filename=f"cronograma_{dni}.xlsx")
        st.download_button("⬇ Descargar Excel (XLSX)", data=xlsx_bytes, file_name=f"cronograma_{dni}.xlsx", mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

        # Mostrar resumen detallado a la derecha
        st.markdown("####  Resumen detallado")
        for k, v in resumen.items():
            st.write(f"**{k}:** {v}")

        # Gráfico simple del saldo
        st.markdown("#### 📈 Evolución del saldo")
        chart_df = df[["N° Cuota", "Saldo Capital"]].set_index("N° Cuota")
        st.line_chart(chart_df)
    else:
        st.write("Aquí aparecerá el cronograma una vez ingreses los datos y presiones calcular.")

# --------------------------
# SIDEBAR: HISTORIAL Y CONTACTO
# --------------------------
st.sidebar.image(LOGO_PATH, width=120)
st.sidebar.markdown("# ABECOIN")
st.sidebar.markdown("Cooperativa de Ahorro y Crédito")
st.sidebar.markdown("---")
st.sidebar.markdown("### Contacto")
st.sidebar.write("📧 Abecooin@gmail.com")
st.sidebar.write("📞 +51 957 607 754")
st.sidebar.markdown("---")
st.sidebar.markdown("### Recomendaciones")
st.sidebar.write("- Usa montos reales para mejores resultados.")
st.sidebar.write("- Elige prorrateado si quieres cuotas estables.")
