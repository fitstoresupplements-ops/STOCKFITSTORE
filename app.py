from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Fit Store Supplements - Gestión Total",
    page_icon="🚀",
    layout="wide",
)

# Tu nueva URL oficial de Google Apps Script
WEB_APP_URL = (
    "https://script.google.com/macros/s/AKfycbxLtLL4AEKqgTkmWv6rFebTXdbxU46MogpaHCqV_gSiSUeXLdLGdfMsFsqui6Q9muAtPA/exec"
)

st.title("Fit Store Supplements — Control Total de Operaciones")
st.markdown("---")


# Función para cargar datos optimizada con caché
@st.cache_data(ttl=5)
def cargar_datos():
  try:
    response = requests.get(WEB_APP_URL)
    if response.status_code == 200:
      data = response.json()
      if data:
        df = pd.DataFrame(data)
        # Limpieza de nombres de columnas
        df.columns = [str(col).strip().capitalize() for col in df.columns]
        return df
    return pd.DataFrame()
  except Exception:
    return pd.DataFrame()


df = cargar_datos()

# Verificación de columnas mínimas requeridas en la planilla
columnas_requeridas = ["Producto", "Stock", "Sucursal", "Fecha"]

if not df.empty and all(col in df.columns for col in columnas_requeridas):
  # Asegurar tipos de datos numéricos y de fecha
  df["Stock"] = pd.to_numeric(df["Stock"], errors="coerce").fillna(0)
  if "Precio" in df.columns:
    df["Precio"] = pd.to_numeric(df["Precio"], errors="coerce").fillna(0)
  else:
    df["Precio"] = 0.0  # Valor por defecto si aún no existe la columna

  df["Fecha"] = pd.to_datetime(df["Fecha"], errors="coerce")

  # Menú de Pestañas Principales en la barra lateral
  st.sidebar.header("Menú de Navegación")
  pestana = st.sidebar.radio(
      "Seleccionar Sección",
      [
          "📦 Inventario General",
          "📥 Registrar Ingresos",
          "🗑️ Eliminar Mercadería",
          "✏️ Editar Precios / Stock",
          "📊 Estadísticas y Ventas",
      ],
  )

  # Filtro global de sucursal
  sucursal_sel = st.sidebar.selectbox(
      "Filtrar por Sucursal", ["Todas", "Alem", "San Javier", "Hulk Gym"]
  )

  if sucursal_sel != "Todas":
    df_filtrado = df[df["Sucursal"] == sucursal_sel].copy()
  else:
    df_filtrado = df.copy()

  # -------------------------------------------------------------------------
  # 1. INVENTARIO GENERAL
  # -------------------------------------------------------------------------
  if pestana == "📦 Inventario General":
    st.subheader(f"Inventario Actual — Sucursal: {sucursal_sel}")

    c1, c2, c3, c4 = st.columns(4)
    with c1:
      st.metric(label="Variedad de Productos", value=len(df_filtrado))
    with c2:
      st.metric(
          label="Unidades Totales", value=int(df_filtrado["Stock"].sum())
      )
    with c3:
      valor_total = (
          (df_filtrado["Stock"] * df_filtrado["Precio"]).sum()
          if "Precio" in df_filtrado.columns
          else 0
      )
      st.metric(
          label="Valorización Estimada", value=f"${valor_total:,.2f}"
      )
    with c4:
      stock_critico_count = len(df_filtrado[df_filtrado["Stock"] <= 3])
      st.metric(label="Alertas de Stock Bajo (<=3)", value=stock_critico_count)

    st.markdown("---")
    st.dataframe(
        df_filtrado.sort_values(by="Stock", ascending=True),
        use_container_width=True,
        hide_index=True,
    )

  # -------------------------------------------------------------------------
  # 2. REGISTRAR INGRESOS
  # -------------------------------------------------------------------------
  elif pestana == "📥 Registrar Ingresos":
    st.subheader("Registro de Nuevos Ingresos de Mercadería")

    with st.form("form_ingresos"):
      col_a, col_b = st.columns(2)
      with col_a:
        prod_ingreso = st.text_input("Nombre del Suplemento / Producto")
        suc_ingreso = st.selectbox(
            "Sucursal de Destino", ["Alem", "San Javier", "Hulk Gym"]
        )
      with col_b:
        cant_ingreso = st.number_input("Cantidad a Ingresar", min_value=1, value=1)
        precio_ingreso = st.number_input(
            "Precio Unitario ($)", min_value=0.0, value=0.0, step=100.0
        )

      btn_ingreso = st.form_submit_button("Confirmar Ingreso de Stock")

      if btn_ingreso:
        if prod_ingreso:
          payload = {
              "producto": prod_ingreso,
              "stock": cant_ingreso,
              "sucursal": suc_ingreso,
              "precio": precio_ingreso,
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "accion": "ingresar",
          }
          try:
            res = requests.post(WEB_APP_URL, json=payload)
            if res.status_code == 200:
              st.cache_data.clear()
              st.success(
                  f"¡Ingreso registrado correctamente para '{prod_ingreso}'!"
              )
              st.rerun()
            else:
              st.error("Error al registrar en la planilla.")
          except Exception as e:
            st.error(f"Falla de conexión: {e}")
        else:
          st.warning("El nombre del producto es obligatorio.")

  # -------------------------------------------------------------------------
  # 3. ELIMINAR MERCADERÍA
  # -------------------------------------------------------------------------
  elif pestana == "🗑️ Eliminar Mercadería":
    st.subheader("Baja o Retiro de Mercadería del Inventario")
    st.write(
        "Selecciona el producto que deseas retirar o descontar por completo:"
    )

    if not df_filtrado.empty:
      productos_lista = df_filtrado["Producto"].unique().tolist()
      with st.form("form_eliminar"):
        prod_a_borrar = st.selectbox(
            "Seleccionar Producto", productos_lista
        )
        motivo_baja = st.selectbox(
            "Motivo", ["Venta Realizada", "Merma / Daño", "Ajuste de Inventario"]
        )
        cant_retiro = st.number_input(
            "Cantidad a retirar", min_value=1, value=1
        )

        btn_eliminar = st.form_submit_button("Procesar Baja de Stock")

        if btn_eliminar:
          payload = {
              "producto": prod_a_borrar,
              "stock": -abs(
                  cant_retiro
              ),  # Negativo para descontar del stock actual
              "sucursal": sucursal_sel if sucursal_sel != "Todas" else "Alem",
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
              "accion": "descontar",
          }
          res = requests.post(WEB_APP_URL, json=payload)
          if res.status_code == 200:
            st.cache_data.clear()
            st.success(f"¡Stock actualizado correctamente para '{prod_a_borrar}'!")
            st.rerun()
          else:
            st.error("Error al procesar la solicitud.")
    else:
      st.info("No hay productos disponibles para eliminar en esta sucursal.")

  # -------------------------------------------------------------------------
  # 4. EDITAR PRECIOS / STOCK
  # -------------------------------------------------------------------------
  elif pestana == "✏️ Editar Precios / Stock":
    st.subheader("Edición Directa de Precios y Stock")
    st.write(
        "Modifica los valores directamente sobre la tabla interactiva y guarda"
        " los cambios."
    )

    # Editor interactivo de datos en Streamlit
    df_editado = st.data_editor(
        df_filtrado, use_container_width=True, hide_index=True, num_rows="dynamic"
    )

    if st.button("Guardar Cambios Masivos en la Planilla"):
      # Convertimos el DataFrame modificado a JSON para enviarlo al script
      datos_nuevos = df_editado.to_dict(orient="records")
      payload = {"accion": "sincronizar_completo", "data": datos_nuevos}
      res = requests.post(WEB_APP_URL, json=payload)
      if res.status_code == 200:
        st.cache_data.clear()
        st.success("¡Base de datos sincronizada y actualizada con éxito!")
        st.rerun()
      else:
        st.error("Error al actualizar la planilla.")

  # -------------------------------------------------------------------------
  # 5. ESTADÍSTICAS Y VENTAS
  # -------------------------------------------------------------------------
  elif pestana == "📊 Estadísticas y Ventas":
    st.subheader("Panel de Estadísticas y Análisis Comercial")

    # Filtros temporales para análisis
    col_t1, col_t2 = st.columns(2)
    with col_t1:
      tipo_periodo = st.selectbox(
          "Agrupar análisis por:", ["Mensual", "Semanal", "Anual"]
      )
    with col_t2:
      st.info(
          "Mostrando métricas consolidadas para las sucursales de Fit Store"
          " Supplements."
      )

    st.markdown("---")

    if not df.empty and "Fecha" in df.columns:
      # Procesamiento temporal
      df_temp = df.copy()
      df_temp = df_temp.dropna(subset=["Fecha"])

      if tipo_periodo == "Mensual":
        df_temp["Periodo"] = df_temp["Fecha"].dt.to_period("M").astype(str)
      elif tipo_periodo == "Semanal":
        df_temp["Periodo"] = (
            df_temp["Fecha"].dt.isocalendar().year.astype(str)
            + "-S"
            + df_temp["Fecha"].dt.isocalendar().week.astype(str)
        )
      else:
        df_temp["Periodo"] = df_temp["Fecha"].dt.year.astype(str)

      # Agrupación por período y sucursal
      resumen_periodo = (
          df_temp.groupby(["Periodo", "Sucursal"])
          .agg({"Stock": "sum"})
          .reset_index()
      )

      st.markdown(f"#### Flujo de Stock Consolidado ({tipo_periodo})")
      st.bar_chart(
          resumen_periodo,
          x="Periodo",
          y="Stock",
          color="Sucursal",
          use_container_width=True,
      )

      st.markdown("---")
      st.subheader("Detalle Analítico por Período")
      st.dataframe(resumen_periodo, use_container_width=True, hide_index=True)
    else:
      st.warning(
          "No hay suficientes registros con fecha válida para generar"
          " estadísticas."
      )

else:
  st.warning(
      "La planilla de Google Sheets está vacía o no tiene el formato de"
      " columnas esperado ('Producto', 'Stock', 'Sucursal', 'Fecha', 'Precio')."
  )
  st.info(
      "Usa la pestaña de 'Registrar Ingresos' o agrega las columnas básicas en"
      " tu planilla para comenzar."
  )