import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
import io
from datetime import date, datetime, timedelta
import altair as alt

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Personal OS", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# --- CONFIGURACIÓN DE USUARIO (RELLENAR) ---
# ==========================================

FOLDER_ID_PHOTOS = "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L" 
EMAIL_CALENDAR = "aeroegen@gmail.com" # 👈 TU EMAIL DE GOOGLE CALENDAR AQUÍ

# Enlaces a fotos de fondo para cada sección (puedes buscar fotos en Unsplash y cambiar los enlaces)
FONDOS = {
    "🧠 Diario": "https://images.unsplash.com/photo-1517816743773-6e0fd5ce9464",
    "💪 Deporte": "https://images.unsplash.com/photo-1517836357463-d25dfeac3438",
    "🥗 Alimentación": "https://images.unsplash.com/photo-1490645935967-10de6ba17061",
    "📚 Lectura": "https://images.unsplash.com/photo-1524995997946-a1c2e315a42f",
    "💡 Ideas/Proyectos": "https://images.unsplash.com/photo-1493612276216-ee3925520721",
    "✈️ Viajes": "https://images.unsplash.com/photo-1436491865332-7a61a109cc05",
    "👔 Outfits": "https://images.unsplash.com/photo-1489987707023-afcb1e97d19c",
    "✨ Pareja/Escapadas": "https://images.unsplash.com/photo-1518199266791-5375a83190b7",
    "📈 Hábitos": "https://images.unsplash.com/photo-1484480974693-6ca0a78fb36b",
    "💰 Finanzas": "https://images.unsplash.com/photo-1554224155-8d04cb21cd6c",
    "📅 Recordatorios": "https://images.unsplash.com/photo-1506784983877-45594efa4cbe",
    "Default": "https://images.unsplash.com/photo-1507525428034-b723cf961d3e"
}

# ==========================================
# --- CONFIGURACIÓN DE GOOGLE ---
# ==========================================

@st.cache_resource
def obtener_credenciales_gcp():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    scopes = [
        'https://spreadsheets.google.com/feeds', 
        'https://www.googleapis.com/auth/drive',
        'https://www.googleapis.com/auth/calendar'
    ]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scopes)
    return creds

creds = obtener_credenciales_gcp()

try:
    client = gspread.authorize(creds)
    sheet = client.open("Mi_Personal_OS")
    db_conectada = True
except Exception as e:
    st.error(f"⚠️ Error de conexión a Base de Datos: {e}")
    db_conectada = False

def guardar_datos(nombre_pestaña, nuevos_datos):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        worksheet.append_row(list(nuevos_datos.values()))
        # ¡NUEVO!: Borramos la memoria cuando guardamos algo nuevo para que se actualice
        st.cache_data.clear() 
        return True
    return False

# ¡NUEVO!: Le decimos a la app que memorice los datos durante 60 segundos
@st.cache_data(ttl=60) 
def cargar_datos(nombre_pestaña):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            list_of_hashes = worksheet.get_all_records()
            return pd.DataFrame(list_of_hashes)
        except:
            return pd.DataFrame()
    return pd.DataFrame()

def eliminar_registro(nombre_pestaña, indice_fila_sheet):
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            worksheet.delete_rows(indice_fila_sheet) 
            # ¡NUEVO!: Borramos la memoria al borrar un dato para que desaparezca al instante
            st.cache_data.clear() 
            return True
        except Exception as e:
            st.error(f"Error al borrar: {e}")
            return False
    return False

def subir_foto_a_drive(archivo_imagen, nombre_foto):
    if FOLDER_ID_PHOTOS == "TU_ID_DE_CARPETA_DE_DRIVE_AQUÍ":
        st.error("⚠️ Falta configurar la ID de la carpeta de Drive.")
        return None
    try:
        service = build('drive', 'v3', credentials=creds)
        file_metadata = {'name': nombre_foto, 'parents': [FOLDER_ID_PHOTOS]}
        media = MediaIoBaseUpload(io.BytesIO(archivo_imagen.getvalue()), mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"❌ Error al subir la foto a Drive: {e}")
        return None

def crear_evento_calendar(titulo, fecha, descripcion=""):
    try:
        service = build('calendar', 'v3', credentials=creds)
        evento = {
            'summary': titulo,
            'description': descripcion,
            'start': {'date': fecha.strftime("%Y-%m-%d")},
            'end': {'date': fecha.strftime("%Y-%m-%d")}, 
        }
        evento_creado = service.events().insert(calendarId=EMAIL_CALENDAR, body=evento).execute()
        return evento_creado.get('htmlLink')
    except Exception as e:
        st.error(f"Error conectando con Google Calendar. ¿Compartiste el calendario con el robot? Error: {e}")
        return None

def establecer_fondo(seccion_actual):
    url_imagen = FONDOS.get(seccion_actual, FONDOS["Default"])
    css = f"""
    <style>
    .stApp {{
        background-image: linear-gradient(rgba(0, 0, 0, 0.75), rgba(0, 0, 0, 0.75)), url("{url_imagen}");
        background-size: cover;
        background-position: center;
        background-attachment: fixed;
    }}
    /* Asegurar que el texto sea blanco para contrastar con el fondo oscuro */
    .stMarkdown, .stText, h1, h2, h3 {{
        color: white !important;
    }}
    </style>
    """
    st.markdown(css, unsafe_allow_html=True)

def mostrar_historial(nombre_pestaña):
    with st.expander(f"📂 Ver mi historial de {nombre_pestaña}"):
        df = cargar_datos(nombre_pestaña)
        if not df.empty:
            st.dataframe(df, use_container_width=True)
        else:
            st.info(f"Aún no tienes registros guardados en {nombre_pestaña}.")

# ==========================================
# --- INTERFAZ PRINCIPAL Y NAVEGACIÓN ---
# ==========================================
fecha_hoy = date.today().strftime("%Y-%m-%d")

st.sidebar.title("🚀 Mi Personal OS")
secciones = ["🧠 Diario", "💪 Deporte", "🥗 Alimentación", "📚 Lectura", "💡 Ideas/Proyectos", "✈️ Viajes", "👔 Outfits", "✨ Pareja/Escapadas", "📈 Hábitos", "💰 Finanzas", "📅 Recordatorios", "🗑️ Gestionar Datos"]
seccion = st.sidebar.radio("Navegación:", secciones)

# Aplicar el fondo dinámico
establecer_fondo(seccion)

# ==========================================
# --- SECCIONES DE LA APLICACIÓN ---
# ==========================================

if seccion == "🧠 Diario":
    st.title("🧠 Diario y Reflexión")
    animo = st.select_slider("Energía de hoy:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar en la nube"):
        if pensamientos:
            datos = {"Fecha": fecha_hoy, "Ánimo": animo, "Pensamientos": pensamientos}
            guardar_datos("Diario", datos)
            st.success("¡Guardado en tu Google Drive!")
    mostrar_historial("Diario")

elif seccion == "💪 Deporte":
    st.title("💪 Registro Deportivo")
    tipo = st.selectbox("Actividad:", ["Futbol", "Padel", "Correr", "Bici", "Gimnasio", "Otro"])
    duracion = st.number_input("Minutos:", min_value=1, value=45)
    if st.button("Registrar Entrenamiento"):
        datos = {"Fecha": fecha_hoy, "Actividad": tipo, "Minutos": str(duracion)}
        guardar_datos("Deporte", datos)
        st.success("¡Entrenamiento registrado!")
    mostrar_historial("Deporte")

elif seccion == "🥗 Alimentación":
    st.title("🥗 Control de Deslices")
    alimento_insano = st.text_input("¿Qué comiste insano?")
    alimento_sano_evitado = st.text_input("¿Qué alimento o bebida sana evitaste?")
    if st.button("Registrar Deslice"):
        if alimento_insano and alimento_sano_evitado:
            datos = {"Fecha": fecha_hoy, "Comida Insana": alimento_insano, "Sano Evitado": alimento_sano_evitado}
            guardar_datos("Alimentación", datos)
            st.success("Deslice registrado. ¡A por la siguiente comida sana!")
    mostrar_historial("Alimentación")

elif seccion == "📚 Lectura":
    st.title("📚 Mi Biblioteca")
    titulo = st.text_input("Título del libro:")
    fecha_inicio = st.date_input("Fecha de inicio:")
    fecha_fin = st.date_input("Fecha de fin (déjalo vacío si estás leyendo):", value=None)
    if st.button("Guardar Libro"):
        if titulo:
            f_fin_str = fecha_fin.strftime("%Y-%m-%d") if fecha_fin else ""
            datos = {"Título": titulo, "Fecha Inicio": fecha_inicio.strftime("%Y-%m-%d"), "Fecha Fin": f_fin_str}
            guardar_datos("Lectura", datos)
            st.success("¡Libro guardado en tu historial!")
    mostrar_historial("Lectura")

elif seccion == "💡 Ideas/Proyectos":
    st.title("💡 Lluvia de Ideas")
    idea = st.text_input("Título de la idea/proyecto:")
    descripcion = st.text_area("Descripción o primeros pasos:")
    if st.button("Capturar Idea"):
        if idea:
            datos = {"Fecha": fecha_hoy, "Idea/Proyecto": idea, "Descripción": descripcion}
            guardar_datos("Ideas", datos)
            st.success("¡Idea capturada! No la olvides.")
    mostrar_historial("Ideas")

elif seccion == "✈️ Viajes":
    st.title("✈️ Bitácora de Viajes")
    destino = st.text_input("Destino:")
    periodo = st.text_input("Periodo (ej: 1-15 Agosto 2024):")
    monumentos = st.text_area("Monumentos/sitios emblemáticos visitados:")
    restaurantes = st.text_area("Restaurantes recomendados:")
    if st.button("Guardar Viaje"):
        if destino:
            datos = {"Fecha Registro": fecha_hoy, "Destino": destino, "Periodo": periodo, "Sitios Visitas": monumentos, "Comida": restaurantes}
            guardar_datos("Viajes", datos)
            st.success(f"¡Viaje a {destino} registrado!")
    mostrar_historial("Viajes")

elif seccion == "👔 Outfits":
    st.title("👔 Gestor de Outfits")
    nombre_outfit = st.text_input("Nombre del conjunto (ej: 'Outfit Lunes casual'):")
    foto_subida = st.file_uploader("Sube una foto del conjunto:", type=['jpg', 'jpeg', 'png'])
    if st.button("Subir Outfit"):
        if nombre_outfit and foto_subida:
            st.info("Subiendo foto a Drive... espera.")
            enlace_foto = subir_foto_a_drive(foto_subida, f"outfit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
            if enlace_foto:
                datos = {"Fecha Creación": fecha_hoy, "Nombre Outfit": nombre_outfit, "Enlace Foto": enlace_foto, "Puestas": "0"}
                guardar_datos("Outfits", datos)
                st.success("¡Outfit guardado con éxito!")
        else:
            st.warning("Falta nombre o foto.")
            
    with st.expander("📂 Ver mi galería de Outfits"):
        df_outfits = cargar_datos("Outfits")
        if not df_outfits.empty:
            st.dataframe(df_outfits[["Nombre Outfit", "Puestas", "Fecha Creación"]], use_container_width=True)
            outfit_nombre_ver = st.selectbox("Selecciona un outfit para ver la foto:", df_outfits['Nombre Outfit'])
            if outfit_nombre_ver:
                fila_outfit = df_outfits[df_outfits['Nombre Outfit'] == outfit_nombre_ver].iloc[0]
                enlace_ver = fila_outfit['Enlace Foto']
                st.link_button(f"Ver foto de '{outfit_nombre_ver}' en Google Drive", enlace_ver)
        else:
            st.info("Aún no tienes outfits guardados.")

elif seccion == "✨ Pareja/Escapadas":
    st.title("✨ Nuestras Escapadas")
    lugar = st.text_input("Lugar de la escapada:")
    fecha_escapada = st.date_input("Fecha:")
    que_hicimos = st.text_area("¿Qué sitios chulos visitamos?")
    if st.button("Guardar Recuerdo"):
        if lugar:
            datos = {"Fecha Registro": fecha_hoy, "Lugar": lugar, "Fecha Escapada": fecha_escapada.strftime("%Y-%m-%d"), "Detalles": que_hicimos}
            guardar_datos("Pareja", datos)
            st.success(f"¡Recuerdo de {lugar} guardado!")
    mostrar_historial("Pareja")

elif seccion == "📈 Hábitos":
    st.title("📈 Tracker de Hábitos")
    
    df_habitos = cargar_datos("Hábitos")
    lista_habitos = []
    if not df_habitos.empty and 'Hábito' in df_habitos.columns:
        lista_habitos = df_habitos['Hábito'].unique().tolist()
        
    col1, col2 = st.columns(2)
    with col1:
        if lista_habitos:
            habito_elegido = st.selectbox("Selecciona un hábito:", ["+ Crear Nuevo..."] + lista_habitos)
            if habito_elegido == "+ Crear Nuevo...":
                habito_elegido = st.text_input("Escribe el nuevo hábito (ej: Leer 10 págs):")
        else:
            habito_elegido = st.text_input("Crea tu primer hábito (ej: Beber 2L de agua):")
            
    with col2:
        estado_habito = st.selectbox("Estado de hoy:", ["Cumplido ✅", "Fallado ❌"])
        fecha_habito = st.date_input("Fecha de registro:", value=date.today())
        
    if st.button("Registrar Hábito"):
        if habito_elegido:
            datos = {"Fecha": fecha_habito.strftime("%Y-%m-%d"), "Hábito": habito_elegido, "Estado": estado_habito}
            guardar_datos("Hábitos", datos)
            st.success("¡Hábito registrado!")
            st.rerun()

    st.divider()
    st.subheader("🔥 Calendario de Cumplimiento")
    
    if not df_habitos.empty and 'Hábito' in df_habitos.columns:
        hab_ver = st.selectbox("Selecciona el hábito para ver su calendario:", lista_habitos)
        df_h = df_habitos[(df_habitos['Hábito'] == hab_ver) & (df_habitos['Estado'] == 'Cumplido ✅')].copy()
        
        if not df_h.empty:
            df_h['Fecha'] = pd.to_datetime(df_h['Fecha'])
            df_h['Semana'] = df_h['Fecha'].dt.isocalendar().week
            df_h['Día de la semana'] = df_h['Fecha'].dt.day_name()
            
            chart = alt.Chart(df_h).mark_rect(cornerRadius=5).encode(
                x=alt.X('Semana:O', axis=alt.Axis(title='Semanas', labels=False, ticks=False)),
                y=alt.Y('Día de la semana:O', sort=['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday'], title=None),
                color=alt.Color('count()', scale=alt.Scale(scheme='greens'), legend=None),
                tooltip=['Fecha', 'Hábito']
            ).properties(
                width='container',
                height=250,
                title=f"Historial de: {hab_ver}"
            ).configure_view(strokeWidth=0)
            
            st.altair_chart(chart, use_container_width=True)
            st.write(f"Has cumplido este hábito **{len(df_h)}** veces en total.")
        else:
            st.info("No hay días marcados como 'Cumplido' para este hábito todavía.")
            
    mostrar_historial("Hábitos")

elif seccion == "💰 Finanzas":
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
            datos = {"Fecha": fecha_hoy, "Tipo": tipo_movimiento, "Categoría": categoria, "Cantidad": str(cantidad), "Concepto": concepto}
            guardar_datos("Finanzas", datos)
            st.success("¡Movimiento financiero registrado!")
            
    mostrar_historial("Finanzas")

elif seccion == "📅 Recordatorios":
    st.title("📅 Enviar a Google Calendar")
    st.write("Crea un evento o recordatorio que aparecerá automáticamente en tu agenda personal.")
    
    tit_rec = st.text_input("Título del evento/recordatorio:")
    fecha_rec = st.date_input("¿Para qué día es?")
    desc_rec = st.text_area("Detalles o notas adicionales:")
    
    if st.button("Añadir a mi Calendario"):
        if tit_rec:
            if EMAIL_CALENDAR == "tu_email_real@gmail.com":
                st.error("⚠️ Primero debes poner tu email en la línea 20 del código para que sepa a qué calendario mandarlo.")
            else:
                st.info("Conectando con Google Calendar...")
                enlace = crear_evento_calendar(tit_rec, fecha_rec, desc_rec)
                if enlace:
                    guardar_datos("Recordatorios", {"Fecha Creación": fecha_hoy, "Fecha Evento": fecha_rec.strftime("%Y-%m-%d"), "Título": tit_rec})
                    st.success("✅ ¡Añadido a tu Google Calendar exitosamente!")
                    st.link_button("Ver en Google Calendar", enlace)
        else:
            st.warning("Debes ponerle un título al recordatorio.")
            
    mostrar_historial("Recordatorios")

elif seccion == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    st.write("Selecciona una categoría y el registro que deseas eliminar para siempre.")
    
    categorias = ["Diario", "Deporte", "Alimentación", "Lectura", "Ideas", "Viajes", "Outfits", "Pareja", "Hábitos", "Finanzas", "Recordatorios"]
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
            else:
                st.error("Hubo un problema al intentar borrar el registro.")
    else:
        st.info("Aún no tienes registros guardados en esta categoría.")
