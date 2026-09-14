from datetime import datetime
import pandas as pd
import requests
import streamlit as st

st.set_page_config(
    page_title="Fit Store Supplements - Gestión Total",
    page_icon="🚀",
    layout="wide",
)

# Tu URL oficial de Google Apps Script
WEB_APP_URL = "https://script.google.com/macros/s/AKfycbxLtLL4AEKqgTkmWv6rFebTXdbxU46MogpaHCqV_gSiSUeXLdLGdfMsFsqui6Q9muAtPA/exec"

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
                df.columns = [str(col).strip() for col in df.columns]
                return df
        return pd.DataFrame()
    except Exception:
        return pd.DataFrame()


df = cargar_datos()

# Verificación de columnas clave según tu planilla actual
columnas_requeridas = ["ID", "Marca", "Nombre", "Precio Base"]

if not df.empty and any(col in df.columns for col in columnas_requeridas):
    # Limpieza profunda y conversión de columnas numéricas (sucursales y precios)
    cols_numericas = ["Precio Base", "San Javier", "Hulk Gym", "Stock Minimo", "Stock Total"]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = pd.to_numeric(
                df[col].astype(str)
                .str.replace('$', '', regex=False)
                .str.replace(' ', '', regex=False)
                .str.replace('.', '', regex=False)
                .str.replace(',', '.', regex=False),
                errors="coerce"
            ).fillna(0)

    # Menú de Pestañas Principales en la barra lateral
    st.sidebar.header("Menú de Navegación")
    pestana = st.sidebar.radio(
        "Seleccionar Sección",
        [
            "📦 Inventario General",
            "🛒 Registrar Venta",
            "📥 Registrar Ingresos",
            "🗑️ Eliminar Mercadería",
            "✏️ Editar Precios / Stock",
            "📊 Estadísticas y Reportes",
        ],
    )

    # Filtro global de sucursal adaptado a tus columnas
    sucursal_sel = st.sidebar.selectbox(
        "Filtrar por Sucursal", ["Todas", "Alem", "Javier", "Hulk Gym"]
    )

    # -------------------------------------------------------------------------
    # 1. INVENTARIO GENERAL
    # -------------------------------------------------------------------------
    if pestana == "📦 Inventario General":
        st.subheader(f"Inventario Actual — Sucursal: {sucursal_sel}")

        df_inventario = df.copy()
        if sucursal_sel == "San Javier" and "San Javier" in df_inventario.columns:
            df_inventario = df_inventario[df_inventario['San Javier'] > 0]
        elif sucursal_sel == "Hulk Gym" and "Hulk Gym" in df_inventario.columns:
            df_inventario = df_inventario[df_inventario['Hulk Gym'] > 0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="Variedad de Productos", value=len(df_inventario))
        with c2:
            unidades_totales = int(df_inventario["Stock Total"].sum()) if "Stock Total" in df_inventario.columns else 0
            st.metric(label="Unidades Totales", value=unidades_totales)
        with c3:
            # Cálculo de valorización robusto garantizando valores numéricos limpios
            valor_inventario = 0
            if "Stock Total" in df_inventario.columns and "Precio Base" in df_inventario.columns:
                valor_inventario = (df_inventario["Stock Total"] * df_inventario["Precio Base"]).sum()
            st.metric(
                label="Valorización Estimada", value=f"${valor_inventario:,.2f}"
            )
        with c4:
            stock_critico = (
                len(df_inventario[df_inventario["Stock Total"] <= df_inventario["Stock Minimo"]])
                if "Stock Total" in df_inventario.columns and "Stock Minimo" in df_inventario.columns
                else 0
            )
            st.metric(label="Alertas de Stock Bajo", value=stock_critico)

        st.markdown("---")
        st.dataframe(df_inventario, use_container_width=True, hide_index=True)

    # -------------------------------------------------------------------------
    # 2. REGISTRAR VENTA
    # -------------------------------------------------------------------------
    elif pestana == "🛒 Registrar Venta":
        st.subheader("Registrar Venta y Descuento de Stock")

        with st.form("form_venta_local"):
            sucursal_venta = st.selectbox("Punto de Venta", ["Alem", "San Javier", "Hulk Gym"])
            
            # Mapear sucursal a la columna correspondiente de stock
            col_suc = "Stock Total"
            if sucursal_venta == "San Javier" and "San Javier" in df.columns:
                col_suc = "San Javier"
            elif sucursal_venta == "Hulk Gym" and "Hulk Gym" in df.columns:
                col_suc = "Hulk Gym"

            productos_disponibles = df["Nombre"].unique().tolist() if "Nombre" in df.columns else []
            prod_seleccionado = st.selectbox("Producto", productos_disponibles)

            # Obtener stock actual y precio base del producto seleccionado
            stock_actual = 0
            precio_base = 0.0
            if prod_seleccionado and not df.empty:
                fila_prod = df[df["Nombre"] == prod_seleccionado]
                if not fila_prod.empty:
                    if col_suc in fila_prod.columns:
                        stock_actual = int(fila_prod[col_suc].values[0])
                    if "Precio Base" in fila_prod.columns:
                        precio_base = float(fila_prod["Precio Base"].values[0])

            # Cálculo automático del precio de venta según la sucursal seleccionada
            if sucursal_venta in ["Alem", "San Javier"]:
                precio_sugerido = precio_base
            else:  # Hulk Gym
                precio_sugerido = precio_base / 0.9 if 0.9 > 0 else precio_base

            st.info(f"Stock disponible en {sucursal_venta}: {stock_actual} unidades | **Precio Unitario Automático: ${precio_sugerido:,.2f}**")

            cant_venta = st.number_input("Cantidad a Vender", min_value=1, max_value=max(1, stock_actual), step=1)

            btn_registrar_venta = st.form_submit_button("Confirmar y Descontar Stock")

            if btn_registrar_venta:
                if cant_venta > stock_actual:
                    st.error("No hay suficiente stock para realizar la venta en esta sucursal.")
                else:
                    total_venta = cant_venta * precio_sugerido

                    # Registrar en el historial de sesión
                    nueva_venta = {
                        'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Punto de Venta': sucursal_venta,
                        'Producto': prod_seleccionado,
                        'Cantidad': cant_venta,
                        'Total': total_venta
                    }
                    
                    if 'ventas' not in st.session_state:
                        st.session_state['ventas'] = pd.DataFrame(columns=['Fecha', 'Punto de Venta', 'Producto', 'Cantidad', 'Total'])
                    
                    st.session_state['ventas'] = pd.concat([st.session_state['ventas'], pd.DataFrame([nueva_venta])], ignore_index=True)

                    # Enviar payload para actualizar en Google Apps Script
                    payload = {
                        "producto": prod_seleccionado,
                        "stock": -abs(cant_venta),
                        "sucursal": sucursal_venta,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                        "accion": "descontar",
                    }
                    try:
                        res = requests.post(WEB_APP_URL, json=payload)
                        if res.status_code == 200:
                            st.cache_data.clear()
                            st.success(f"¡Venta registrada con éxito! Stock descontado de {sucursal_venta}. Total: ${total_venta:,.2f}")
                            st.rerun()
                        else:
                            st.error("Venta registrada localmente pero hubo un error al sincronizar con Google Sheets.")
                    except Exception as e:
                        st.error(f"Falla de conexión: {e}")

    # -------------------------------------------------------------------------
    # 3. REGISTRAR INGRESOS
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
    # 4. ELIMINAR MERCADERÍA
    # -------------------------------------------------------------------------
    elif pestana == "🗑️ Eliminar Mercadería":
        st.subheader("Baja o Retiro de Mercadería del Inventario")

        if not df.empty and "Nombre" in df.columns:
            productos_lista = df["Nombre"].unique().tolist()
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
                        "stock": -abs(cant_retiro),
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
            st.info("No hay productos disponibles para eliminar.")

    # -------------------------------------------------------------------------
    # 5. EDITAR PRECIOS / STOCK
    # -------------------------------------------------------------------------
    elif pestana == "✏️ Editar Precios / Stock":
        st.subheader("Edición Directa de Precios y Stock")
        st.write(
            "Modifica los valores directamente sobre la tabla interactiva y guarda"
            " los cambios."
        )

        df_editado = st.data_editor(
            df, use_container_width=True, hide_index=True, num_rows="dynamic"
        )

        if st.button("Guardar Cambios Masivos en la Planilla"):
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
    # 6. ESTADÍSTICAS Y REPORTES
    # -------------------------------------------------------------------------
    elif pestana == "📊 Estadísticas y Reportes":
        st.subheader("Estadísticas y Reportes de Ventas")

        if 'ventas' not in st.session_state or st.session_state['ventas'].empty:
            st.info("Aún no hay ventas registradas en esta sesión para mostrar estadísticas. Registrá ventas en la pestaña correspondiente.")
        else:
            df_ventas = st.session_state['ventas'].copy()
            df_ventas['Fecha'] = pd.to_datetime(df_ventas['Fecha'])
            df_ventas['Mes'] = df_ventas['Fecha'].dt.to_period('M').astype(str)
            df_ventas['Año'] = df_ventas['Fecha'].dt.year

            periodo = st.selectbox("Filtrar por período", ["Todos", "Mes Actual", "Año Actual"])

            if periodo == "Mes Actual":
                mes_actual = pd.Timestamp.now().strftime('%Y-%m')
                df_ventas = df_ventas[df_ventas['Mes'] == mes_actual]
            elif periodo == "Año Actual":
                anio_actual = pd.Timestamp.now().year
                df_ventas = df_ventas[df_ventas['Año'] == anio_actual]

            total_recaudado = df_ventas['Total'].sum()
            total_unidades = df_ventas['Cantidad'].sum()

            col1, col2 = st.columns(2)
            col1.metric("Facturación Total", f"${total_recaudado:,.2f}")
            col2.metric("Unidades Vendidas", int(total_unidades))

            st.markdown("### Facturación por Punto de Venta")
            if not df_ventas.empty:
                ventas_por_pv = df_ventas.groupby('Punto de Venta')['Total'].sum().reset_index()
                st.bar_chart(ventas_por_pv.set_index('Punto de Venta'))
                
                mejor_pv = ventas_por_pv.loc[ventas_por_pv['Total'].idxmax()]['Punto de Venta']
                st.success(f"🏆 El punto de venta con mayor salida es: **{mejor_pv}**")

            st.markdown("### Detalle de Transacciones")
            st.dataframe(df_ventas, use_container_width=True, hide_index=True)

else:
    st.warning(
        "La planilla de Google Sheets no coincide con la estructura esperada"
        " (se buscan columnas como 'ID', 'Marca', 'Nombre', 'Precio Base"
        " Alem')."
    )
    st.info(
        "Revisá que la primera fila de tu Google Sheet mantenga los encabezados"
        " correctos."
    )