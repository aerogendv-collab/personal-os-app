import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
import io
from datetime import date, datetime

# --- CONFIGURACIÓN DE PÁGINA ---
st.set_page_config(page_title="Mi Personal OS", page_icon="🚀", layout="wide")

# ==========================================
# --- CONFIGURACIÓN DE GOOGLE (PRO) ---
# ==========================================

# 1. PEGA AQUÍ LA ID DE TU CARPETA DE DRIVE
FOLDER_ID_PHOTOS = "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L" 

@st.cache_resource
def obtener_credenciales_gcp():
    """Lee y carga las credenciales secretas."""
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    scope_sheets = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    scope_drive = ['https://www.googleapis.com/auth/drive']
    creds_sheets = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope_sheets)
    creds_drive = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope_drive)
    return creds_sheets, creds_drive

creds_sheets, creds_drive = obtener_credenciales_gcp()

# Conexión inteligente a Google Sheets
try:
    client = gspread.authorize(creds_sheets)
    sheet = client.open("Mi_Personal_OS")
    db_conectada = True
except Exception as e:
    st.error(f"⚠️ Error de conexión a Base de Datos")
    db_conectada = False

def guardar_datos(nombre_pestaña, nuevos_datos):
    """Guarda una fila de datos en una pestaña del Sheet."""
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
        except:
            worksheet = sheet.add_worksheet(title=nombre_pestaña, rows="1000", cols="20")
            worksheet.append_row(list(nuevos_datos.keys()))
        worksheet.append_row(list(nuevos_datos.values()))
        return True
    return False

def cargar_datos(nombre_pestaña):
    """Carga los datos de una pestaña como un DataFrame de Pandas."""
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            list_of_hashes = worksheet.get_all_records()
            return pd.DataFrame(list_of_hashes)
        except:
            return pd.DataFrame()
    return pd.DataFrame()
def eliminar_registro(nombre_pestaña, indice_fila_sheet):
    """Elimina una fila específica en la pestaña de Google Sheets."""
    if db_conectada:
        try:
            worksheet = sheet.worksheet(nombre_pestaña)
            worksheet.delete_row(indice_fila_sheet) # gspread usa delete_row para borrar
            return True
        except Exception as e:
            st.error(f"Error al borrar: {e}")
            return False
    return False
# Conexión a Google Drive para fotos
def subir_foto_a_drive(archivo_imagen, nombre_foto):
    """Sube una foto a la carpeta de Drive y devuelve el enlace."""
    if FOLDER_ID_PHOTOS == "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L":
        st.error("⚠️ Falta configurar la ID de la carpeta de Drive.")
        return None
    
    try:
        service = build('drive', 'v3', credentials=creds_drive)
        file_metadata = {
            'name': nombre_foto,
            'parents': [FOLDER_ID_PHOTOS]
        }
        # Convertimos la imagen de Streamlit a un formato que Drive entienda
        media = MediaIoBaseUpload(io.BytesIO(archivo_imagen.getvalue()), mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        
        # Hacemos la foto pública con el enlace (para que la app la pueda leer)
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        
        # El webViewLink es el enlace para ver la foto en un navegador
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"❌ Error al subir la foto a Drive")
        return None

# ==========================================
# --- INTERFAZ PRINCIPAL Y NAVEGACIÓN ---
# ==========================================
fecha_hoy = date.today().strftime("%Y-%m-%d")

st.sidebar.title("🚀 Mi Personal OS")
st.sidebar.markdown("Tu centro de control centralizado")
seccion = st.sidebar.radio("Navegación:", 
    ["📊 Dashboard", "🧠 Diario", "💪 Deporte", "🥗 Alimentación", "📚 Lectura", "💡 Ideas/Proyectos", "✈️ Viajes", "👔 Outfits", "✨ Pareja/Escapadas", "🗑️ Gestionar Datos"]
)

# ==========================================
# --- SECCIONES DE LA APLICACIÓN ---
# ==========================================

if seccion == "📊 Dashboard":
    st.title("📊 Tu Resumen Visual")
    st.write("Datos en tiempo real de tu Google Sheet.")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Mini dashboard de deporte
        df_deporte = cargar_datos("Deporte")
        if not df_deporte.empty:
            st.subheader("Tu actividad física")
            df_deporte['Minutos'] = pd.to_numeric(df_deporte['Minutos'])
            st.write(f"Has registrado **{df_deporte.shape[0]}** entrenamientos.")
            st.write(f"Tiempo total: **{df_deporte['Minutos'].sum()}** minutos.")
            # Gráfico simple de barras por tipo
            chart_data = df_deporte.groupby('Actividad')['Minutos'].sum()
            st.bar_chart(chart_data)
        else:
            st.info("Aún no hay datos de deporte.")
            
    with col2:
        # Mini dashboard de lectura
        df_lectura = cargar_datos("Lectura")
        if not df_lectura.empty:
            st.subheader("Libros leídos o en proceso")
            for i, row in df_lectura.iterrows():
                estado = "📖 Leyendo" if not row['Fecha Fin'] or row['Fecha Fin'] == "" else "✅ Terminado"
                st.write(f"- **{row['Título']}** ({estado})")
        else:
            st.info("Aún no hay datos de lectura.")
    
    st.divider()
    
    # Vista rápida del Diario
    st.subheader("Últimas 5 reflexiones")
    df_diario = cargar_datos("Diario")
    if not df_diario.empty:
        # Invertimos el orden para ver lo más nuevo primero
        st.dataframe(df_diario.sort_values(by='Fecha', ascending=False).head(5), use_container_width=True)
    else:
        st.info("Diario vacío.")

elif seccion == "🧠 Diario":
    st.title("🧠 Diario y Reflexión")
    animo = st.select_slider("Energía de hoy:", ["Baja", "Media", "Alta", "Imparable"])
    pensamientos = st.text_area("¿Qué tienes en mente?")
    if st.button("Guardar en la nube"):
        if pensamientos:
            datos = {"Fecha": fecha_hoy, "Ánimo": animo, "Pensamientos": pensamientos}
            guardar_datos("Diario", datos)
            st.success("¡Guardado en tu Google Drive!")

elif seccion == "💪 Deporte":
    st.title("💪 Registro Deportivo")
    tipo = st.selectbox("Actividad:", ["Futbol", "Padel", "Correr", "Bici", "Gimnasio", "Otro"])
    duracion = st.number_input("Minutos:", min_value=1, value=45)
    if st.button("Registrar Entrenamiento"):
        datos = {"Fecha": fecha_hoy, "Actividad": tipo, "Minutos": str(duracion)}
        guardar_datos("Deporte", datos)
        st.success("¡Entrenamiento registrado!")

elif seccion == "🥗 Alimentación":
    st.title("🥗 Control de Deslices")
    alimento_insano = st.text_input("¿Qué comiste insano?")
    alimento_sano_evitado = st.text_input("¿Qué alimento o bebida sana evitaste?")
    if st.button("Registrar Deslice"):
        if alimento_insano and alimento_sano_evitado:
            datos = {"Fecha": fecha_hoy, "Comida Insana": alimento_insano, "Sano Evitado": alimento_sano_evitado}
            guardar_datos("Alimentación", datos)
            st.success("Deslice registrado. ¡A por la siguiente comida sana!")

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

elif seccion == "💡 Ideas/Proyectos":
    st.title("💡 Lluvia de Ideas")
    idea = st.text_input("Título de la idea/proyecto:")
    descripcion = st.text_area("Descripción o primeros pasos:")
    
    if st.button("Capturar Idea"):
        if idea:
            datos = {"Fecha": fecha_hoy, "Idea/Proyecto": idea, "Descripción": descripcion}
            guardar_datos("Ideas", datos)
            st.success("¡Idea capturada! No la olvides.")

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

elif seccion == "👔 Outfits":
    st.title("👔 Gestor de Outfits")
    
    pestana_crear, pestana_ver = st.tabs(["🆕 Crear Outfit", "👕 Ver Historial"])
    
    with pestana_crear:
        nombre_outfit = st.text_input("Nombre del conjunto (ej: 'Outfit Lunes casual', 'Outfit Boda'):")
        foto_subida = st.file_uploader("Sube una foto del conjunto:", type=['jpg', 'jpeg', 'png'])
        
        if st.button("Subir Outfit"):
            if nombre_outfit and foto_subida:
                st.info("Subiendo foto a Drive... espera.")
                # El truco: subimos la foto, obtenemos el enlace público
                enlace_foto = subir_foto_a_drive(foto_subida, f"outfit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.jpg")
                if enlace_foto:
                    # Guardamos los datos CON EL ENLACE DE LA FOTO en el Excel
                    datos = {"Fecha Creación": fecha_hoy, "Nombre Outfit": nombre_outfit, "Enlace Foto": enlace_foto, "Puestas": "0"}
                    guardar_datos("Outfits", datos)
                    st.success("¡Outfit guardado con éxito! Puedes verlo en la pestaña 'Ver Historial'")
            else:
                st.warning("Falta nombre o foto.")
                
    with pestana_ver:
        st.subheader("Tus conjuntos")
        df_outfits = cargar_datos("Outfits")
        if not df_outfits.empty:
            # Mostramos el DataFrame para que sea interactivo
            st.dataframe(df_outfits[["Nombre Outfit", "Puestas", "Fecha Creación"]], use_container_width=True)
            
            # Buscador para ver la foto de un outfit específico
            outfit_nombre_ver = st.selectbox("Selecciona un outfit para ver la foto:", df_outfits['Nombre Outfit'])
            if outfit_nombre_ver:
                # Buscamos el enlace en el DataFrame
                fila_outfit = df_outfits[df_outfits['Nombre Outfit'] == outfit_nombre_ver].iloc[0]
                enlace_ver = fila_outfit['Enlace Foto']
                
                # Streamlit no puede mostrar fotos de Drive directamente con st.image(enlace)
                # Así que ponemos un botón que abre el enlace en una nueva pestaña.
                st.link_button(f"Ver foto de '{outfit_nombre_ver}' en Google Drive", enlace_ver)
                
                # Para la parte de "actualizar las puestas", esto es complejo con Sheets directamente.
                # Lo más fácil es abrir el Excel y cambiar el número a mano.
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
 elif seccion == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    st.write("Selecciona una categoría y el registro que deseas eliminar para siempre.")
    
    # 1. Elegir de dónde queremos borrar
    categorias = ["Diario", "Deporte", "Alimentación", "Lectura", "Ideas", "Viajes", "Outfits", "Pareja"]
    categoria_seleccionada = st.selectbox("Selecciona la categoría:", categorias)
    
    st.divider()
    
    # 2. Cargar y mostrar los datos
    df = cargar_datos(categoria_seleccionada)
    
    if not df.empty:
        # TRUCO: Calculamos el número de fila real en tu Google Sheets
        # En Pandas la primera fila es la 0. En Excel, la 1 es el título, así que los datos empiezan en la 2.
        # Por tanto: Fila de Excel = Índice de Pandas + 2
        df['Fila_Excel'] = df.index + 2 
        
        st.write("### Tus datos actuales:")
        # Mostramos la tabla para que puedas revisar qué hay
        st.dataframe(df, use_container_width=True)
        
        st.write("### Selecciona qué borrar")
        # Creamos una lista legible para el menú desplegable
        opciones_borrado = []
        for index, row in df.iterrows():
            # Extraemos los dos primeros datos para que sepas qué estás borrando (ej. Fecha y Título)
            valores = list(row.values())
            resumen = f"Fila {row['Fila_Excel']} ➔ {valores[0]} | {valores[1]}"
            opciones_borrado.append(resumen)
            
        seleccion = st.selectbox("Elige el registro a eliminar:", opciones_borrado)
        
        # 3. El botón peligroso
        if st.button("🚨 Eliminar Registro Definitivamente"):
            # Extraemos el número de fila del texto seleccionado
            # Si el texto es "Fila 3 ➔ 2024-04-02 | Correr", sacamos el "3"
            fila_a_borrar = int(seleccion.split(" ")[1])
            
            st.warning(f"Borrando fila {fila_a_borrar} de la nube...")
            if eliminar_registro(categoria_seleccionada, fila_a_borrar):
                st.success("¡Registro eliminado con éxito! Recarga la página o cambia de sección para ver tu base de datos limpia.")
            else:
                st.error("Hubo un problema al intentar borrar el registro.")
    else:
        st.info("Aún no tienes registros guardados en esta categoría.")           
