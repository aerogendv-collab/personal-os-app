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
st.set_page_config(page_title="Personal OS", page_icon="🚀", layout="wide")

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

# Sidebar
st.sidebar.title("🚀 Personal OS")
seccion = st.sidebar.radio("Ir a:", secciones, index=secciones.index(st.session_state.seccion_activa))
st.session_state.seccion_activa = seccion

# ==========================================
# --- CONFIGURACIÓN DE GOOGLE ---
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
except Exception:
    db_conectada = False

def guardar_datos(nombre_pestaña, nuevos_datos):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        worksheet.append_row(list(nuevos_datos.values()))
        st.cache_data.clear()
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
            st.cache_data.clear()
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

def establecer_fondo(seccion_actual):
    url = FONDOS.get(seccion_actual, FONDOS["Default"])
    st.markdown(f"""<style>.stApp {{ background-image: linear-gradient(rgba(0,0,0,0.7), rgba(0,0,0,0.7)), url("{url}"); background-size: cover; background-attachment: fixed; }} .stMarkdown, .stText, h1, h2, h3, p {{ color: white !important; }} </style>""", unsafe_allow_html=True)

establecer_fondo(st.session_state.seccion_activa)

# ==========================================
# --- SECCIONES ---
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
        if st.button("💪 Deporte", use_container_width=True): ir_a("💪 Deporte")
        if st.button("🎬 Watchlist/Wishlist", use_container_width=True): ir_a("🎬 Watchlist/Wishlist")

    with cols[1]:
        if st.button("💰 Registrar Gasto", use_container_width=True): ir_a("💰 Finanzas")
        if st.button("📚 Mi Biblioteca", use_container_width=True): ir_a("📚 Lectura")
        if st.button("🤝 Contactos CRM", use_container_width=True): ir_a("🤝 Personal CRM")

    with cols[2]:
        if st.button("💡 Nuevas Ideas", use_container_width=True): ir_a("💡 Ideas/Proyectos")
        if st.button("📅 Agendar Recordatorio", use_container_width=True): ir_a("📅 Recordatorios")
        if st.button("👔 Elegir Outfit", use_container_width=True): ir_a("👔 Outfits")

elif st.session_state.seccion_activa == "🎬 Watchlist/Wishlist":
    st.title("🎬 Watchlist & Wishlist")
    st.write("Controla tus antojos y organiza tu ocio.")
    tipo = st.selectbox("Categoría:", ["Película/Serie 🍿", "Producto/Capricho 💸", "Libro/Curso 🎓"])
    nombre = st.text_input("Nombre del item:")
    precio = st.text_input("Precio estimado (si aplica):")
    porque = st.text_area("¿Por qué lo quieres / Quién lo recomendó?")
    
    if st.button("Añadir a la lista"):
        if nombre:
            datos = {"Fecha": str(date.today()), "Tipo": tipo, "Item": nombre, "Precio": precio, "Notas": porque}
            guardar_datos("Watchlist", datos)
            st.success("¡Añadido con éxito!")
    
    df_w = cargar_datos("Watchlist")
    if not df_w.empty:
        st.dataframe(df_w, use_container_width=True)

elif st.session_state.seccion_activa == "🤝 Personal CRM":
    st.title("🤝 Personal CRM (Networking)")
    st.write("No olvides a las personas clave que conoces.")
    nombre_p = st.text_input("Nombre de la persona:")
    donde = st.text_input("¿Dónde os conocisteis?")
    intereses = st.text_input("Intereses/Temas de conversación:")
    notas_p = st.text_area("Notas importantes o próximos pasos:")
    
    if st.button("Guardar Contacto"):
        if nombre_p:
            datos = {"Fecha": str(date.today()), "Nombre": nombre_p, "Contexto": donde, "Intereses": intereses, "Notas": notas_p}
            guardar_datos("CRM", datos)
            st.success(f"Contacto de {nombre_p} guardado.")
            
    df_c = cargar_datos("CRM")
    if not df_c.empty:
        st.dataframe(df_c, use_container_width=True)

# [Aquí irían el resto de secciones: Diario, Deporte, Finanzas, etc. manteniendo su lógica previa]
# Por brevedad y para que el código sea funcional de inmediato, incluyo la estructura base:

elif st.session_state.seccion_activa == "🧠 Diario":
    st.title("🧠 Diario")
    animo = st.select_slider("Energía:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar"):
        guardar_datos("Diario", {"Fecha": str(date.today()), "Ánimo": animo, "Texto": pensamientos})
        st.success("Guardado.")

elif st.session_state.seccion_activa == "💪 Deporte":
    st.title("💪 Deporte")
    tipo = st.selectbox("Actividad:", ["Gimnasio", "Correr", "Padel", "Futbol", "Otro"])
    duracion = st.number_input("Minutos:", 1, 300, 45)
    if st.button("Registrar"):
        guardar_datos("Deporte", {"Fecha": str(date.today()), "Actividad": tipo, "Minutos": str(duracion)})
        st.success("Registrado.")

elif st.session_state.seccion_activa == "💰 Finanzas":
    st.title("💰 Finanzas")
    tipo_m = st.radio("Tipo:", ["Gasto 📉", "Ingreso 📈"])
    cant = st.number_input("Cantidad (€):", 0.0)
    cat = st.text_input("Categoría:")
    if st.button("Guardar"):
        guardar_datos("Finanzas", {"Fecha": str(date.today()), "Tipo": tipo_m, "Euros": str(cant), "Cat": cat})
        st.success("Registrado.")

elif st.session_state.seccion_activa == "📅 Recordatorios":
    st.title("📅 Calendar")
    tit = st.text_input("Evento:")
    fec = st.date_input("Día:")
    if st.button("Enviar a Google Calendar"):
        link = crear_evento_calendar(tit, fec)
        if link: st.success("¡Enviado!"); st.link_button("Ver", link)

elif st.session_state.seccion_activa == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    cat_sel = st.selectbox("Categoría:", ["Diario", "Deporte", "Finanzas", "Watchlist", "CRM", "Lectura", "Viajes", "Outfits"])
    df_del = cargar_datos(cat_sel)
    if not df_del.empty:
        df_del['Fila'] = df_del.index + 2
        st.dataframe(df_del)
        fila = st.number_input("Fila a borrar:", min_value=2, step=1)
        if st.button("BORRAR PERMANENTEMENTE"):
            if eliminar_registro(cat_sel, fila): st.success("Borrado."); st.rerun()

# [Añadir el resto de secciones Lectura, Viajes, Outfits, etc. siguiendo el patrón]
