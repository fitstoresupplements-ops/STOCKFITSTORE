import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(
    page_title="Fit Store Supplements - Control de Stock y Precios",
    page_icon="💪",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- ESTILOS CSS PERSONALIZADOS ---
st.markdown("""
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
""", unsafe_allow_html=True)

if 'productos' not in st.session_state:
    st.session_state['productos'] = []

if 'historial_movimientos' not in st.session_state:
    st.session_state['historial_movimientos'] = []

UBICACIONES = {
    "Alem": "alem",
    "San Javier": "san_javier",
    "Hulk Gym": "hulk_gym"
}

CATEGORIAS = ["Proteinas", "Creatina", "Pre-Entreno", "Aminoacidos (BCAA)", "Vitaminas", "Otros", "Magnesio", "Colageno"]

st.sidebar.title("💪 Fit Store Supplements")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegacion",
    ["📊 Dashboard General", "📦 Inventario Completo", "📥 Ingreso de Mercaderia", "🔄 Transferir entre Locales", "🛒 Registrar Venta", "➕ Nuevo Producto", "💾 Respaldos (Backup)"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Precios:** Alem y San Javier usan el Precio Base. Hulk Gym (consignación) calcula su precio como (Precio Base / 0,9).")

if menu == "📊 Dashboard General":
    st.title("📊 Panel de Control General")
    st.markdown("Vista global del inventario y valoración en los puntos de venta.")

    df = pd.DataFrame(st.session_state['productos'])
    
    if not df.empty:
        df['Stock Total'] = df['alem'] + df['san_javier'] + df['hulk_gym']
        df['Precio Hulk Gym'] = (df['precio_base'] / 0.9).round(2)
        
        total_alem = df['alem'].sum()
        total_san_javier = df['san_javier'].sum()
        total_hulk = df['hulk_gym'].sum()
        gran_total = df['Stock Total'].sum()

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
            if row['stock_minimo'] > 0:
                for loc_nombre, loc_key in UBICACIONES.items():
                    if row[loc_key] <= row['stock_minimo']:
                        alertas.append({
                            "Marca": row.get('marca', 'Sin marca'),
                            "Producto": row['nombre'],
                            "Presentacion": row['presentacion'],
                            "Ubicacion": loc_nombre,
                            "Stock Actual": row[loc_key],
                            "Minimo Requerido": row['stock_minimo']
                        })
        
        if alertas:
            df_alertas = pd.DataFrame(alertas)
            st.dataframe(df_alertas, use_container_width=True, hide_index=True)
        else:
            st.success("¡Excelente! No hay productos con stock critico o activo con alertas pendientes.")

        st.markdown("---")
        st.subheader("📋 Resumen de Precios y Stock por Producto")
        df_resumen = df.copy()
        df_resumen['Precio Hulk Gym'] = df_resumen['Precio Hulk Gym'].round(2)
        columnas_resumen = ['id', 'marca', 'nombre', 'categoria', 'presentacion', 'precio_base', 'Precio Hulk Gym', 'alem', 'san_javier', 'hulk_gym', 'Stock Total', 'stock_minimo']
        vista_resumen = df_resumen[[col for col in columnas_resumen if col in df_resumen.columns]].rename(columns={'precio_base': 'Precio Base (Alem/S.Javier)', 'stock_minimo': 'Stock Mínimo'})
        st.dataframe(vista_resumen, use_container_width=True, hide_index=True)

    else:
        st.warning("No hay productos cargados todavia. Dirigete a 'Nuevo Producto' para empezar.")

elif menu == "📦 Inventario Completo":
    st.title("📦 Inventario Detallado y Precios")
    st.markdown("Consulta precios diferenciados y stock por ubicación.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        df['Stock Total'] = df['alem'] + df['san_javier'] + df['hulk_gym']
        df['Precio Hulk Gym'] = (df['precio_base'] / 0.9).round(2)
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            busqueda = st.text_input("🔍 Buscar por nombre o marca de producto:", "")
        with col_f2:
            cat_filtro = st.selectbox("Filtrar por categoria:", ["Todas"] + CATEGORIAS)

        df_filtrado = df.copy()
        if busqueda:
            criterio = busqueda.lower()
            df_filtrado = df_filtrado[
                df_filtrado['nombre'].str.lower().str.contains(criterio, na=False) | 
                df_filtrado['marca'].str.lower().str.contains(criterio, na=False)
            ]
        if cat_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == cat_filtro]

        columnas_inv = ['id', 'marca', 'nombre', 'categoria', 'sabor', 'presentacion', 'precio_base', 'Precio Hulk Gym', 'alem', 'san_javier', 'hulk_gym', 'Stock Total', 'stock_minimo']
        df_inv_view = df_filtrado[[col for col in columnas_inv if col in df_filtrado.columns]].rename(columns={'precio_base': 'Precio Base (Alem/S.Javier)', 'stock_minimo': 'Stock Mínimo'})
        st.dataframe(df_inv_view, use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos registrados.")

elif menu == "📥 Ingreso de Mercaderia":
    st.title("📥 Ingreso de Nueva Mercaderia")
    st.markdown("Registra entradas de stock desde proveedores seleccionando el punto de venta de destino.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_ingreso"):
            opciones_prod = {f"[{row.get('marca', 'Genérica')}] {row['nombre']} ({row['presentacion']} - {row['sabor']}) [ID: {row['id']}]": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            destino_ingreso = st.selectbox("Punto de Venta de destino:", list(UBICACIONES.keys()))
            key_ingreso = UBICACIONES[destino_ingreso]
            
            cantidad_ingreso = st.number_input("Cantidad a ingresar:", min_value=1, step=1, value=10)
            nota_ingreso = st.text_input("Observaciones / Proveedor (Opcional):", "Compra a proveedor")
            
            submit_ingreso = st.form_submit_button("Registrar Ingreso")
            
            if submit_ingreso:
                for p in st.session_state['productos']:
                    if p['id'] == prod_id:
                        p[key_ingreso] += cantidad_ingreso
                        st.session_state['historial_movimientos'].insert(0, {
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "tipo": "Ingreso Proveedor",
                            "producto": f"{p.get('marca', '')} {p['nombre']}".strip(),
                            "cantidad": cantidad_ingreso,
                            "destino": f"{destino_ingreso} (+{cantidad_ingreso})"
                        })
                        st.success(f"¡Ingreso registrado con exito! Se sumaron {cantidad_ingreso} unidades de {p['nombre']} a {destino_ingreso}.")
                        break
    else:
        st.warning("Primero debes dar de alta al menos un producto.")

elif menu == "🔄 Transferir entre Locales":
    st.title("🔄 Transferencia de Stock")
    st.markdown("Mueve mercaderia entre los diferentes puntos de venta.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_transferencia"):
            origen_nombre = st.selectbox("Origen (Enviar desde):", list(UBICACIONES.keys()))
            key_origen = UBICACIONES[origen_nombre]
            
            destinos_disponibles = [loc for loc in UBICACIONES.keys() if loc != origen_nombre]
            destino_nombre = st.selectbox("Destino (Enviar hacia):", destinos_disponibles)
            key_destino = UBICACIONES[destino_nombre]

            opciones_prod = {f"[{row.get('marca', 'Genérica')}] {row['nombre']} ({row['presentacion']}) - Stock en {origen_nombre}: {row[key_origen]}": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            prod_actual = next((p for p in st.session_state['productos'] if p['id'] == prod_id), None)
            
            cantidad_trans = st.number_input("Cantidad a transferir:", min_value=1, step=1, value=5)
            
            submit_trans = st.form_submit_button("Ejecutar Transferencia")
            
            if submit_trans:
                if prod_actual and prod_actual[key_origen] >= cantidad_trans:
                    prod_actual[key_origen] -= cantidad_trans
                    prod_actual[key_destino] += cantidad_trans
                    
                    st.session_state['historial_movimientos'].insert(0, {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": "Transferencia",
                        "producto": f"{prod_actual.get('marca', '')} {prod_actual['nombre']}".strip(),
                        "cantidad": cantidad_trans,
                        "destino": f"{origen_nombre} ➔ {destino_nombre}"
                    })
                    st.success(f"¡Transferencia exitosa! Se enviaron {cantidad_trans} unidades de {origen_nombre} a {destino_nombre}.")
                    st.rerun()
                else:
                    st.error(f"Error: Stock insuficiente en {origen_nombre} para realizar la transferencia.")
    else:
        st.warning("No hay productos disponibles para transferir.")

elif menu == "🛒 Registrar Venta":
    st.title("🛒 Registro de Ventas / Salidas")
    st.markdown("Descuenta stock y calcula el importe según el precio correspondiente al local.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_venta"):
            punto_venta = st.selectbox("Punto de Venta donde se efectua la venta:", list(UBICACIONES.keys()))
            key_pv = UBICACIONES[punto_venta]
            
            opciones_prod = {f"[{row.get('marca', 'Genérica')}] {row['nombre']} ({row['presentacion']}) - Stock en {punto_venta}: {row[key_pv]}": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            prod_actual = next((p for p in st.session_state['productos'] if p['id'] == prod_id), None)
            
            cantidad_venta = st.number_input("Cantidad vendida:", min_value=1, step=1, value=1)
            
            # Cálculo de precio unitario según ubicación (Hulk Gym = precio_base / 0.9)
            if prod_actual:
                precio_unitario = (prod_actual['precio_base'] / 0.9) if punto_venta == "Hulk Gym" else prod_actual['precio_base']
                total_venta = precio_unitario * cantidad_venta
                st.info(f"💵 **Precio unitario aplicado en {punto_venta}:** ${precio_unitario:,.2f} | **Total a cobrar:** ${total_venta:,.2f}")

            submit_venta = st.form_submit_button("Registrar Venta")
            
            if submit_venta:
                if prod_actual and prod_actual[key_pv] >= cantidad_venta:
                    prod_actual[key_pv] -= cantidad_venta
                    
                    st.session_state['historial_movimientos'].insert(0, {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": "Venta",
                        "producto": f"{prod_actual.get('marca', '')} {prod_actual['nombre']}".strip(),
                        "cantidad": cantidad_venta,
                        "destino": f"Venta en {punto_venta} (${total_venta:,.2f})"
                    })
                    st.success(f"¡Venta registrada con exito! Se descontaron {cantidad_venta} unidades en {punto_venta}. Total: ${total_venta:,.2f}")
                    st.rerun()
                else:
                    st.error(f"Error: No hay suficiente stock en {punto_venta} para completar esta venta.")
    else:
        st.warning("No hay productos registrados.")

elif menu == "➕ Nuevo Producto":
    st.title("➕ Alta de Nuevo Suplemento")
    st.markdown("Agrega un nuevo producto especificando su precio base y opción de stock mínimo (0 para desactivar alertas).")

    with st.form("form_nuevo_prod"):
        col1, col2 = st.columns(2)
        with col1:
            marca = st.text_input("Marca del Suplemento (Ej: Star Nutrition, ENA):", "Star Nutrition")
            nombre = st.text_input("Nombre del Suplemento:", "Whey Gold Standard")
            categoria = st.selectbox("Categoria:", CATEGORIAS)
            precio_base = st.number_input("Precio Base (para Alem y San Javier):", min_value=0.0, value=50000.0, step=100.0)
        with col2:
            sabor = st.text_input("Sabor:", "Chocolate")
            presentacion = st.text_input("Presentacion (Ej: 900g, 2kg, 60 caps):", "900 g")
            stock_minimo = st.number_input("Alerta de Stock Minimo por local (0 = Sin control):", min_value=0, value=0, step=1)
            
        id_prod = st.text_input("Codigo o SKU unico:", f"SUP-{len(st.session_state['productos'])+1:03d}")

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
                    "stock_minimo": stock_minimo
                }
                st.session_state['productos'].append(nuevo)
                st.session_state['historial_movimientos'].insert(0, {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tipo": "Alta Producto",
                    "producto": f"{marca} {nombre}".strip(),
                    "cantidad": init_alem + init_san_javier + init_hulk,
                    "destino": "Stock Inicial Global"
                })
                st.success(f"¡Producto '{marca} - {nombre}' creado exitosamente con Precio Base de ${precio_base:,.2f}!")

elif menu == "💾 Respaldos (Backup)":
    st.title("💾 Gestion de Respaldos de Datos")
    st.markdown("Exporta o importa toda la informacion de tu inventario en un archivo JSON para mantener tus datos seguros.")

    col_exp, col_imp = st.columns(2)

    with col_exp:
        st.subheader("📤 Exportar Datos")
        st.write("Descarga un archivo con todo el estado actual del stock y movimientos.")
        
        datos_respaldo = {
            "productos": st.session_state['productos'],
            "historial_movimientos": st.session_state['historial_movimientos']
        }
        json_str = json.dumps(datos_respaldo, indent=4, ensure_ascii=False)
        
        st.download_button(
            label="📥 Descargar Backup (JSON)",
            data=json_str,
            file_name=f"fitstore_backup_{datetime.now().strftime('%Y-%m-%d')}.json",
            mime="application/json"
        )

    with col_imp:
        st.subheader("📥 Importar Datos")
        st.write("Sube un archivo JSON previo para restaurar tu inventario.")
        
        archivo_subido = st.file_uploader("Selecciona tu archivo de respaldo (.json)", type=["json"])
        if archivo_subido is not None:
            try:
                datos_cargados = json.load(archivo_subido)
                if "productos" in datos_cargados and "historial_movimientos" in datos_cargados:
                    if st.button("Confirmar Restauracion"):
                        st.session_state['productos'] = datos_cargados['productos']
                        st.session_state['historial_movimientos'] = datos_cargados['historial_movimientos']
                        st.success("¡Datos restaurados con exito! Actualiza la pagina si es necesario.")
                else:
                    st.error("El archivo no tiene el formato correcto.")
            except Exception as e:
                st.error(f"Error al leer el archivo: {e}")

st.markdown("---")
with st.expander("📜 Ver Historial Reciente de Movimientos"):
    if st.session_state['historial_movimientos']:
        df_mov = pd.DataFrame(st.session_state['historial_movimientos'])
        st.dataframe(df_mov, use_container_width=True, hide_index=True)
    else:
        st.info("No hay movimientos registrados aun.")