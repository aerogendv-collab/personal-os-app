import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
import io
import random
import threading
from datetime import date, datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Personal OS", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# --- CONFIGURACIÓN DE USUARIO (RELLENAR) ---
# ==========================================

FOLDER_ID_PHOTOS = "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L" 
EMAIL_CALENDAR = "aerogendv@gmail.com" 

FONDOS = {
    "🏠 Inicio & Dashboard": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
    "🧠 Diario": "https://images.unsplash.com/photo-1517816743773-6e0fd5ce9464",
    "💪 Deporte": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438",
    "🥗 Alimentación": "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
    "📚 Lectura": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f",
    "💡 Ideas/Proyectos": "https://images.unsplash.com/photo-1493612276216-ee3925520721",
    "🎬 Watchlist/Wishlist": "https://images.unsplash.com/photo-1485846234645-a62644f84728",
    "🤝 Personal CRM": "https://images.unsplash.com/photo-1521791136064-7986c2920216",
    "✈️ Viajes": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05",
    "👔 Outfits": "https://images.unsplash.com/photo-1489987707023-afcb1e97d19c",
    "✨ Pareja/Escapadas": "https://images.unsplash.com/photo-1518199266791-5375a83190b7",
    "💰 Finanzas": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c",
    "📅 Recordatorios": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe",
    "Default": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
}

# ==========================================
# --- ESTADO Y NAVEGACIÓN ---
# ==========================================
secciones = list(FONDOS.keys())
secciones.remove("Default")
secciones.append("🗑️ Gestionar Datos")

if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "🏠 Inicio & Dashboard"
if 'memoria_datos' not in st.session_state:
    st.session_state.memoria_datos = {} # Caché profunda RAM

def ir_a(nombre_seccion):
    st.session_state.seccion_activa = nombre_seccion
    st.rerun()

st.sidebar.title("🚀 Personal OS")
seccion = st.sidebar.radio("Navegación:", secciones, index=secciones.index(st.session_state.seccion_activa))
st.session_state.seccion_activa = seccion

# ==========================================
# --- CONEXIÓN A GOOGLE (OPTIMIZADA) ---
# ==========================================
@st.cache_resource
def obtener_credenciales_gcp():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    scopes = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive', 'https://www.googleapis.com/auth/calendar']
    return ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)

creds = obtener_credenciales_gcp()

try:
    client = gspread.authorize(creds)
    sheet = client.open("Mi_Personal_OS")
    db_conectada = True
except Exception as e:
    db_conectada = False

def cargar_datos(nombre_pestaña, forzar_actualizacion=False):
    """Carga desde la memoria RAM si existe, si no, va a Google."""
    if not db_conectada: return pd.DataFrame()
    
    if forzar_actualizacion or nombre_pestaña not in st.session_state.memoria_datos:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            df = pd.DataFrame(worksheet.get_all_records())
            st.session_state.memoria_datos[nombre_pestaña] = df
        except:
            st.session_state.memoria_datos[nombre_pestaña] = pd.DataFrame()
            
    return st.session_state.memoria_datos[nombre_pestaña]

def guardar_datos(nombre_pestaña, nuevos_datos):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        worksheet.append_row(list(nuevos_datos.values()))
        cargar_datos(nombre_pestaña, forzar_actualizacion=True) # Actualiza RAM
        return True
    return False

def eliminar_registro(nombre_pestaña, indice_fila):
    if db_conectada:
        try:
            sheet.worksheet(nombre_pestaña).delete_rows(indice_fila)
            cargar_datos(nombre_pestaña, forzar_actualizacion=True)
            return True
        except: return False
    return False

# Funciones de Google (Drive y Calendar)
def subir_foto_background(archivo_bytes, nombre_foto):
    """Hilo en segundo plano para no congelar la app"""
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': nombre_foto, 'parents': [FOLDER_ID_PHOTOS]}
        media = MediaIoBaseUpload(io.BytesIO(archivo_bytes), mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
    except Exception as e:
        print(f"Error subiendo foto: {e}")

def crear_evento_calendar(titulo, fecha, descripcion=""):
    try:
        service = build('calendar', 'v3', credentials=creds)
        evento = {'summary': titulo, 'description': descripcion, 'start': {'date': fecha.strftime("%Y-%m-%d")}, 'end': {'date': fecha.strftime("%Y-%m-%d")}}
        return service.events().insert(calendarId=EMAIL_CALENDAR, body=evento).execute().get('htmlLink')
    except: return None

# ==========================================
# --- INTERFAZ Y GLOBALES ---
# ==========================================
def establecer_fondo(seccion_actual):
    url = FONDOS.get(seccion_actual, FONDOS["Default"])
    st.markdown(f"""<style>.stApp {{ background-image: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{url}"); background-size: cover; background-attachment: fixed; background-position: center; }} .stMarkdown, .stText, h1, h2, h3, p, label {{ color: white !important; }} </style>""", unsafe_allow_html=True)

def mostrar_historial(nombre_pestaña):
    st.divider()
    with st.expander(f"📂 Ver mi historial de {nombre_pestaña}"):
        df = cargar_datos(nombre_pestaña)
        if not df.empty: st.dataframe(df, use_container_width=True)
        else: st.info(f"Aún no tienes registros guardados en {nombre_pestaña}.")

establecer_fondo(st.session_state.seccion_activa)
fecha_hoy_str = date.today().strftime("%Y-%m-%d")

# ==========================================
# --- MÓDULOS Y SECCIONES ---
# ==========================================

if st.session_state.seccion_activa == "🏠 Inicio & Dashboard":
    st.title("Centro de Mando Personal")
    
    # --- MÓDULO ALTO VALOR 1: METAS ANUALES (OKRs) ---
    st.subheader("🎯 Mis Metas del Año")
    df_metas = cargar_datos("Metas")
    
    with st.expander("Añadir nueva meta"):
        nueva_meta = st.text_input("Objetivo principal (Ej: Ahorrar 5000€):")
        if st.button("Guardar Meta"):
            guardar_datos("Metas", {"Fecha": fecha_hoy_str, "Meta": nueva_meta, "Estado": "En progreso"})
            st.rerun()

    if not df_metas.empty:
        for idx, row in df_metas.iterrows():
            st.checkbox(row['Meta'], value=(row.get('Estado') == 'Completada'), key=f"meta_{idx}", disabled=True)
    else: st.write("*No hay metas definidas aún.*")

    st.divider()
    
    # --- MÓDULO ALTO VALOR 2 & SINERGIA: DASHBOARD FINANCIERO Y CORRELACIÓN ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("💰 Resumen Financiero")
        df_fin = cargar_datos("Finanzas")
        if not df_fin.empty:
            # Limpiamos datos para cálculos matemáticos
            df_fin['Cantidad'] = pd.to_numeric(df_fin['Cantidad'].astype(str).str.replace(',', '.'), errors='coerce').fillna(0)
            ingresos = df_fin[df_fin['Tipo'].str.contains('Ingreso')]['Cantidad'].sum()
            gastos = df_fin[df_fin['Tipo'].str.contains('Gasto')]['Cantidad'].sum()
            balance = ingresos - gastos
            
            st.metric(label="Balance Total", value=f"{balance:.2f} €", delta=f"{ingresos:.2f} Ingresos | {gastos:.2f} Gastos")
            # Gráfico visual de finanzas nativo de Streamlit
            df_grafico = pd.DataFrame({"Ingresos": [ingresos], "Gastos": [gastos]}, index=["Total"])
            st.bar_chart(df_grafico)
        else:
            st.info("Registra ingresos/gastos para ver tu gráfico.")

    with col2:
        st.subheader("🧠 vs 💪 Sinergia Diario-Deporte")
        df_diario = cargar_datos("Diario")
        df_deporte = cargar_datos("Deporte")
        
        if not df_diario.empty and not df_deporte.empty:
            dias_deporte = df_deporte['Fecha'].tolist()
            # Filtramos el diario: días que hicimos deporte vs días que no
            df_diario['Hizo_Deporte'] = df_diario['Fecha'].isin(dias_deporte)
            
            altos_con_deporte = len(df_diario[(df_diario['Hizo_Deporte'] == True) & (df_diario['Ánimo'].isin(['Alta', 'Imparable']))])
            altos_sin_deporte = len(df_diario[(df_diario['Hizo_Deporte'] == False) & (df_diario['Ánimo'].isin(['Alta', 'Imparable']))])
            
            st.write("📊 **Impacto del ejercicio en tu ánimo:**")
            st.write(f"Días de energía Alta/Imparable habiendo hecho deporte: **{altos_con_deporte}**")
            st.write(f"Días de energía Alta/Imparable sin hacer deporte: **{altos_sin_deporte}**")
            if altos_con_deporte > altos_sin_deporte:
                st.success("¡El deporte está afectando positivamente a tu energía!")
        else:
            st.info("Necesitas datos en el Diario y en Deporte para ver la correlación.")

    st.divider()
    st.write("### Accesos Rápidos")
    c1, c2, c3, c4 = st.columns(4)
    with c1: 
        if st.button("🧠 Diario", use_container_width=True): ir_a("🧠 Diario")
    with c2: 
        if st.button("💪 Deporte", use_container_width=True): ir_a("💪 Deporte")
    with c3: 
        if st.button("💰 Gasto", use_container_width=True): ir_a("💰 Finanzas")
    with c4:
        if st.button("🎬 Watchlist", use_container_width=True): ir_a("🎬 Watchlist/Wishlist")

elif st.session_state.seccion_activa == "🧠 Diario":
    st.title("🧠 Diario y Reflexión")
    animo = st.select_slider("Energía de hoy:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar en la nube"):
        if pensamientos:
            guardar_datos("Diario", {"Fecha": fecha_hoy_str, "Ánimo": animo, "Pensamientos": pensamientos})
            st.success("¡Guardado!")
    mostrar_historial("Diario")

elif st.session_state.seccion_activa == "💪 Deporte":
    st.title("💪 Registro Deportivo")
    tipo = st.selectbox("Actividad:", ["Futbol", "Padel", "Correr", "Bici", "Gimnasio", "Otro"])
    duracion = st.number_input("Minutos:", min_value=1, value=45)
    if st.button("Registrar Entrenamiento"):
        guardar_datos("Deporte", {"Fecha": fecha_hoy_str, "Actividad": tipo, "Minutos": str(duracion)})
        st.success("¡Entrenamiento registrado!")
    mostrar_historial("Deporte")

elif st.session_state.seccion_activa == "🥗 Alimentación":
    st.title("🥗 Control de Deslices")
    alimento_insano = st.text_input("¿Qué comiste insano?")
    alimento_sano_evitado = st.text_input("¿Qué alimento sano evitaste?")
    if st.button("Registrar Deslice"):
        if alimento_insano and alimento_sano_evitado:
            guardar_datos("Alimentación", {"Fecha": fecha_hoy_str, "Comida Insana": alimento_insano, "Sano Evitado": alimento_sano_evitado})
            st.success("Deslice registrado.")
    mostrar_historial("Alimentación")

elif st.session_state.seccion_activa == "📚 Lectura":
    st.title("📚 Mi Biblioteca")
    titulo = st.text_input("Título del libro:")
    fecha_inicio = st.date_input("Fecha de inicio:")
    fecha_fin = st.date_input("Fecha fin (vacío si estás leyendo):", value=None)
    if st.button("Guardar Libro"):
        if titulo:
            f_fin_str = fecha_fin.strftime("%Y-%m-%d") if fecha_fin else ""
            guardar_datos("Lectura", {"Título": titulo, "Fecha Inicio": fecha_inicio.strftime("%Y-%m-%d"), "Fecha Fin": f_fin_str})
            st.success("¡Libro guardado!")
    mostrar_historial("Lectura")

elif st.session_state.seccion_activa == "💡 Ideas/Proyectos":
    st.title("💡 Lluvia de Ideas")
    idea = st.text_input("Título de la idea/proyecto:")
    descripcion = st.text_area("Descripción:")
    if st.button("Capturar Idea"):
        if idea:
            guardar_datos("Ideas", {"Fecha": fecha_hoy_str, "Idea/Proyecto": idea, "Descripción": descripcion})
            st.success("¡Idea capturada!")
    mostrar_historial("Ideas")

elif st.session_state.seccion_activa == "🎬 Watchlist/Wishlist":
    st.title("🎬 Watchlist & Wishlist")
    tipo = st.selectbox("Categoría:", ["Película/Serie 🍿", "Producto/Capricho 💸", "Libro/Curso 🎓", "Lugar 🗺️"])
    nombre = st.text_input("Nombre del item:")
    precio = st.text_input("Precio estimado (€):")
    porque = st.text_area("¿Por qué lo quieres?")
    
    if st.button("Añadir a la lista"):
        if nombre:
            guardar_datos("Watchlist", {"Fecha": fecha_hoy_str, "Tipo": tipo, "Item": nombre, "Precio": precio, "Notas": porque})
            st.success("¡Añadido!")
            
    # --- SINERGIA: WATCHLIST -> FINANZAS ---
    st.divider()
    st.subheader("🛍️ ¿Compraste algo de tu Wishlist?")
    df_w = cargar_datos("Watchlist")
    if not df_w.empty:
        items_compra = df_w[df_w['Tipo'].str.contains('Producto/Capricho')]['Item'].tolist()
        if items_compra:
            item_comprado = st.selectbox("Selecciona qué te has comprado:", items_compra)
            if st.button("¡Lo he comprado! Mover a Finanzas"):
                # 1. Buscamos el precio original y la fila para borrarla
                fila_datos = df_w[df_w['Item'] == item_comprado].iloc[0]
                fila_index = int(df_w[df_w['Item'] == item_comprado].index[0]) + 2
                precio_estimado = fila_datos['Precio'] if fila_datos['Precio'] != "" else "0"
                
                # 2. Guardamos en Finanzas
                guardar_datos("Finanzas", {"Fecha": fecha_hoy_str, "Tipo": "Gasto 📉", "Categoría": "Capricho/Wishlist", "Cantidad": str(precio_estimado), "Concepto": item_comprado})
                # 3. Borramos de Watchlist
                eliminar_registro("Watchlist", fila_index)
                st.success(f"¡Hecho! '{item_comprado}' eliminado de la Wishlist y registrado como Gasto.")
                st.rerun()

    mostrar_historial("Watchlist")

elif st.session_state.seccion_activa == "🤝 Personal CRM":
    st.title("🤝 Personal CRM (Networking)")
    nombre_p = st.text_input("Nombre de la persona:")
    donde = st.text_input("¿Dónde os conocisteis?")
    intereses = st.text_input("Intereses:")
    notas_p = st.text_area("Notas importantes:")
    
    # --- SINERGIA: CRM -> CALENDAR ---
    recordatorio = st.checkbox("📅 Crear recordatorio en Google Calendar para escribirle en 1 semana")
    
    if st.button("Guardar Contacto"):
        if nombre_p:
            guardar_datos("CRM", {"Fecha": fecha_hoy_str, "Nombre": nombre_p, "Contexto": donde, "Intereses": intereses, "Notas": notas_p})
            st.success("Contacto guardado.")
            if recordatorio:
                fecha_recordatorio = date.today() + timedelta(days=7)
                link = crear_evento_calendar(f"Escribir a {nombre_p}", fecha_recordatorio, f"Le conociste en: {donde}. Notas: {notas_p}")
                if link: st.info(f"Recordatorio creado en Calendar para el {fecha_recordatorio}.")
    mostrar_historial("CRM")

elif st.session_state.seccion_activa == "✈️ Viajes":
    st.title("✈️ Bitácora de Viajes")
    destino = st.text_input("Destino:")
    periodo = st.text_input("Periodo:")
    monumentos = st.text_area("Monumentos visitados:")
    restaurantes = st.text_area("Restaurantes:")
    if st.button("Guardar Viaje"):
        if destino:
            guardar_datos("Viajes", {"Fecha Registro": fecha_hoy_str, "Destino": destino, "Periodo": periodo, "Sitios": monumentos, "Comida": restaurantes})
            st.success("¡Viaje registrado!")
    mostrar_historial("Viajes")

elif st.session_state.seccion_activa == "👔 Outfits":
    st.title("👔 Gestor de Outfits")
    nombre_outfit = st.text_input("Nombre del conjunto:")
    foto_subida = st.file_uploader("Sube foto:", type=['jpg', 'jpeg', 'png'])
    
    # --- RENDIMIENTO: HILOS PARA SUBIDA EN SEGUNDO PLANO ---
    if st.button("Subir Outfit"):
        if nombre_outfit and foto_subida:
            nombre_archivo = f"outfit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg"
            bytes_img = foto_subida.getvalue() # Leer antes de lanzar el hilo
            
            # Lanzamos la subida a Drive en segundo plano para no bloquear al usuario
            thread = threading.Thread(target=subir_foto_background, args=(bytes_img, nombre_archivo))
            thread.start()
            
            # Guardamos el texto inmediatamente en la BBDD (asumiendo que se subirá)
            # Nota: No tendremos el link web exacto de Drive al instante, pondremos el nombre.
            guardar_datos("Outfits", {"Fecha": fecha_hoy_str, "Nombre Outfit": nombre_outfit, "Archivo de Drive": nombre_archivo})
            st.success("¡El conjunto se está subiendo en segundo plano! Puedes seguir usando la aplicación.")
        else:
            st.warning("Falta nombre o foto.")
    mostrar_historial("Outfits")

elif st.session_state.seccion_activa == "✨ Pareja/Escapadas":
    st.title("✨ Nuestras Escapadas")
    lugar = st.text_input("Lugar:")
    fecha_escapada = st.date_input("Fecha:")
    que_hicimos = st.text_area("¿Qué hicimos?")
    if st.button("Guardar Recuerdo"):
        if lugar:
            guardar_datos("Pareja", {"Fecha Registro": fecha_hoy_str, "Lugar": lugar, "Fecha Escapada": fecha_escapada.strftime("%Y-%m-%d"), "Detalles": que_hicimos})
            st.success("¡Recuerdo guardado!")
    mostrar_historial("Pareja")

elif st.session_state.seccion_activa == "💰 Finanzas":
    st.title("💰 Control de Finanzas")
    col1, col2 = st.columns(2)
    with col1:
        tipo_movimiento = st.radio("Tipo:", ["Gasto 📉", "Ingreso 📈"], horizontal=True)
        cantidad = st.number_input("Cantidad (€):", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        categoria = st.text_input("Etiqueta (ej: Comida, Sueldo):")
        concepto = st.text_input("Concepto:")
        
    if st.button("Registrar Movimiento"):
        if categoria and cantidad > 0:
            guardar_datos("Finanzas", {"Fecha": fecha_hoy_str, "Tipo": tipo_movimiento, "Categoría": categoria, "Cantidad": str(cantidad), "Concepto": concepto})
            st.success("¡Movimiento registrado!")
    mostrar_historial("Finanzas")

elif st.session_state.seccion_activa == "📅 Recordatorios":
    st.title("📅 Enviar a Google Calendar")
    tit_rec = st.text_input("Título del recordatorio:")
    fecha_rec = st.date_input("Día:")
    desc_rec = st.text_area("Detalles:")
    
    if st.button("Añadir a mi Calendario"):
        if tit_rec:
            enlace = crear_evento_calendar(tit_rec, fecha_rec, desc_rec)
            if enlace:
                guardar_datos("Recordatorios", {"Fecha Creación": fecha_hoy_str, "Fecha Evento": fecha_rec.strftime("%Y-%m-%d"), "Título": tit_rec})
                st.success("✅ ¡Añadido a Calendar!")
                st.link_button("Ver", enlace)
    mostrar_historial("Recordatorios")

elif st.session_state.seccion_activa == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    categorias = ["Metas", "Diario", "Deporte", "Alimentación", "Lectura", "Ideas", "Watchlist", "CRM", "Viajes", "Outfits", "Pareja", "Finanzas", "Recordatorios"]
    categoria_seleccionada = st.selectbox("Selecciona la categoría:", categorias)
    st.divider()
    df = cargar_datos(categoria_seleccionada)
    
    if not df.empty:
        df['Fila_Excel'] = df.index + 2 
        st.dataframe(df, use_container_width=True)
        opciones = [f"Fila {row['Fila_Excel']} ➔ {row.tolist()[0]} | {row.tolist()[1] if len(row.tolist())>1 else ''}" for _, row in df.iterrows()]
        seleccion = st.selectbox("Elige el registro a eliminar:", opciones)
        
        if st.button("🚨 Eliminar Definitivamente"):
            fila_a_borrar = int(seleccion.split(" ")[1])
            if eliminar_registro(categoria_seleccionada, fila_a_borrar):
                st.success("¡Borrado con éxito!")
                st.rerun()
    else:
        st.info("No hay datos aquí.")
