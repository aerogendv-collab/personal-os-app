import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseUpload
import json
import io
from datetime import date, datetime, timedelta

# --- CONFIGURACIÓN DE PÁGINA ---
# Añadimos initial_sidebar_state="collapsed" para que intente cerrarse/empezar cerrada
st.set_page_config(page_title="Mi Personal OS", page_icon="🚀", layout="wide", initial_sidebar_state="collapsed")

# ==========================================
# --- CONFIGURACIÓN DE GOOGLE ---
# ==========================================

FOLDER_ID_PHOTOS = "1CbBY4x3sdvBk5q9WTPlvMtWcO2jObL5L" 

@st.cache_resource
def obtener_credenciales_gcp():
    creds_dict = json.loads(st.secrets["gcp_service_account"])
    scope_sheets = ['https://spreadsheets.google.com/feeds', 'https://www.googleapis.com/auth/drive']
    scope_drive = ['https://www.googleapis.com/auth/drive']
    creds_sheets = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope_sheets)
    creds_drive = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope_drive)
    return creds_sheets, creds_drive

creds_sheets, creds_drive = obtener_credenciales_gcp()

try:
    client = gspread.authorize(creds_sheets)
    sheet = client.open("Mi_Personal_OS")
    db_conectada = True
except Exception as e:
    st.error(f"⚠️ Error de conexión a Base de Datos")
    db_conectada = False

def guardar_datos(nombre_pestaña, nuevos_datos):
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
        service = build('drive', 'v3', credentials=creds_drive)
        file_metadata = {'name': nombre_foto, 'parents': [FOLDER_ID_PHOTOS]}
        media = MediaIoBaseUpload(io.BytesIO(archivo_imagen.getvalue()), mimetype='image/jpeg')
        file = service.files().create(body=file_metadata, media_body=media, fields='id, webViewLink').execute()
        service.permissions().create(fileId=file.get('id'), body={'type': 'anyone', 'role': 'reader'}).execute()
        return file.get('webViewLink')
    except Exception as e:
        st.error(f"❌ Error al subir la foto a Drive")
        return None

# ==========================================
# --- FUNCIÓN REUTILIZABLE PARA HISTORIAL ---
# ==========================================
def mostrar_historial(nombre_pestaña):
    """Crea un desplegable automático con el historial de la sección actual."""
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
seccion = st.sidebar.radio("Navegación:", 
    ["🧠 Diario", "💪 Deporte", "🥗 Alimentación", "📚 Lectura", "💡 Ideas/Proyectos", "✈️ Viajes", "👔 Outfits", "✨ Pareja/Escapadas", "📈 Hábitos", "💰 Finanzas", "🗑️ Gestionar Datos"]
)

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
        
    if st.button("Registrar Hábito"):
        if habito_elegido:
            datos = {"Fecha": fecha_hoy, "Hábito": habito_elegido, "Estado": estado_habito}
            guardar_datos("Hábitos", datos)
            st.success("¡Hábito registrado!")
            st.rerun()

    st.divider()
    st.subheader("🔥 Tus Rachas y Estadísticas")
    
    if not df_habitos.empty and 'Hábito' in df_habitos.columns:
        # Lógica de cálculo de racha (días consecutivos)
        for hab in lista_habitos:
            df_h = df_habitos[df_habitos['Hábito'] == hab].copy()
            df_h['Fecha'] = pd.to_datetime(df_h['Fecha']).dt.date
            fechas_cumplidas = set(df_h[df_h['Estado'] == 'Cumplido ✅']['Fecha'])
            fechas_registradas = set(df_h['Fecha'])
            
            racha_actual = 0
            fecha_evaluar = date.today()
            
            # Si no lo hemos marcado hoy, empezamos a contar desde ayer
            if fecha_evaluar not in fechas_registradas:
                fecha_evaluar -= timedelta(days=1)
                
            while fecha_evaluar in fechas_cumplidas:
                racha_actual += 1
                fecha_evaluar -= timedelta(days=1)
                
            st.write(f"- **{hab}**: Racha activa de **{racha_actual}** días 🔥")

        st.write("📊 **Progreso de los últimos 7 días**")
        df_habitos['Fecha_Dt'] = pd.to_datetime(df_habitos['Fecha'])
        hace_7_dias = pd.to_datetime(date.today() - timedelta(days=7))
        df_ultimos = df_habitos[(df_habitos['Fecha_Dt'] >= hace_7_dias) & (df_habitos['Estado'] == 'Cumplido ✅')]
        
        if not df_ultimos.empty:
            conteo = df_ultimos.groupby([df_ultimos['Fecha_Dt'].dt.strftime('%Y-%m-%d'), 'Hábito']).size().unstack(fill_value=0)
            st.bar_chart(conteo)
        else:
            st.info("Aún no hay hábitos cumplidos en los últimos 7 días.")
            
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

elif seccion == "🗑️ Gestionar Datos":
    st.title("🗑️ Eliminar Registros")
    st.write("Selecciona una categoría y el registro que deseas eliminar para siempre.")
    
    categorias = ["Diario", "Deporte", "Alimentación", "Lectura", "Ideas", "Viajes", "Outfits", "Pareja", "Hábitos", "Finanzas"]
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
