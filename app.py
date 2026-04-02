import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import json
from datetime import date

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Personal OS", page_icon="🚀", layout="wide")

# --- CONEXIÓN A LA BASE DE DATOS (GOOGLE SHEETS) ---
@st.cache_resource
def conectar_db():
    scope = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    # Lee las credenciales ocultas (secretos)
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    client = gspread.authorize(creds)
    return client.open("Mi_Personal_OS")

try:
    sheet = conectar_db()
    db_conectada = True
except Exception as e:
    st.error("⚠️ Esperando conexión a la Base de Datos...")
    db_conectada = False

# Función inteligente para guardar datos
def guardar_datos(nombre_pestaña, nuevos_datos):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            # Si la pestaña no existe en el Excel, la crea y pone los títulos
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        
        # Añade la nueva fila de datos
        worksheet.append_row(list(nuevos_datos.values()))
        return True
    return False

# --- INTERFAZ DE LA APLICACIÓN ---
st.sidebar.title("🚀 Mi Personal OS")
seccion = st.sidebar.radio("Navegación:", ["🧠 Diario", "💪 Deporte", "🥗 Comidas"])
fecha_hoy = date.today().strftime("%Y-%m-%d")

if seccion == "🧠 Diario":
    st.title("🧠 Reflexión del Día")
    animo = st.select_slider("Energía de hoy:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar en la nube"):
        if pensamientos:
            datos = {"Fecha": fecha_hoy, "Ánimo": animo, "Pensamientos": pensamientos}
            guardar_datos("Diario", datos)
            st.success("¡Guardado en tu Google Drive!")

elif seccion == "💪 Deporte":
    st.title("💪 Registro Deportivo")
    tipo = st.selectbox("Actividad:", ["Gimnasio", "Correr", "Yoga", "Pádel/Fútbol", "Otro"])
    duracion = st.number_input("Minutos:", min_value=1, value=45)
    if st.button("Registrar Entrenamiento"):
        datos = {"Fecha": fecha_hoy, "Actividad": tipo, "Minutos": str(duracion)}
        guardar_datos("Deporte", datos)
        st.success("¡Entrenamiento registrado!")

elif seccion == "🥗 Comidas":
    st.title("🥗 Control de Hábitos")
    agua = st.number_input("Vasos de agua:", min_value=0, value=0)
    sano = st.radio("¿Comiste sano?", ["Sí", "Más o menos", "No"])
    if st.button("Guardar Hábitos"):
        datos = {"Fecha": fecha_hoy, "Vasos Agua": str(agua), "Sano": sano}
        guardar_datos("Comidas", datos)
        st.success("¡Hábitos actualizados!")