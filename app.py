from datetime import datetime, timedelta
import json
import pandas as pd
import streamlit as st

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(
    page_title="Fit Store Supplements - Control Integral",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded",
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown(
    """
    <style>
    .main {
        background-color: #f8fafc;
    }
    .metric-card {
        background-color: white;
        padding: 20px;
        border-radius: 12px;
        box-shadow: 0 1px 3px rgba(0,0,0,0.1);
        border: 1px solid #e2e8f0;
    }
    .stButton>button {
        border-radius: 8px;
        font-weight: 600;
    }
    </style>
""",
    unsafe_allow_html=True,
)

if "productos" not in st.session_state:
  st.session_state["productos"] = []

if "historial_movimientos" not in st.session_state:
  st.session_state["historial_movimientos"] = []

if "eventos_calendario" not in st.session_state:
  st.session_state["eventos_calendario"] = []

UBICACIONES = {"Alem": "alem", "San Javier": "san_javier", "Hulk Gym": "hulk_gym"}

CATEGORIAS = [
    "Proteinas",
    "Creatina",
    "Pre-Entreno",
    "Aminoacidos (BCAA)",
    "Vitaminas",
    "Otros",
    "Magnesio",
    "Colageno",
]

st.sidebar.title("💪 Fit Store Supplements")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegacion",
    [
        "📊 Dashboard General",
        "📦 Inventario Completo",
        "📥 Ingreso de Mercaderia",
        "🔄 Transferir entre Locales",
        "🛒 Registrar Venta",
        "➕ Nuevo Producto",
        "✏️ Modificar Precios",
        "📈 Estadísticas de Ventas",
        "📅 Calendario y Eventos",
        "💾 Respaldos (Backup)",
    ],
)

st.sidebar.markdown("---")
st.sidebar.info(
    "💡 **Precios:** Alem y San Javier usan Precio Base. Hulk Gym calcula su"
    " precio como (Precio Base / 0,9). Stock mínimo 0 deshabilita alertas."
)

if menu == "📊 Dashboard General":
  st.title("📊 Panel de Control General")
  st.markdown("Vista global del inventario y valoración en los puntos de venta.")

  df = pd.DataFrame(st.session_state["productos"])

  if not df.empty:
    df["Stock Total"] = df["alem"] + df["san_javier"] + df["hulk_gym"]
    df["Precio Hulk Gym"] = (df["precio_base"] / 0.9).round(2)

    total_alem = df["alem"].sum()
    total_san_javier = df["san_javier"].sum()
    total_hulk = df["hulk_gym"].sum()
    gran_total = df["Stock Total"].sum()

    col1, col2, col3, col4 = st.columns(4)
    with col1:
      st.metric("📦 Stock General", f"{gran_total} un.")
    with col2:
      st.metric("🏬 Alem", f"{total_alem} un.")
    with col3:
      st.metric("🏬 San Javier", f"{total_san_javier} un.")
    with col4:
      st.metric("🏋️‍♂️ Hulk Gym", f"{total_hulk} un.")

    st.markdown("---")

    st.subheader("⚠️ Alertas de Stock Bajo")
    alertas = []
    for index, row in df.iterrows():
      if row["stock_minimo"] > 0:
        for loc_nombre, loc_key in UBICACIONES.items():
          if row[loc_key] <= row["stock_minimo"]:
            alertas.append({
                "Marca": row.get("marca", "Sin marca"),
                "Producto": row["nombre"],
                "Presentacion": row["presentacion"],
                "Ubicacion": loc_nombre,
                "Stock Actual": row[loc_key],
                "Minimo Requerido": row["stock_minimo"],
            })

    if alertas:
      df_alertas = pd.DataFrame(alertas)
      st.dataframe(df_alertas, use_container_width=True, hide_index=True)
    else:
      st.success(
          "¡Excelente! No hay productos con stock critico o activo con alertas"
          " pendientes."
      )

    st.markdown("---")
    st.subheader("📋 Resumen de Precios y Stock por Producto")
    df_resumen = df.copy()
    df_resumen["Precio Hulk Gym"] = df_resumen["Precio Hulk Gym"].round(2)
    columnas_resumen = [
        "id",
        "marca",
        "nombre",
        "categoria",
        "presentacion",
        "precio_base",
        "Precio Hulk Gym",
        "alem",
        "san_javier",
        "hulk_gym",
        "Stock Total",
        "stock_minimo",
    ]
    vista_resumen = df_resumen[
        [col for col in columnas_resumen if col in df_resumen.columns]
    ].rename(
        columns={
            "precio_base": "Precio Base (Alem/S.Javier)",
            "stock_minimo": "Stock Mínimo",
        }
    )
    st.dataframe(vista_resumen, use_container_width=True, hide_index=True)

  else:
    st.warning(
        "No hay productos cargados todavia. Dirigete a 'Nuevo Producto' para"
        " empezar."
    )

elif menu == "📦 Inventario Completo":
  st.title("📦 Inventario Detallado y Precios")
  st.markdown("Consulta precios diferenciados y stock por ubicación.")

  df = pd.DataFrame(st.session_state["productos"])
  if not df.empty:
    df["Stock Total"] = df["alem"] + df["san_javier"] + df["hulk_gym"]
    df["Precio Hulk Gym"] = (df["precio_base"] / 0.9).round(2)

    vista_ubicacion = st.radio(
        "Filtrar vista por ubicación:",
        ["Inventario Total", "Alem", "San Javier", "Hulk Gym"],
        horizontal=True,
    )
    st.markdown("---")

    col_f1, col_f2 = st.columns(2)
    with col_f1:
      busqueda = st.text_input("🔍 Buscar por nombre o marca de producto:", "")
    with col_f2:
      cat_filtro = st.selectbox("Filtrar por categoria:", ["Todas"] + CATEGORIAS)

    df_filtrado = df.copy()
    if busqueda:
      criterio = busqueda.lower()
      df_filtrado = df_filtrado[
          df_filtrado["nombre"].str.lower().str.contains(criterio, na=False)
          | df_filtrado["marca"].str.lower().str.contains(criterio, na=False)
      ]
    if cat_filtro != "Todas":
      df_filtrado = df_filtrado[df_filtrado["categoria"] == cat_filtro]

    if vista_ubicacion == "Inventario Total":
      columnas_inv = [
          "id",
          "marca",
          "nombre",
          "categoria",
          "sabor",
          "presentacion",
          "precio_base",
          "Precio Hulk Gym",
          "alem",
          "san_javier",
          "hulk_gym",
          "Stock Total",
          "stock_minimo",
      ]
    elif vista_ubicacion == "Alem":
      columnas_inv = [
          "id",
          "marca",
          "nombre",
          "categoria",
          "sabor",
          "presentacion",
          "precio_base",
          "alem",
          "stock_minimo",
      ]
    elif vista_ubicacion == "San Javier":
      columnas_inv = [
          "id",
          "marca",
          "nombre",
          "categoria",
          "sabor",
          "presentacion",
          "precio_base",
          "san_javier",
          "stock_minimo",
      ]
    elif vista_ubicacion == "Hulk Gym":
      columnas_inv = [
          "id",
          "marca",
          "nombre",
          "categoria",
          "sabor",
          "presentacion",
          "Precio Hulk Gym",
          "hulk_gym",
          "stock_minimo",
      ]

    df_inv_view = df_filtrado[
        [col for col in columnas_inv if col in df_filtrado.columns]
    ].rename(
        columns={
            "precio_base": "Precio Base (Alem/S.Javier)",
            "stock_minimo": "Stock Mínimo",
            "alem": "Stock en Alem",
            "san_javier": "Stock en San Javier",
            "hulk_gym": "Stock en Hulk Gym",
        }
    )
    st.dataframe(df_inv_view, use_container_width=True, hide_index=True)
  else:
    st.info("No hay productos registrados.")

elif menu == "📥 Ingreso de Mercaderia":
  st.title("📥 Ingreso de Nueva Mercaderia")
  st.markdown(
      "Registra entradas de stock desde proveedores seleccionando el punto de"
      " venta de destino."
  )

  df = pd.DataFrame(st.session_state["productos"])
  if not df.empty:
    with st.form("form_ingreso"):
      opciones_prod = {
          (
              f"[{row.get('marca', 'Genérica')}] {row['nombre']}"
              f" ({row['presentacion']} - {row['sabor']}) [ID: {row['id']}]"
          ): row["id"]
          for index, row in df.iterrows()
      }
      prod_seleccionado_str = st.selectbox(
          "Seleccionar Producto:", list(opciones_prod.keys())
      )
      prod_id = opciones_prod[prod_seleccionado_str]

      destino_ingreso = st.selectbox(
          "Punto de Venta de destino:", list(UBICACIONES.keys())
      )
      key_ingreso = UBICACIONES[destino_ingreso]

      cantidad_ingreso = st.number_input(
          "Cantidad a ingresar:", min_value=1, step=1, value=10
      )
      nota_ingreso = st.text_input(
          "Observaciones / Proveedor (Opcional):", "Compra a proveedor"
      )

      submit_ingreso = st.form_submit_button("Registrar Ingreso")

      if submit_ingreso:
        for p in st.session_state["productos"]:
          if p["id"] == prod_id:
            p[key_ingreso] += cantidad_ingreso
            st.session_state["historial_movimientos"].insert(0, {
                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                "tipo": "Ingreso Proveedor",
                "producto": f"{p.get('marca', '')} {p['nombre']}".strip(),
                "cantidad": cantidad_ingreso,
                "destino": f"{destino_ingreso} (+{cantidad_ingreso})",
                "monto": 0.0,
            })
            st.success(
                f"¡Ingreso registrado con exito! Se sumaron {cantidad_ingreso}"
                f" unidades de {p['nombre']} a {destino_ingreso}."
            )
            break
  else:
    st.warning("Primero debes dar de alta al menos un producto.")

elif menu == "🔄 Transferir entre Locales":
  st.title("🔄 Transferencia de Stock")
  st.markdown("Mueve mercaderia entre los diferentes puntos de venta.")

  df = pd.DataFrame(st.session_state["productos"])
  if not df.empty:
    with st.form("form_transferencia"):
      origen_nombre = st.selectbox(
          "Origen (Enviar desde):", list(UBICACIONES.keys())
      )
      key_origen = UBICACIONES[origen_nombre]

      destinos_disponibles = [
          loc for loc in UBICACIONES.keys() if loc != origen_nombre
      ]
      destino_nombre = st.selectbox(
          "Destino (Enviar hacia):", destinos_disponibles
      )
      key_destino = UBICACIONES[destino_nombre]

      opciones_prod = {
          (
              f"[{row.get('marca', 'Genérica')}] {row['nombre']}"
              f" ({row['presentacion']}) - Stock en {origen_nombre}:"
              f" {row[key_origen]}"
          ): row["id"]
          for index, row in df.iterrows()
      }
      prod_seleccionado_str = st.selectbox(
          "Seleccionar Producto:", list(opciones_prod.keys())
      )
      prod_id = opciones_prod[prod_seleccionado_str]

      prod_actual = next(
          (p for p in st.session_state["productos"] if p["id"] == prod_id), None
      )

      cantidad_trans = st.number_input(
          "Cantidad a transferir:", min_value=1, step=1, value=5
      )

      submit_trans = st.form_submit_button("Ejecutar Transferencia")

      if submit_trans:
        if prod_actual and prod_actual[key_origen] >= cantidad_trans:
          prod_actual[key_origen] -= cantidad_trans
          prod_actual[key_destino] += cantidad_trans

          st.session_state["historial_movimientos"].insert(0, {
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "tipo": "Transferencia",
              "producto": (
                  f"{prod_actual.get('marca', '')} {prod_actual['nombre']}"
                  .strip()
              ),
              "cantidad": cantidad_trans,
              "destino": f"{origen_nombre} ➔ {destino_nombre}",
              "monto": 0.0,
          })
          st.success(
              f"¡Transferencia exitosa! Se enviaron {cantidad_trans} unidades"
              f" de {origen_nombre} a {destino_nombre}."
          )
          st.rerun()
        else:
          st.error(
              f"Error: Stock insuficiente en {origen_nombre} para realizar la"
              " transferencia."
          )
  else:
    st.warning("No hay productos disponibles para transferir.")

elif menu == "🛒 Registrar Venta":
  st.title("🛒 Registro de Ventas / Salidas")
  st.markdown(
      "Descuenta stock y calcula el importe según el precio correspondiente al"
      " local."
  )

  df = pd.DataFrame(st.session_state["productos"])
  if not df.empty:
    with st.form("form_venta"):
      punto_venta = st.selectbox(
          "Punto de Venta donde se efectua la venta:", list(UBICACIONES.keys())
      )
      key_pv = UBICACIONES[punto_venta]

      opciones_prod = {
          (
              f"[{row.get('marca', 'Genérica')}] {row['nombre']}"
              f" ({row['presentacion']}) - Stock en {punto_venta}: {row[key_pv]}"
          ): row["id"]
          for index, row in df.iterrows()
      }
      prod_seleccionado_str = st.selectbox(
          "Seleccionar Producto:", list(opciones_prod.keys())
      )
      prod_id = opciones_prod[prod_seleccionado_str]

      prod_actual = next(
          (p for p in st.session_state["productos"] if p["id"] == prod_id), None
      )

      cantidad_venta = st.number_input(
          "Cantidad vendida:", min_value=1, step=1, value=1
      )

      if prod_actual:
        if punto_venta == "Hulk Gym":
          precio_publico = prod_actual["precio_base"] / 0.9
          neto_ingreso = prod_actual["precio_base"]
          total_venta = precio_publico * cantidad_venta
          total_neto = neto_ingreso * cantidad_venta
          st.info(
              f"🏋️‍♂️ **Hulk Gym (Precio Público):** ${precio_publico:,.2f} |"
              f" **Tu Ingreso Real (Neto -10%):** ${neto_ingreso:,.2f} c/u\n\n💵"
              f" **Total a cobrar al cliente:** ${total_venta:,.2f} | **Tu"
              f" ingreso neto:** ${total_neto:,.2f}"
          )
        else:
          precio_unitario = prod_actual["precio_base"]
          total_venta = precio_unitario * cantidad_venta
          st.info(
              f"💵 **Precio unitario en {punto_venta}:** ${precio_unitario:,.2f}"
              f" | **Total:** ${total_venta:,.2f}"
          )

      submit_venta = st.form_submit_button("Registrar Venta")

      if submit_venta:
        if prod_actual and prod_actual[key_pv] >= cantidad_venta:
          prod_actual[key_pv] -= cantidad_venta

          if punto_venta == "Hulk Gym":
            monto_registrado = (prod_actual["precio_base"]) * cantidad_venta
            detalle_destino = (
                "Venta en Hulk Gym"
                f" (${precio_publico * cantidad_venta:,.2f} público, neto"
                f" tuyo: ${monto_registrado:,.2f})"
            )
          else:
            monto_registrado = prod_actual["precio_base"] * cantidad_venta
            detalle_destino = f"Venta en {punto_venta} (${monto_registrado:,.2f})"

          st.session_state["historial_movimientos"].insert(0, {
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "tipo": "Venta",
              "producto": (
                  f"{prod_actual.get('marca', '')} {prod_actual['nombre']}"
                  .strip()
              ),
              "cantidad": cantidad_venta,
              "destino": detalle_destino,
              "monto": monto_registrado,
          })
          st.success(
              f"¡Venta registrada con exito! Se descontaron {cantidad_venta}"
              f" unidades en {punto_venta}."
          )
          st.rerun()
        else:
          st.error(
              f"Error: No hay suficiente stock en {punto_venta} para completar"
              " esta venta."
          )
  else:
    st.warning("No hay productos registrados.")

elif menu == "➕ Nuevo Producto":
  st.title("➕ Alta de Nuevo Suplemento")
  st.markdown(
      "Agrega un nuevo producto especificando su precio base y opción de stock"
      " mínimo (0 para desactivar alertas)."
  )

  with st.form("form_nuevo_prod"):
    col1, col2 = st.columns(2)
    with col1:
      marca = st.text_input(
          "Marca del Suplemento (Ej: Star Nutrition, ENA):", "Star Nutrition"
      )
      nombre = st.text_input("Nombre del Suplemento:", "Whey Gold Standard")
      categoria = st.selectbox("Categoria:", CATEGORIAS)
      precio_base = st.number_input(
          "Precio Base (para Alem y San Javier):",
          min_value=0.0,
          value=50000.0,
          step=100.0,
      )
    with col2:
      sabor = st.text_input("Sabor:", "Chocolate")
      presentacion = st.text_input(
          "Presentacion (Ej: 900g, 2kg, 60 caps):", "900 g"
      )
      stock_minimo = st.number_input(
          "Alerta de Stock Minimo por local (0 = Sin control):",
          min_value=0,
          value=0,
          step=1,
      )

    id_prod = st.text_input(
        "Codigo o SKU unico:", f"SUP-{len(st.session_state['productos'])+1:03d}"
    )

    st.markdown("### Stock Inicial por Ubicacion")
    col_s1, col_s2, col_s3 = st.columns(3)
    with col_s1:
      init_alem = st.number_input("Alem", min_value=0, value=0, step=1)
    with col_s2:
      init_san_javier = st.number_input("San Javier", min_value=0, value=0, step=1)
    with col_s3:
      init_hulk = st.number_input("Hulk Gym", min_value=0, value=0, step=1)

    submit_nuevo = st.form_submit_button("Guardar Nuevo Producto")

    if submit_nuevo:
      if nombre.strip() == "":
        st.error("El nombre del producto no puede estar vacio.")
      else:
        nuevo = {
            "id": id_prod,
            "marca": marca.strip(),
            "nombre": nombre.strip(),
            "categoria": categoria,
            "sabor": sabor.strip(),
            "presentacion": presentacion.strip(),
            "precio_base": precio_base,
            "alem": init_alem,
            "san_javier": init_san_javier,
            "hulk_gym": init_hulk,
            "stock_minimo": stock_minimo,
        }
        st.session_state["productos"].append(nuevo)
        st.session_state["historial_movimientos"].insert(0, {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": "Alta Producto",
            "producto": f"{marca} {nombre}".strip(),
            "cantidad": init_alem + init_san_javier + init_hulk,
            "destino": "Stock Inicial Global",
            "monto": 0.0,
        })
        st.success(
            f"¡Producto '{marca} - {nombre}' creado exitosamente con Precio Base"
            f" de ${precio_base:,.2f}!"
        )

elif menu == "✏️ Modificar Precios":
  st.title("✏️ Modificación de Precios")
  st.markdown(
      "Actualiza el precio base de cualquier suplemento. Los precios se"
      " recalculan automáticamente para los puntos de venta."
  )

  df = pd.DataFrame(st.session_state["productos"])
  if not df.empty:
    with st.form("form_modificar_precio"):
      opciones_prod = {
          (
              f"[{row.get('marca', 'Genérica')}] {row['nombre']}"
              f" ({row['presentacion']}) - Actual:"
              f" ${row['precio_base']:,.2f}"
          ): row["id"]
          for index, row in df.iterrows()
      }
      prod_seleccionado_str = st.selectbox(
          "Seleccionar Producto a Modificar:", list(opciones_prod.keys())
      )
      prod_id = opciones_prod[prod_seleccionado_str]

      prod_actual = next(
          (p for p in st.session_state["productos"] if p["id"] == prod_id), None
      )

      nuevo_precio_base = st.number_input(
          "Nuevo Precio Base (Alem y San Javier):",
          min_value=0.0,
          value=float(prod_actual["precio_base"]) if prod_actual else 0.0,
          step=100.0,
      )

      submit_precio = st.form_submit_button("Actualizar Precio")

      if submit_precio:
        if prod_actual:
          precio_anterior = prod_actual["precio_base"]
          prod_actual["precio_base"] = nuevo_precio_base

          st.session_state["historial_movimientos"].insert(0, {
              "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
              "tipo": "Modificación de Precio",
              "producto": (
                  f"{prod_actual.get('marca', '')} {prod_actual['nombre']}"
                  .strip()
              ),
              "cantidad": 0,
              "destino": (
                  f"Precio Base: ${precio_anterior:,.2f} ➔"
                  f" ${nuevo_precio_base:,.2f}"
              ),
              "monto": 0.0,
          })
          st.success(
              f"¡Precio actualizado con éxito para {prod_actual['nombre']}!"
              f" Nuevo precio base: ${nuevo_precio_base:,.2f}"
          )
          st.rerun()
  else:
    st.warning("No hay productos registrados para modificar.")

elif menu == "📈 Estadísticas de Ventas":
  st.title("📈 Estadísticas y Rendimiento de Ventas")
  st.markdown(
      "Análisis financiero, histórico y comparativa de ventas (con descuento"
      " del 10% aplicado a ventas en Hulk Gym)."
  )

  ventas_hist = [
      m for m in st.session_state["historial_movimientos"] if m["tipo"] == "Venta"
  ]

  if ventas_hist:
    df_v = pd.DataFrame(ventas_hist)
    df_v["fecha_dt"] = pd.to_datetime(df_v["fecha"])
    df_v["año_mes"] = df_v["fecha_dt"].dt.to_period("M")

    ahora = datetime.now()
    hace_7_dias = ahora - timedelta(days=7)
    hace_30_dias = ahora - timedelta(days=30)

    ventas_7d = df_v[df_v["fecha_dt"] >= hace_7_dias]
    ventas_30d = df_v[df_v["fecha_dt"] >= hace_30_dias]

    total_7d = ventas_7d["monto"].sum()
    total_30d = ventas_30d["monto"].sum()
    total_historico = df_v["monto"].sum()

    col1, col2, col3 = st.columns(3)
    with col1:
      st.metric("🔥 Ingresos Netos (Últimos 7 Días)", f"${total_7d:,.2f}")
    with col2:
      st.metric("📅 Ingresos Netos (Últimos 30 días)", f"${total_30d:,.2f}")
    with col3:
      st.metric("💰 Facturación Neta Histórica", f"${total_historico:,.2f}")

    st.markdown("---")

    ventas_por_mes = df_v.groupby("año_mes")["monto"].sum().reset_index()
    if not ventas_por_mes.empty:
      max_fila = ventas_por_mes.loc[ventas_por_mes["monto"].idxmax()]
      mes_mayor = str(max_fila["año_mes"])
      monto_mayor = max_fila["monto"]
      st.success(
          f"🏆 **Mes de mayor facturación neta:** {mes_mayor} con un total de"
          f" **${monto_mayor:,.2f}**."
      )

    st.markdown("---")
    st.subheader("📋 Detalle de Ventas Registradas (Ingreso Neto)")
    st.dataframe(
        df_v[["fecha", "producto", "cantidad", "destino", "monto"]].rename(
            columns={"monto": "Ingreso Neto ($)"}
        ),
        use_container_width=True,
        hide_index=True,
    )
  else:
    st.info("Aún no hay ventas registradas para generar estadísticas.")

elif menu == "📅 Calendario y Eventos":
  st.title("📅 Calendario y Gestión de Eventos")
  st.markdown(
      "Programa entregas, cierres de caja, campañas de promoción (como CreaSale)"
      " o feriados."
  )

  with st.form("form_evento"):
    col_e1, col_e2 = st.columns(2)
    with col_e1:
      titulo_evento = st.text_input(
          "Título del Evento / Tarea:", "Inicio Campaña CreaSale"
      )
      fecha_evento = st.date_input("Fecha:", datetime.now())
    with col_e2:
      categoria_evento = st.selectbox(
          "Categoría:",
          [
              "Entrega San Javier",
              "Promoción / Campaña",
              "Reposición Proveedor",
              "Cierre de Caja / Mensual",
              "Otro",
          ],
      )
      descripcion_evento = st.text_input(
          "Notas / Descripción:", "Liquidación de stock de creatina"
      )

    submit_evento = st.form_submit_button("Guardar Evento en Calendario")
    if submit_evento:
      if titulo_evento.strip() == "":
        st.error("El título no puede estar vacío.")
      else:
        nuevo_evento = {
            "fecha": str(fecha_evento),
            "titulo": titulo_evento.strip(),
            "categoria": categoria_evento,
            "descripcion": descripcion_evento.strip(),
        }
        st.session_state["eventos_calendario"].append(nuevo_evento)
        st.success(f"¡Evento '{titulo_evento}' guardado para el {fecha_evento}!")

elif menu == "💾 Respaldos (Backup)":
  st.title("💾 Copias de Seguridad y Respaldos")
  st.markdown(
      "Exporta o importa los datos de tu aplicación (productos, historial y"
      " eventos) en formato JSON para no perder nada."
  )

  datos_backup = {
      "productos": st.session_state["productos"],
      "historial_movimientos": st.session_state["historial_movimientos"],
      "eventos_calendario": st.session_state["eventos_calendario"],
  }

  json_str = json.dumps(datos_backup, indent=4, ensure_ascii=False)

  st.download_button(
      label="📥 Descargar Backup Completo (JSON)",
      data=json_str,
      file_name=f"fitstore_backup_{datetime.now().strftime('%Y-%m-%d')}.json",
      mime="application/json",
  )

  st.markdown("---")
  st.subheader("📤 Restaurar / Cargar Respaldo")
  archivo_subido = st.file_uploader(
      "Selecciona un archivo JSON de respaldo previo:", type=["json"]
  )

  if archivo_subido is not None:
    try:
      datos_cargados = json.load(archivo_subido)
      if st.button("⚠️ Confirmar Restauración de Datos"):
        st.session_state["productos"] = datos_cargados.get("productos", [])
        st.session_state["historial_movimientos"] = datos_cargados.get(
            "historial_movimientos", []
        )
        st.session_state["eventos_calendario"] = datos_cargados.get(
            "eventos_calendario", []
        )
        st.success("¡Datos restaurados con éxito! Actualiza la página.")
    except Exception as e:
      st.error(f"Error al leer el archivo de respaldo: {e}")