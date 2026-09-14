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


def limpiar_numero(valor):
    if pd.isna(valor):
        return 0.0
    val_str = str(valor).strip()
    if not val_str or val_str == '$':
        return 0.0
    
    val_str = val_str.replace('$', '').replace(' ', '')
    
    if ',' in val_str and '.' in val_str:
        val_str = val_str.replace('.', '').replace(',', '.')
    elif '.' in val_str:
        partes = val_str.split('.')
        if len(partes) > 2 or (len(partes) == 2 and len(partes[1]) == 3):
            val_str = val_str.replace('.', '')
    elif ',' in val_str:
        val_str = val_str.replace(',', '.')

    try:
        return float(val_str)
    except ValueError:
        return 0.0


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

columnas_requeridas = ["ID", "Marca", "Nombre", "Precio Base"]

if not df.empty and any(col in df.columns for col in columnas_requeridas):
    # Limpieza de columnas numéricas
    cols_numericas = ["Precio Base", "San Javier", "Hulk Gym", "Stock Minimo", "Stock Total", "Alem", "Jav"]
    for col in cols_numericas:
        if col in df.columns:
            df[col] = df[col].apply(limpiar_numero)

    # Crear columna combinada "Marca - Nombre - Presentación - Sabor"
    if "Marca" in df.columns and "Nombre" in df.columns:
        col_pres = "Presentacion" if "Presentacion" in df.columns else ("Presentación" if "Presentación" in df.columns else None)
        
        def construir_display(row):
            marca = str(row.get("Marca", "")).strip()
            nombre = str(row.get("Nombre", "")).strip()
            
            pres = ""
            if col_pres:
                pres = str(row.get(col_pres, "")).strip()
            
            sabor = ""
            if "Sabor" in df.columns:
                sabor = str(row.get("Sabor", "")).strip()
            
            partes = [marca, nombre]
            if pres and pres.lower() != 'nan':
                partes.append(pres)
            if sabor and sabor.lower() != 'nan':
                partes.append(sabor)
                
            return " - ".join([p for p in partes if p])

        df["Producto_Display"] = df.apply(construir_display, axis=1)
    else:
        df["Producto_Display"] = df["Nombre"].astype(str) if "Nombre" in df.columns else df.index.astype(str)

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

    sucursal_sel = st.sidebar.selectbox(
        "Filtrar por Sucursal", ["Todas", "Alem", "San Javier", "Hulk Gym"]
    )

    # -------------------------------------------------------------------------
    # 1. INVENTARIO GENERAL
    # -------------------------------------------------------------------------
    if pestana == "📦 Inventario General":
        st.subheader(f"Inventario Actual — Sucursal: {sucursal_sel}")

        df_inventario = df.copy()
        if sucursal_sel == "San Javier":
            col_sj = next((c for c in df_inventario.columns if "javier" in c.lower()), "San Javier")
            if col_sj in df_inventario.columns:
                df_inventario = df_inventario[df_inventario[col_sj] > 0]
        elif sucursal_sel == "Hulk Gym":
            col_hulk = next((c for c in df_inventario.columns if "hulk" in c.lower() or "gym" in c.lower()), "Hulk Gym")
            if col_hulk in df_inventario.columns:
                df_inventario = df_inventario[df_inventario[col_hulk] > 0]

        c1, c2, c3, c4 = st.columns(4)
        with c1:
            st.metric(label="Variedad de Productos", value=len(df_inventario))
        with c2:
            unidades_totales = int(df_inventario["Stock Total"].sum()) if "Stock Total" in df_inventario.columns else 0
            st.metric(label="Unidades Totales", value=unidades_totales)
        with c3:
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

        sucursal_venta = st.selectbox("Punto de Venta", ["Alem", "San Javier", "Hulk Gym"], key="venta_sucursal")
        
        productos_disponibles = df["Producto_Display"].tolist() if "Producto_Display" in df.columns else []
        prod_seleccionado_display = st.selectbox("Producto (Marca - Nombre - Presentación - Sabor)", productos_disponibles, key="venta_producto")

        # Búsqueda flexible de la columna de la sucursal correspondiente
        col_suc = "Stock Total"
        columnas_disponibles = df.columns.tolist()
        
        if sucursal_venta == "San Javier":
            posible_col = next((c for c in columnas_disponibles if "javier" in c.lower()), None)
            col_suc = posible_col if posible_col else "Stock Total"
        elif sucursal_venta == "Hulk Gym":
            posible_col = next((c for c in columnas_disponibles if "hulk" in c.lower() or "gym" in c.lower()), None)
            col_suc = posible_col if posible_col else "Stock Total"
        elif sucursal_venta == "Alem":
            posible_col = next((c for c in columnas_disponibles if "alem" in c.lower()), None)
            col_suc = posible_col if posible_col else "Stock Total"

        stock_actual = 0
        precio_base = 0.0
        nombre_real_prod = ""
        sabor_real_prod = ""
        id_real_prod = ""
        
        if prod_seleccionado_display and not df.empty:
            fila_prod = df[df["Producto_Display"] == prod_seleccionado_display]
            if not fila_prod.empty:
                nombre_real_prod = fila_prod["Nombre"].values[0] if "Nombre" in fila_prod.columns else ""
                sabor_real_prod = fila_prod["Sabor"].values[0] if "Sabor" in fila_prod.columns else ""
                id_real_prod = fila_prod["ID"].values[0] if "ID" in fila_prod.columns else ""
                
                if col_suc in fila_prod.columns:
                    val_stock = fila_prod[col_suc].values[0]
                    stock_actual = int(limpiar_numero(val_stock))
                if "Precio Base" in fila_prod.columns:
                    precio_base = float(limpiar_numero(fila_prod["Precio Base"].values[0]))

        # Cálculo automático del precio de venta según la sucursal seleccionada
        if sucursal_venta in ["Alem", "San Javier"]:
            precio_sugerido = precio_base
        else:  # Hulk Gym (Precio base dividido 0.9)
            precio_sugerido = precio_base / 0.9 if 0.9 > 0 else precio_base

        st.info(f"Stock disponible en {sucursal_venta}: {stock_actual} unidades | **Precio Unitario Automático: ${precio_sugerido:,.2f}**")

        with st.form("form_venta_local"):
            cant_venta = st.number_input("Cantidad a Vender", min_value=1, max_value=max(1, stock_actual), step=1)
            btn_registrar_venta = st.form_submit_button("Confirmar y Descontar Stock")

            if btn_registrar_venta:
                if cant_venta > stock_actual:
                    st.error("No hay suficiente stock para realizar la venta en esta sucursal.")
                else:
                    total_venta = cant_venta * precio_sugerido

                    nueva_venta = {
                        'Fecha': datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
                        'Punto de Venta': sucursal_venta,
                        'Producto': prod_seleccionado_display,
                        'Cantidad': cant_venta,
                        'Total': total_venta
                    }
                    
                    if 'ventas' not in st.session_state:
                        st.session_state['ventas'] = pd.DataFrame(columns=['Fecha', 'Punto de Venta', 'Producto', 'Cantidad', 'Total'])
                    
                    st.session_state['ventas'] = pd.concat([st.session_state['ventas'], pd.DataFrame([nueva_venta])], ignore_index=True)

                    payload = {
                        "accion": "descontar",
                        "id": str(id_real_prod),
                        "producto": str(nombre_real_prod),
                        "sabor": str(sabor_real_prod),
                        "stock": -abs(cant_venta),
                        "sucursal": sucursal_venta,
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
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
    # 3. REGISTRAR INGRESOS (NUEVO VS EXISTENTE)
    # -------------------------------------------------------------------------
    elif pestana == "📥 Registrar Ingresos":
        st.subheader("Registro de Nuevos Ingresos de Mercadería")

        tipo_ingreso = st.radio("Tipo de Ingreso", ["Producto Existente", "Producto Nuevo"], horizontal=True)

        if tipo_ingreso == "Producto Nuevo":
            nuevo_id = "SUP-001"
            if "ID" in df.columns and not df.empty:
                ids_numericos = []
                for i_val in df["ID"].dropna():
                    val_str = str(i_val)
                    digits = "".join(filter(str.isdigit, val_str))
                    if digits:
                        ids_numericos.append(int(digits))
                if ids_numericos:
                    nuevo_id = f"SUP-{max(ids_numericos) + 1:03d}"

            st.info(f"🆔 ID Asignado Automáticamente: **{nuevo_id}**")

            with st.form("form_ingreso_nuevo"):
                col_n1, col_n2 = st.columns(2)
                with col_n1:
                    marca_nuevo = st.text_input("Marca (ej. ENA, Star Nutrition)")
                    nombre_nuevo = st.text_input("Nombre del Producto")
                    categoria_nuevo = st.text_input("Categoría (ej. Creatina, Proteína)")
                with col_n2:
                    presentacion_nuevo = st.text_input("Presentación (ej. 300g, 60 caps)")
                    sabor_nuevo = st.text_input("Sabor")
                    precio_base_nuevo = st.number_input("Precio Base ($)", min_value=0.0, step=100.0)

                col_n3, col_n4 = st.columns(2)
                with col_n3:
                    suc_ingreso_nuevo = st.selectbox("Sucursal de Destino", ["Alem", "San Javier", "Hulk Gym"], key="suc_nue")
                with col_n4:
                    cant_ingreso_nuevo = st.number_input("Cantidad a Ingresar", min_value=1, value=1, key="cant_nue")

                btn_guardar_nuevo = st.form_submit_button("Registrar Nuevo Producto y Stock")

                if btn_guardar_nuevo:
                    if nombre_nuevo:
                        payload = {
                            "accion": "ingresar_nuevo",
                            "id": nuevo_id,
                            "marca": marca_nuevo,
                            "nombre": nombre_nuevo,
                            "categoria": categoria_nuevo,
                            "presentacion": presentacion_nuevo,
                            "sabor": sabor_nuevo,
                            "precio_base": precio_base_nuevo,
                            "sucursal": suc_ingreso_nuevo,
                            "stock": cant_ingreso_nuevo,
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                        }
                        try:
                            res = requests.post(WEB_APP_URL, json=payload)
                            if res.status_code == 200:
                                st.cache_data.clear()
                                st.success(f"¡Nuevo producto '{marca_nuevo} - {nombre_nuevo}' registrado con éxito!")
                                st.rerun()
                            else:
                                st.error("Error al registrar el producto nuevo en la planilla.")
                        except Exception as e:
                            st.error(f"Falla de conexión: {e}")
                    else:
                        st.warning("El nombre del producto es obligatorio.")

        else:  # Producto Existente
            productos_lista = df["Producto_Display"].tolist() if "Producto_Display" in df.columns else []
            
            prod_elegido = st.selectbox("Seleccionar Producto Existente", productos_lista, key="select_prod_existente")

            precio_auto = 0.0
            nombre_real_existente = ""
            marca_existente = ""
            categoria_existente = ""
            presentacion_existente = ""
            id_existente = ""
            sabores_existentes = []

            if prod_elegido and not df.empty:
                filas_prod = df[df["Producto_Display"] == prod_elegido]
                if not filas_prod.empty:
                    primera_fila = filas_prod.iloc[0]
                    nombre_real_existente = primera_fila.get("Nombre", "")
                    marca_existente = primera_fila.get("Marca", "")
                    categoria_existente = primera_fila.get("Categoría" if "Categoría" in df.columns else "Categoria", "")
                    presentacion_existente = primera_fila.get("Presentacion" if "Presentacion" in df.columns else "Presentación", "")
                    id_existente = primera_fila.get("ID", "")
                    
                    if "Precio Base" in primera_fila:
                        precio_auto = float(limpiar_numero(primera_fila["Precio Base"]))
                    
                    if "Sabor" in df.columns:
                        sabores_existentes = [str(s).strip() for s in filas_prod["Sabor"].dropna().unique().tolist() if str(s).strip() and str(s).strip().lower() != 'nan']

            st.markdown(f"💰 **Precio Base Registrado:** ${precio_auto:,.2f}")

            if sabores_existentes:
                tipo_sabor = st.radio("¿El sabor ya está registrado para este producto o es un sabor nuevo?", ["Sabor Existente", "Sabor Nuevo"], horizontal=True, key="radio_tipo_sabor")
            else:
                st.info("No hay sabores previos registrados para este producto. Se registrará como un nuevo sabor.")
                tipo_sabor = "Sabor Nuevo"

            with st.form("form_ingreso_existente"):
                if tipo_sabor == "Sabor Existente" and sabores_existentes:
                    sabor_final = st.selectbox("Seleccionar Sabor Existente", sabores_existentes, key="select_sabor_existente")
                else:
                    sabor_final = st.text_input("Ingrese el Nombre del Nuevo Sabor", key="input_nuevo_sabor")

                col_e1, col_e2 = st.columns(2)
                with col_e1:
                    suc_ingreso_ex = st.selectbox("Sucursal de Destino", ["Alem", "San Javier", "Hulk Gym"], key="suc_ex")
                with col_e2:
                    cant_ingreso_ex = st.number_input("Cantidad a Ingresar", min_value=1, value=1, key="cant_ex")

                btn_guardar_existente = st.form_submit_button("Sumar Stock / Registrar Variante")

                if btn_guardar_existente:
                    if tipo_sabor == "Sabor Nuevo" and not sabor_final.strip():
                        st.warning("Debes ingresar el nombre del nuevo sabor.")
                    else:
                        if tipo_sabor == "Sabor Nuevo":
                            nuevo_id = "SUP-001"
                            if "ID" in df.columns and not df.empty:
                                ids_numericos = []
                                for i_val in df["ID"].dropna():
                                    val_str = str(i_val)
                                    digits = "".join(filter(str.isdigit, val_str))
                                    if digits:
                                        ids_numericos.append(int(digits))
                                if ids_numericos:
                                    nuevo_id = f"SUP-{max(ids_numericos) + 1:03d}"

                            payload = {
                                "accion": "ingresar_nuevo",
                                "id": nuevo_id,
                                "marca": marca_existente,
                                "nombre": nombre_real_existente,
                                "categoria": categoria_existente,
                                "presentacion": presentacion_existente,
                                "sabor": sabor_final.strip(),
                                "precio_base": precio_auto,
                                "sucursal": suc_ingreso_ex,
                                "stock": cant_ingreso_ex,
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                            }
                        else:
                            payload = {
                                "accion": "ingresar",
                                "id": str(id_existente),
                                "producto": str(nombre_real_existente),
                                "sabor": str(sabor_final),
                                "stock": cant_ingreso_ex,
                                "sucursal": suc_ingreso_ex,
                                "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                            }

                        try:
                            res = requests.post(WEB_APP_URL, json=payload)
                            if res.status_code == 200:
                                st.cache_data.clear()
                                st.success(f"¡Ingreso registrado con éxito para '{prod_elegido}' (Sabor: {sabor_final})!")
                                st.rerun()
                            else:
                                st.error("Error al registrar el ingreso en la planilla.")
                        except Exception as e:
                            st.error(f"Falla de conexión: {e}")

    # -------------------------------------------------------------------------
    # 4. ELIMINAR MERCADERÍA
    # -------------------------------------------------------------------------
    elif pestana == "🗑️ Eliminar Mercadería":
        st.subheader("Baja o Retiro de Mercadería del Inventario")

        if not df.empty and "Producto_Display" in df.columns:
            productos_lista = df["Producto_Display"].tolist()
            with st.form("form_eliminar"):
                prod_a_borrar_display = st.selectbox(
                    "Seleccionar Producto (Marca - Nombre - Presentación - Sabor)", productos_lista
                )
                
                nombre_baja_real = prod_a_borrar_display
                sabor_baja_real = ""
                id_baja_real = ""
                
                fila_baja = df[df["Producto_Display"] == prod_a_borrar_display]
                if not fila_baja.empty:
                    if "Nombre" in fila_baja.columns:
                        nombre_baja_real = fila_baja["Nombre"].values[0]
                    if "Sabor" in fila_baja.columns:
                        sabor_baja_real = fila_baja["Sabor"].values[0]
                    if "ID" in fila_baja.columns:
                        id_baja_real = fila_baja["ID"].values[0]

                motivo_baja = st.selectbox(
                    "Motivo", ["Venta Realizada", "Merma / Daño", "Ajuste de Inventario"]
                )
                cant_retiro = st.number_input(
                    "Cantidad a retirar", min_value=1, value=1
                )

                btn_eliminar = st.form_submit_button("Procesar Baja de Stock")

                if btn_eliminar:
                    payload = {
                        "accion": "descontar",
                        "id": str(id_baja_real),
                        "producto": str(nombre_baja_real),
                        "sabor": str(sabor_baja_real),
                        "stock": -abs(cant_retiro),
                        "sucursal": sucursal_sel if sucursal_sel != "Todas" else "Alem",
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                    }
                    res = requests.post(WEB_APP_URL, json=payload)
                    if res.status_code == 200:
                        st.cache_data.clear()
                        st.success(f"¡Stock actualizado correctamente para '{prod_a_borrar_display}'!")
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
        " (se buscan columnas como 'ID', 'Marca', 'Nombre', 'Precio Base')."
    )
    st.info(
        "Revisá que la primera fila de tu Google Sheet mantenga los encabezados"
        " correctos."
    )