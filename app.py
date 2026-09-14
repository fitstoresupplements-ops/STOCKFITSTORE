from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Fit Store - Control de Stock Automatizado",
    page_icon="📦",
    layout="wide",
)

# Tu enlace de Google Apps Script recién generado
WEB_APP_URL = (
    "https://script.google.com/macros/s/AKfycbzicNKXQtHp21umxx70Hh-PogUyJ71fFtbw3z1EITNoh1p-wbj77luSxbG3oMA8WNkbgw/exec"
)

st.title("Fit Store Supplements - Control de Stock Automatizado")
st.markdown("---")


# Función para leer el stock actual desde Google Sheets
@st.cache_data(ttl=10)
def cargar_stock_sheets():
  try:
    response = requests.get(WEB_APP_URL)
    if response.status_code == 200:
      data = response.json()
      if data:
        return pd.DataFrame(data)
    return pd.DataFrame()
  except Exception:
    return pd.DataFrame()


df = cargar_stock_sheets()

# Diseño de la interfaz principal en columnas
col1, col2 = st.columns([2, 1])

with col1:
  st.subheader("Inventario Actual en Google Sheets")
  if not df.empty:
    st.dataframe(df, use_container_width=True)
  else:
    st.info(
        "La planilla está vacía o cargando datos. Agrega un producto abajo para"
        " empezar."
    )

with col2:
  st.subheader("Resumen General")
  if not df.empty:
    st.metric(label="Total de Registros", value=len(df))
  else:
    st.metric(label="Total de Registros", value=0)

st.markdown("---")
st.subheader("Registrar Nuevo Producto o Movimiento")

# Formulario para escribir datos de vuelta a Google Sheets
with st.form("form_stock_web"):
  col_a, col_b, col_c = st.columns(3)
  with col_a:
    producto = st.text_input("Nombre del Suplemento / Producto")
  with col_b:
    stock = st.number_input("Cantidad / Stock", min_value=0, value=1)
  with col_c:
    sucursal = st.selectbox(
        "Sucursal", ["Alem", "San Javier", "Hulk Gym"]
    )

  enviado = st.form_submit_button("Guardar en Google Sheets")

  if enviado:
    if producto:
      payload = {
          "producto": producto,
          "stock": stock,
          "sucursal": sucursal,
          "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
      }
      try:
        res = requests.post(WEB_APP_URL, json=payload)
        if res.status_code == 200:
          st.cache_data.clear()
          st.success(
              f"¡Guardado correctamente en Google Sheets para '{producto}'!"
          )
          st.rerun()
        else:
          st.error("Error al comunicarse con la planilla.")
      except Exception as e:
        st.error(f"Error de conexión: {e}")
    else:
      st.warning("Por favor, ingresa el nombre del producto.")