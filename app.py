import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
import io
import random
from datetime import date, datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Personal OS", page_icon="🚀", layout="wide", initial_sidebar_state="expanded")

# ==========================================
# --- CONFIGURACIÓN DE USUARIO (RELLENAR) ---
# ==========================================

FOLDER_ID_PHOTOS = "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L" 
EMAIL_CALENDAR = "aerogendv@gmail.com" 

FONDOS = {
    "🏠 Inicio": "https://images.unsplash.com/photo-1451187580459-43490279c0fa",
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
# --- SISTEMA DE NAVEGACIÓN ---
# ==========================================
secciones = list(FONDOS.keys())
secciones.remove("Default")
secciones.append("🗑️ Gestionar Datos")

if 'seccion_activa' not in st.session_state:
    st.session_state.seccion_activa = "🏠 Inicio"

def ir_a(nombre_seccion):
    st.session_state.seccion_activa = nombre_seccion
    st.rerun()

st.sidebar.title("🚀 Personal OS")
seccion = st.sidebar.radio("Navegación:", secciones, index=secciones.index(st.session_state.seccion_activa))
st.session_state.seccion_activa = seccion

# ==========================================
# --- CONFIGURACIÓN DE GOOGLE Y CACHÉ ---
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
    st.error(f"⚠️ Error de conexión a BD: {e}")
    db_conectada = False

def guardar_datos(nombre_pestaña, nuevos_datos):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        worksheet.append_row(list(nuevos_datos.values()))
        st.cache_data.clear() # Limpia caché al guardar
        return True
    return False

@st.cache_data(ttl=60)
def cargar_datos(nombre_pestaña):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            return pd.DataFrame(worksheet.get_all_records())
        except: return pd.DataFrame()
    return pd.DataFrame()

def eliminar_registro(nombre_pestaña, indice_fila):
    if db_conectada:
        try:
            sheet.worksheet(nombre_pestaña).delete_rows(indice_fila)
            st.cache_data.clear() # Limpia caché al borrar
            return True
        except: return False
    return False

def subir_foto_a_drive(archivo_imagen, nombre_foto):
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': nombre_foto, 'parents': [FOLDER_ID_PHOTOS]}
        media = MediaIoBaseUpload(io.BytesIO(archivo_imagen.getvalue()), mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except: return None

def crear_evento_calendar(titulo, fecha, descripcion=""):
    try:
        service = build('calendar', 'v3', credentials=creds)
        evento = {'summary': titulo, 'description': descripcion, 'start': {'date': fecha.strftime("%Y-%m-%d")}, 'end': {'date': fecha.strftime("%Y-%m-%d")}}
        return service.events().insert(calendarId=EMAIL_CALENDAR, body=evento).execute().get('htmlLink')
    except: return None

# ==========================================
# --- FUNCIONES DE INTERFAZ ---
# ==========================================

def establecer_fondo(seccion_actual):
    url = FONDOS.get(seccion_actual, FONDOS["Default"])
    st.markdown(f"""<style>.stApp {{ background-image: linear-gradient(rgba(0,0,0,0.75), rgba(0,0,0,0.75)), url("{url}"); background-size: cover; background-attachment: fixed; background-position: center; }} .stMarkdown, .stText, h1, h2, h3, p, label {{ color: white !important; }} </style>""", unsafe_allow_html=True)

def mostrar_historial(nombre_pestaña):
    st.divider()
    with st.expander(f"📂 Ver mi historial de {nombre_pestaña}"):
        df = cargar_datos(nombre_pestaña)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"Aún no tienes registros guardados en {nombre_pestaña}.")

establecer_fondo(st.session_state.seccion_activa)
fecha_hoy = date.today().strftime("%Y-%m-%d")

# ==========================================
# --- SECCIONES DE LA APLICACIÓN ---
# ==========================================

if st.session_state.seccion_activa == "🏠 Inicio":
    st.title("¡Bienvenido a tu Personal OS!")
    
    frases = [
        "El éxito es la suma de pequeños esfuerzos repetidos día tras día.",
        "No cuentes los días, haz que los días cuenten.",
        "La mejor forma de predecir el futuro es creándolo.",
        "Tu tiempo es limitado, no lo malgastes viviendo la vida de otro.",
        "Enfócate en ser productivo, no en estar ocupado."
    ]
    st.subheader(f"✨ _{random.choice(frases)}_")
    st.divider()
    
    st.write("### ¿A dónde quieres ir hoy?")
    cols = st.columns(3)
    
    with cols[0]:
        if st.button("🧠 Escribir Diario", use_container_width=True): ir_a("🧠 Diario")
        if st.button("💪 Registrar Deporte", use_container_width=True): ir_a("💪 Deporte")
        if st.button("🎬 Watchlist/Wishlist", use_container_width=True): ir_a("🎬 Watchlist/Wishlist")

    with cols[1]:
        if st.button("💰 Registrar Gasto", use_container_width=True): ir_a("💰 Finanzas")
        if st.button("📚 Mi Biblioteca", use_container_width=True): ir_a("📚 Lectura")
        if st.button("🤝 Contactos CRM", use_container_width=True): ir_a("🤝 Personal CRM")

    with cols[2]:
        if st.button("💡 Nuevas Ideas", use_container_width=True): ir_a("💡 Ideas/Proyectos")
        if st.button("📅 Agendar Recordatorio", use_container_width=True): ir_a("📅 Recordatorios")
        if st.button("👔 Elegir Outfit", use_container_width=True): ir_a("👔 Outfits")

elif st.session_state.seccion_activa == "🧠 Diario":
    st.title("🧠 Diario y Reflexión")
    animo = st.select_slider("Energía de hoy:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar en la nube"):
        if pensamientos:
            guardar_datos("Diario", {"Fecha": fecha_hoy, "Ánimo": animo, "Pensamientos": pensamientos})
            st.success("¡Guardado!")
    mostrar_historial("Diario")

elif st.session_state.seccion_activa == "💪 Deporte":
    st.title("💪 Registro Deportivo")
    tipo = st.selectbox("Actividad:", ["Futbol", "Padel", "Correr", "Bici", "Gimnasio", "Otro"])
    duracion = st.number_input("Minutos:", min_value=1, value=45)
    if st.button("Registrar Entrenamiento"):
        guardar_datos("Deporte", {"Fecha": fecha_hoy, "Actividad": tipo, "Minutos": str(duracion)})
        st.success("¡Entrenamiento registrado!")
    mostrar_historial("Deporte")

elif st.session_state.seccion_activa == "🥗 Alimentación":
    st.title("🥗 Control de Deslices")
    alimento_insano = st.text_input("¿Qué comiste insano?")
    alimento_sano_evitado = st.text_input("¿Qué alimento o bebida sana evitaste?")
    if st.button("Registrar Deslice"):
        if alimento_insano and alimento_sano_evitado:
            guardar_datos("Alimentación", {"Fecha": fecha_hoy, "Comida Insana": alimento_insano, "Sano Evitado": alimento_sano_evitado})
            st.success("Deslice registrado. ¡A por la siguiente comida sana!")
    mostrar_historial("Alimentación")

elif st.session_state.seccion_activa == "📚 Lectura":
    st.title("📚 Mi Biblioteca")
    titulo = st.text_input("Título del libro:")
    fecha_inicio = st.date_input("Fecha de inicio:")
    fecha_fin = st.date_input("Fecha de fin (déjalo vacío si estás leyendo):", value=None)
    if st.button("Guardar Libro"):
        if titulo:
            f_fin_str = fecha_fin.strftime("%Y-%m-%d") if fecha_fin else ""
            guardar_datos("Lectura", {"Título": titulo, "Fecha Inicio": fecha_inicio.strftime("%Y-%m-%d"), "Fecha Fin": f_fin_str})
            st.success("¡Libro guardado en tu historial!")
    mostrar_historial("Lectura")

elif st.session_state.seccion_activa == "💡 Ideas/Proyectos":
    st.title("💡 Lluvia de Ideas")
    idea = st.text_input("Título de la idea/proyecto:")
    descripcion = st.text_area("Descripción o primeros pasos:")
    if st.button("Capturar Idea"):
        if idea:
            guardar_datos("Ideas", {"Fecha": fecha_hoy, "Idea/Proyecto": idea, "Descripción": descripcion})
            st.success("¡Idea capturada! No la olvides.")
    mostrar_historial("Ideas")

elif st.session_state.seccion_activa == "🎬 Watchlist/Wishlist":
    st.title("🎬 Watchlist & Wishlist")
    st.write("Controla tus antojos y organiza tu ocio.")
    tipo = st.selectbox("Categoría:", ["Película/Serie 🍿", "Producto/Capricho 💸", "Libro/Curso 🎓", "Lugar/Restaurante 🗺️"])
    nombre = st.text_input("Nombre del item:")
    precio = st.text_input("Precio estimado (si aplica):")
    porque = st.text_area("¿Por qué lo quieres / Quién lo recomendó?")
    
    if st.button("Añadir a la lista"):
        if nombre:
            datos = {"Fecha": fecha_hoy, "Tipo": tipo, "Item": nombre, "Precio": precio, "Notas": porque}
            guardar_datos("Watchlist", datos)
            st.success("¡Añadido con éxito!")
    mostrar_historial("Watchlist")

elif st.session_state.seccion_activa == "🤝 Personal CRM":
    st.title("🤝 Personal CRM (Networking)")
    st.write("No olvides a las personas clave que conoces.")
    nombre_p = st.text_input("Nombre de la persona:")
    donde = st.text_input("¿Dónde os conocisteis?")
    intereses = st.text_input("Intereses/Temas de conversación:")
    notas_p = st.text_area("Notas importantes o próximos pasos:")
    
    if st.button("Guardar Contacto"):
        if nombre_p:
            datos = {"Fecha": fecha_hoy, "Nombre": nombre_p, "Contexto": donde, "Intereses": intereses, "Notas": notas_p}
            guardar_datos("CRM", datos)
            st.success(f"Contacto de {nombre_p} guardado.")
    mostrar_historial("CRM")

elif st.session_state.seccion_activa == "✈️ Viajes":
    st.title("✈️ Bitácora de Viajes")
    destino = st.text_input("Destino:")
    periodo = st.text_input("Periodo (ej: 1-15 Agosto 2024):")
    monumentos = st.text_area("Monumentos/sitios emblemáticos visitados:")
    restaurantes = st.text_area("Restaurantes recomendados:")
    if st.button("Guardar Viaje"):
        if destino:
            guardar_datos("Viajes", {"Fecha Registro": fecha_hoy, "Destino": destino, "Periodo": periodo, "Sitios Visitas": monumentos, "Comida": restaurantes})
            st.success(f"¡Viaje a {destino} registrado!")
    mostrar_historial("Viajes")

elif st.session_state.seccion_activa == "👔 Outfits":
    st.title("👔 Gestor de Outfits")
    nombre_outfit = st.text_input("Nombre del conjunto (ej: 'Outfit Lunes casual'):")
    foto_subida = st.file_uploader("Sube una foto del conjunto:", type=['jpg', 'jpeg', 'png'])
    if st.button("Subir Outfit"):
        if nombre_outfit and foto_subida:
            st.info("Subiendo foto a Drive... espera.")
            enlace_foto = subir_foto_a_drive(foto_subida, f"outfit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            if enlace_foto:
                guardar_datos("Outfits", {"Fecha Creación": fecha_hoy, "Nombre Outfit": nombre_outfit, "Enlace Foto": enlace_foto, "Puestas": "0"})
                st.success("¡Outfit guardado con éxito!")
        else:
            st.warning("Falta nombre o foto.")
            
    st.divider()
    with st.expander("📂 Ver mi galería de Outfits"):
        df_outfits = cargar_datos("Outfits")
        if not df_outfits.empty:
            st.dataframe(df_outfits[["Nombre Outfit", "Puestas", "Fecha Creación"]], use_container_width=True)
            outfit_nombre_ver = st.selectbox("Selecciona un outfit para ver la foto:", df_outfits['Nombre Outfit'])
            if outfit_nombre_ver:
                enlace_ver = df_outfits[df_outfits['Nombre Outfit'] == outfit_nombre_ver].iloc[0]['Enlace Foto']
                st.link_button(f"Ver foto de '{outfit_nombre_ver}' en Google Drive", enlace_ver)
        else:
            st.info("Aún no tienes outfits guardados.")

elif st.session_state.seccion_activa == "✨ Pareja/Escapadas":
    st.title("✨ Nuestras Escapadas")
    lugar = st.text_input("Lugar de la escapada:")
    fecha_escapada = st.date_input("Fecha:")
    que_hicimos = st.text_area("¿Qué sitios chulos visitamos?")
    if st.button("Guardar Recuerdo"):
        if lugar:
            guardar_datos("Pareja", {"Fecha Registro": fecha_hoy, "Lugar": lugar, "Fecha Escapada": fecha_escapada.strftime("%Y-%m-%d"), "Detalles": que_hicimos})
            st.success(f"¡Recuerdo de {lugar} guardado!")
    mostrar_historial("Pareja")

elif st.session_state.seccion_activa == "💰 Finanzas":
    st.title("💰 Control de Finanzas")
    col1, col2 = st.columns(2)
    with col1:
        tipo_movimiento = st.radio("Tipo de movimiento:", ["Gasto 📉", "Ingreso 📈"], horizontal=True)
        cantidad = st.number_input("Cantidad (€):", min_value=0.0, step=1.0, format="%.2f")
    with col2:
        categoria = st.text_input("Etiqueta (ej: Comida, Sueldo, Ocio):")
        concepto = st.text_input("Concepto / Detalles:")
        
    if st.button("Registrar Movimiento"):
        if categoria and cantidad > 0:
            guardar_datos("Finanzas", {"Fecha": fecha_hoy, "Tipo": tipo_movimiento, "Categoría": categoria, "Cantidad": str(cantidad), "Concepto": concepto})
            st.success("¡Movimiento financiero registrado!")
    mostrar_historial("Finanzas")

elif st.session_state.seccion_activa == "📅 Recordatorios":
    st.title("📅 Enviar a Google Calendar")
    st.write("Crea un evento o recordatorio que aparecerá automáticamente en tu agenda personal.")
    
    tit_rec = st.text_input("Título del evento/recordatorio:")
    fecha_rec = st.date_input("¿Para qué día es?")
    desc_rec = st.text_area("Detalles o notas adicionales:")
    
    if st.button("Añadir a mi Calendario"):
        if tit_rec:
            st.info("Conectando con Google Calendar...")
            enlace = crear_evento_calendar(tit_rec, fecha_rec, desc_rec)
            if enlace:
                guardar_datos("Recordatorios", {"Fecha Creación": fecha_hoy, "Fecha Evento": fecha_rec.strftime("%Y-%m-%d"), "Título": tit_rec})
                st.success("✅ ¡Añadido a tu Google Calendar exitosamente!")
                st.link_button("Ver en Google Calendar", enlace)
        else:
            st.warning("Debes ponerle un título al recordatorio.")
    mostrar_historial("Recordatorios")

elif st.session_state.seccion_activa == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    st.write("Selecciona una categoría y el registro que deseas eliminar para siempre.")
    
    categorias = ["Diario", "Deporte", "Alimentación", "Lectura", "Ideas", "Watchlist", "CRM", "Viajes", "Outfits", "Pareja", "Finanzas", "Recordatorios"]
    categoria_seleccionada = st.selectbox("Selecciona la categoría:", categorias)
    st.divider()
    df = cargar_datos(categoria_seleccionada)
    
    if not df.empty:
        df['Fila_Excel'] = df.index + 2 
        st.write("### Tus datos actuales:")
        st.dataframe(df, use_container_width=True)
        
        st.write("### Selecciona qué borrar")
        opciones_borrado = []
        for index, row in df.iterrows():
            valores = row.tolist()
            col1_val = valores[0] if len(valores) > 0 else ""
            col2_val = valores[1] if len(valores) > 1 else ""
            resumen = f"Fila {row['Fila_Excel']} ➔ {col1_val} | {col2_val}"
            opciones_borrado.append(resumen)
            
        seleccion = st.selectbox("Elige el registro a eliminar:", opciones_borrado)
        
        if st.button("🚨 Eliminar Registro Definitivamente"):
            fila_a_borrar = int(seleccion.split(" ")[1])
            st.warning(f"Borrando fila {fila_a_borrar} de la nube...")
            if eliminar_registro(categoria_seleccionada, fila_a_borrar):
                st.success("¡Registro eliminado con éxito! Cambia de sección para ver tu base de datos limpia.")
                st.rerun()
            else:
                st.error("Hubo un problema al intentar borrar el registro.")
    else:
        st.info("Aún no tienes registros guardados en esta categoría.")
