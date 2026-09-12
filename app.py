import streamlit as st
import pandas as pd
import json
from datetime import datetime

# --- CONFIGURACION DE LA PAGINA ---
st.set_page_config(
    page_title="Suplix - Control de Stock",
    page_icon="💊",
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
    st.session_state['productos'] = [
        {
            "id": "SUP-001",
            "nombre": "Whey Protein 100% Isolate",
            "categoria": "Proteinas",
            "sabor": "Vainilla",
            "presentacion": "1 kg",
            "stock_central": 45,
            "local_1": 10,
            "local_2": 8,
            "local_3": 12,
            "stock_minimo": 5
        },
        {
            "id": "SUP-002",
            "nombre": "Creatina Monohidratada",
            "categoria": "Creatina",
            "sabor": "Neutro",
            "presentacion": "300 g",
            "stock_central": 60,
            "local_1": 15,
            "local_2": 20,
            "local_3": 10,
            "stock_minimo": 10
        },
        {
            "id": "SUP-003",
            "nombre": "Pre-Workout Explosion",
            "categoria": "Pre-Entreno",
            "sabor": "Frutos Rojos",
            "presentacion": "250 g",
            "stock_central": 25,
            "local_1": 5,
            "local_2": 4,
            "local_3": 6,
            "stock_minimo": 8
        }
    ]

if 'historial_movimientos' not in st.session_state:
    st.session_state['historial_movimientos'] = [
        {
            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
            "tipo": "Ingreso Inicial",
            "producto": "Whey Protein 100% Isolate",
            "cantidad": 75,
            "destino": "Todos los puntos"
        }
    ]

UBICACIONES = {
    "Deposito Central": "stock_central",
    "Local 1 (Centro)": "local_1",
    "Local 2 (Zona Norte)": "local_2",
    "Local 3 (Shopping)": "local_3"
}

CATEGORIAS = ["Proteinas", "Creatina", "Pre-Entreno", "Aminoacidos (BCAA)", "Vitaminas", "Accesorios"]

st.sidebar.title("💊 Suplix Stock Manager")
st.sidebar.markdown("---")
menu = st.sidebar.radio(
    "Navegacion",
    ["📊 Dashboard General", "📦 Inventario Completo", "📥 Ingreso de Mercaderia", "🔄 Transferir entre Locales", "🛒 Registrar Venta", "➕ Nuevo Producto", "💾 Respaldos (Backup)"]
)

st.sidebar.markdown("---")
st.sidebar.info("💡 **Consejo:** El Stock Total se calcula sumando automaticamente el Deposito Central y los 3 Puntos de Venta.")

if menu == "📊 Dashboard General":
    st.title("📊 Panel de Control General")
    st.markdown("Vista global del inventario en el Deposito Central y los 3 Puntos de Venta.")

    df = pd.DataFrame(st.session_state['productos'])
    
    if not df.empty:
        df['Stock Total'] = df['stock_central'] + df['local_1'] + df['local_2'] + df['local_3']
        
        total_central = df['stock_central'].sum()
        total_l1 = df['local_1'].sum()
        total_l2 = df['local_2'].sum()
        total_l3 = df['local_3'].sum()
        gran_total = df['Stock Total'].sum()

        col1, col2, col3, col4, col5 = st.columns(5)
        with col1:
            st.metric("📦 Stock General", f"{gran_total} un.")
        with col2:
            st.metric("🏢 Deposito Central", f"{total_central} un.")
        with col3:
            st.metric("🏬 Local 1", f"{total_l1} un.")
        with col4:
            st.metric("🏬 Local 2", f"{total_l2} un.")
        with col5:
            st.metric("🏬 Local 3", f"{total_l3} un.")

        st.markdown("---")

        st.subheader("⚠️ Alertas de Stock Bajo")
        alertas = []
        for index, row in df.iterrows():
            for loc_nombre, loc_key in UBICACIONES.items():
                if row[loc_key] <= row['stock_minimo']:
                    alertas.append({
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
            st.success("¡Excelente! No hay productos con stock critico en ninguna ubicacion.")

        st.markdown("---")
        st.subheader("📋 Resumen Rapido por Producto")
        vista_resumen = df[['id', 'nombre', 'categoria', 'sabor', 'presentacion', 'stock_central', 'local_1', 'local_2', 'local_3', 'Stock Total']]
        st.dataframe(vista_resumen, use_container_width=True, hide_index=True)

    else:
        st.warning("No hay productos cargados todavia. Dirigete a 'Nuevo Producto' para empezar.")

elif menu == "📦 Inventario Completo":
    st.title("📦 Inventario Detallado por Ubicacion")
    st.markdown("Consulta y filtrado de todos los suplementos en stock.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        df['Stock Total'] = df['stock_central'] + df['local_1'] + df['local_2'] + df['local_3']
        
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            busqueda = st.text_input("🔍 Buscar por nombre de producto:", "")
        with col_f2:
            cat_filtro = st.selectbox("Filtrar por categoria:", ["Todas"] + CATEGORIAS)

        df_filtrado = df.copy()
        if busqueda:
            df_filtrado = df_filtrado[df_filtrado['nombre'].str.contains(busqueda, case=False, na=False)]
        if cat_filtro != "Todas":
            df_filtrado = df_filtrado[df_filtrado['categoria'] == cat_filtro]

        st.dataframe(df_filtrado, use_container_width=True, hide_index=True)
    else:
        st.info("No hay productos registrados.")

elif menu == "📥 Ingreso de Mercaderia":
    st.title("📥 Ingreso de Nueva Mercaderia")
    st.markdown("Registra entradas de stock desde proveedores directamente al **Deposito Central**.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_ingreso"):
            opciones_prod = {f"{row['nombre']} ({row['presentacion']} - {row['sabor']}) [ID: {row['id']}]": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            cantidad_ingreso = st.number_input("Cantidad a ingresar en Deposito Central:", min_value=1, step=1, value=10)
            nota_ingreso = st.text_input("Observaciones / Proveedor (Opcional):", "Compra a proveedor")
            
            submit_ingreso = st.form_submit_button("Registrar Ingreso")
            
            if submit_ingreso:
                for p in st.session_state['productos']:
                    if p['id'] == prod_id:
                        p['stock_central'] += cantidad_ingreso
                        st.session_state['historial_movimientos'].insert(0, {
                            "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                            "tipo": "Ingreso Proveedor",
                            "producto": p['nombre'],
                            "cantidad": cantidad_ingreso,
                            "destino": f"Deposito Central (+{cantidad_ingreso})"
                        })
                        st.success(f"¡Ingreso registrado con exito! Se sumaron {cantidad_ingreso} unidades de {p['nombre']} al Deposito Central.")
                        break
    else:
        st.warning("Primero debes dar de alta al menos un producto.")

elif menu == "🔄 Transferir entre Locales":
    st.title("🔄 Transferencia de Stock")
    st.markdown("Mueve mercaderia desde el **Deposito Central** hacia cualquiera de los 3 Puntos de Venta.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_transferencia"):
            opciones_prod = {f"{row['nombre']} ({row['presentacion']}) - Stock Central: {row['stock_central']}": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            prod_actual = next((p for p in st.session_state['productos'] if p['id'] == prod_id), None)
            
            destino_nombre = st.selectbox("Enviar hacia:", ["Local 1 (Centro)", "Local 2 (Zona Norte)", "Local 3 (Shopping)"])
            cantidad_trans = st.number_input("Cantidad a transferir:", min_value=1, step=1, value=5)
            
            submit_trans = st.form_submit_button("Ejecutar Transferencia")
            
            if submit_trans:
                if prod_actual and prod_actual['stock_central'] >= cantidad_trans:
                    key_destino = UBICACIONES[destino_nombre]
                    prod_actual['stock_central'] -= cantidad_trans
                    prod_actual[key_destino] += cantidad_trans
                    
                    st.session_state['historial_movimientos'].insert(0, {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": "Transferencia",
                        "producto": prod_actual['nombre'],
                        "cantidad": cantidad_trans,
                        "destino": f"Deposito Central ➔ {destino_nombre}"
                    })
                    st.success(f"¡Transferencia exitosa! Se enviaron {cantidad_trans} unidades a {destino_nombre}.")
                    st.rerun()
                else:
                    st.error("Error: Stock insuficiente en el Deposito Central para realizar la transferencia.")
    else:
        st.warning("No hay productos disponibles para transferir.")

elif menu == "🛒 Registrar Venta":
    st.title("🛒 Registro de Ventas / Salidas")
    st.markdown("Descuenta stock directamente desde el punto de venta donde se realizo la venta al cliente.")

    df = pd.DataFrame(st.session_state['productos'])
    if not df.empty:
        with st.form("form_venta"):
            punto_venta = st.selectbox("Punto de Venta donde se efectua la venta:", ["Local 1 (Centro)", "Local 2 (Zona Norte)", "Local 3 (Shopping)", "Deposito Central"])
            key_pv = UBICACIONES[punto_venta]
            
            opciones_prod = {f"{row['nombre']} ({row['presentacion']}) - Stock en {punto_venta}: {row[key_pv]}": row['id'] for index, row in df.iterrows()}
            prod_seleccionado_str = st.selectbox("Seleccionar Producto:", list(opciones_prod.keys()))
            prod_id = opciones_prod[prod_seleccionado_str]
            
            prod_actual = next((p for p in st.session_state['productos'] if p['id'] == prod_id), None)
            
            cantidad_venta = st.number_input("Cantidad vendida:", min_value=1, step=1, value=1)
            
            submit_venta = st.form_submit_button("Registrar Venta")
            
            if submit_venta:
                if prod_actual and prod_actual[key_pv] >= cantidad_venta:
                    prod_actual[key_pv] -= cantidad_venta
                    
                    st.session_state['historial_movimientos'].insert(0, {
                        "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                        "tipo": "Venta",
                        "producto": prod_actual['nombre'],
                        "cantidad": cantidad_venta,
                        "destino": f"Venta en {punto_venta}"
                    })
                    st.success(f"¡Venta registrada con exito! Se descontaron {cantidad_venta} unidades en {punto_venta}.")
                    st.rerun()
                else:
                    st.error(f"Error: No hay suficiente stock en {punto_venta} para completar esta venta.")
    else:
        st.warning("No hay productos registrados.")

elif menu == "➕ Nuevo Producto":
    st.title("➕ Alta de Nuevo Suplemento")
    st.markdown("Agrega un nuevo producto al catalogo general especificando su stock inicial.")

    with st.form("form_nuevo_prod"):
        col1, col2 = st.columns(2)
        with col1:
            nombre = st.text_input("Nombre del Suplemento:", "Whey Gold Standard")
            categoria = st.selectbox("Categoria:", CATEGORIAS)
            sabor = st.text_input("Sabor:", "Chocolate")
        with col2:
            presentacion = st.text_input("Presentacion (Ej: 900g, 2kg, 60 caps):", "900 g")
            stock_minimo = st.number_input("Alerta de Stock Minimo por local:", min_value=1, value=5, step=1)
            id_prod = st.text_input("Codigo o SKU unico:", f"SUP-{len(st.session_state['productos'])+1:03d}")

        st.markdown("### Stock Inicial por Ubicacion")
        col_s1, col_s2, col_s3, col_s4 = st.columns(4)
        with col_s1:
            init_central = st.number_input("Deposito Central", min_value=0, value=20, step=1)
        with col_s2:
            init_l1 = st.number_input("Local 1", min_value=0, value=5, step=1)
        with col_s3:
            init_l2 = st.number_input("Local 2", min_value=0, value=5, step=1)
        with col_s4:
            init_l3 = st.number_input("Local 3", min_value=0, value=5, step=1)

        submit_nuevo = st.form_submit_button("Guardar Nuevo Producto")

        if submit_nuevo:
            if nombre.strip() == "":
                st.error("El nombre del producto no puede estar vacio.")
            else:
                nuevo = {
                    "id": id_prod,
                    "nombre": nombre,
                    "categoria": categoria,
                    "sabor": sabor,
                    "presentacion": presentacion,
                    "stock_central": init_central,
                    "local_1": init_l1,
                    "local_2": init_l2,
                    "local_3": init_l3,
                    "stock_minimo": stock_minimo
                }
                st.session_state['productos'].append(nuevo)
                st.session_state['historial_movimientos'].insert(0, {
                    "fecha": datetime.now().strftime("%Y-%m-%d %H:%M"),
                    "tipo": "Alta Producto",
                    "producto": nombre,
                    "cantidad": init_central + init_l1 + init_l2 + init_l3,
                    "destino": "Stock Inicial Global"
                })
                st.success(f"¡Producto '{nombre}' creado exitosamente!")

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
            file_name=f"suplix_backup_{datetime.now().strftime('%Y-%m-%d')}.json",
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